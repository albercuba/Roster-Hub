from __future__ import annotations

from datetime import timedelta, timezone

from fastapi import HTTPException, Request, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import get_settings
from ..models import SessionToken, User
from ..security import hash_session_token, random_token, utc_now, verify_password

settings = get_settings()


def authenticate_user(db: Session, email: str, password: str) -> User | None:
    normalized = email.strip().lower()
    user = db.scalar(select(User).where(User.email == normalized, User.is_active.is_(True)))
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


def create_user_session(db: Session, user: User) -> str:
    token = random_token(32)
    now = utc_now()
    db.add(
        SessionToken(
            user_id=user.id,
            token_hash=hash_session_token(settings.secret_key, token),
            created_at=now,
            expires_at=now + timedelta(hours=settings.session_ttl_hours),
        )
    )
    return token


def set_session_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        settings.session_cookie_name,
        token,
        httponly=True,
        secure=settings.session_secure,
        samesite="lax",
        max_age=settings.session_ttl_hours * 3600,
    )


def clear_session_cookie(response: Response) -> None:
    response.delete_cookie(settings.session_cookie_name)


def session_from_request(request: Request, db: Session) -> SessionToken:
    token = request.cookies.get(settings.session_cookie_name)
    if not token:
        raise HTTPException(status_code=401)
    token_hash = hash_session_token(settings.secret_key, token)
    session = db.scalar(select(SessionToken).where(SessionToken.token_hash == token_hash))
    if not session:
        raise HTTPException(status_code=401)
    expires_at = session.expires_at if session.expires_at.tzinfo else session.expires_at.replace(tzinfo=timezone.utc)
    revoked_at = session.revoked_at if not session.revoked_at or session.revoked_at.tzinfo else session.revoked_at.replace(tzinfo=timezone.utc)
    if revoked_at or expires_at <= utc_now():
        raise HTTPException(status_code=401)
    return session


def revoke_session(db: Session, session: SessionToken) -> None:
    session.revoked_at = utc_now()
