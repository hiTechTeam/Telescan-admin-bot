from typing import Annotated
from urllib.parse import urlsplit

from pydantic import BeforeValidator, Field, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


def _parse_admin_ids(value: object) -> object:
    if isinstance(value, str):
        return [item.strip() for item in value.split(",") if item.strip()]
    return value


AdminIDs = Annotated[list[int], NoDecode, BeforeValidator(_parse_admin_ids)]


class Settings(BaseSettings):
    environment: str = "development"
    bot_token: str = ""
    admin_telegram_ids: AdminIDs = Field(default_factory=list)
    telegram_proxy_url: str | None = None

    api_base_url: str = "http://telescan-api:8000"
    moderation_service_secret: str = Field(
        default="development-moderation-secret-change-me",
        min_length=32,
    )
    api_timeout_seconds: float = Field(default=15, gt=0, le=30)
    report_poll_interval_seconds: float = Field(default=30, ge=10, le=300)

    internal_host: str = "0.0.0.0"
    internal_port: int = Field(default=8080, ge=1, le=65535)
    database_path: str = "/data/notifications.sqlite3"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @model_validator(mode="after")
    def validate_runtime(self) -> "Settings":
        if not self.admin_telegram_ids:
            raise ValueError("ADMIN_TELEGRAM_IDS must contain at least one ID")
        if any(admin_id <= 0 for admin_id in self.admin_telegram_ids):
            raise ValueError("ADMIN_TELEGRAM_IDS must contain positive IDs")
        if len(set(self.admin_telegram_ids)) != len(self.admin_telegram_ids):
            raise ValueError("ADMIN_TELEGRAM_IDS must not contain duplicates")
        if self.environment.lower() == "production":
            if not self.bot_token:
                raise ValueError("BOT_TOKEN is required")
            if self.moderation_service_secret.startswith(
                "development-"
            ) or self.moderation_service_secret.startswith("replace-"):
                raise ValueError("MODERATION_SERVICE_SECRET must be configured")
            api_url = urlsplit(self.api_base_url)
            if (
                api_url.scheme != "http"
                or api_url.hostname != "telescan-api"
                or api_url.port != 8000
                or api_url.username is not None
                or api_url.password is not None
                or api_url.path not in {"", "/"}
            ):
                raise ValueError("Production API must use the private Docker network")
        return self


__all__ = ["Settings"]
