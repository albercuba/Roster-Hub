from __future__ import annotations

from sqlalchemy import select

from ..config import get_settings
from ..database import Base, engine, SessionLocal
from ..models import EmailSettings, User, ROLE_ADMIN
from ..security import hash_password
from .language_service import ensure_language_storage_seeded

settings = get_settings()


def bootstrap() -> None:
    ensure_language_storage_seeded()
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        admin = db.scalar(select(User).where(User.role == ROLE_ADMIN).limit(1))
        if not admin:
            db.add(
                User(
                    email=settings.initial_admin_email.strip().lower(),
                    password_hash=hash_password(settings.initial_admin_password),
                    role=ROLE_ADMIN,
                    language_preference=settings.default_language.upper(),
                )
            )
        if not db.get(EmailSettings, 1):
            db.add(
                EmailSettings(
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
            )
        db.commit()
