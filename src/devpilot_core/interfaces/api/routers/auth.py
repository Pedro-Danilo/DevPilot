from __future__ import annotations

import hashlib
from typing import Any

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from devpilot_core.application import AuthApplicationService
from devpilot_core.identity.auth_models import CSRF_COOKIE_NAME, CSRF_HEADER_NAME, SESSION_COOKIE_NAME
from devpilot_core.identity.session_service import AuthenticationError, BootstrapUnavailable, CsrfInvalid, SessionInvalid

from ..dependencies import get_auth_service

router = APIRouter(tags=["auth"])

AUTH_LOGIN_ATTEMPTS_PER_MINUTE = 10
AUTH_LOGIN_WINDOW_SECONDS = 60


def _auth_rate_key(request: Request, username: str) -> str:
    normalized = (username or "").strip().lower()
    digest = hashlib.sha256(normalized.encode("utf-8", errors="ignore")).hexdigest()[:16]
    client = request.client.host if request.client is not None else "local"
    return f"login:{client}:{digest}"


def _check_login_rate(request: Request, username: str) -> tuple[bool, int]:
    limiter = request.app.state.auth_login_limiter
    allowed, _remaining, retry_after = limiter.consume(
        _auth_rate_key(request, username),
        limit=AUTH_LOGIN_ATTEMPTS_PER_MINUTE,
        window_seconds=AUTH_LOGIN_WINDOW_SECONDS,
    )
    return allowed, retry_after



