from __future__ import annotations

import smtplib
from email.message import EmailMessage

from sqlalchemy.orm import Session

from ..config import get_settings
from ..models import EmailSettings, Request

settings = get_settings()


def get_effective_email_settings(db: Session) -> EmailSettings:
    record = db.get(EmailSettings, 1)
    if record:
        return record
    seeded = EmailSettings(
        id=1,
        smtp_enabled=settings.smtp_enabled,
        smtp_host=settings.smtp_host,
        smtp_port=settings.smtp_port,
        smtp_username=settings.smtp_username,
        smtp_password=settings.smtp_password,
        smtp_from_address=settings.smtp_from_address,
        smtp_from_name=settings.smtp_from_name,
        smtp_use_tls=settings.smtp_use_tls,
        smtp_use_ssl=settings.smtp_use_ssl,
    )
    db.add(seeded)
    db.flush()
    return seeded


def send_request_notification_email(db: Session, request_record: Request) -> bool:
    company = request_record.company
    email_settings = get_effective_email_settings(db)
    if not email_settings.smtp_enabled:
        return False
    if not company.notification_email:
        return False
    if not email_settings.smtp_host or not email_settings.smtp_from_address or not email_settings.smtp_port:
        return False

    message = EmailMessage()
    message["Subject"] = f"Roster Hub {request_record.process_type.title()} request for {request_record.employee_name}"
    sender_name = email_settings.smtp_from_name or settings.smtp_from_name or "Roster Hub"
    message["From"] = f"{sender_name} <{email_settings.smtp_from_address}>"
    message["To"] = company.notification_email
    lines = [
        f"Company: {company.name}",
        f"Process: {request_record.process_type}",
        f"Employee: {request_record.employee_name}",
        f"Relevant date: {request_record.relevant_date.isoformat()}",
        f"Submitted by: {request_record.created_by_user.email}",
        f"Status: {request_record.status}",
        "",
        "Notes:",
        request_record.notes or "-",
        "",
        "Variable values:",
    ]
    for item in request_record.variable_values:
        lines.append(f"- {item.company_variable.label}: {item.value or '-'}")
    message.set_content("\n".join(lines))

    if email_settings.smtp_use_ssl:
        with smtplib.SMTP_SSL(email_settings.smtp_host, email_settings.smtp_port) as server:
            if email_settings.smtp_username:
                server.login(email_settings.smtp_username, email_settings.smtp_password or "")
            server.send_message(message)
        return True

    with smtplib.SMTP(email_settings.smtp_host, email_settings.smtp_port) as server:
        if email_settings.smtp_use_tls:
            server.starttls()
        if email_settings.smtp_username:
            server.login(email_settings.smtp_username, email_settings.smtp_password or "")
        server.send_message(message)
    return True
