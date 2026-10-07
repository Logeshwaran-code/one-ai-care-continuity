"""Auth dependencies, RBAC and consent-based, audited patient-data access."""
import json
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.models import AuditLog, Consent, PatientProfile, User
from app.security import decode_access_token

bearer = HTTPBearer(auto_error=False)
Session = Annotated[AsyncSession, Depends(get_session)]
ALL_SCOPES = ["medications", "measurements", "adherence", "appointments", "summary", "screening"]


async def current_user(session: Session, cred: HTTPAuthorizationCredentials | None = Depends(bearer)) -> User:
    if cred is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not authenticated")
    try:
        data = decode_access_token(cred.credentials)
    except jwt.PyJWTError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired token") from exc
    user = await session.get(User, int(data["sub"]))
    if user is None or not user.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Unknown user")
    return user


CurrentUser = Annotated[User, Depends(current_user)]


def require_roles(*roles: str):  # type: ignore[no-untyped-def]
    async def dep(user: CurrentUser) -> User:
        if user.role not in roles:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Role not permitted")
        return user

    return dep


async def authorize(session: AsyncSession, actor: User, patient_id: int, scope: str, action: str) -> None:
    """Allow self access; otherwise require an active patient consent that includes `scope`. Always audited.
    Admins never get PHI access (they manage users and read the audit log only)."""
    allowed = actor.id == patient_id and actor.role == "patient"
    if not allowed and actor.role != "admin":
        c = await session.scalar(select(Consent).where(
            Consent.patient_id == patient_id, Consent.grantee_id == actor.id, Consent.revoked_at.is_(None)))
        allowed = c is not None and scope in c.scopes
    session.add(AuditLog(actor_id=actor.id, actor_role=actor.role, patient_id=patient_id, action=action, scope=scope, allowed=allowed))
    await session.commit()
    if not allowed:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "No consent for this data")


async def profile_lists(session: AsyncSession, patient_id: int) -> tuple[list[str], list[str]]:
    p = await session.get(PatientProfile, patient_id)
    if p is None:
        return [], []
    return json.loads(p.allergies_enc or "[]"), json.loads(p.conditions_enc or "[]")
