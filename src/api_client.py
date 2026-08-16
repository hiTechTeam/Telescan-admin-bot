from collections.abc import Mapping
from types import TracebackType
from uuid import UUID

import aiohttp

from src.errors import ModerationAPIError, ReportNotFound
from src.models import ModerationDecision, ModerationReport, ReportStatus


class ModerationAPIClient:
    def __init__(
        self,
        base_url: str,
        service_secret: str,
        timeout_seconds: float,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._headers = {"Authorization": f"Bearer {service_secret}"}
        self._timeout = aiohttp.ClientTimeout(total=timeout_seconds)
        self._session: aiohttp.ClientSession | None = None

    async def __aenter__(self) -> "ModerationAPIClient":
        await self.start()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        await self.close()

    async def start(self) -> None:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                headers=self._headers,
                timeout=self._timeout,
            )

    async def close(self) -> None:
        if self._session is not None:
            await self._session.close()
            self._session = None

    async def list_reports(
        self,
        status: ReportStatus,
        limit: int = 100,
    ) -> list[ModerationReport]:
        payload = await self._request_json(
            "GET",
            "/internal/v1/moderation/reports",
            params={"status": status.value, "limit": str(limit)},
        )
        if not isinstance(payload, list):
            raise ModerationAPIError(502, "Moderation API returned an invalid list")
        return [ModerationReport.model_validate(item) for item in payload]

    async def get_report(self, report_id: UUID) -> ModerationReport:
        payload = await self._request_json(
            "GET",
            f"/internal/v1/moderation/reports/{report_id}",
        )
        return ModerationReport.model_validate(payload)

    async def update_report(
        self,
        report_id: UUID,
        status: ReportStatus,
        moderator_id: str,
        note: str | None = None,
    ) -> ModerationReport:
        decision = ModerationDecision.model_validate(
            {
                "status": status,
                "moderatorId": moderator_id,
                "note": note,
            }
        )
        payload = await self._request_json(
            "PATCH",
            f"/internal/v1/moderation/reports/{report_id}",
            json=decision.model_dump(by_alias=True, mode="json"),
        )
        return ModerationReport.model_validate(payload)

    async def _request_json(
        self,
        method: str,
        path: str,
        params: Mapping[str, str] | None = None,
        json: Mapping[str, object] | None = None,
    ) -> object:
        await self.start()
        if self._session is None:
            raise RuntimeError("HTTP session did not start")
        try:
            async with self._session.request(
                method,
                f"{self._base_url}{path}",
                params=params,
                json=json,
            ) as response:
                if response.status == 404:
                    raise ReportNotFound(404, "Report not found")
                if not 200 <= response.status < 300:
                    body = (await response.text())[:500]
                    raise ModerationAPIError(
                        response.status,
                        f"Moderation API returned {response.status}: {body}",
                    )
                return await response.json()
        except TimeoutError as error:
            raise ModerationAPIError(504, "Moderation API timed out") from error
        except aiohttp.ClientError as error:
            raise ModerationAPIError(503, "Moderation API is unavailable") from error
