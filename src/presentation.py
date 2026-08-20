from html import escape
from zoneinfo import ZoneInfo

from src.models import ModerationReport, ReportReason, ReportStatus

REASON_LABELS = {
    ReportReason.SPAM: "Спам",
    ReportReason.HARASSMENT: "Домогательства или травля",
    ReportReason.INAPPROPRIATE: "Неприемлемый контент",
    ReportReason.IMPERSONATION: "Выдаёт себя за другого",
    ReportReason.OTHER: "Другое",
}

STATUS_LABELS = {
    ReportStatus.PENDING: "Новая",
    ReportStatus.REVIEWING: "В работе",
    ReportStatus.RESOLVED: "Решена",
    ReportStatus.DISMISSED: "Отклонена",
}

STATUS_ICONS = {
    ReportStatus.PENDING: "🆕",
    ReportStatus.REVIEWING: "🔎",
    ReportStatus.RESOLVED: "✅",
    ReportStatus.DISMISSED: "🚫",
}


def report_list_title(status: ReportStatus, count: int) -> str:
    return (
        f"<b>{STATUS_ICONS[status]} {STATUS_LABELS[status]}: {count}</b>\n"
        "Выберите жалобу для просмотра."
    )


def report_button_title(report: ModerationReport) -> str:
    target = report.target_username or report.target_name or "без username"
    target = target if target.startswith("@") else f"@{target}"
    return f"{REASON_LABELS[report.reason]} · {target}"[:60]


def report_notification(report: ModerationReport) -> str:
    return "🆕 <b>Новая жалоба Telescan</b>\n\n" + report_summary(report)


def report_card(report: ModerationReport) -> str:
    return "<b>Жалоба Telescan</b>\n\n" + report_summary(report, detailed=True)


def report_summary(report: ModerationReport, *, detailed: bool = False) -> str:
    username = report.target_username or "—"
    if username != "—" and not username.startswith("@"):
        username = f"@{username}"
    name = report.target_name or "—"
    reporter = (
        str(report.reporter_telescan_id) if report.reporter_telescan_id else "удалён"
    )
    details = escape(report.details) if report.details else "—"
    created = report.created_at.astimezone(ZoneInfo("Europe/Moscow")).strftime(
        "%d.%m.%Y %H:%M MSK"
    )

    lines = [
        f"<b>Статус:</b> {STATUS_ICONS[report.status]} {STATUS_LABELS[report.status]}",
        f"<b>Причина:</b> {escape(REASON_LABELS[report.reason])}",
        f"<b>Профиль:</b> {escape(name)} · {escape(username)}",
    ]
    if report.target_bio:
        lines.append(f"<b>BIO:</b> {escape(report.target_bio)}")
    lines.extend(
        [
            f"<b>Комментарий:</b> {details}",
            f"<b>Создана:</b> {created}",
        ]
    )
    if detailed:
        lines.extend(
            [
                f"<b>ID жалобы:</b> <code>{report.report_id}</code>",
                f"<b>Кто отправил:</b> <code>{escape(reporter)}</code>",
                f"<b>На кого:</b> <code>{report.target_telescan_id}</code>",
            ]
        )
        if report.moderator_id:
            lines.append(f"<b>Модератор:</b> {escape(report.moderator_id)}")
        if report.moderator_note:
            lines.append(f"<b>Заметка:</b> {escape(report.moderator_note)}")
    return "\n".join(lines)
