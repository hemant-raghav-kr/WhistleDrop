"""WhistleDrop Backend Main Application Entrypoint.

Provides:
- FastAPI application lifecycle & configuration
- CORS middleware
- Centralized exception handlers ensuring zero internal stack trace / database query leakage
- OpenAPI & Swagger documentation configuration
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.v1.api import api_router
from app.core.config import settings

logger = logging.getLogger("whistledrop")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager."""
    # Ensure tables exist for local SQLite development
    if settings.DATABASE_URL.startswith("sqlite"):
        from app.db.base import Base
        from app.db.session import engine
        Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    lifespan=lifespan,
    description=(
        "## WhistleDrop — Speak Without Being Seen\n\n"
        "Confidential whistleblower reporting system for the GDG on Campus SRM Technical Domain recruitment.\n\n"
        "### Key Security & Privacy Guarantees:\n"
        "- **Zero-Knowledge Anonymity**: No reporter identities, names, emails, phones, or IP addresses are stored.\n"
        "- **Cryptographic Case Codes**: High-entropy codes (2^80 combinations) stored exclusively as HMAC-SHA256 digests.\n"
        "- **Internal ID Concealment**: Public reporter endpoints never reveal database UUIDs or hashes.\n"
        "- **Strict Lifecycle State Transitions**: SUBMITTED -> UNDER_REVIEW -> RESOLVED or DISMISSED.\n"
        "- **Independent Moderator Auth**: Salted bcrypt password hashing and signed JWT bearer tokens."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    contact={
        "name": "WhistleDrop Security Team",
        "url": "https://github.com/hemant-raghav-kr/WhistleDrop",
    },
    license_info={
        "name": "MIT License",
    },
)

# Configure Cross-Origin Resource Sharing (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =====================================================================
# Centralized Error Handlers (Zero Implementation Leakage)
# =====================================================================

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Sanitize and format 422 validation errors."""
    formatted_errors = []
    for err in exc.errors():
        field_path = " -> ".join(str(loc) for loc in err.get("loc", []))
        formatted_errors.append({
            "field": field_path,
            "message": err.get("msg", "Invalid value"),
            "type": err.get("type", "value_error"),
        })

    return JSONResponse(
        status_code=422,
        content={
            "detail": formatted_errors,
            "error_type": "VALIDATION_ERROR",
        },
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Preserve standard HTTP exceptions without altering payload."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers=exc.headers,
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """Catch-all safety net: prevent raw database errors, schema info, or tracebacks from leaking."""
    logger.error("Unhandled server exception: %s", exc, exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "An internal server error occurred. Please contact system administrator.",
            "error_type": "INTERNAL_SERVER_ERROR",
        },
    )


# Mount API v1 router
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/", tags=["Health"])
def root_status():
    """Service status and foundational metadata."""
    return {
        "service": settings.PROJECT_NAME,
        "status": "online",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/health", tags=["Health"])
def health_check():
    """Liveness probe."""
    return {"status": "healthy"}
