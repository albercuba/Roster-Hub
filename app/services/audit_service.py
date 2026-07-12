from __future__ import annotations

from sqlalchemy.orm import Session

from ..models import AuditLog, User


def write_audit_log(
    db: Session,
    *,
    user: User | None,
    action: str,
    target_type: str | None = None,
    target_id: str | None = None,
) -> None:
    db.add(
        AuditLog(
            user_id=user.id if user else None,
            action=action,
            target_type=target_type,
            target_id=target_id,
        )
    )
