from __future__ import annotations

import json
import re
import shutil
from dataclasses import dataclass
from pathlib import Path

from fastapi import UploadFile

from ..config import get_settings

BASE_LANG_DIR = Path(__file__).resolve().parent.parent / "lang"
LANG_CODE_RE = re.compile(r"^[A-Z]{2}(?:-[A-Z]{2})?$")
DEFAULT_LANGUAGE_FILENAME = "EN.json"


class LanguageValidationError(Exception):
    def __init__(self, message: str, *, missing_keys: list[str] | None = None, untranslated_keys: list[str] | None = None):
        super().__init__(message)
        self.missing_keys = missing_keys or []
        self.untranslated_keys = untranslated_keys or []


@dataclass
class LanguagePack:
    code: str
    display_name: str
    strings: dict[str, str]
    path: Path


REQUIRED_LANGUAGE_KEYS = [
    "app.name", "app.tagline", "app.footer", "nav.dashboard", "nav.companies", "nav.users", "nav.requests", "nav.email_settings", "nav.languages", "nav.logout", "nav.client_portal", "nav.new_request", "nav.history", "nav.theme", "nav.language", "theme.light", "theme.dark", "auth.title", "auth.subtitle", "auth.email", "auth.password", "auth.login", "auth.logout_success", "auth.invalid_credentials", "common.save", "common.cancel", "common.delete", "common.edit", "common.create", "common.update", "common.search", "common.status", "common.actions", "common.notes", "common.language", "common.company", "common.role", "common.email", "common.required", "common.optional", "common.download", "common.upload", "common.template", "common.details", "common.back", "dashboard.admin_title", "dashboard.client_title", "dashboard.welcome_admin", "dashboard.welcome_client", "dashboard.recent_requests", "dashboard.request_counts", "companies.title", "companies.create", "companies.empty", "companies.name", "companies.notification_email", "companies.notes", "companies.contact_users", "companies.variables", "companies.requests", "companies.saved", "companies.deleted", "users.title", "users.create", "users.empty", "users.email", "users.password", "users.role", "users.company", "users.language_preference", "users.saved", "users.deleted", "roles.admin", "roles.client_contact", "variables.title", "variables.create", "variables.empty", "variables.label", "variables.field_type", "variables.options", "variables.required", "variables.help_text", "variables.applies_to", "variables.sort_order", "variables.saved", "variables.deleted", "variables.field_type.text", "variables.field_type.dropdown", "variables.applies_to.onboarding", "variables.applies_to.offboarding", "variables.applies_to.both", "requests.title", "requests.new_title", "requests.empty", "requests.employee_name", "requests.process_type", "requests.relevant_date", "requests.notes", "requests.status", "requests.submitted", "requests.saved", "requests.status.submitted", "requests.status.in_progress", "requests.status.completed", "requests.process_type.onboarding", "requests.process_type.offboarding", "requests.start_onboarding", "requests.start_offboarding", "requests.history", "requests.created_by", "requests.company", "requests.variable_values", "requests.status_updated", "email.title", "email.saved", "email.smtp_enabled", "email.smtp_host", "email.smtp_port", "email.smtp_username", "email.smtp_password", "email.smtp_from_address", "email.smtp_from_name", "email.smtp_use_tls", "email.smtp_use_ssl", "languages.title", "languages.available", "languages.upload", "languages.download_template", "languages.saved", "languages.invalid_json", "languages.missing_keys", "languages.untranslated_keys", "languages.code", "languages.display_name", "languages.file", "messages.access_denied", "messages.not_found", "messages.request_notification_subject", "messages.language_upload_success", "messages.language_upload_failed", "messages.no_company_assigned", "messages.validation_failed", "validation.required", "validation.invalid_email", "validation.invalid_language_code", "validation.missing_company", "validation.dropdown_options_required"
]


def _storage_dir() -> Path:
    settings = get_settings()
    path = Path(settings.language_storage_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path


def ensure_language_storage_seeded() -> None:
    storage = _storage_dir()
    for source in BASE_LANG_DIR.glob("*.json"):
        target = storage / source.name
        if not target.exists():
            shutil.copy2(source, target)


def _load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _normalize_pack(data: dict, path: Path) -> LanguagePack:
    code = str(data.get("LANG", "")).upper().strip()
    display_name = str(data.get("DISPLAY_NAME", code)).strip() or code
    strings = data.get("STRINGS")
    if not LANG_CODE_RE.match(code):
        raise LanguageValidationError("Invalid language code")
    if not isinstance(strings, dict):
        raise LanguageValidationError("Invalid language file")
    normalized_strings: dict[str, str] = {}
    for key, value in strings.items():
        if not isinstance(key, str) or not isinstance(value, str):
            raise LanguageValidationError("Invalid language file")
        normalized_strings[key] = value
    return LanguagePack(code=code, display_name=display_name, strings=normalized_strings, path=path)


def list_languages() -> list[LanguagePack]:
    ensure_language_storage_seeded()
    packs: list[LanguagePack] = []
    for path in sorted(_storage_dir().glob("*.json")):
        try:
            packs.append(_normalize_pack(_load_json(path), path))
        except LanguageValidationError:
            continue
    default_language = get_settings().default_language.upper()
    return sorted(packs, key=lambda item: (item.code != default_language, item.display_name.lower()))


def get_language(code: str | None) -> LanguagePack:
    default_language = get_settings().default_language.upper()
    wanted = (code or default_language).upper()
    languages = {pack.code: pack for pack in list_languages()}
    return languages.get(wanted) or languages[default_language]


def validate_language_payload(data: dict) -> tuple[LanguagePack, list[str]]:
    pack = _normalize_pack(data, Path("<upload>"))
    missing = [key for key in REQUIRED_LANGUAGE_KEYS if key not in pack.strings]
    if missing:
        raise LanguageValidationError("Missing required keys", missing_keys=missing)
    default_language = get_settings().default_language.upper()
    english = get_language(default_language)
    untranslated = [
        key for key in REQUIRED_LANGUAGE_KEYS
        if not pack.strings.get(key, "").strip() or (pack.code != default_language and pack.strings.get(key) == english.strings.get(key))
    ]
    return pack, untranslated


def save_uploaded_language(upload: UploadFile) -> tuple[LanguagePack, list[str]]:
    if not upload.filename or not upload.filename.lower().endswith(".json"):
        raise LanguageValidationError("Invalid file type")
    payload = upload.file.read()
    try:
        data = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise LanguageValidationError("Invalid JSON file") from exc
    pack, untranslated = validate_language_payload(data)
    target = _storage_dir() / f"{pack.code}.json"
    with target.open("w", encoding="utf-8") as handle:
        json.dump({"LANG": pack.code, "DISPLAY_NAME": pack.display_name, "STRINGS": pack.strings}, handle, ensure_ascii=False, indent=2)
    return LanguagePack(code=pack.code, display_name=pack.display_name, strings=pack.strings, path=target), untranslated


def template_language_payload() -> dict:
    english = get_language(get_settings().default_language)
    return {
        "LANG": "XX",
        "DISPLAY_NAME": "New Language",
        "STRINGS": {key: english.strings.get(key, "") for key in REQUIRED_LANGUAGE_KEYS},
    }
