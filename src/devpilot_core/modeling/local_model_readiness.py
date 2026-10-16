"""R02-02: read-only local model readiness; never inference or authority grant."""
from __future__ import annotations
import os
import platform
from pathlib import Path
from typing import Any

from devpilot_core.modeling.local_provider_discovery import LocalProviderDiscoveryOptions, LocalProviderDiscoveryService

PROVIDERS = ("ollama", "lmstudio")
TASKS = ("product-definition", "technical-design")


def host_resources() -> dict[str, Any]:
    """Observed host properties only; missing values explicitly remain unknown."""
    cpu = os.cpu_count()
    ram = None
    try:
        if os.name == "nt":
            import ctypes
            class MemoryStatus(ctypes.Structure):
                _fields_ = [("dwLength",ctypes.c_ulong),("dwMemoryLoad",ctypes.c_ulong),
                    ("ullTotalPhys",ctypes.c_ulonglong),("ullAvailPhys",ctypes.c_ulonglong),
                    ("ullTotalPageFile",ctypes.c_ulonglong),("ullAvailPageFile",ctypes.c_ulonglong),
                    ("ullTotalVirtual",ctypes.c_ulonglong),("ullAvailVirtual",ctypes.c_ulonglong),
                    ("ullAvailExtendedVirtual",ctypes.c_ulonglong)]
            data = MemoryStatus(); data.dwLength = ctypes.sizeof(data)
            if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(data)):
                ram = int(data.ullTotalPhys)
        elif Path("/proc/meminfo").is_file():
            for line in Path("/proc/meminfo").read_text(encoding="ascii").splitlines():
                if line.startswith("MemTotal:"):
                    ram = int(line.split()[1]) * 1024
                    break
    except (OSError, ValueError, AttributeError):
        pass
    return {"cpu_logical_count": cpu, "ram_total_bytes": ram,
            "host_architecture": platform.machine() or "NOT_AVAILABLE",
            "gpu": "NOT_AVAILABLE", "gpu_vram_bytes": None,
            "measured": {"cpu": cpu is not None, "ram": ram is not None, "gpu": False},
            "note": "Hardware inventory is diagnostic, not a model fit benchmark."}


def project_local_readiness(root: Path, *, probe: bool = False) -> dict[str, Any]:
    """No probe on refresh; explicit probe may contact validated local loopback endpoints."""
    result = LocalProviderDiscoveryService(Path(root), LocalProviderDiscoveryOptions(
        probe=probe, provider_ids=PROVIDERS, probe_timeout_seconds=2.0)).build()
    report = (result.data or {}).get("report", {})
    items = []
    for row in report.get("providers", []):
        configured = bool(row.get("configured"))
        policy_ok = bool((row.get("endpoint_policy") or {}).get("ok"))
        healthy = row.get("healthy") is True and row.get("probe_attempted") is True
        installed = bool(row.get("model_discovered"))
        reasons = []
        if not configured: reasons.append("LOCAL_PROVIDER_NOT_CONFIGURED")
        if configured and not policy_ok: reasons.append("LOCAL_ENDPOINT_POLICY_DENIED")
        if not probe: reasons.append("HEALTH_NOT_PROBED")
        elif configured and policy_ok and not healthy: reasons.append("LOCAL_HEALTH_NOT_CONFIRMED")
        if healthy and not installed: reasons.append("NO_MODEL_DISCOVERED")
        reasons.append("TASK_DATASET_EVALUATION_REQUIRED")
        tasks = [{"task_type": task, "evaluated": False, "evaluation_state": "NOT_TESTED",
                  "eligible": False, "reason": "TASK_DATASET_EVALUATION_REQUIRED"} for task in TASKS]
        items.append({"provider_id": row["provider_id"], "supported": True,
            "configured": configured, "healthy": healthy if probe and configured and policy_ok else None,
            "healthy_state": ("HEALTHY" if healthy else "UNAVAILABLE") if probe and configured and policy_ok else "NOT_TESTED",
            "models": list(row.get("models") or [])[:32] if probe else [],
            "model_discovered": installed if probe else None,
            "evaluated": False, "eligible": False, "tasks": tasks, "reasons": reasons,
            "endpoint_policy_ok": policy_ok, "endpoint_class": "loopback-only",
            "probe_attempted": bool(row.get("probe_attempted")),
            "configured_enabled": bool(row.get("enabled")),
            "runtime_modified": False, "fallback": "mock-explicit-only"})
    return {"schema": "MP132.R02.02.local_readiness.v1", "providers": items,
        "host": host_resources(), "probe_requested": probe,
        "network_scope": "loopback-only" if probe else "none",
        "external_api_calls": 0, "inference_calls": 0, "source_writes": 0,
        "provider_enablement_changed": False, "secrets_exposed": False,
        "monetary_cost_usd": 0.0, "task_evaluation": "NOT_TESTED",
        "deterministic_route_available": True,
        "note": "HEALTHY does not mean EVALUATED or ELIGIBLE; no model inference was executed."}
