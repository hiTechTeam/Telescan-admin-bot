import asyncio
import logging

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError

from src.api_client import ModerationAPIClient
from src.errors import ModerationAPIError
from src.keyboards import notification_keyboard
from src.models import ReportStatus
from src.presentation import report_notification
from src.storage import NotificationStore

logger = logging.getLogger(__name__)


class ReportNotifier:
    def __init__(
        self,
        bot: Bot,
        api: ModerationAPIClient,
        store: NotificationStore,
        admin_ids: set[int],
        interval_seconds: float,
    ) -> None:
        self._bot = bot
        self._api = api
        self._store = store
        self._admin_ids = admin_ids
        self._interval = interval_seconds

    async def run(self, stop: asyncio.Event) -> None:
        while not stop.is_set():
            try:
                await self._poll_once()
            except Exception:
                logger.exception("Unexpected report notifier failure")
            try:
                await asyncio.wait_for(stop.wait(), timeout=self._interval)
            except TimeoutError:
                pass

    async def _poll_once(self) -> None:
        try:
            reports = await self._api.list_reports(ReportStatus.PENDING)
        except ModerationAPIError:
            logger.exception("Could not poll pending reports")
            return

        for report in reversed(reports):
            for admin_id in self._admin_ids:
                if await self._store.was_notified(report.report_id, admin_id):
                    continue
                try:
                    await self._bot.send_message(
                        admin_id,
                        report_notification(report),
                        reply_markup=notification_keyboard(report),
                    )
                except TelegramAPIError:
                    logger.exception(
                        "Could not notify Telegram admin %s",
                        admin_id,
                    )
                    continue
                await self._store.mark_notified(report.report_id, admin_id)
