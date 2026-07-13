from __future__ import annotations

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from ..config import get_settings
from ..database import get_db
from ..deps import current_user, optional_user
from ..models import User
from ..services.auth_service import authenticate_user, clear_session_cookie, create_user_session, set_session_cookie, session_from_request, revoke_session
from ..web import render_template

router = APIRouter()
settings = get_settings()


def _redirect_target(user: User) -> str:
    return "/portal" if user.role == "client_contact" else "/dashboard"


@router.get("/login")
def login_page(request: Request, user: User | None = Depends(optional_user)):
    if user:
        return RedirectResponse(_redirect_target(user), status_code=303)
    return render_template(request, "login.html", {"active_page": "login"})


@router.post("/login")
def login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    user = authenticate_user(db, email, password)
    if not user:
        return render_template(
            request,
            "login.html",
            {"active_page": "login", "error_key": "auth.invalid_credentials", "entered_email": email},
            status_code=400,
        )
    token = create_user_session(db, user)
    db.commit()
    response = RedirectResponse(_redirect_target(user), status_code=303)
    set_session_cookie(response, token)
    return response


@router.post("/logout")
def logout(request: Request, db: Session = Depends(get_db)):
    try:
        session = session_from_request(request, db)
        revoke_session(db, session)
        db.commit()
    except Exception:
        pass
    response = RedirectResponse("/login?toast=auth.logout_success", status_code=303)
    clear_session_cookie(response)
    return response


@router.post("/preferences/language")
def set_language(
    request: Request,
    language_code: str = Form(...),
    db: Session = Depends(get_db),
    user: User | None = Depends(optional_user),
):
    redirect_to = request.headers.get("referer") or "/"
    response = RedirectResponse(redirect_to, status_code=303)
    normalized = language_code.upper()
    response.set_cookie("roster_hub_language", normalized, httponly=False, samesite="lax", secure=settings.session_secure, max_age=31536000)
    if user:
        user.language_preference = normalized
        db.commit()
    return response


@router.post("/preferences/theme")
def set_theme(request: Request, theme: str = Form(...)):
    redirect_to = request.headers.get("referer") or "/"
    response = RedirectResponse(redirect_to, status_code=303)
    response.set_cookie("roster_hub_theme", theme, httponly=False, samesite="lax", secure=settings.session_secure, max_age=31536000)
    return response

