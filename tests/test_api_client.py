from uuid import uuid4

import pytest
from aiohttp import web
from aiohttp.test_utils import TestServer

from src.api_client import ModerationAPIClient
from src.models import ReportStatus


@pytest.mark.asyncio
async def test_client_lists_and_updates_reports_with_service_auth() -> None:
    report_id = uuid4()
    target_id = uuid4()
    reporter_id = uuid4()
    calls: list[tuple[str, str, object]] = []

    def payload(status: str) -> dict[str, object]:
        return {
            "reportId": str(report_id),
            "reporterTelescanId": str(reporter_id),
            "targetTelescanId": str(target_id),
            "reason": "spam",
            "details": None,
            "targetName": "Target",
            "targetUsername": "target",
            "targetBio": "Open to networking",
            "targetPhotoUrl": None,
            "targetPhotoEvidenceStatus": "absent",
            "status": status,
            "createdAt": "2026-08-16T12:00:00Z",
            "updatedAt": "2026-08-16T12:00:00Z",
            "resolvedAt": None,
            "retentionUntil": None,
            "moderatorId": None,
            "moderatorNote": None,
            "revision": 0,
        }

    async def list_reports(request: web.Request) -> web.Response:
        calls.append(
            (
                request.method,
                request.headers.get("Authorization", ""),
                dict(request.query),
            )
        )
        return web.json_response([payload("pending")])

    async def update_report(request: web.Request) -> web.Response:
        body = await request.json()
        calls.append(
            (
                request.method,
                request.headers.get("Authorization", ""),
                body,
            )
        )
        return web.json_response(payload(body["status"]))

    application = web.Application()
    application.router.add_get(
        "/internal/v1/moderation/reports",
        list_reports,
    )
    application.router.add_patch(
        "/internal/v1/moderation/reports/{report_id}",
        update_report,
    )
    server = TestServer(application)
    await server.start_server()
    client = ModerationAPIClient(
        str(server.make_url("/")).rstrip("/"),
        "service-secret-value-that-is-long-enough",
        2,
    )

    try:
        reports = await client.list_reports(ReportStatus.PENDING)
        updated = await client.update_report(
            report_id,
            ReportStatus.REVIEWING,
            "telegram:2045659349",
            "checking",
            revision=0,
        )
    finally:
        await client.close()
        await server.close()

    assert reports[0].report_id == report_id
    assert reports[0].target_bio == "Open to networking"
    assert updated.status == ReportStatus.REVIEWING
    assert [call[0] for call in calls] == ["GET", "PATCH"]
    assert all(
        call[1] == "Bearer service-secret-value-that-is-long-enough" for call in calls
    )
    assert calls[0][2] == {"status": "pending", "limit": "100"}
    assert calls[1][2] == {
        "status": "reviewing",
        "moderatorId": "telegram:2045659349",
        "note": "checking",
        "revision": 0,
    }
