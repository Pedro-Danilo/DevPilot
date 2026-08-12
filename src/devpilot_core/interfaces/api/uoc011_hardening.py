from __future__ import annotations

from dataclasses import dataclass
import hashlib
from threading import Lock
import time
from typing import Any

from fastapi import Request

UOC011_CONTENT_SECURITY_POLICY = (
    "default-src 'none'; base-uri 'none'; frame-ancestors 'none'; form-action 'none'; "
    "img-src 'self' data:; style-src 'self'; script-src 'self'; "
    "connect-src 'self' http://127.0.0.1:8787 http://localhost:8787"
)

UOC011_API_HARDENING_HEADERS: dict[str, str] = {
    "Content-Security-Policy": UOC011_CONTENT_SECURITY_POLICY,
    "X-DevPilot-UOC011-Hardening": "csp+size+rate+cache",
}

@dataclass(frozen=True)
class Uoc011ApiHardeningConfig:
    max_request_body_bytes: int = 1_048_576
    rate_limit_window_seconds: int = 60
    rate_limit_requests_per_window: int = 600


class FixedWindowRateLimiter:
    """Process-local bounded limiter for the localhost API.

    This is intentionally not a distributed quota mechanism. It limits accidental
    or abusive local bursts without introducing Redis/network dependencies.
    """

    def __init__(self) -> None:
        self._lock = Lock()
        self._entries: dict[str, tuple[int, float]] = {}

    def consume(self, key: str, *, limit: int, window_seconds: int, now: float | None = None) -> tuple[bool, int, int]:
        current = time.monotonic() if now is None else float(now)
        with self._lock:
            count, started = self._entries.get(key, (0, current))
            if current - started >= window_seconds:
                count, started = 0, current
            count += 1
            self._entries[key] = (count, started)
            remaining = max(0, limit - count)
            retry_after = max(1, int(window_seconds - (current - started)))
            return count <= limit, remaining, retry_after


def request_rate_key(request: Request) -> str:
    token = request.headers.get("X-DevPilot-Token") or request.headers.get("Authorization") or ""
    if token:
        digest = hashlib.sha256(token.encode("utf-8", errors="ignore")).hexdigest()[:16]
        return f"token:{digest}"
    client_host = request.client.host if request.client is not None else "unknown"
    return f"client:{client_host}"


async def inspect_request_hardening(
    request: Request,
    *,
    config: Uoc011ApiHardeningConfig,
    limiter: FixedWindowRateLimiter,
) -> dict[str, Any]:
    """Return a deterministic PASS/BLOCK decision for local request budgets."""

    if request.method.upper() == "OPTIONS" or not request.url.path.startswith("/api/v1/"):
        return {"ok": True, "remaining": config.rate_limit_requests_per_window}

    allowed, remaining, retry_after = limiter.consume(
        request_rate_key(request),
        limit=config.rate_limit_requests_per_window,
        window_seconds=config.rate_limit_window_seconds,
    )
    if not allowed:
        return {
            "ok": False,
            "status_code": 429,
            "finding_id": "API_LOCAL_RATE_LIMIT_BLOCK",
            "message": "Local API request budget exceeded; retry after the bounded window.",
            "remaining": 0,
            "retry_after": retry_after,
        }

    if request.method.upper() in {"POST", "PUT", "PATCH"}:
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                declared = int(content_length)
            except ValueError:
                return {
                    "ok": False,
                    "status_code": 400,
                    "finding_id": "API_CONTENT_LENGTH_INVALID_BLOCK",
                    "message": "Invalid Content-Length for local API request.",
                    "remaining": remaining,
                }
            if declared > config.max_request_body_bytes:
                return {
                    "ok": False,
                    "status_code": 413,
                    "finding_id": "API_REQUEST_BODY_SIZE_BLOCK",
                    "message": "Local API request body exceeds the configured size budget.",
                    "remaining": remaining,
                }
        body = await request.body()
        if len(body) > config.max_request_body_bytes:
            return {
                "ok": False,
                "status_code": 413,
                "finding_id": "API_REQUEST_BODY_SIZE_BLOCK",
                "message": "Local API request body exceeds the configured size budget.",
                "remaining": remaining,
            }

    return {"ok": True, "remaining": remaining}
