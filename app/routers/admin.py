from __future__ import annotations

import json
from datetime import datetime

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, RedirectResponse, Response
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from ..database import get_db
from ..deps import require_admin
from ..models import Company, CompanyVariable, EmailSettings, Request as RequestModel, RequestVariableValue, ROLE_CLIENT_CONTACT, User
from ..security import hash_password
from ..services.audit_service import write_audit_log
from ..services.language_service import LanguageValidationError, get_language, list_languages, save_uploaded_language, template_language_payload
from ..web import render_template

router = APIRouter(prefix="/admin")


def _redirect(path: str, toast: str | None = None) -> RedirectResponse:
    target = path if not toast else f"{path}?toast={toast}"
    return RedirectResponse(target, status_code=303)


def _company_or_404(db: Session, company_id: str) -> Company:
    company = db.get(Company, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return company


def _variable_or_404(db: Session, variable_id: str) -> CompanyVariable:
    variable = db.get(CompanyVariable, variable_id)
    if not variable:
        raise HTTPException(status_code=404, detail="Variable not found")
    return variable


def _user_or_404(db: Session, user_id: str) -> User:
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.get("/companies")
def companies_page(request: Request, db: Session = Depends(get_db), user: User = Depends(require_admin)):
    companies = db.scalars(select(Company).order_by(Company.name.asc())).all()
    return render_template(request, "admin_companies.html", {"user": user, "active_page": "companies", "companies": companies, "toast": request.query_params.get("toast")}, user=user)


@router.post("/companies")
def create_company(
    request: Request,
    name: str = Form(...),
    notification_email: str = Form(""),
    notes: str = Form(""),
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
):
    company = Company(name=name.strip(), notification_email=notification_email.strip() or None, notes=notes.strip() or None)
    db.add(company)
    db.flush()
    write_audit_log(db, user=user, action="company.create", target_type="company", target_id=company.id)
    db.commit()
    return _redirect(f"/admin/companies/{company.id}", "companies.saved")


@router.get("/companies/{company_id}")
def company_detail(company_id: str, request: Request, db: Session = Depends(get_db), user: User = Depends(require_admin)):
    company = db.scalar(
        select(Company)
        .options(selectinload(Company.users), selectinload(Company.variables), selectinload(Company.requests))
        .where(Company.id == company_id)
    )
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return render_template(request, "admin_company_detail.html", {"user": user, "active_page": "companies", "company": company, "toast": request.query_params.get("toast")}, user=user)


@router.post("/companies/{company_id}")
def update_company(
    company_id: str,
    name: str = Form(...),
    notification_email: str = Form(""),
    notes: str = Form(""),
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
):
    company = _company_or_404(db, company_id)
    company.name = name.strip()
    company.notification_email = notification_email.strip() or None
    company.notes = notes.strip() or None
    write_audit_log(db, user=user, action="company.update", target_type="company", target_id=company.id)
    db.commit()
    return _redirect(f"/admin/companies/{company.id}", "companies.saved")


@router.post("/companies/{company_id}/delete")
def delete_company(company_id: str, db: Session = Depends(get_db), user: User = Depends(require_admin)):
    company = _company_or_404(db, company_id)
    db.delete(company)
    write_audit_log(db, user=user, action="company.delete", target_type="company", target_id=company_id)
    db.commit()
    return _redirect("/admin/companies", "companies.deleted")


@router.post("/companies/{company_id}/variables")
def create_variable(
    company_id: str,
    label: str = Form(...),
    field_type: str = Form(...),
    options_text: str = Form(""),
    required: bool = Form(False),
    help_text: str = Form(""),
    applies_to: str = Form("both"),
    sort_order: int = Form(0),
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
):
    company = _company_or_404(db, company_id)
    options = [item.strip() for item in options_text.splitlines() if item.strip()] if field_type == "dropdown" else None
    if field_type == "dropdown" and not options:
        raise HTTPException(status_code=400, detail="Dropdown options required")
    variable = CompanyVariable(
        company_id=company.id,
        label=label.strip(),
        field_type=field_type,
        options=options,
        required=required,
        help_text=help_text.strip() or None,
        applies_to=applies_to,
        sort_order=sort_order,
    )
    db.add(variable)
    db.flush()
    write_audit_log(db, user=user, action="variable.create", target_type="company_variable", target_id=variable.id)
    db.commit()
    return _redirect(f"/admin/companies/{company.id}", "variables.saved")


@router.post("/variables/{variable_id}")
def update_variable(
    variable_id: str,
    label: str = Form(...),
    field_type: str = Form(...),
    options_text: str = Form(""),
    required: bool = Form(False),
    help_text: str = Form(""),
    applies_to: str = Form("both"),
    sort_order: int = Form(0),
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
):
    variable = _variable_or_404(db, variable_id)
    options = [item.strip() for item in options_text.splitlines() if item.strip()] if field_type == "dropdown" else None
    if field_type == "dropdown" and not options:
        raise HTTPException(status_code=400, detail="Dropdown options required")
    variable.label = label.strip()
    variable.field_type = field_type
    variable.options = options
    variable.required = required
    variable.help_text = help_text.strip() or None
    variable.applies_to = applies_to
    variable.sort_order = sort_order
    write_audit_log(db, user=user, action="variable.update", target_type="company_variable", target_id=variable.id)
    db.commit()
    return _redirect(f"/admin/companies/{variable.company_id}", "variables.saved")


@router.post("/variables/{variable_id}/delete")
def delete_variable(variable_id: str, db: Session = Depends(get_db), user: User = Depends(require_admin)):
    variable = _variable_or_404(db, variable_id)
    company_id = variable.company_id
    db.delete(variable)
    write_audit_log(db, user=user, action="variable.delete", target_type="company_variable", target_id=variable_id)
    db.commit()
    return _redirect(f"/admin/companies/{company_id}", "variables.deleted")


@router.get("/users")
def users_page(request: Request, db: Session = Depends(get_db), user: User = Depends(require_admin)):
    users = db.scalars(select(User).options(selectinload(User.company)).order_by(User.email.asc())).all()
    companies = db.scalars(select(Company).order_by(Company.name.asc())).all()
    return render_template(request, "admin_users.html", {"user": user, "active_page": "users", "users": users, "companies": companies, "toast": request.query_params.get("toast")}, user=user)


@router.post("/users")
def create_user(
    email: str = Form(...),
    password: str = Form(...),
    role: str = Form(...),
    company_id: str = Form(""),
    language_preference: str = Form("EN"),
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
):
    assigned_company_id = company_id or None
    if role == ROLE_CLIENT_CONTACT and not assigned_company_id:
        raise HTTPException(status_code=400, detail="Company required")
    new_user = User(
        email=email.strip().lower(),
        password_hash=hash_password(password),
        role=role,
        company_id=assigned_company_id if role == ROLE_CLIENT_CONTACT else None,
        language_preference=language_preference.upper(),
    )
    db.add(new_user)
    db.flush()
    write_audit_log(db, user=user, action="user.create", target_type="user", target_id=new_user.id)
    db.commit()
    return _redirect("/admin/users", "users.saved")


@router.post("/users/{user_id}")
def update_user(
    user_id: str,
    email: str = Form(...),
    role: str = Form(...),
    company_id: str = Form(""),
    language_preference: str = Form("EN"),
    password: str = Form(""),
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
):
    target = _user_or_404(db, user_id)
    target.email = email.strip().lower()
    target.role = role
    target.company_id = (company_id or None) if role == ROLE_CLIENT_CONTACT else None
    target.language_preference = language_preference.upper()
    if password.strip():
        target.password_hash = hash_password(password)
    write_audit_log(db, user=user, action="user.update", target_type="user", target_id=target.id)
    db.commit()
    return _redirect("/admin/users", "users.saved")


@router.post("/users/{user_id}/delete")
def delete_user(user_id: str, db: Session = Depends(get_db), user: User = Depends(require_admin)):
    target = _user_or_404(db, user_id)
    if target.role == ROLE_ADMIN and target.id == user.id:
        raise HTTPException(status_code=400, detail="Cannot delete current admin")
    db.delete(target)
    write_audit_log(db, user=user, action="user.delete", target_type="user", target_id=user_id)
    db.commit()
    return _redirect("/admin/users", "users.deleted")


@router.get("/requests")
def requests_page(request: Request, db: Session = Depends(get_db), user: User = Depends(require_admin)):
    requests_list = db.scalars(
        select(RequestModel)
        .options(
            selectinload(RequestModel.company),
            selectinload(RequestModel.created_by_user),
            selectinload(RequestModel.variable_values).selectinload(RequestVariableValue.company_variable),
        )
        .order_by(RequestModel.created_at.desc())
    ).all()
    return render_template(request, "admin_requests.html", {"user": user, "active_page": "requests", "requests_list": requests_list, "toast": request.query_params.get("toast")}, user=user)


@router.post("/requests/{request_id}/status")
def update_request_status(
    request_id: str,
    status: str = Form(...),
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
):
    request_record = db.get(RequestModel, request_id)
    if not request_record:
        raise HTTPException(status_code=404, detail="Request not found")
    request_record.status = status
    request_record.updated_at = datetime.utcnow()
    write_audit_log(db, user=user, action="request.status_update", target_type="request", target_id=request_record.id)
    db.commit()
    return _redirect("/admin/requests", "requests.status_updated")


@router.get("/settings/email")
def email_settings_page(request: Request, db: Session = Depends(get_db), user: User = Depends(require_admin)):
    settings_record = db.get(EmailSettings, 1)
    return render_template(request, "admin_email_settings.html", {"user": user, "active_page": "settings", "active_settings": "email_settings", "settings_record": settings_record, "toast": request.query_params.get("toast")}, user=user)


@router.post("/settings/email")
def update_email_settings(
    smtp_enabled: bool = Form(False),
    smtp_host: str = Form(""),
    smtp_port: int = Form(587),
    smtp_username: str = Form(""),
    smtp_password: str = Form(""),
    smtp_from_address: str = Form(""),
    smtp_from_name: str = Form("Roster Hub"),
    smtp_use_tls: bool = Form(False),
    smtp_use_ssl: bool = Form(False),
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
):
    record = db.get(EmailSettings, 1)
    if not record:
        record = EmailSettings(id=1)
        db.add(record)
    record.smtp_enabled = smtp_enabled
    record.smtp_host = smtp_host.strip() or None
    record.smtp_port = smtp_port
    record.smtp_username = smtp_username.strip() or None
    record.smtp_password = smtp_password.strip() or None
    record.smtp_from_address = smtp_from_address.strip() or None
    record.smtp_from_name = smtp_from_name.strip() or None
    record.smtp_use_tls = smtp_use_tls
    record.smtp_use_ssl = smtp_use_ssl
    write_audit_log(db, user=user, action="email_settings.update", target_type="email_settings", target_id="1")
    db.commit()
    return _redirect("/admin/settings/email", "email.saved")


@router.get("/languages")
def languages_page(request: Request, user: User = Depends(require_admin)):
    return render_template(request, "admin_languages.html", {"user": user, "active_page": "settings", "active_settings": "languages", "languages": list_languages(), "toast": request.query_params.get("toast"), "warnings": request.query_params.get("warnings", "")}, user=user)


@router.post("/languages/upload")
def upload_language(
    request: Request,
    language_file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
):
    try:
        pack, untranslated = save_uploaded_language(language_file)
    except LanguageValidationError as exc:
        return render_template(
            request,
            "admin_languages.html",
            {
                "user": user,
                "active_page": "settings",
                "active_settings": "languages",
                "languages": list_languages(),
                "error_message": str(exc),
                "missing_keys": exc.missing_keys,
                "untranslated_keys": exc.untranslated_keys,
            },
            user=user,
            status_code=400,
        )
    write_audit_log(db, user=user, action="language.upload", target_type="language", target_id=pack.code)
    db.commit()
    warnings = ",".join(untranslated)
    path = "/admin/languages?toast=messages.language_upload_success"
    if warnings:
        path += f"&warnings={warnings}"
    return RedirectResponse(path, status_code=303)


@router.get("/languages/template")
def download_language_template(user: User = Depends(require_admin)):
    payload = json.dumps(template_language_payload(), ensure_ascii=False, indent=2)
    return Response(content=payload, media_type="application/json", headers={"Content-Disposition": 'attachment; filename="language-template.json"'})


@router.get("/languages/{code}")
def download_language(code: str, user: User = Depends(require_admin)):
    pack = get_language(code)
    return FileResponse(pack.path, filename=pack.path.name, media_type="application/json")
