import logging
import time
import uuid
from collections import defaultdict, deque
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
from sqlalchemy import text

from app.config import settings
from app.db import SessionLocal, init_db
from app.routers import auth, patient, tools

logging.basicConfig(level=logging.INFO, format='{"ts":"%(asctime)s","level":"%(levelname)s","logger":"%(name)s","msg":"%(message)s"}')
log = logging.getLogger("api")
REQS = Counter("http_requests_total", "HTTP requests", ["method", "path", "status"])
LAT = Histogram("http_request_seconds", "HTTP latency", ["method", "path"])


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    settings.validate_for_env()
    await init_db()
    yield


app = FastAPI(title="ONE AI Healthcare Continuity Platform", version="0.1.0", lifespan=lifespan,
              description="AI assists. Humans decide. See SAFETY_AND_GUARDRAILS.md.")
_hits: dict[str, deque[float]] = defaultdict(deque)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5500",
        "http://127.0.0.1:5500",
        "http://localhost:8001",
        "http://127.0.0.1:8001",
        "http://localhost:8002",
        "http://127.0.0.1:8002",
        "http://localhost:8003",
        "http://127.0.0.1:8003",
    ] + (["null"] if settings.env == "dev" else []),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
#_hits: dict[str, deque[float]] = defaultdict(deque)

@app.middleware("http")
async def platform_middleware(request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
    rid = request.headers.get("x-request-id") or uuid.uuid4().hex[:12]
    ip = request.client.host if request.client else "?"
    now = time.monotonic()
    q = _hits[ip]
    while q and q[0] < now - 60:
        q.popleft()
    if request.url.path.startswith("/api") and len(q) >= settings.rate_limit_per_min:
        return JSONResponse({"detail": "Rate limit exceeded"}, status_code=429, headers={"Retry-After": "60"})
    q.append(now)
    start = time.perf_counter()
    response = await call_next(request)
    route = request.scope.get("route")
    path = getattr(route, "path", "unmatched")
    LAT.labels(request.method, path).observe(time.perf_counter() - start)
    REQS.labels(request.method, path, str(response.status_code)).inc()
    response.headers.update({"x-request-id": rid, "X-Content-Type-Options": "nosniff", "X-Frame-Options": "DENY", "Referrer-Policy": "no-referrer",
                             "Content-Security-Policy": "default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; script-src 'self'",
                             "Permissions-Policy": "microphone=(self)"})
    log.info("request", extra={"rid": rid, "path": path, "status": response.status_code})
    return response


for r in (auth.router, patient.router, tools.router):
    app.include_router(r, prefix="/api/v1")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/ready")
async def ready() -> dict[str, str]:
    async with SessionLocal() as s:
        await s.execute(text("select 1"))
    return {"status": "ready"}


@app.get("/metrics")
async def metrics() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


_static = Path(__file__).resolve().parent.parent / "static"
if not _static.exists():
    _static = Path(__file__).resolve().parent.parent.parent / "frontend"
if _static.exists():
    app.mount("/", StaticFiles(directory=_static, html=True), name="frontend")
