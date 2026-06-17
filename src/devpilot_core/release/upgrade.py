from __future__ import annotations

import re
import tomllib
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity

_SEMVER_RE = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:[-+][0-9A-Za-z.-]+)?$")


@dataclass(frozen=True)
class UpgradeCheckOptions:
    """Options for FUNC-SPRINT-83 local upgrade readiness checks."""

    target_version: str | None = None


class UpgradeCheckBuilder:
    """Generate a local upgrade plan without mutating the workspace."""

    def __init__(self, root: Path, *, options: UpgradeCheckOptions) -> None:
        self.root = Path(root).resolve()
        self.options = options

    def build(self) -> CommandResult:
        current_version = _project_version(self.root)
        target_version = self.options.target_version or current_version
        if not _SEMVER_RE.match(target_version):
            return CommandResult(
                command="upgrade check",
                ok=False,
                exit_code=ExitCode.ERROR,
                message="Upgrade check failed because target version is invalid.",
                data={"summary": {"target_version": target_version, "valid_target_version": False, "preliminary": True}},
                findings=[Finding("UPGRADE_TARGET_VERSION_INVALID", "Target version must be SemVer-compatible.", Severity.ERROR)],
            )

        required_paths = [
            ".devpilot/project.yaml",
            ".devpilot/miasi/agent_registry.json",
            ".devpilot/miasi/tool_registry.json",
            ".devpilot/miasi/policy_matrix.json",
            ".devpilot/providers.yaml.example",
            "docs/05_operations/backup_restore_upgrade.md",
            "docs/05_operations/install_guide.md",
            "docs/05_operations/release_verification.md",
        ]
        path_status = [
            {"path": item, "exists": (self.root / item).exists(), "required": True}
            for item in required_paths
        ]
        missing_required = [item["path"] for item in path_status if not item["exists"]]
        latest_backup = _latest_backup_manifest(self.root)
        findings: list[Finding] = []
        if latest_backup is None:
            findings.append(
                Finding(
                    "UPGRADE_BACKUP_RECOMMENDED",
                    "No local backup sidecar manifest was found; run backup create --execute before a real upgrade.",
                    Severity.WARNING,
                )
            )
        if missing_required:
            findings.append(
                Finding(
                    "UPGRADE_REQUIRED_PATHS_MISSING",
                    "Upgrade check detected missing expected local release/backup documents or state files.",
                    Severity.WARNING,
                    metadata={"missing": missing_required},
                )
            )

        checks = [
            {"id": "workspace-state", "passed": all((self.root / p).exists() for p in required_paths[:5]), "description": "Core .devpilot state exists."},
            {"id": "backup-before-upgrade", "passed": latest_backup is not None, "description": "At least one local backup manifest exists.", "severity_if_failed": "warning"},
            {"id": "install-strategy", "passed": (self.root / "docs/05_operations/install_guide.md").exists(), "description": "Installation strategy exists."},
            {"id": "release-verification", "passed": (self.root / "docs/05_operations/release_verification.md").exists(), "description": "Release verification procedure exists."},
            {"id": "no-remote-required", "passed": True, "description": "Upgrade check does not require network or external APIs."},
            {"id": "dry-run-default", "passed": True, "description": "Upgrade check is plan-only and non-mutating."},
        ]
        plan_steps = [
            {"order": 1, "command": "python -m pytest -q", "purpose": "Confirmar regresión antes de upgrade."},
            {"order": 2, "command": "python -m devpilot_core validate all --json", "purpose": "Validar contratos y documentación."},
            {"order": 3, "command": "python -m devpilot_core backup create --execute --json --write-report", "purpose": "Crear backup local antes de modificar estado."},
            {"order": 4, "command": "python -m devpilot_core package build --kind all --version 0.1.0 --execute --json --write-report", "purpose": "Regenerar artefactos de release local."},
            {"order": 5, "command": "python -m devpilot_core release verify --artifact dist/release/devpilot-local-0.1.0-source.zip --json --write-report", "purpose": "Verificar artefacto antes de instalación/upgrade."},
            {"order": 6, "command": "python -m devpilot_core install plan --mode all --json --write-report", "purpose": "Confirmar estrategia de instalación."},
            {"order": 7, "command": "python -m devpilot_core backup restore --backup-id <id> --dry-run --json", "purpose": "Validar plan de recuperación antes de cualquier ejecución real."},
        ]
        summary = {
            "schema_version": "1.0.0",
            "preliminary": True,
            "current_version": current_version,
            "target_version": target_version,
            "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "upgrade_ready": all(check["passed"] or check.get("severity_if_failed") == "warning" for check in checks),
            "checks_total": len(checks),
            "checks_passed": len([check for check in checks if check["passed"]]),
            "checks_warning": len([check for check in checks if not check["passed"] and check.get("severity_if_failed") == "warning"]),
            "missing_required_total": len(missing_required),
            "latest_backup_manifest": latest_backup,
            "dry_run_default": True,
            "mutations_performed": False,
            "network_used": False,
            "external_api_used": False,
            "publishes_artifacts": False,
            "deploys_artifacts": False,
            "git_tagging_performed": False,
            "rollback_path_documented": True,
        }
        return CommandResult(
            command="upgrade check",
            ok=True,
            exit_code=ExitCode.PASS,
            message="Local upgrade readiness plan generated.",
            data={
                "summary": summary,
                "checks": checks,
                "path_status": path_status,
                "upgrade_plan": {
                    "schema_version": "1.0.0",
                    "current_version": current_version,
                    "target_version": target_version,
                    "steps": plan_steps,
                    "restore_policy": {
                        "restore_dry_run_first": True,
                        "restore_execute_requires_confirmation": True,
                    },
                    "limitations": [
                        "FUNC-SPRINT-83 does not perform schema migrations automatically.",
                        "Upgrade check is a local readiness plan, not an auto-updater.",
                        "Real upgrade execution remains a future controlled workflow.",
                    ],
                },
            },
            findings=findings,
        )


def _project_version(root: Path) -> str:
    pyproject = root / "pyproject.toml"
    if not pyproject.exists():
        return "0.1.0"
    try:
        data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    except Exception:
        return "0.1.0"
    project = data.get("project") or {}
    version = project.get("version")
    return str(version or "0.1.0")


def _latest_backup_manifest(root: Path) -> str | None:
    backup_dir = root / ".devpilot" / "backups"
    manifests = sorted(backup_dir.glob("*.manifest.json"), reverse=True)
    if not manifests:
        return None
    try:
        return str(manifests[0].resolve().relative_to(root.resolve())).replace("\\", "/")
    except ValueError:
        return str(manifests[0])
