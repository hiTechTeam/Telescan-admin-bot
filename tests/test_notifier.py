from types import SimpleNamespace
from typing import Any, cast
from unittest.mock import AsyncMock

import pytest
from aiogram import Bot

from src.api_client import ModerationAPIClient
from src.notifier import ReportNotifier
from src.storage import NotificationStore
from tests.test_presentation import make_report


class FakeAPI:
    def __init__(self) -> None:
        self.list_reports = AsyncMock(return_value=[make_report()])


@pytest.mark.asyncio
async def test_notifier_sends_each_report_once_per_admin(tmp_path) -> None:
    bot = cast(Bot, cast(Any, SimpleNamespace(send_message=AsyncMock())))
    api = cast(ModerationAPIClient, cast(Any, FakeAPI()))
    store = NotificationStore(str(tmp_path / "notifications.sqlite3"))
    await store.initialize()
    notifier = ReportNotifier(bot, api, store, {1, 2}, 30)

    await notifier._poll_once()
    await notifier._poll_once()

    assert cast(AsyncMock, bot.send_message).await_count == 2
