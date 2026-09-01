from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ReportReason(StrEnum):
    SPAM = "spam"
    HARASSMENT = "harassment"
    INAPPROPRIATE = "inappropriate"
    IMPERSONATION = "impersonation"
    OTHER = "other"


class ReportStatus(StrEnum):
    PENDING = "pending"
    REVIEWING = "reviewing"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"


class ReportPhotoEvidenceStatus(StrEnum):
    AVAILABLE = "available"
    ABSENT = "absent"
    COPY_FAILED = "copy_failed"


class ModerationReport(BaseModel):
    report_id: UUID = Field(alias="reportId")
    reporter_telescan_id: UUID | None = Field(
        default=None,
        alias="reporterTelescanId",
    )
    target_telescan_id: UUID = Field(alias="targetTelescanId")
    reason: ReportReason
    details: str | None = None
    target_name: str | None = Field(default=None, alias="targetName")
    target_username: str | None = Field(default=None, alias="targetUsername")
    target_bio: str | None = Field(default=None, alias="targetBio")
    target_photo_url: str | None = Field(default=None, alias="targetPhotoUrl")
    target_photo_evidence_status: ReportPhotoEvidenceStatus = Field(
        default=ReportPhotoEvidenceStatus.ABSENT,
        alias="targetPhotoEvidenceStatus",
    )
    status: ReportStatus
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")
    resolved_at: datetime | None = Field(default=None, alias="resolvedAt")
    retention_until: datetime | None = Field(default=None, alias="retentionUntil")
    moderator_id: str | None = Field(default=None, alias="moderatorId")
    moderator_note: str | None = Field(default=None, alias="moderatorNote")
    revision: int = 0

    model_config = ConfigDict(populate_by_name=True)


class ModerationDecision(BaseModel):
    status: ReportStatus
    moderator_id: str = Field(alias="moderatorId", min_length=1, max_length=100)
    note: str | None = Field(default=None, max_length=1000)
    revision: int | None = Field(default=None, ge=0)

    model_config = ConfigDict(populate_by_name=True)
