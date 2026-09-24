import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.core.config import get_settings
from app.middleware.logging import StructuredLoggingMiddleware
from app.middleware.observability import ObservabilityMiddleware
from app.middleware.security import SecurityHardeningMiddleware
from app.core.database import init_db
from app.routers.health import router as health_router
from app.routers.sources import router as sources_router
from app.routers.corpus import router as corpus_router
from app.routers.rag import router as rag_router
from app.routers.intake import router as intake_router
from app.routers.documents import router as documents_router
from app.routers.generator import router as generator_router
from app.routers.escalation import router as escalation_router
from app.routers.compare import router as compare_router
from app.routers.meta import router as meta_router

# Configure root logger
settings = get_settings()
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger("nyayamitra")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing NyayaMitra Legal Access Platform Backend...")
    try:
        await init_db()
        logger.info("Database tables verified.")
    except Exception as exc:
        logger.warning(f"Database initialization warning: {exc}")
    yield
    logger.info("Shutting down NyayaMitra Backend...")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="NyayaMitra: AI for Legal Assistance & Access in India",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Correlation-ID"],
)

# Custom Structured Logging & PII Protection Middleware
app.add_middleware(StructuredLoggingMiddleware)


# Security Headers Middleware
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        return response


app.add_middleware(SecurityHeadersMiddleware)

# Security Hardening & Rate Limiting Middleware
app.add_middleware(SecurityHardeningMiddleware)

# Observability & Correlation ID Middleware
app.add_middleware(ObservabilityMiddleware)

# Mount versioned API routers
app.include_router(health_router, prefix=settings.API_V1_PREFIX)
app.include_router(sources_router, prefix=settings.API_V1_PREFIX)
app.include_router(corpus_router, prefix=settings.API_V1_PREFIX)
app.include_router(rag_router, prefix=settings.API_V1_PREFIX)
app.include_router(intake_router, prefix=settings.API_V1_PREFIX)
app.include_router(documents_router, prefix=settings.API_V1_PREFIX)
app.include_router(generator_router, prefix=settings.API_V1_PREFIX)
app.include_router(escalation_router, prefix=settings.API_V1_PREFIX)
app.include_router(compare_router, prefix=settings.API_V1_PREFIX)
app.include_router(meta_router, prefix=settings.API_V1_PREFIX)


@app.get("/")
async def root():
    return JSONResponse({
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "message": "Welcome to NyayaMitra Legal Access Platform API",
        "docs": "/docs",
        "health": f"{settings.API_V1_PREFIX}/health"
    })
