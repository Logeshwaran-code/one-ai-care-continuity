"""Central configuration, all via environment variables (12-factor)."""
import base64
import hashlib
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[2] / ".env",
        extra="ignore",
    )

    env: str = "dev"
    database_url: str = "sqlite+aiosqlite:///./oneai.db"
    redis_url: str = ""
    jwt_secret: str = "dev-only-secret-change-me-dev-only-secret-change-me"
    access_ttl_min: int = 15
    refresh_ttl_days: int = 14
    phi_encryption_key: str = ""  # urlsafe-base64 32-byte Fernet key; REQUIRED when env != dev
    llm_provider: str = "mock"  # mock | openai_compat
    llm_base_url: str = ""
    llm_api_key: str = ""
    llm_model: str = ""
    llm_timeout_s: float = 20.0
    llm_retries: int = 2
    llm_cache_ttl_s: int = 600
    rate_limit_per_min: int = 120
    ocr_provider: str = "none"  # none | tesseract
    seed_demo: bool = True

    def fernet_key(self) -> bytes:
        if self.phi_encryption_key:
            return self.phi_encryption_key.encode()
        if self.env != "dev":
            raise RuntimeError("PHI_ENCRYPTION_KEY must be set outside dev")
        return base64.urlsafe_b64encode(hashlib.sha256(self.jwt_secret.encode()).digest())

    def validate_for_env(self) -> None:
        if self.env != "dev" and self.jwt_secret.startswith("dev-only"):
            raise RuntimeError("JWT_SECRET must be overridden outside dev")


settings = Settings()
