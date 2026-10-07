"""SQLAlchemy 2.0 models. PHI free-text columns use EncryptedText."""
from datetime import UTC, date, datetime

from sqlalchemy import JSON, Boolean, Date, DateTime, Float, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.security import EncryptedText


def utcnow() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(120))
    role: Mapped[str] = mapped_column(String(20), index=True)  # patient|family|health_worker|doctor|admin
    password_hash: Mapped[str] = mapped_column(String(255))
    language: Mapped[str] = mapped_column(String(5), default="en")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    revoked: Mapped[bool] = mapped_column(Boolean, default=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime)


class PatientProfile(Base):
    __tablename__ = "patient_profiles"
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    birth_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    allergies_enc: Mapped[str | None] = mapped_column(EncryptedText, nullable=True)  # JSON list
    conditions_enc: Mapped[str | None] = mapped_column(EncryptedText, nullable=True)  # JSON list


class Consent(Base):
    __tablename__ = "consents"
    id: Mapped[int] = mapped_column(primary_key=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    grantee_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    scopes: Mapped[list[str]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id: Mapped[int] = mapped_column(primary_key=True)
    at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)
    actor_id: Mapped[int | None] = mapped_column(Integer, index=True)
    actor_role: Mapped[str | None] = mapped_column(String(20))
    patient_id: Mapped[int | None] = mapped_column(Integer, index=True)
    action: Mapped[str] = mapped_column(String(80))
    scope: Mapped[str | None] = mapped_column(String(40))
    allowed: Mapped[bool] = mapped_column(Boolean, default=True)


class Medication(Base):
    __tablename__ = "medications"
    id: Mapped[int] = mapped_column(primary_key=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    prescriber_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    raw_name: Mapped[str] = mapped_column(String(200))
    product_key: Mapped[str | None] = mapped_column(String(120), nullable=True)
    generic_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    dose_text: Mapped[str | None] = mapped_column(EncryptedText, nullable=True)
    timing: Mapped[list[str]] = mapped_column(JSON, default=list)  # morning|afternoon|evening|night
    start_date: Mapped[date] = mapped_column(Date)
    course_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_antibiotic: Mapped[bool] = mapped_column(Boolean, default=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    confirmed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class Measurement(Base):
    __tablename__ = "measurements"
    __table_args__ = (Index("ix_meas_patient_kind_at", "patient_id", "kind", "measured_at"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    kind: Mapped[str] = mapped_column(String(10))  # bp|glucose|weight
    v1: Mapped[float] = mapped_column(Float)  # systolic | mg/dL | kg
    v2: Mapped[float | None] = mapped_column(Float, nullable=True)  # diastolic
    measured_at: Mapped[datetime] = mapped_column(DateTime)
    source: Mapped[str] = mapped_column(String(10), default="manual")
    note: Mapped[str | None] = mapped_column(EncryptedText, nullable=True)


class DoseLog(Base):
    __tablename__ = "dose_logs"
    __table_args__ = (UniqueConstraint("medication_id", "day", "slot"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    medication_id: Mapped[int] = mapped_column(ForeignKey("medications.id"))
    day: Mapped[date] = mapped_column(Date)
    slot: Mapped[str] = mapped_column(String(10))
    logged_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    source: Mapped[str] = mapped_column(String(10), default="manual")


class Appointment(Base):
    __tablename__ = "appointments"
    id: Mapped[int] = mapped_column(primary_key=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    when: Mapped[datetime] = mapped_column(DateTime)
    with_name: Mapped[str] = mapped_column(String(120))


class Task(Base):
    __tablename__ = "tasks"
    id: Mapped[int] = mapped_column(primary_key=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    assignee_role: Mapped[str] = mapped_column(String(20), default="health_worker")
    kind: Mapped[str] = mapped_column(String(30))
    title: Mapped[str] = mapped_column(String(200))
    detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(10), default="open")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class Screening(Base):
    __tablename__ = "screenings"
    id: Mapped[int] = mapped_column(primary_key=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    instrument: Mapped[str] = mapped_column(String(10))
    answers_enc: Mapped[str] = mapped_column(EncryptedText)
    score: Mapped[int] = mapped_column(Integer)
    band: Mapped[str] = mapped_column(String(30))
    escalated: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class VisitSummary(Base):
    __tablename__ = "visit_summaries"
    id: Mapped[int] = mapped_column(primary_key=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    created_by: Mapped[int] = mapped_column(Integer)
    content_enc: Mapped[str] = mapped_column(EncryptedText)  # JSON
    status: Mapped[str] = mapped_column(String(10), default="draft")  # draft|approved
    approved_by: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
