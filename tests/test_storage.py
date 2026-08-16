from uuid import uuid4

import pytest

from src.storage import NotificationStore


@pytest.mark.asyncio
async def test_notification_store_persists_per_admin(tmp_path) -> None:
    database = tmp_path / "notifications.sqlite3"
    report_id = uuid4()
    first = NotificationStore(str(database))
    await first.initialize()

    assert not await first.was_notified(report_id, 1)
    await first.mark_notified(report_id, 1)
    await first.mark_notified(report_id, 1)
    assert await first.was_notified(report_id, 1)
    assert not await first.was_notified(report_id, 2)

    restarted = NotificationStore(str(database))
    await restarted.initialize()
    assert await restarted.was_notified(report_id, 1)
