from __future__ import annotations

from pathlib import Path

from fastapi import Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from .branding import uploaded_logo_path
from .config import get_settings
from .database import SessionLocal
from .models import IntegrationSettings
from .services.language_service import get_language, list_languages

settings = get_settings()
APP_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(APP_DIR / "templates"))


def current_brand_logo_url(db: Session | None = None) -> str | None:
    if uploaded_logo_path(settings.branding_upload_dir):
        return "/branding/logo"
    close_db = False
    if db is None:
        db = SessionLocal()
        close_db = True
    try:
        integration_settings = db.get(IntegrationSettings, 1)
        return integration_settings.branding_logo_url if integration_settings else None
    finally:
        if close_db:
            db.close()


def preferred_language_code(request: Request, user=None) -> str:
    if user and getattr(user, "language_preference", None):
        return str(user.language_preference).upper()
    cookie = request.cookies.get("roster_hub_language")
    if cookie:
        return cookie.upper()
    return settings.default_language.upper()


def current_language(request: Request, user=None):
    return get_language(preferred_language_code(request, user))


def render_template(request: Request, template_name: str, context: dict, *, user=None, db: Session | None = None, status_code: int = 200):
    language = current_language(request, user or context.get("user"))
    payload = dict(context)
    payload.setdefault("request", request)
    payload.setdefault("user", user)
    payload.setdefault("lang", language)
    payload.setdefault("language_options", list_languages())
    payload.setdefault("theme", request.cookies.get("roster_hub_theme", "system"))
    payload.setdefault("active_page", None)
    payload.setdefault("toast", None)
    payload.setdefault("app_name", settings.app_name)
    payload.setdefault("brand_logo_url", current_brand_logo_url(db))

    def translate(key: str, **kwargs):
        text = language.strings.get(key) or get_language(settings.default_language).strings.get(key) or key
        if kwargs:
            try:
                return text.format(**kwargs)
            except Exception:
                return text
        return text

    payload.setdefault("t", translate)
    return templates.TemplateResponse(request, template_name, payload, status_code=status_code)
