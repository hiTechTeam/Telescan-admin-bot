from collections.abc import Sequence

from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.models import ModerationReport, ReportStatus
from src.presentation import STATUS_ICONS, STATUS_LABELS, report_button_title

PAGE_SIZE = 6


class ReportListCallback(CallbackData, prefix="lst"):
    status: str
    page: int


class ReportOpenCallback(CallbackData, prefix="rpt"):
    report_id: str
    origin_status: str
    origin_page: int


class ReportActionCallback(CallbackData, prefix="act"):
    action: str
    report_id: str
    origin_status: str
    origin_page: int


class ReportConfirmCallback(CallbackData, prefix="cfm"):
    decision: str
    report_id: str
    origin_status: str
    origin_page: int


def main_menu_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text="🆕 Новые жалобы",
        callback_data=ReportListCallback(
            status=ReportStatus.PENDING.value,
            page=0,
        ),
    )
    builder.button(
        text="🔎 В работе",
        callback_data=ReportListCallback(
            status=ReportStatus.REVIEWING.value,
            page=0,
        ),
    )
    builder.adjust(1)
    return builder.as_markup()


def reports_keyboard(
    reports: Sequence[ModerationReport],
    status: ReportStatus,
    page: int,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    start = page * PAGE_SIZE
    page_items = reports[start : start + PAGE_SIZE]
    for report in page_items:
        builder.button(
            text=report_button_title(report),
            callback_data=ReportOpenCallback(
                report_id=str(report.report_id),
                origin_status=status.value,
                origin_page=page,
            ),
        )
    builder.adjust(1)

    navigation: list[InlineKeyboardButton] = []
    if page > 0:
        navigation.append(
            InlineKeyboardButton(
                text="←",
                callback_data=ReportListCallback(
                    status=status.value,
                    page=page - 1,
                ).pack(),
            )
        )
    if start + PAGE_SIZE < len(reports):
        navigation.append(
            InlineKeyboardButton(
                text="→",
                callback_data=ReportListCallback(
                    status=status.value,
                    page=page + 1,
                ).pack(),
            )
        )
    if navigation:
        builder.row(*navigation)

    builder.row(
        *[
            InlineKeyboardButton(
                text=f"{STATUS_ICONS[item]} {STATUS_LABELS[item]}",
                callback_data=ReportListCallback(status=item.value, page=0).pack(),
            )
            for item in ReportStatus
        ],
        width=2,
    )
    builder.row(InlineKeyboardButton(text="🏠 Меню", callback_data="menu"))
    return builder.as_markup()


def report_keyboard(
    report: ModerationReport,
    origin_status: ReportStatus,
    origin_page: int,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    common = {
        "report_id": str(report.report_id),
        "origin_status": origin_status.value,
        "origin_page": origin_page,
    }
    if report.status == ReportStatus.PENDING:
        builder.button(
            text="🔎 Взять в работу",
            callback_data=ReportActionCallback(action="review", **common),
        )
    if report.status in {ReportStatus.PENDING, ReportStatus.REVIEWING}:
        builder.button(
            text="✍️ Добавить заметку",
            callback_data=ReportActionCallback(action="note", **common),
        )
        builder.button(
            text="✅ Решить",
            callback_data=ReportActionCallback(action="resolve", **common),
        )
        builder.button(
            text="🚫 Отклонить",
            callback_data=ReportActionCallback(action="dismiss", **common),
        )
    builder.adjust(1, 1, 2)
    if report.target_photo_url and report.target_photo_url.startswith("https://"):
        builder.row(
            InlineKeyboardButton(text="🖼 Фото профиля", url=report.target_photo_url)
        )
    builder.row(
        InlineKeyboardButton(
            text="↻ Обновить",
            callback_data=ReportOpenCallback(**common).pack(),
        ),
        InlineKeyboardButton(
            text="← К списку",
            callback_data=ReportListCallback(
                status=origin_status.value,
                page=origin_page,
            ).pack(),
        ),
    )
    return builder.as_markup()


def confirmation_keyboard(
    decision: str,
    report_id: str,
    origin_status: str,
    origin_page: int,
) -> InlineKeyboardMarkup:
    label = "✅ Подтвердить решение" if decision == "r" else "🚫 Подтвердить"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=label,
                    callback_data=ReportConfirmCallback(
                        decision=decision,
                        report_id=report_id,
                        origin_status=origin_status,
                        origin_page=origin_page,
                    ).pack(),
                )
            ],
            [
                InlineKeyboardButton(
                    text="Отмена",
                    callback_data=ReportOpenCallback(
                        report_id=report_id,
                        origin_status=origin_status,
                        origin_page=origin_page,
                    ).pack(),
                )
            ],
        ]
    )


def notification_keyboard(report: ModerationReport) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Открыть жалобу",
                    callback_data=ReportOpenCallback(
                        report_id=str(report.report_id),
                        origin_status=ReportStatus.PENDING.value,
                        origin_page=0,
                    ).pack(),
                )
            ]
        ]
    )