class BootstrapOwnerBody(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    display_name: str = Field(min_length=1, max_length=128)
    password: str = Field(min_length=12, max_length=128)


class LoginBody(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=1, max_length=128)


def _cookie_secure(request: Request) -> bool:
    return request.url.scheme.lower() == "https"


def _set_session_cookies(response: JSONResponse, request: Request, token: str, csrf_token: str) -> None:
    secure = _cookie_secure(request)
    response.set_cookie(SESSION_COOKIE_NAME, token, httponly=True, secure=secure, samesite="strict", path="/")
    response.set_cookie(CSRF_COOKIE_NAME, csrf_token, httponly=False, secure=secure, samesite="strict", path="/")


def _clear_session_cookies(response: JSONResponse, request: Request) -> None:
    secure = _cookie_secure(request)
    response.delete_cookie(SESSION_COOKIE_NAME, path="/", secure=secure, httponly=True, samesite="strict")
    response.delete_cookie(CSRF_COOKIE_NAME, path="/", secure=secure, httponly=False, samesite="strict")


def _safe_session_payload(issue) -> dict[str, Any]:
    return {"ok": True, "session": issue.context.to_safe_dict(), "csrf_delivery": "double-submit-cookie", "session_cookie": {"name": SESSION_COOKIE_NAME, "http_only": True, "same_site": "strict", "secret_in_body": False}}


def _error(message: str, status: int, code: str) -> JSONResponse:
    return JSONResponse({"ok": False, "error": {"code": code, "message": message}, "secret_exposed": False}, status_code=status)


@router.get("/api/v1/auth/bootstrap/status")
def bootstrap_status(service: AuthApplicationService = Depends(get_auth_service)) -> dict[str, Any]:
    return {"ok": True, **service.bootstrap_status()}


@router.post("/api/v1/auth/bootstrap/owner")
def bootstrap_owner(body: BootstrapOwnerBody, request: Request, service: AuthApplicationService = Depends(get_auth_service)) -> JSONResponse:
    try:
        issue = service.bootstrap_owner(username=body.username, display_name=body.display_name, password=body.password)
    except (BootstrapUnavailable, ValueError) as exc:
        return _error(str(exc), 409 if isinstance(exc, BootstrapUnavailable) else 400, "AUTH_BOOTSTRAP_BLOCK")
    response = JSONResponse(_safe_session_payload(issue), status_code=201)
    _set_session_cookies(response, request, issue.token, issue.csrf_token)
    return response


@router.get("/api/v1/auth/session/status")
def session_status(request: Request, service: AuthApplicationService = Depends(get_auth_service)) -> dict[str, Any]:
    token = request.cookies.get(SESSION_COOKIE_NAME, "")
    return {"ok": True, **service.inspect_session_state(token), "secret_exposed": False}


@router.post("/api/v1/auth/login")
def login(body: LoginBody, request: Request, service: AuthApplicationService = Depends(get_auth_service)) -> JSONResponse:
    allowed, retry_after = _check_login_rate(request, body.username)
    if not allowed:
        response = _error("local login attempt budget exceeded", 429, "AUTH_LOGIN_RATE_LIMIT_BLOCK")
        response.headers["Retry-After"] = str(retry_after)
        return response
    try:
        issue = service.login(username=body.username, password=body.password)
    except (AuthenticationError, ValueError):
        return _error("invalid credentials", 401, "AUTH_INVALID_CREDENTIALS")
    response = JSONResponse(_safe_session_payload(issue), status_code=200)
    _set_session_cookies(response, request, issue.token, issue.csrf_token)
    return response


@router.get("/api/v1/auth/session")
def session(request: Request, service: AuthApplicationService = Depends(get_auth_service)) -> JSONResponse:
    token = request.cookies.get(SESSION_COOKIE_NAME, "")
    try:
        context = service.resolve(token)
    except SessionInvalid:
        return _error("authenticated session required", 401, "AUTH_SESSION_REQUIRED")
    return JSONResponse({"ok": True, "session": context.to_safe_dict()}, status_code=200)


@router.post("/api/v1/auth/session/rotate")
def rotate(request: Request, service: AuthApplicationService = Depends(get_auth_service)) -> JSONResponse:
    token = request.cookies.get(SESSION_COOKIE_NAME, "")
    csrf = request.headers.get(CSRF_HEADER_NAME, "")
    try:
        issue = service.rotate(token=token, csrf_token=csrf)
    except (SessionInvalid, CsrfInvalid):
        return _error("session rotation denied", 403, "AUTH_SESSION_ROTATION_BLOCK")
    response = JSONResponse(_safe_session_payload(issue), status_code=200)
    _set_session_cookies(response, request, issue.token, issue.csrf_token)
    return response


@router.post("/api/v1/auth/logout")
def logout(request: Request, service: AuthApplicationService = Depends(get_auth_service)) -> JSONResponse:
    token = request.cookies.get(SESSION_COOKIE_NAME, "")
    csrf = request.headers.get(CSRF_HEADER_NAME, "")
    try:
        result = service.logout(token=token, csrf_token=csrf)
    except (SessionInvalid, CsrfInvalid):
        return _error("logout denied", 403, "AUTH_LOGOUT_BLOCK")
    response = JSONResponse({"ok": result.revoked, "revoked": result.revoked, "reason": result.reason, "secret_exposed": False}, status_code=200)
    _clear_session_cookies(response, request)
    return response


@router.post("/api/v1/auth/session/revoke")
def revoke_current(request: Request, service: AuthApplicationService = Depends(get_auth_service)) -> JSONResponse:
    token = request.cookies.get(SESSION_COOKIE_NAME, "")
    csrf = request.headers.get(CSRF_HEADER_NAME, "")
    try:
        result = service.revoke_current(token=token, csrf_token=csrf)
    except (SessionInvalid, CsrfInvalid):
        return _error("session revoke denied", 403, "AUTH_SESSION_REVOKE_BLOCK")
    response = JSONResponse({"ok": result.revoked, "revoked": result.revoked, "secret_exposed": False}, status_code=200)
    _clear_session_cookies(response, request)
    return response


@router.get("/api/v1/auth/capabilities")
def capabilities(request: Request) -> JSONResponse:
    principal = getattr(request.state, "authenticated_principal", None)
    if principal is None:
        return _error("authenticated human session required", 401, "AUTH_SESSION_REQUIRED")
    workspace_id = request.query_params.get("workspace_id") or "devpilot-local"
    view = request.app.state.application_service.rbac.capability_view(principal, workspace_id=workspace_id)
    return JSONResponse({"ok": True, "capability_view": view}, status_code=200)
