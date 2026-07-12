from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from ..database import get_db
from ..deps import ensure_request_access, require_client_contact
from ..models import CompanyVariable, Request as RequestModel, RequestVariableValue, STATUS_SUBMITTED, User
from ..services.audit_service import write_audit_log
from ..services.mail_service import send_request_notification_email
from ..web import render_template

router = APIRouter(prefix="/portal")


@router.get("")
def portal_home(request: Request, db: Session = Depends(get_db), user: User = Depends(require_client_contact)):
    requests_list = db.scalars(
        select(RequestModel)
        .options(selectinload(RequestModel.variable_values).selectinload(RequestVariableValue.company_variable))
        .where(RequestModel.company_id == user.company_id)
        .order_by(RequestModel.created_at.desc())
    ).all()
    return render_template(request, "client_portal.html", {"user": user, "active_page": "client_portal", "requests_list": requests_list, "toast": request.query_params.get("toast")}, user=user)


@router.get("/requests/new")
def new_request_page(
    request: Request,
    process_type: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_client_contact),
):
    if process_type not in {"onboarding", "offboarding"}:
        raise HTTPException(status_code=400, detail="Invalid process type")
    variables = db.scalars(
        select(CompanyVariable)
        .where(CompanyVariable.company_id == user.company_id)
        .order_by(CompanyVariable.sort_order.asc(), CompanyVariable.label.asc())
    ).all()
    filtered = [item for item in variables if item.applies_to in {"both", process_type}]
    return render_template(request, "client_request_form.html", {"user": user, "active_page": "new_request", "process_type": process_type, "variables": filtered, "toast": request.query_params.get("toast")}, user=user)


@router.get("/requests/{request_id}")
def request_detail(request_id: str, request: Request, db: Session = Depends(get_db), user: User = Depends(require_client_contact)):
    request_record = db.scalar(
        select(RequestModel)
        .options(
            selectinload(RequestModel.company),
            selectinload(RequestModel.created_by_user),
            selectinload(RequestModel.variable_values).selectinload(RequestVariableValue.company_variable),
        )
        .where(RequestModel.id == request_id)
    )
    if not request_record:
        raise HTTPException(status_code=404, detail="Request not found")
    ensure_request_access(user, request_record)
    return render_template(request, "client_request_detail.html", {"user": user, "active_page": "client_portal", "request_record": request_record}, user=user)


@router.post("/requests")
async def submit_request(
    request: Request,
    process_type: str = Form(...),
    employee_name: str = Form(...),
    relevant_date: str = Form(...),
    notes: str = Form(""),
    db: Session = Depends(get_db),
    user: User = Depends(require_client_contact),
):
    if process_type not in {"onboarding", "offboarding"}:
        raise HTTPException(status_code=400, detail="Invalid process type")
    relevant_date_value = datetime.strptime(relevant_date, "%Y-%m-%d").date()
    variables = db.scalars(
        select(CompanyVariable)
        .where(CompanyVariable.company_id == user.company_id)
        .order_by(CompanyVariable.sort_order.asc(), CompanyVariable.label.asc())
    ).all()
    applicable = [item for item in variables if item.applies_to in {"both", process_type}]
    form_data = await request.form()

    request_record = RequestModel(
        company_id=user.company_id,
        created_by_user_id=user.id,
        process_type=process_type,
        employee_name=employee_name.strip(),
        relevant_date=relevant_date_value,
        notes=notes.strip() or None,
        status=STATUS_SUBMITTED,
    )
    db.add(request_record)
    db.flush()

    for variable in applicable:
        value = str(form_data.get(f"variable_{variable.id}", "")).strip()
        if variable.required and not value:
            raise HTTPException(status_code=400, detail=f"Missing value for {variable.label}")
        db.add(
            RequestVariableValue(
                request_id=request_record.id,
                company_variable_id=variable.id,
                value=value or None,
            )
        )

    db.flush()
    request_record = db.scalar(
        select(RequestModel)
        .options(
            selectinload(RequestModel.company),
            selectinload(RequestModel.created_by_user),
            selectinload(RequestModel.variable_values).selectinload(RequestVariableValue.company_variable),
        )
        .where(RequestModel.id == request_record.id)
    )
    write_audit_log(db, user=user, action="request.submit", target_type="request", target_id=request_record.id)
    send_request_notification_email(db, request_record)
    db.commit()
    return RedirectResponse("/portal?toast=requests.submitted", status_code=303)
