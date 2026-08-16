import pytest
from pydantic import ValidationError

from src.config import Settings


def test_admin_ids_are_parsed_from_environment_format() -> None:
    settings = Settings(
        admin_telegram_ids="2045659349, 42",  # type: ignore[arg-type]
    )

    assert settings.admin_telegram_ids == [2045659349, 42]


def test_production_rejects_default_moderation_secret() -> None:
    with pytest.raises(ValidationError, match="MODERATION_SERVICE_SECRET"):
        Settings(
            environment="production",
            bot_token="123456:valid-looking-token",
            admin_telegram_ids=[2045659349],
        )


def test_production_uses_private_api_network() -> None:
    with pytest.raises(ValidationError, match="private Docker network"):
        Settings(
            environment="production",
            bot_token="123456:valid-looking-token",
            admin_telegram_ids=[2045659349],
            moderation_service_secret="s" * 32,
            api_base_url="https://api.tgtelescan.ru",
        )
