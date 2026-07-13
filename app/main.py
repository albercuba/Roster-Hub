from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from .branding import uploaded_logo_path
from .config import get_settings
from .routers import admin, auth, client, dashboard
from .services.bootstrap import bootstrap
from .web import APP_DIR

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    bootstrap()
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.mount("/static", StaticFiles(directory=str(APP_DIR / "static")), name="static")


@app.middleware("http")
async def security_middleware(request: Request, call_next):
    response = await call_next(request)
    if settings.security_headers_enabled:
        response.headers.setdefault("Content-Security-Policy", settings.content_security_policy)
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("Referrer-Policy", settings.referrer_policy)
        response.headers.setdefault("Permissions-Policy", settings.permissions_policy)
    return response


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    if exc.status_code == 401 and request.url.path != "/login":
        response = RedirectResponse("/login", status_code=303)
        response.delete_cookie(settings.session_cookie_name)
        return response
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail or "Error"})


@app.get("/branding/logo")
def branding_logo():
    logo_path = uploaded_logo_path(settings.branding_upload_dir)
    if not logo_path:
        raise HTTPException(status_code=404, detail="Logo not found")
    media_type = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".webp": "image/webp",
    }.get(logo_path.suffix.lower(), "application/octet-stream")
    return FileResponse(logo_path, media_type=media_type)


app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(admin.router)
app.include_router(client.router)
