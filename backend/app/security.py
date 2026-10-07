"""Password hashing, JWT, refresh-token helpers and field-level PHI encryption."""
import hashlib
import hmac
import secrets
from datetime import UTC, datetime, timedelta
from functools import lru_cache
from typing import Any

import jwt
from cryptography.fernet import Fernet
from sqlalchemy import Text
from sqlalchemy.types import TypeDecorator

from app.config import settings

_ITER = 200_000
ALGO = "HS256"


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, _ITER)
    return f"pbkdf2${_ITER}${salt.hex()}${dk.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        _, it, salt, dk = stored.split("$")
        calc = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), int(it))
        return hmac.compare_digest(calc.hex(), dk)
    except ValueError:
        return False


def create_access_token(user_id: int, role: str) -> str:
    now = datetime.now(UTC)
    payload = {"sub": str(user_id), "role": role, "iat": now, "exp": now + timedelta(minutes=settings.access_ttl_min), "typ": "access"}
    return jwt.encode(payload, settings.jwt_secret, algorithm=ALGO)


def decode_access_token(token: str) -> dict[str, Any]:
    data = jwt.decode(token, settings.jwt_secret, algorithms=[ALGO])
    if data.get("typ") != "access":
        raise jwt.InvalidTokenError("wrong token type")
    return data


def new_refresh_token() -> tuple[str, str]:
    raw = secrets.token_urlsafe(48)
    return raw, hash_token(raw)


def hash_token(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


@lru_cache(maxsize=1)
def _fernet() -> Fernet:
    return Fernet(settings.fernet_key())


class EncryptedText(TypeDecorator):  # type: ignore[type-arg]
    """Transparent field-level encryption (Fernet: AES-128-CBC + HMAC) for PHI columns."""

    impl = Text
    cache_ok = True

    def process_bind_param(self, value: str | None, dialect: Any) -> str | None:
        return None if value is None else _fernet().encrypt(value.encode()).decode()

    def process_result_value(self, value: str | None, dialect: Any) -> str | None:
        return None if value is None else _fernet().decrypt(value.encode()).decode()
