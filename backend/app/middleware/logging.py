import json
import logging
import re
import time
import uuid
from collections.abc import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("nyayamitra.access")

# Regex patterns for common Indian PII
PHONE_REGEX = re.compile(r"(\+91[-\s]?)?[6-9]\d{9}")
AADHAAR_REGEX = re.compile(r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}\b")
PAN_REGEX = re.compile(r"\b[A-Z]{5}[0-9]{4}[A-Z]{1}\b", re.IGNORECASE)
EMAIL_REGEX = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")


def redact_pii(text: str) -> str:
    """Mask sensitive citizen identifiers in logs."""
    if not text:
        return text
    text = AADHAAR_REGEX.sub("[REDACTED_AADHAAR]", text)
    text = PAN_REGEX.sub("[REDACTED_PAN]", text)
    text = PHONE_REGEX.sub("[REDACTED_PHONE]", text)
    text = EMAIL_REGEX.sub("[REDACTED_EMAIL]", text)
    return text


class StructuredLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware that assigns a unique correlation ID to each request,
    computes request duration, and logs structured JSON without raw PII.
    """
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
        request.state.correlation_id = correlation_id
        start_time = time.perf_counter()

        response: Response = await call_next(request)

        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
        response.headers["X-Correlation-ID"] = correlation_id

        log_data = {
            "timestamp": time.time(),
            "correlation_id": correlation_id,
            "method": request.method,
            "path": redact_pii(request.url.path),
            "status_code": response.status_code,
            "duration_ms": duration_ms,
            "client_ip": request.client.host if request.client else "unknown",
        }

        logger.info(json.dumps(log_data))
        return response
