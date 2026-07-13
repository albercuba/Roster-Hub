from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="", extra="ignore")

    app_name: str = "Roster Hub"
    app_env: str = "development"
    public_url: str = "http://localhost:8084"
    database_url: str = "postgresql+psycopg://rosterhub:rosterhub@db:5432/rosterhub"
    secret_key: str = "change-me"
    session_cookie_name: str = "roster_hub_session"
    session_secure: bool = False
    session_ttl_hours: int = 12
    initial_admin_email: str = "admin@example.com"
    initial_admin_password: str = "change-me"
    allowed_hosts: str = "localhost,127.0.0.1,testserver"
    default_language: str = "EN"
    language_storage_dir: str = "/var/lib/roster-hub/languages"
    branding_upload_dir: str = "/var/lib/roster-hub/branding"
    branding_logo_max_bytes: int = 1_000_000
    smtp_enabled: bool = False
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_username: str | None = None
    smtp_password: str | None = None
    smtp_from_address: str | None = None
    smtp_from_name: str = "Roster Hub"
    smtp_use_tls: bool = True
    smtp_use_ssl: bool = False
    security_headers_enabled: bool = True
    content_security_policy: str = (
        "default-src 'self'; img-src 'self' data:; "
        "style-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com https://fonts.googleapis.com; "
        "script-src 'self' 'unsafe-inline'; "
        "font-src 'self' data: https://cdnjs.cloudflare.com https://fonts.gstatic.com; "
        "frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
    )
    referrer_policy: str = "strict-origin-when-cross-origin"
    permissions_policy: str = "geolocation=(), microphone=(), camera=()"

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
