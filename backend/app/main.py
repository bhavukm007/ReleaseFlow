from contextlib import asynccontextmanager
from collections import defaultdict, deque
import logging
import os
from time import monotonic

from fastapi import FastAPI
from fastapi import Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse

from app.api.auth import router as auth_router
from app.api.activities import router as activities_router
from app.api.releases import router as releases_router
from app.api.realtime import router as realtime_router
from app.api.teams import router as teams_router
from app.core.config import get_settings

settings = get_settings()
logger = logging.getLogger("uvicorn.error")
process_started = float(os.getenv("RELEASEFLOW_PROCESS_STARTED", monotonic()))


@asynccontextmanager
async def lifespan(_: FastAPI):
    logger.info(
        "startup_phase phase=application_ready elapsed_ms=%.1f pool_size=%d max_overflow=%d",
        (monotonic() - process_started) * 1000,
        settings.database_pool_size,
        settings.database_max_overflow,
    )
    yield


app = FastAPI(title=settings.app_name, version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=500)
requests_by_ip: dict[str, deque[float]] = defaultdict(deque)


@app.middleware("http")
async def rate_limit(request: Request, call_next):
    if request.url.path == "/health":
        return await call_next(request)
    now = monotonic()
    key = request.client.host if request.client else "unknown"
    bucket = requests_by_ip[key]
    while bucket and bucket[0] < now - 60:
        bucket.popleft()
    if len(bucket) >= settings.rate_limit_per_minute:
        return JSONResponse(status_code=429, content={"detail": "Too many requests"})
    bucket.append(now)
    return await call_next(request)


app.include_router(auth_router)
app.include_router(activities_router)
app.include_router(releases_router)
app.include_router(teams_router)
app.include_router(realtime_router)


@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
    return {"status": "healthy"}
