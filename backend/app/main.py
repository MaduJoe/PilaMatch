import asyncio
import logging
import time

import structlog
from fastapi import Depends, FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logging import setup_logging
from app.api.v1.router import api_router
from app.db.session import get_db

limiter = Limiter(key_func=get_remote_address, default_limits=["100/minute"])

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json" if settings.DEBUG else None,
    docs_url=f"{settings.API_V1_PREFIX}/docs" if settings.DEBUG else None,
    redoc_url=f"{settings.API_V1_PREFIX}/redoc" if settings.DEBUG else None,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
)


@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    if not settings.DEBUG:
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response


@app.middleware("http")
async def log_requests(request, call_next):
    logger = structlog.get_logger()
    start = time.time()
    response = await call_next(request)
    duration = time.time() - start
    logger.info(
        "request",
        method=request.method,
        path=request.url.path,
        status=response.status_code,
        duration_ms=round(duration * 1000),
    )
    return response



@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch unhandled exceptions and return safe error response."""
    logger = structlog.get_logger()
    logger.error(
        "unhandled_exception",
        method=request.method,
        path=request.url.path,
        error=str(exc),
        error_type=type(exc).__name__,
    )
    return JSONResponse(
        status_code=500,
        content={
            "detail": {
                "code": "INTERNAL_ERROR",
                "message": "서버 내부 오류가 발생했습니다. 잠시 후 다시 시도해주세요.",
            }
        },
    )


# Include API router
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    checks = {"status": "healthy", "version": settings.APP_VERSION}
    try:
        await db.execute(text("SELECT 1"))
        checks["database"] = "connected"
    except Exception:
        checks["database"] = "disconnected"
        checks["status"] = "degraded"
    return checks


_renewal_task = None
_dispatch_timeout_task = None
_availability_expiry_task = None
_completion_auto_task = None


async def _renewal_scheduler():
    """Background task: check and process auto-renewals every hour."""
    renewal_logger = logging.getLogger("renewal_scheduler")
    while True:
        await asyncio.sleep(3600)  # Check every hour
        try:
            from app.db.session import AsyncSessionLocal
            async with AsyncSessionLocal() as db:
                from app.services.subscription import SubscriptionService
                service = SubscriptionService(db)
                due = await service.check_renewals_due()
                if due:
                    renewal_logger.info(f"Processing {len(due)} subscription renewals")
                    for sub in due:
                        try:
                            await service.process_auto_renewal(sub.id)
                        except Exception as e:
                            renewal_logger.error(f"Renewal failed for {sub.id}: {e}")
        except Exception as e:
            renewal_logger.error(f"Renewal scheduler error: {e}")


async def _dispatch_timeout_scheduler():
    """Check for timed-out dispatch records every 30 seconds."""
    scheduler_logger = logging.getLogger("dispatch_timeout_scheduler")
    while True:
        await asyncio.sleep(30)
        try:
            from app.db.session import AsyncSessionLocal
            async with AsyncSessionLocal() as db:
                from app.services.dispatch_engine import DispatchEngine
                engine = DispatchEngine(db)
                count = await engine.check_dispatch_timeouts()
                if count > 0:
                    await db.commit()
        except Exception as e:
            scheduler_logger.error(f"Dispatch timeout scheduler error: {e}")


async def _availability_expiry_scheduler():
    """Expire stale availability records every 5 minutes."""
    scheduler_logger = logging.getLogger("availability_expiry_scheduler")
    while True:
        await asyncio.sleep(300)
        try:
            from app.db.session import AsyncSessionLocal
            async with AsyncSessionLocal() as db:
                from app.services.instructor_availability import expire_stale_availabilities
                count = await expire_stale_availabilities(db)
                if count > 0:
                    await db.commit()
        except Exception as e:
            scheduler_logger.error(f"Availability expiry scheduler error: {e}")


async def _completion_auto_scheduler():
    """Auto-complete stale completion records every hour."""
    scheduler_logger = logging.getLogger("completion_auto_scheduler")
    while True:
        await asyncio.sleep(3600)
        try:
            from app.db.session import AsyncSessionLocal
            async with AsyncSessionLocal() as db:
                from app.services.completion import auto_complete_stale_records
                count = await auto_complete_stale_records(db)
                if count > 0:
                    await db.commit()
        except Exception as e:
            scheduler_logger.error(f"Completion auto scheduler error: {e}")


@app.on_event("startup")
async def startup_event():
    global _renewal_task, _dispatch_timeout_task, _availability_expiry_task, _completion_auto_task
    setup_logging()

    from app.core.firebase import init_firebase
    init_firebase()

    _renewal_task = asyncio.create_task(_renewal_scheduler())
    _dispatch_timeout_task = asyncio.create_task(_dispatch_timeout_scheduler())
    _availability_expiry_task = asyncio.create_task(_availability_expiry_scheduler())
    _completion_auto_task = asyncio.create_task(_completion_auto_scheduler())


@app.on_event("shutdown")
async def shutdown_event():
    global _renewal_task, _dispatch_timeout_task, _availability_expiry_task, _completion_auto_task
    if _renewal_task:
        _renewal_task.cancel()
    if _dispatch_timeout_task:
        _dispatch_timeout_task.cancel()
    if _availability_expiry_task:
        _availability_expiry_task.cancel()
    if _completion_auto_task:
        _completion_auto_task.cancel()
