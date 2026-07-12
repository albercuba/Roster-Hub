from __future__ import annotations

from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from .database import get_db
from .models import ROLE_ADMIN, ROLE_CLIENT_CONTACT, Request as RequestModel, User
from .services.auth_service import session_from_request


def current_user(request: Request, db: Session = Depends(get_db)) -> User:
    session = session_from_request(request, db)
    return session.user


def optional_user(request: Request, db: Session = Depends(get_db)) -> User | None:
    try:
        return current_user(request, db)
    except HTTPException:
        return None


def require_admin(user: User = Depends(current_user)) -> User:
    if user.role != ROLE_ADMIN:
        raise HTTPException(status_code=403, detail="Access denied")
    return user


def require_client_contact(user: User = Depends(current_user)) -> User:
    if user.role != ROLE_CLIENT_CONTACT:
        raise HTTPException(status_code=403, detail="Access denied")
    if not user.company_id:
        raise HTTPException(status_code=403, detail="No company assigned")
    return user


def ensure_request_access(user: User, request_record: RequestModel) -> None:
    if user.role == ROLE_ADMIN:
        return
    if user.role == ROLE_CLIENT_CONTACT and user.company_id == request_record.company_id:
        return
    raise HTTPException(status_code=404, detail="Request not found")
