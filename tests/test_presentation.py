from datetime import UTC, datetime
from uuid import uuid4

from src.keyboards import report_keyboard, reports_keyboard
from src.models import ModerationReport, ReportReason, ReportStatus
from src.presentation import report_card


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
        status=status,
        createdAt=now,
        updatedAt=now,
    )


def test_report_card_escapes_user_controlled_text() -> None:
    text = report_card(make_report())

    assert "<script>" not in text
    assert "&lt;script&gt;unsafe&lt;/script&gt;" in text
    assert "Ada &amp; Bob" in text
    assert "iOS engineer &amp; organizer" in text


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
