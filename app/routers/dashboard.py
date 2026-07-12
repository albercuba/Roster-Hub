from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse

from ..database import get_db
from ..deps import current_user
from ..models import Company, Request as RequestModel, User
from ..web import render_template

router = APIRouter()


@router.get("/")
def index(user: User = Depends(current_user)):
    return RedirectResponse("/portal" if user.role == "client_contact" else "/dashboard", status_code=303)


@router.get("/dashboard")
def dashboard(request: Request, db: Session = Depends(get_db), user: User = Depends(current_user)):
    if user.role == "client_contact":
        return RedirectResponse("/portal", status_code=303)
    total_companies = db.scalar(select(func.count()).select_from(Company)) or 0
    total_users = db.scalar(select(func.count()).select_from(User)) or 0
    recent_requests = db.scalars(select(RequestModel).order_by(RequestModel.created_at.desc()).limit(10)).all()
    request_counts = {
        "submitted": db.scalar(select(func.count()).select_from(RequestModel).where(RequestModel.status == "submitted")) or 0,
        "in_progress": db.scalar(select(func.count()).select_from(RequestModel).where(RequestModel.status == "in_progress")) or 0,
        "completed": db.scalar(select(func.count()).select_from(RequestModel).where(RequestModel.status == "completed")) or 0,
    }
    return render_template(
        request,
        "dashboard.html",
        {
            "user": user,
            "active_page": "dashboard",
            "recent_requests": recent_requests,
            "request_counts": request_counts,
            "total_companies": total_companies,
            "total_users": total_users,
            "toast": request.query_params.get("toast"),
        },
        user=user,
    )
