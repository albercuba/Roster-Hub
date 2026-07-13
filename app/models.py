from __future__ import annotations

import uuid
from datetime import date, datetime, timezone

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


ROLE_ADMIN = "admin"
ROLE_CLIENT_CONTACT = "client_contact"
PROCESS_ONBOARDING = "onboarding"
PROCESS_OFFBOARDING = "offboarding"
STATUS_SUBMITTED = "submitted"
STATUS_IN_PROGRESS = "in_progress"
STATUS_COMPLETED = "completed"
VARIABLE_TEXT = "text"
VARIABLE_DROPDOWN = "dropdown"


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def uuid_str() -> str:
    return str(uuid.uuid4())


class Company(Base):
    __tablename__ = "companies"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    name: Mapped[str] = mapped_column(String(200), nullable=False, unique=True)
    notification_email: Mapped[str | None] = mapped_column(String(320), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, nullable=False)

    users: Mapped[list["User"]] = relationship(back_populates="company")
    variables: Mapped[list["CompanyVariable"]] = relationship(back_populates="company", cascade="all, delete-orphan")
    requests: Mapped[list["Request"]] = relationship(back_populates="company", cascade="all, delete-orphan")


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    role: Mapped[str] = mapped_column(String(30), nullable=False, default=ROLE_CLIENT_CONTACT)
    company_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("companies.id", ondelete="SET NULL"), nullable=True, index=True)
    language_preference: Mapped[str] = mapped_column(String(10), nullable=False, default="EN")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, nullable=False)

    company: Mapped[Company | None] = relationship(back_populates="users")
    sessions: Mapped[list["SessionToken"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    created_requests: Mapped[list["Request"]] = relationship(back_populates="created_by_user")
    audit_entries: Mapped[list["AuditLog"]] = relationship(back_populates="user")


class SessionToken(Base):
    __tablename__ = "sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped[User] = relationship(back_populates="sessions")


class EmailSettings(Base):
    __tablename__ = "email_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    smtp_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    smtp_host: Mapped[str | None] = mapped_column(String(255), nullable=True)
    smtp_port: Mapped[int | None] = mapped_column(Integer, nullable=True)
    smtp_username: Mapped[str | None] = mapped_column(String(320), nullable=True)
    smtp_password: Mapped[str | None] = mapped_column(Text, nullable=True)
    smtp_from_address: Mapped[str | None] = mapped_column(String(320), nullable=True)
    smtp_from_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    smtp_use_tls: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    smtp_use_ssl: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, nullable=False)


class IntegrationSettings(Base):
    __tablename__ = "integration_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    microsoft_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    microsoft_tenant_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    microsoft_client_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    microsoft_client_secret: Mapped[str | None] = mapped_column(Text, nullable=True)
    microsoft_audience: Mapped[str | None] = mapped_column(String(255), nullable=True)
    microsoft_authority: Mapped[str | None] = mapped_column(String(255), nullable=True)
    microsoft_admin_group_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    microsoft_admin_group_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    microsoft_user_group_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    microsoft_user_group_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    branding_logo_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, nullable=False)


class CompanyVariable(Base):
    __tablename__ = "company_variables"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    company_id: Mapped[str] = mapped_column(String(36), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    label: Mapped[str] = mapped_column(String(200), nullable=False)
    field_type: Mapped[str] = mapped_column(String(30), nullable=False, default=VARIABLE_TEXT)
    options: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    help_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    applies_to: Mapped[str] = mapped_column(String(30), nullable=False, default="both")
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, nullable=False)

    company: Mapped[Company] = relationship(back_populates="variables")
    values: Mapped[list["RequestVariableValue"]] = relationship(back_populates="company_variable")


class Request(Base):
    __tablename__ = "requests"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    company_id: Mapped[str] = mapped_column(String(36), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    created_by_user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    process_type: Mapped[str] = mapped_column(String(30), nullable=False)
    employee_name: Mapped[str] = mapped_column(String(200), nullable=False)
    relevant_date: Mapped[date] = mapped_column(Date, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default=STATUS_SUBMITTED)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, nullable=False)

    company: Mapped[Company] = relationship(back_populates="requests")
    created_by_user: Mapped[User] = relationship(back_populates="created_requests")
    variable_values: Mapped[list["RequestVariableValue"]] = relationship(back_populates="request", cascade="all, delete-orphan")


class RequestVariableValue(Base):
    __tablename__ = "request_variable_values"
    __table_args__ = (UniqueConstraint("request_id", "company_variable_id", name="uq_request_variable"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    request_id: Mapped[str] = mapped_column(String(36), ForeignKey("requests.id", ondelete="CASCADE"), nullable=False, index=True)
    company_variable_id: Mapped[str] = mapped_column(String(36), ForeignKey("company_variables.id", ondelete="CASCADE"), nullable=False, index=True)
    value: Mapped[str | None] = mapped_column(Text, nullable=True)

    request: Mapped[Request] = relationship(back_populates="variable_values")
    company_variable: Mapped[CompanyVariable] = relationship(back_populates="values")


class AuditLog(Base):
    __tablename__ = "audit_log"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    action: Mapped[str] = mapped_column(String(120), nullable=False)
    target_type: Mapped[str | None] = mapped_column(String(80), nullable=True)
    target_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, nullable=False)

    user: Mapped[User | None] = relationship(back_populates="audit_entries")
