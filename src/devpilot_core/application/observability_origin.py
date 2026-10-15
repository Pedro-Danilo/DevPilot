"""R01-12: secret-free, evidence-backed provider observability (no execution)."""
from __future__ import annotations
from typing import Any, Mapping
import re

_ID = re.compile(r"^[a-zA-Z0-9_.:/-]{1,128}$")

def _identity(value: Any) -> str:
    if value is None or value == "":
        return "NOT_AVAILABLE"
    s = str(value)
    return s if _ID.fullmatch(s) else "REDACTED"

def _hash(value: Any) -> str:
    s = str(value or "")
    return s if re.fullmatch(r"[a-f0-9]{64}", s) else "NOT_AVAILABLE"

def _category(value: Any) -> str:
    # Arbitrary denial messages and free-text metadata are never echoed.
    s = str(value or "")
    return s if re.fullmatch(r"[a-zA-Z0-9_-]{1,80}", s) else "NOT_AVAILABLE"

def project_provider_origin(
    provenance: Mapping[str, Any] | None,
    receipt: Mapping[str, Any] | None,
    *, demonstration: bool = False,
) -> dict[str, Any]:
    """Project real receipt fields only; no secret-bearing metadata or prompt content."""
    p, rc = dict(provenance or {}), dict(receipt or {})
    linked = (
        bool(p) and bool(rc)
        and _hash(p.get("provenance_sha256")) != "NOT_AVAILABLE"
        and _hash(p.get("provenance_sha256")) == _hash(rc.get("provenance_sha256"))
        and _hash(p.get("route_sha256")) == _hash(rc.get("route_sha256"))
        and _identity(p.get("request_id")) == _identity(rc.get("request_id"))
    )
    called = linked and rc.get("model_call_performed") is True
    cost = rc.get("cost_usd")
    # Zero is established only for an explicit non-executed deterministic preview.
    zero_known = linked and demonstration and rc.get("model_call_performed") is False and rc.get("execution_attempted") is False and cost == 0
    measured = called and isinstance(cost, (int, float)) and not isinstance(cost, bool) and 0 <= cost < 1e9
    if measured: cost_state, amount = "RECEIPT_REPORTED", float(cost)
    elif zero_known: cost_state, amount = "ZERO_NO_EXECUTION", 0.0
    else: cost_state, amount = "NOT_AVAILABLE", None
    return {
        "schema": "MP132.R01.12.origin.v1",
        "source": "FOUNDATION_PREVIEW" if demonstration else "RUNTIME_RECEIPT",
        "receipt_linked": linked,
        "status": _category(rc.get("outcome")) if linked else "NOT_AVAILABLE",
        "request_id": _identity(rc.get("request_id")) if linked else "NOT_AVAILABLE",
        "provider_class": _identity(rc.get("provider_class")) if linked else "NOT_AVAILABLE",
        "provider": _identity(rc.get("provider_id")) if linked else "NOT_AVAILABLE",
        "model": _identity(rc.get("model_id")) if linked else "NOT_AVAILABLE",
        "route_sha256": _hash(rc.get("route_sha256")) if linked else "NOT_AVAILABLE",
        "receipt_sha256": _hash(rc.get("receipt_sha256")) if linked else "NOT_AVAILABLE",
        "fallback": _category((rc.get("fallback") or {}).get("reason")) if linked and isinstance(rc.get("fallback"), dict) else "NOT_AVAILABLE",
        "error": _category(rc.get("denial_reason")) if linked else "NOT_AVAILABLE",
        "cost": {"status": cost_state, "usd": amount},
        "network_used": rc.get("network_used") is True if linked else None,
        "external_api_used": rc.get("external_api_used") is True if linked else None,
        "model_call_performed": called if linked else None,
        "warning": "La vista previa no acredita inferencia ni costo de un modelo" if demonstration else "No sustituye mediciones ni permisos operativos",
    }
