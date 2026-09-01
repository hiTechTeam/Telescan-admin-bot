from datetime import UTC, datetime
from uuid import uuid4

from src.keyboards import (
    ReportActionCallback,
    ReportConfirmCallback,
    confirmation_keyboard,
    report_keyboard,
    reports_keyboard,
)
from src.models import (
    ModerationReport,
    ReportPhotoEvidenceStatus,
    ReportReason,
    ReportStatus,
)
from src.presentation import report_button_title, report_card


def make_report(status: ReportStatus = ReportStatus.PENDING) -> ModerationReport:
    now = datetime.now(UTC)
    return ModerationReport(
        reportId=uuid4(),
        reporterTelescanId=uuid4(),
        targetTelescanId=uuid4(),
        reason=ReportReason.HARASSMENT,
        details="<script>unsafe</script>",
        targetName="Ada & Bob",
        targetUsername="nearby",
        targetBio="iOS engineer & organizer",
        targetPhotoUrl="https://storage.example/photo.jpg",
        targetPhotoEvidenceStatus=ReportPhotoEvidenceStatus.AVAILABLE,
        status=status,
        createdAt=now,
        updatedAt=now,
        revision=7,
    )


def test_report_card_escapes_user_controlled_text() -> None:
    text = report_card(make_report())

    assert "<script>" not in text
    assert "&lt;script&gt;unsafe&lt;/script&gt;" in text
    assert "Ada &amp; Bob" in text
    assert "iOS engineer &amp; organizer" in text
    assert "Фото-доказательство:</b> сохранено" in text


def test_callback_payloads_fit_telegram_limit() -> None:
    report = make_report()
    keyboards = [
        reports_keyboard([report], ReportStatus.PENDING, 0),
        report_keyboard(report, ReportStatus.PENDING, 0),
    ]

    callback_data = [
        button.callback_data
        for keyboard in keyboards
        for row in keyboard.inline_keyboard
        for button in row
        if button.callback_data
    ]
    assert callback_data
    assert all(len(value.encode()) <= 64 for value in callback_data)


def test_card_revision_is_frozen_in_action_and_confirmation_callbacks() -> None:
    report = make_report()
    keyboard = report_keyboard(report, ReportStatus.PENDING, 0)
    action_payload = next(
        button.callback_data
        for row in keyboard.inline_keyboard
        for button in row
        if button.text == "✅ Решить"
    )
    assert action_payload is not None
    action = ReportActionCallback.unpack(action_payload)
    assert action.revision == 7

    confirmation = confirmation_keyboard(
        "r",
        str(report.report_id),
        ReportStatus.PENDING.value,
        0,
        action.revision,
    )
    confirm_payload = confirmation.inline_keyboard[0][0].callback_data
    assert confirm_payload is not None
    confirm = ReportConfirmCallback.unpack(confirm_payload)
    assert confirm.revision == 7


def test_universal_report_uses_clear_moderation_label() -> None:
    report = make_report()
    report.reason = ReportReason.OTHER

    assert report_button_title(report).startswith("Жалоба · ")
    assert "<b>Причина:</b> Жалоба" in report_card(report)


def test_reviewing_report_has_no_dead_note_action() -> None:
    keyboard = report_keyboard(
        make_report(ReportStatus.REVIEWING), ReportStatus.REVIEWING, 0
    )
    labels = [button.text for row in keyboard.inline_keyboard for button in row]

    assert "✍️ Добавить заметку" not in labels
    assert "✅ Решить" in labels
