from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select, update

from app.config import settings
from app.deps import CurrentUser, Session, require_roles
from app.models import AuditLog, PatientProfile, RefreshToken, User, utcnow
from app.security import create_access_token, hash_password, hash_token, new_refresh_token, verify_password

router = APIRouter(tags=["auth"])
EMAIL = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
ROLES = {"patient", "family", "health_worker", "doctor", "admin"}


class RegisterIn(BaseModel):
    email: str = Field(pattern=EMAIL, max_length=255)
    name: str = Field(min_length=1, max_length=120)
    password: str = Field(min_length=10, max_length=128)
    role: str = "patient"
    language: str = "en"
    birth_year: int | None = Field(default=None, ge=1900, le=2100)


class LoginIn(BaseModel):
    email: str = Field(pattern=EMAIL, max_length=255)
    password: str


class RefreshIn(BaseModel):
    refresh_token: str


class TokenOut(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    role: str
    user_id: int


async def _issue(session: Session, user: User) -> TokenOut:
    raw, h = new_refresh_token()
    session.add(RefreshToken(user_id=user.id, token_hash=h, expires_at=utcnow() + timedelta(days=settings.refresh_ttl_days)))
    await session.commit()
    return TokenOut(access_token=create_access_token(user.id, user.role), refresh_token=raw, role=user.role, user_id=user.id)


async def _create(session: Session, body: RegisterIn) -> User:
    if await session.scalar(select(User).where(User.email == body.email.lower())):
        raise HTTPException(status.HTTP_409_CONFLICT, "Email already registered")
    user = User(email=body.email.lower(), name=body.name, role=body.role, password_hash=hash_password(body.password), language=body.language)
    session.add(user)
    await session.flush()
    if body.role == "patient":
        session.add(PatientProfile(user_id=user.id, birth_year=body.birth_year, allergies_enc="[]", conditions_enc="[]"))
    await session.commit()
    return user


@router.post("/auth/register", response_model=TokenOut, status_code=201)
async def register(body: RegisterIn, session: Session) -> TokenOut:
    if body.role not in {"patient", "family"}:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Clinical and admin accounts are created by an admin")
    return await _issue(session, await _create(session, body))


@router.post("/admin/users", status_code=201, dependencies=[Depends(require_roles("admin"))])
async def admin_create_user(body: RegisterIn, session: Session) -> dict[str, int | str]:
    if body.role not in ROLES:
        raise HTTPException(422, "Unknown role")
    u = await _create(session, body)
    return {"id": u.id, "role": u.role}


@router.post("/auth/login", response_model=TokenOut)
async def login(body: LoginIn, session: Session) -> TokenOut:
    user = await session.scalar(select(User).where(User.email == body.email.lower()))
    if user is None or not user.is_active or not verify_password(body.password, user.password_hash):
        session.add(AuditLog(actor_id=user.id if user else None, action="login_failed", allowed=False))
        await session.commit()
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid email or password")
    session.add(AuditLog(actor_id=user.id, actor_role=user.role, action="login"))
    return await _issue(session, user)


@router.post("/auth/refresh", response_model=TokenOut)
async def refresh(body: RefreshIn, session: Session) -> TokenOut:
    """Rotating refresh tokens with reuse detection: replaying a used token revokes every session of that user."""
    tok = await session.scalar(select(RefreshToken).where(RefreshToken.token_hash == hash_token(body.refresh_token)))
    if tok is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid refresh token")
    if tok.revoked:
        await session.execute(update(RefreshToken).where(RefreshToken.user_id == tok.user_id).values(revoked=True))
        await session.commit()
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Refresh token reuse detected; all sessions revoked")
    if tok.expires_at < utcnow():
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Refresh token expired")
    tok.revoked = True
    user = await session.get(User, tok.user_id)
    if user is None or not user.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Unknown user")
    return await _issue(session, user)


@router.get("/me")
async def me(user: CurrentUser) -> dict[str, int | str]:
    return {"id": user.id, "name": user.name, "email": user.email, "role": user.role, "language": user.language}


@router.get("/admin/audit", dependencies=[Depends(require_roles("admin"))])
async def audit(session: Session, limit: int = 50, offset: int = 0) -> list[dict[str, object]]:
    rows = (await session.scalars(select(AuditLog).order_by(AuditLog.id.desc()).limit(min(limit, 200)).offset(offset))).all()
    return [{"id": r.id, "at": r.at.isoformat(), "actor_id": r.actor_id, "role": r.actor_role, "patient_id": r.patient_id,
             "action": r.action, "scope": r.scope, "allowed": r.allowed} for r in rows]
