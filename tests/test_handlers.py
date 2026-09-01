from typing import cast
from uuid import uuid4

import pytest

from src.api_client import ModerationAPIClient
from src.errors import ModerationAPIError
from src.handlers import _submit_confirmed_decision
from src.models import ReportStatus

NOTE_UNSET = object()


class StaleAPI:
    def __init__(self) -> None:
        self.get_calls = 0
        self.update_revisions: list[int | None] = []

    async def get_report(self, _report_id):
        self.get_calls += 1
        raise AssertionError("confirmation must not refresh the card revision")

    async def update_report(
        self,
        _report_id,
        _status,
        _moderator_id,
        _note: object = NOTE_UNSET,
        revision: int | None = None,
    ) -> None:
        self.update_revisions.append(revision)
        raise ModerationAPIError(409, "stale revision")


@pytest.mark.asyncio
async def test_stale_confirmation_submits_original_revision_without_refetch() -> None:
    api = StaleAPI()

    with pytest.raises(ModerationAPIError, match="stale revision"):
        await _submit_confirmed_decision(
            cast(ModerationAPIClient, api),
            uuid4(),
            ReportStatus.RESOLVED,
            "telegram:42",
            revision=3,
        )

    assert api.get_calls == 0
    assert api.update_revisions == [3]
