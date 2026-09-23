"""
NyayaMitra Observability & Correlation ID Middleware
Generates and propagates distributed correlation IDs, injects Server-Timing headers,
and enforces PII redaction on all request telemetry.
"""

from datetime import datetime, timezone
import logging
import re
import time
import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("nyayamitra.observability")


def mask_sensitive_pii(text: str) -> str:
    """Masks Indian national IDs, phone numbers, and emails from trace logs."""
    # Aadhaar (12 digits)
    text = re.sub(r"\b\d{4}[ -]?\d{4}[ -]?\d{4}\b", "[AADHAAR_REDACTED]", text)
    # PAN card (5 letters, 4 digits, 1 letter)
    text = re.sub(r"\b[A-Z]{5}\d{4}[A-Z]\b", "[PAN_REDACTED]", text, flags=re.IGNORECASE)
    # Phone number (10 digits starting with 6-9)
    text = re.sub(r"\b(?:(?:\+91|0)?[ -]?)?[6789]\d{9}\b", "[PHONE_REDACTED]", text)
    # Email address
    text = re.sub(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", "[EMAIL_REDACTED]", text)
    return text


class ObservabilityMiddleware(BaseHTTPMiddleware):
    """
    Tracks request latency, injects standard correlation and timing headers,
    and records metrics in the metrics collector.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        start_time = time.perf_counter()
        
        # 1. Extract or Generate Correlation and Request IDs
        correlation_id = request.headers.get("X-Correlation-ID") or f"corr-{uuid.uuid4().hex[:12]}"
        request_id = request.headers.get("X-Request-ID") or f"req-{uuid.uuid4().hex[:12]}"

        # Attach to request state for downstream handlers
        request.state.correlation_id = correlation_id
        request.state.request_id = request_id

        # 2. Process Request
        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception as exc:
            duration_ms = (time.perf_counter() - start_time) * 1000
            safe_err = mask_sensitive_pii(str(exc))
            logger.error(f"Unhandled exception [cid={correlation_id}] {request.method} {request.url.path}: {safe_err} ({duration_ms:.2f}ms)")
            raise exc

        # 3. Calculate Latency & Inject Headers
        duration_ms = (time.perf_counter() - start_time) * 1000
        
        response.headers["X-Correlation-ID"] = correlation_id
        response.headers["X-Request-ID"] = request_id
        response.headers["Server-Timing"] = f"app;dur={duration_ms:.2f}, desc=\"FastAPI Execution\""

        # 4. Asynchronously record in global metrics collector if available
        try:
            from app.services.metrics_collector import global_metrics
            global_metrics.record_request(
                method=request.method,
                path=request.url.path,
                status_code=status_code,
                duration_ms=duration_ms,
            )
        except Exception:
            pass

        return response
