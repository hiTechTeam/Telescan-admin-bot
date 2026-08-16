import logging
from uuid import UUID

from aiogram import F, Router
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message

from src.api_client import ModerationAPIClient
from src.errors import ModerationAPIError
from src.keyboards import (
    PAGE_SIZE,
    ReportActionCallback,
    ReportConfirmCallback,
    ReportListCallback,
    ReportOpenCallback,
    confirmation_keyboard,
    main_menu_keyboard,
    report_keyboard,
    reports_keyboard,
)
from src.middleware import AdminOnlyMiddleware
from src.models import ReportStatus
from src.presentation import report_card, report_list_title

logger = logging.getLogger(__name__)


class ModerationStates(StatesGroup):
    waiting_for_note = State()


def build_router(api: ModerationAPIClient, admin_ids: set[int]) -> Router:
    router = Router(name="moderation")
    router.message.outer_middleware(AdminOnlyMiddleware(admin_ids))
    router.callback_query.outer_middleware(AdminOnlyMiddleware(admin_ids))

    @router.message(CommandStart())
    @router.message(Command("menu"))
    async def start(message: Message, state: FSMContext) -> None:
        await state.clear()
        await message.answer(
            "<b>Telescan Admin</b>\n\n"
            "Закрытый интерфейс обработки жалоб. Доступ подтверждён.",
            reply_markup=main_menu_keyboard(),
        )

    @router.message(Command("reports"))
    async def reports_command(message: Message, state: FSMContext) -> None:
        await state.clear()
        try:
            reports = await api.list_reports(ReportStatus.PENDING)
        except ModerationAPIError:
            logger.exception("Could not load reports")
            await message.answer("API модерации временно недоступен.")
            return
        await message.answer(
            report_list_title(ReportStatus.PENDING, len(reports)),
            reply_markup=reports_keyboard(reports, ReportStatus.PENDING, 0),
        )

    @router.message(Command("cancel"))
    async def cancel_note(message: Message, state: FSMContext) -> None:
        await state.clear()
        await message.answer("Ввод заметки отменён.", reply_markup=main_menu_keyboard())

    @router.callback_query(F.data == "menu")
    async def menu_callback(callback: CallbackQuery, state: FSMContext) -> None:
        await state.clear()
        await _edit_callback(
            callback,
            "<b>Telescan Admin</b>\n\nВыберите очередь жалоб.",
            main_menu_keyboard(),
        )

    @router.callback_query(ReportListCallback.filter())
    async def list_callback(
        callback: CallbackQuery,
        callback_data: ReportListCallback,
        state: FSMContext,
    ) -> None:
        await state.clear()
        status = ReportStatus(callback_data.status)
        try:
            reports = await api.list_reports(status)
        except ModerationAPIError:
            logger.exception("Could not load %s reports", status)
            await callback.answer("API модерации недоступен", show_alert=True)
            return
        maximum_page = max(0, (len(reports) - 1) // PAGE_SIZE)
        page = min(callback_data.page, maximum_page)
        await _edit_callback(
            callback,
            report_list_title(status, len(reports)),
            reports_keyboard(reports, status, page),
        )

    @router.callback_query(ReportOpenCallback.filter())
    async def open_callback(
        callback: CallbackQuery,
        callback_data: ReportOpenCallback,
    ) -> None:
        try:
            report = await api.get_report(UUID(callback_data.report_id))
        except (ValueError, ModerationAPIError):
            logger.exception("Could not load report %s", callback_data.report_id)
            await callback.answer("Жалоба недоступна", show_alert=True)
            return
        origin_status = ReportStatus(callback_data.origin_status)
        await _edit_callback(
            callback,
            report_card(report),
            report_keyboard(report, origin_status, callback_data.origin_page),
        )

    @router.callback_query(ReportActionCallback.filter())
    async def action_callback(
        callback: CallbackQuery,
        callback_data: ReportActionCallback,
        state: FSMContext,
    ) -> None:
        if callback.from_user is None:
            return
        report_id = UUID(callback_data.report_id)
        origin_status = ReportStatus(callback_data.origin_status)
        if callback_data.action == "review":
            try:
                report = await api.update_report(
                    report_id,
                    ReportStatus.REVIEWING,
                    _moderator_id(callback.from_user.id),
                )
            except ModerationAPIError:
                logger.exception("Could not claim report %s", report_id)
                await callback.answer("Не удалось обновить жалобу", show_alert=True)
                return
            await _edit_callback(
                callback,
                report_card(report),
                report_keyboard(report, origin_status, callback_data.origin_page),
            )
            return

        if callback_data.action == "note":
            try:
                report = await api.get_report(report_id)
            except ModerationAPIError:
                await callback.answer("Жалоба недоступна", show_alert=True)
                return
            if report.status not in {ReportStatus.PENDING, ReportStatus.REVIEWING}:
                await callback.answer("Решение по жалобе уже принято", show_alert=True)
                return
            await state.set_state(ModerationStates.waiting_for_note)
            await state.set_data(
                {
                    "report_id": str(report_id),
                    "status": report.status.value,
                    "origin_status": origin_status.value,
                    "origin_page": callback_data.origin_page,
                }
            )
            await callback.answer()
            if isinstance(callback.message, Message):
                await callback.message.answer(
                    "Отправьте заметку модератора одним сообщением "
                    "(до 1000 символов). Для отмены: /cancel"
                )
            return

        decision = "r" if callback_data.action == "resolve" else "d"
        decision_text = "решить" if decision == "r" else "отклонить"
        await _edit_callback(
            callback,
            f"Подтвердите действие: <b>{decision_text} жалобу</b>.",
            confirmation_keyboard(
                decision,
                callback_data.report_id,
                callback_data.origin_status,
                callback_data.origin_page,
            ),
        )

    @router.callback_query(ReportConfirmCallback.filter())
    async def confirm_callback(
        callback: CallbackQuery,
        callback_data: ReportConfirmCallback,
    ) -> None:
        if callback.from_user is None:
            return
        status = (
            ReportStatus.RESOLVED
            if callback_data.decision == "r"
            else ReportStatus.DISMISSED
        )
        try:
            report = await api.update_report(
                UUID(callback_data.report_id),
                status,
                _moderator_id(callback.from_user.id),
            )
        except (ValueError, ModerationAPIError):
            logger.exception("Could not decide report %s", callback_data.report_id)
            await callback.answer("Не удалось сохранить решение", show_alert=True)
            return
        origin_status = ReportStatus(callback_data.origin_status)
        await _edit_callback(
            callback,
            report_card(report),
            report_keyboard(report, origin_status, callback_data.origin_page),
        )

    @router.message(ModerationStates.waiting_for_note, F.text)
    async def save_note(message: Message, state: FSMContext) -> None:
        if message.from_user is None or message.text is None:
            return
        note = message.text.strip()
        if not note or len(note) > 1000:
            await message.answer("Заметка должна содержать от 1 до 1000 символов.")
            return
        data = await state.get_data()
        current_status = ReportStatus(str(data["status"]))
        next_status = (
            ReportStatus.REVIEWING
            if current_status == ReportStatus.PENDING
            else current_status
        )
        try:
            report = await api.update_report(
                UUID(str(data["report_id"])),
                next_status,
                _moderator_id(message.from_user.id),
                note,
            )
        except (ValueError, ModerationAPIError):
            logger.exception("Could not save moderation note")
            await message.answer("Не удалось сохранить заметку. Попробуйте ещё раз.")
            return
        await state.clear()
        origin_status = ReportStatus(str(data["origin_status"]))
        await message.answer(
            report_card(report),
            reply_markup=report_keyboard(
                report,
                origin_status,
                int(data["origin_page"]),
            ),
        )

    return router


def _moderator_id(telegram_id: int) -> str:
    return f"telegram:{telegram_id}"


async def _edit_callback(
    callback: CallbackQuery,
    text: str,
    reply_markup: InlineKeyboardMarkup,
) -> None:
    try:
        if isinstance(callback.message, Message):
            await callback.message.edit_text(
                text,
                parse_mode=ParseMode.HTML,
                reply_markup=reply_markup,
            )
        await callback.answer()
    except TelegramBadRequest as error:
        if "message is not modified" in str(error).lower():
            await callback.answer()
            return
        raise
