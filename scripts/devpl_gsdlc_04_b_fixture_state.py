from __future__ import annotations

import hashlib
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

FIXTURE_STATE_VERSION = "1.0.9"
DEFAULT_FIXTURE = Path(r"D:\Projects\DevPilot_E2E_Evaluation\worktrees\DEVPL_GSDLC_04_B_BROWSER")
LEGACY_MARKER = ".devpilot-gsdlc04b-browser-fixture.json"
EXPECTED_TRACKED = {
    ".devpilot/project.yaml",
    "docs/manual_authoring.json",
    "docs/manual_authoring.md",
}
EXPECTED_BLOB_SHA256 = {
    ".devpilot/project.yaml": "a35547f6a45bd7888a37842fa61d4095b4e4379ff8c9daf9ee82ce4655788623",
    "docs/manual_authoring.json": "8176d3ffed688819ea0316be7814db5432f0e6612b3bccbbeddd9b05c535dea8",
    "docs/manual_authoring.md": "1f79747c99fcba3f81d43086adacbf1ce20d82c2b0bae25f05d820e933da0038",
}
BOOTSTRAP_EXECUTION_REL = ".devpilot/bootstrap-execution.json"
WORKSPACE_REGISTRATION_REL = ".devpilot/workspace-registration.json"
EXPECTED_BROWSER_PROJECT_ID = "gsdlc04b-browser"
_SHA64 = re.compile(r"^[0-9a-f]{64}$")


