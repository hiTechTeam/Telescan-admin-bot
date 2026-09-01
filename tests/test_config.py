from pathlib import Path

import pytest
from pydantic import ValidationError

from src.config import Settings


def test_admin_ids_are_parsed_from_environment_format(monkeypatch) -> None:
    monkeypatch.setenv("ADMIN_TELEGRAM_IDS", "2045659349, 42")
    settings = Settings()

    assert settings.admin_telegram_ids == [2045659349, 42]


def test_production_rejects_default_moderation_secret() -> None:
    with pytest.raises(ValidationError, match="MODERATION_SERVICE_SECRET"):
        Settings(
            environment="production",
            bot_token="123456:valid-looking-token",
            admin_telegram_ids=[2045659349],
        )


@pytest.mark.parametrize(
    "api_base_url",
    [
        "https://api.tgtelescan.ru",
        "http://telescan-api:8000?redirect=evil",
    ],
)
def test_production_uses_private_api_network(api_base_url: str) -> None:
    with pytest.raises(ValidationError, match="private Docker network"):
        Settings(
            environment="production",
            bot_token="123456:valid-looking-token",
            admin_telegram_ids=[2045659349],
            moderation_service_secret="s" * 32,
            api_base_url=api_base_url,
        )


@pytest.mark.parametrize(
    "token",
    [
        "",
        "replace-token",
        "development-token",
        "change-me-token",
        "not-a-telegram-token",
    ],
)
def test_production_rejects_missing_or_placeholder_bot_token(token: str) -> None:
    with pytest.raises(ValidationError, match="BOT_TOKEN"):
        Settings(
            environment="production",
            bot_token=token,
            admin_telegram_ids=[2045659349],
            moderation_service_secret="s" * 32,
        )


def test_deploy_dispatches_durable_locked_controller_with_rollback() -> None:
    repository = Path(__file__).resolve().parents[1]
    workflow = (repository / ".github/workflows/deploy.yml").read_text(encoding="utf-8")
    controller = (repository / "ops/deploy-production.sh").read_text(encoding="utf-8")

    assert ".releases/Telescan-admin-bot/" in workflow
    assert "sudo systemd-run --wait --collect" in workflow
    main = controller[controller.index("main() {") :]
    assert main.index("flock -w 1800 9") < main.index('deploy_release "$2" "$3"')
    assert '"$snapshot_dir/" "$ACTIVE_DIR/"' in controller
    assert "protected previous release did not recover healthy" in controller
    assert "intent phase --expected prepared --new committed" in controller
    assert '"$container_id" != "$global_ids"' in controller
