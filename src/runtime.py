import asyncio
import contextlib
import logging

from aiogram import Dispatcher
from aiogram.types import BotCommand

from src.api_client import ModerationAPIClient
from src.config import Settings
from src.handlers import build_router
from src.health import start_health_server
from src.notifier import ReportNotifier
from src.storage import NotificationStore
from src.telegram import create_bot

logger = logging.getLogger(__name__)


async def run(settings: Settings) -> None:
    admin_ids = set(settings.admin_telegram_ids)
    bot = create_bot(settings)
    dispatcher = Dispatcher()
    api = ModerationAPIClient(
        settings.api_base_url,
        settings.moderation_service_secret,
        settings.api_timeout_seconds,
    )
    store = NotificationStore(settings.database_path)
    await store.initialize()
    dispatcher.include_router(build_router(api, admin_ids))
    notifier = ReportNotifier(
        bot,
        api,
        store,
        admin_ids,
        settings.report_poll_interval_seconds,
    )
    stop = asyncio.Event()
    notifier_task: asyncio.Task[None] | None = None
    health_runner = await start_health_server(
        settings.internal_host,
        settings.internal_port,
    )

    try:
        await api.start()
        await bot.delete_webhook(drop_pending_updates=False)
        await bot.set_my_commands(
            [
                BotCommand(command="start", description="Открыть меню"),
                BotCommand(command="reports", description="Новые жалобы"),
                BotCommand(command="cancel", description="Отменить ввод"),
            ]
        )
        notifier_task = asyncio.create_task(
            notifier.run(stop),
            name="report-notifier",
        )
        logger.info("Starting Telescan admin bot for %d admin(s)", len(admin_ids))
        await dispatcher.start_polling(bot, close_bot_session=False)
    finally:
        stop.set()
        if notifier_task is not None:
            with contextlib.suppress(asyncio.CancelledError):
                await notifier_task
        await api.close()
        await bot.session.close()
        await health_runner.cleanup()
