import asyncio
import sqlite3
from pathlib import Path
from uuid import UUID


class NotificationStore:
    def __init__(self, database_path: str) -> None:
        self._path = Path(database_path)

    async def initialize(self) -> None:
        await asyncio.to_thread(self._initialize_sync)

    async def was_notified(self, report_id: UUID, admin_id: int) -> bool:
        return await asyncio.to_thread(
            self._was_notified_sync,
            str(report_id),
            admin_id,
        )

    async def mark_notified(self, report_id: UUID, admin_id: int) -> None:
        await asyncio.to_thread(
            self._mark_notified_sync,
            str(report_id),
            admin_id,
        )

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self._path)
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("PRAGMA busy_timeout=5000")
        return connection

    def _initialize_sync(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS sent_notifications (
                    report_id TEXT NOT NULL,
                    admin_id INTEGER NOT NULL,
                    sent_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (report_id, admin_id)
                )
                """
            )

    def _was_notified_sync(self, report_id: str, admin_id: int) -> bool:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT 1
                FROM sent_notifications
                WHERE report_id = ? AND admin_id = ?
                """,
                (report_id, admin_id),
            ).fetchone()
        return row is not None

    def _mark_notified_sync(self, report_id: str, admin_id: int) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT OR IGNORE INTO sent_notifications (report_id, admin_id)
                VALUES (?, ?)
                """,
                (report_id, admin_id),
            )
