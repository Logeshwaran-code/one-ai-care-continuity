"""Container entrypoint step: create tables (Alembic migration if available) and seed demo data."""
import asyncio
import subprocess  # noqa: S404  # nosec B404
import sys

from app.config import settings
from app.db import init_db
from app.seed import seed

if __name__ == "__main__":
    if settings.env == "dev" and settings.database_url.startswith("sqlite"):
        asyncio.run(init_db())
    else:
        r = subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"], check=False)  # noqa: S603  # nosec B603
        if r.returncode != 0:
            print("alembic upgrade failed; refusing to start", file=sys.stderr)
            sys.exit(r.returncode or 1)
    if settings.seed_demo:
        asyncio.run(seed())
