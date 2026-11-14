"""
Notifications service: in-app notifications and email dispatch.

In development or when SMTP is disabled/fails, it gracefully falls back to
console logging so local development never breaks.
"""
from __future__ import annotations

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import TYPE_CHECKING

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.notification import Notification

if TYPE_CHECKING:
    from app.models.probation import ProbationCase
    from app.models.user import User

logger = logging.getLogger("notifications")


def create_in_app_notification(
    db: Session,
    recipient_id: int,
    probation_case_id: int,
    message: str,
) -> Notification:
    """Create and persist an in-app notification record."""
    notif = Notification(
        recipient_id=recipient_id,
        probation_case_id=probation_case_id,
        message=message,
        is_read=False,
    )
    db.add(notif)
    db.commit()
    db.refresh(notif)
    return notif


def send_email_alert(
    to_email: str,
    subject: str,
    body_text: str,
    body_html: str | None = None,
) -> bool:
    """
    Send an email via SMTP if configured, or print to console if disabled/failed.
    Designed to be safely called in FastAPI BackgroundTasks.
    """
    if not settings.EMAILS_ENABLED or not settings.SMTP_USER:
        print("\n" + "=" * 60)
        print("📧 [CONSOLE EMAIL FALLBACK - EMAILS_ENABLED=False]")
        print(f"To:      {to_email}")
        print(f"Subject: {subject}")
        print("-" * 60)
        print(body_text)
        print("=" * 60 + "\n")
        return True

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = settings.SMTP_USER
        msg["To"] = to_email

        msg.attach(MIMEText(body_text, "plain"))
        if body_html:
            msg.attach(MIMEText(body_html, "html"))

        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as server:
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.sendmail(settings.SMTP_USER, [to_email], msg.as_string())

        logger.info(f"Email sent successfully to {to_email}")
        return True
    except Exception as exc:
        logger.warning(f"SMTP sending failed ({exc}); falling back to console.")
        print(f"[EMAIL ERROR FALLBACK to {to_email}]: {subject}\n{body_text}")
        return False


def notify_advisor_of_probation(
    db: Session,
    case: ProbationCase,
    advisor: User | None,
    action: str = "flagged",  # 'flagged' or 'cleared'
) -> Notification | None:
    """
    Helper to trigger both in-app notification and email to an advisor.
    """
    if not advisor:
        return None

    student_name = case.student.name if case.student else f"Student #{case.student_id}"
    matric_no = case.student.matric_no if case.student else ""
    sem_name = f"{case.semester.session} ({case.semester.name})" if case.semester else f"Semester #{case.semester_id}"

    if action == "flagged":
        subject = f"URGENT: Academic Probation Alert - {student_name} ({matric_no})"
        msg_text = (
            f"Dear {advisor.name},\n\n"
            f"This is an automated alert that your advisee {student_name} ({matric_no}) "
            f"has been placed on academic probation for {sem_name}.\n\n"
            f"Reason(s): {case.reasons}\n\n"
            f"Please log in to the dashboard to review their academic record and schedule an advising session."
        )
    else:
        subject = f"UPDATE: Academic Probation Cleared - {student_name} ({matric_no})"
        msg_text = (
            f"Dear {advisor.name},\n\n"
            f"Your advisee {student_name} ({matric_no}) has cleared their probation conditions "
            f"for {sem_name}.\n\n"
            f"Current Status: Cleared\nNotes: {case.notes or 'Performance criteria satisfied.'}"
        )

    # 1. In-app notification
    notif = create_in_app_notification(
        db=db,
        recipient_id=advisor.id,
        probation_case_id=case.id,
        message=f"[{action.upper()}] {student_name} ({matric_no}) - {case.reasons}",
    )

    # 2. Email alert
    if advisor.email:
        send_email_alert(
            to_email=advisor.email,
            subject=subject,
            body_text=msg_text,
        )

    return notif