class FixtureStateError(RuntimeError):
    pass


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _git(fixture: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[bytes]:
    cp = subprocess.run(
        ["git", *args],
        cwd=str(fixture),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        shell=False,
        timeout=60,
    )
    if check and cp.returncode != 0:
        raise FixtureStateError(
            f"Git command failed ({cp.returncode}): git {' '.join(args)}; "
            f"stderr={cp.stderr.decode('utf-8', 'replace')[-500:]}"
        )
    return cp


def _status_entries(fixture: Path) -> list[str]:
    cp = _git(fixture, "status", "--porcelain=v1", "-z")
    return [item.decode("utf-8", "replace") for item in cp.stdout.split(b"\0") if item]


def _tracked_paths(fixture: Path) -> set[str]:
    cp = _git(fixture, "ls-files", "-z")
    return {item.decode("utf-8", "replace") for item in cp.stdout.split(b"\0") if item}


def _head(fixture: Path) -> str:
    return _git(fixture, "rev-parse", "HEAD").stdout.decode("utf-8", "replace").strip()


def _blob_sha256(fixture: Path, rel: str) -> str:
    cp = _git(fixture, "show", f"HEAD:{rel}")
    return sha256_bytes(cp.stdout)


def _validate_exact_fixture_path(fixture: Path) -> None:
    expected = str(DEFAULT_FIXTURE).replace("/", "\\").lower()
    actual = str(fixture).replace("/", "\\").lower()
    if actual != expected:
        raise FixtureStateError(f"Fixture no autorizado para 04-B: {fixture}. Debe ser exactamente {DEFAULT_FIXTURE}.")
    if "inventory-sales-local" in actual or "devpilot_workspaces" in actual:
        raise FixtureStateError("El fixture 04-B no puede apuntar al workspace piloto real.")


def _read_json(path: Path, label: str) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise FixtureStateError(f"{label} no es JSON válido: {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise FixtureStateError(f"{label} debe ser un objeto JSON: {path}")
    return payload


def _same_path(raw: object, fixture: Path) -> bool:
    if not isinstance(raw, str) or not raw.strip():
        return False
    expected = str(fixture.resolve()).replace("/", "\\").lower()
    actual = str(Path(raw).resolve()).replace("/", "\\").lower()
    return actual == expected


def _validate_post_open_metadata(fixture: Path) -> dict[str, Any]:
    execution_path = fixture / BOOTSTRAP_EXECUTION_REL
    registration_path = fixture / WORKSPACE_REGISTRATION_REL
    execution_exists = execution_path.is_file()
    registration_exists = registration_path.is_file()

    if not execution_exists and not registration_exists:
        return {
            "phase": "PRE_OPEN",
            "post_open_metadata_present": False,
            "bootstrap_execution": None,
            "workspace_registration": None,
        }
    if execution_exists != registration_exists:
        missing = WORKSPACE_REGISTRATION_REL if execution_exists else BOOTSTRAP_EXECUTION_REL
        raise FixtureStateError(
            f"Estado post-Open incompleto: falta {missing}. Preserve evidencia; no se reparará ni eliminará automáticamente."
        )

    execution = _read_json(execution_path, "bootstrap-execution")
    registration = _read_json(registration_path, "workspace-registration")
    errors: list[str] = []

    if execution.get("schema_id") != "SCHEMA-DEVPL-GSDLC-03-D-BOOTSTRAP-EXECUTION-V1":
        errors.append("bootstrap.schema_id")
    if execution.get("status") != "PASS":
        errors.append("bootstrap.status")
    if execution.get("entry_mode") != "OPEN_EXISTING":
        errors.append("bootstrap.entry_mode")
    if execution.get("project_id") != EXPECTED_BROWSER_PROJECT_ID:
        errors.append("bootstrap.project_id")
    if not _same_path(execution.get("target_root"), fixture):
        errors.append("bootstrap.target_root")
    if execution.get("network_used") is not False:
        errors.append("bootstrap.network_used")
    if execution.get("external_api_used") is not False:
        errors.append("bootstrap.external_api_used")
    if int(execution.get("writes_outside_workspace", -1)) != 0:
        errors.append("bootstrap.writes_outside_workspace")
    if not isinstance(execution.get("approval_id"), str) or not str(execution.get("approval_id")).strip():
        errors.append("bootstrap.approval_id")
    for key in ("plan_hash", "preimage_hash"):
        if not isinstance(execution.get(key), str) or not _SHA64.fullmatch(str(execution.get(key))):
            errors.append(f"bootstrap.{key}")
    verification = execution.get("verification")
    if not isinstance(verification, dict) or verification.get("ok") is not True or verification.get("git_clean") is not True or list(verification.get("failures") or []):
        errors.append("bootstrap.verification")

    if registration.get("schema_id") != "devpilot.gsdlc03d.workspace_registration.v1":
        errors.append("registration.schema_id")
    if registration.get("workspace_id") != EXPECTED_BROWSER_PROJECT_ID or registration.get("project_id") != EXPECTED_BROWSER_PROJECT_ID:
        errors.append("registration.project_id")
    if not _same_path(registration.get("root_path"), fixture):
        errors.append("registration.root_path")
    if registration.get("status") != "registered-local":
        errors.append("registration.status")
    if registration.get("default_effect") != "deny":
        errors.append("registration.default_effect")
    if registration.get("network_allowed") is not False:
        errors.append("registration.network_allowed")
    if registration.get("external_api_allowed") is not False:
        errors.append("registration.external_api_allowed")

    if errors:
        raise FixtureStateError(
            "Metadata post-Open existe pero no demuestra un OPEN_EXISTING PASS seguro: " + ", ".join(errors) + ". "
            "Preserve evidencia; no se eliminará automáticamente."
        )

    return {
        "phase": "POST_OPEN_PASS",
        "post_open_metadata_present": True,
        "bootstrap_execution": {
            "project_id": execution.get("project_id"),
            "entry_mode": execution.get("entry_mode"),
            "target_root": execution.get("target_root"),
            "plan_hash": execution.get("plan_hash"),
            "preimage_hash": execution.get("preimage_hash"),
            "approval_id": execution.get("approval_id"),
            "status": execution.get("status"),
            "verification_ok": verification.get("ok"),
            "verification_git_clean": verification.get("git_clean"),
            "network_used": execution.get("network_used"),
            "external_api_used": execution.get("external_api_used"),
            "writes_outside_workspace": execution.get("writes_outside_workspace"),
        },
        "workspace_registration": {
            "workspace_id": registration.get("workspace_id"),
            "project_id": registration.get("project_id"),
            "root_path": registration.get("root_path"),
            "status": registration.get("status"),
            "default_effect": registration.get("default_effect"),
            "network_allowed": registration.get("network_allowed"),
            "external_api_allowed": registration.get("external_api_allowed"),
        },
    }


def inspect_fixture(
    fixture: Path,
    *,
    enforce_exact_windows_path: bool = True,
    phase_policy: str = "either",
) -> dict[str, Any]:
    """Inspect the disposable fixture with an explicit lifecycle state.

    ``PRE_OPEN`` is the clean baseline before Project Entry execution.
    ``POST_OPEN_PASS`` is a successfully registered fixture after OPEN_EXISTING;
    bootstrap-execution.json and workspace-registration.json are expected runtime
    metadata in that phase and must never be treated as generic residue.
    """
    fixture = Path(fixture).resolve()
    if enforce_exact_windows_path:
        _validate_exact_fixture_path(fixture)
    if phase_policy not in {"either", "pre-open", "post-open-pass"}:
        raise FixtureStateError(f"phase_policy inválida: {phase_policy}")
    if not fixture.is_dir():
        raise FixtureStateError(f"Fixture browser no existe: {fixture}")
    if not (fixture / ".git").is_dir():
        raise FixtureStateError("Fixture browser no es un repositorio Git local.")

    tracked = _tracked_paths(fixture)
    missing_tracked = sorted(EXPECTED_TRACKED - tracked)
    unexpected_tracked = sorted(tracked - EXPECTED_TRACKED)
    if missing_tracked or unexpected_tracked:
        raise FixtureStateError(
            f"Fixture tracked-set inesperado. missing={missing_tracked}; unexpected={unexpected_tracked}. "
            "No se intentará reparar automáticamente."
        )

    blob_hashes = {rel: _blob_sha256(fixture, rel) for rel in sorted(EXPECTED_TRACKED)}
    blob_mismatches = {
        rel: {"expected": EXPECTED_BLOB_SHA256[rel], "actual": digest}
        for rel, digest in blob_hashes.items()
        if digest != EXPECTED_BLOB_SHA256[rel]
    }
    if blob_mismatches:
        raise FixtureStateError(f"Fixture Git HEAD no coincide con el baseline 04-B: {blob_mismatches}")

    lifecycle = _validate_post_open_metadata(fixture)
    if phase_policy == "pre-open" and lifecycle["phase"] != "PRE_OPEN":
        raise FixtureStateError(
            "El checkpoint exige PRE_OPEN, pero el fixture ya contiene un OPEN_EXISTING PASS. "
            "No repita Project Entry ni elimine metadata de bootstrap."
        )
    if phase_policy == "post-open-pass" and lifecycle["phase"] != "POST_OPEN_PASS":
        raise FixtureStateError(
            "El checkpoint de restart exige POST_OPEN_PASS, pero no existe metadata completa de un Open Existing exitoso."
        )

    status = _status_entries(fixture)
    legacy_marker = fixture / LEGACY_MARKER
    legacy_marker_only = status == [f"?? {LEGACY_MARKER}"] and legacy_marker.is_file()
    return {
        "fixture": str(fixture),
        "head": _head(fixture),
        "tracked_paths": sorted(tracked),
        "blob_hashes": blob_hashes,
        "git_status_entries": status,
        "git_clean": not status,
        "legacy_marker_present": legacy_marker.is_file(),
        "legacy_marker_only_dirty_entry": legacy_marker_only,
        "fixture_phase": lifecycle["phase"],
        "post_open_metadata_present": lifecycle["post_open_metadata_present"],
        "bootstrap_execution": lifecycle["bootstrap_execution"],
        "workspace_registration": lifecycle["workspace_registration"],
    }


def repair_legacy_marker(
    fixture: Path,
    *,
    evidence_dir: Path,
    enforce_exact_windows_path: bool = True,
) -> dict[str, Any]:
    fixture = Path(fixture).resolve()
    evidence_dir = Path(evidence_dir).resolve()
    evidence_dir.mkdir(parents=True, exist_ok=True)
    state = inspect_fixture(
        fixture,
        enforce_exact_windows_path=enforce_exact_windows_path,
        phase_policy="pre-open",
    )
    if state["git_clean"]:
        action = "already-clean"
    elif state["legacy_marker_only_dirty_entry"]:
        marker = fixture / LEGACY_MARKER
        try:
            payload = json.loads(marker.read_text(encoding="utf-8"))
        except Exception as exc:
            raise FixtureStateError(f"Legacy marker inválido; no se eliminará: {exc}") from exc
        if payload.get("fixture_id") != "DEVPL-GSDLC-04-B-BROWSER-FIXTURE":
            raise FixtureStateError("Legacy marker no pertenece al fixture GSDLC-04-B; no se eliminará.")
        marker_target = str(payload.get("target") or "").replace("/", "\\").lower()
        current_target = str(fixture).replace("/", "\\").lower()
        if marker_target and marker_target != current_target:
            raise FixtureStateError("Legacy marker apunta a otra ruta; no se eliminará.")
        archive = evidence_dir / "legacy_fixture_marker_v1_0_7.json"
        if not archive.exists():
            archive.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        marker.unlink()
        action = "removed-v1.0.7-untracked-marker"
    else:
        raise FixtureStateError(
            f"Fixture tiene cambios no autorizados: {state['git_status_entries']}. "
            f"Solo es reparable automáticamente el marcador legado {LEGACY_MARKER}."
        )

    final = inspect_fixture(
        fixture,
        enforce_exact_windows_path=enforce_exact_windows_path,
        phase_policy="pre-open",
    )
    if not final["git_clean"]:
        raise FixtureStateError(f"Fixture sigue dirty después de repair: {final['git_status_entries']}")
    ownership = {
        "schema_id": "devpilot.gsdlc04b.browser_fixture_ownership.v1",
        "version": FIXTURE_STATE_VERSION,
        "fixture_id": "DEVPL-GSDLC-04-B-BROWSER-FIXTURE",
        "fixture": str(fixture),
        "git_head": final["head"],
        "tracked_paths": final["tracked_paths"],
        "blob_hashes": final["blob_hashes"],
        "git_clean": True,
        "fixture_phase": final["fixture_phase"],
        "ownership_scope": "external-evidence-only/no-marker-inside-fixture",
        "repair_action": action,
        "updated_at": utcnow(),
    }
    (evidence_dir / "DEVPL_GSDLC_04_B_BROWSER_FIXTURE_OWNERSHIP_CURRENT.json").write_text(
        json.dumps(ownership, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return {"status": "PASS", "repair_action": action, "fixture_state": final, "ownership": ownership}
