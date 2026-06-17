from __future__ import annotations

import re
import tomllib
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity

_SEMVER_RE = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:[-+][0-9A-Za-z.-]+)?$")

_ALLOWED_MODES = {"editable", "wheel", "zip", "desktop-bridge", "all"}
_ARTIFACT_MODES = {"wheel", "zip"}


@dataclass(frozen=True)
class InstallPlanOptions:
    """Options for FUNC-SPRINT-82 local installation planning.

    The install planner is intentionally plan-only. It never creates virtual
    environments, installs packages, creates services, enables auto-update,
    downloads dependencies, mutates source files or requires administrator
    privileges.
    """

    mode: str = "all"
    version: str | None = None
    artifact: str | None = None
    python_executable: str = "python"


class InstallPlanBuilder:
    """Build a governed local installation strategy and dry-run install plan."""

    def __init__(self, root: Path, *, options: InstallPlanOptions) -> None:
        self.root = Path(root).resolve()
        self.options = options

    def build(self) -> CommandResult:
        mode = self.options.mode
        if mode not in _ALLOWED_MODES:
            return CommandResult(
                command="install plan",
                ok=False,
                exit_code=ExitCode.ERROR,
                message=f"Unsupported install mode: {mode}",
                data={
                    "summary": {
                        "mode": mode,
                        "supported_modes": sorted(_ALLOWED_MODES),
                        "preliminary": True,
                        **_security_summary(),
                    }
                },
                findings=[
                    Finding(
                        id="INSTALL_MODE_UNSUPPORTED",
                        message=f"Unsupported install mode '{mode}'.",
                        severity=Severity.ERROR,
                    )
                ],
            )

        version = _effective_version(self.root, self.options.version)
        if not _SEMVER_RE.match(version):
            return CommandResult(
                command="install plan",
                ok=False,
                exit_code=ExitCode.ERROR,
                message=f"Invalid SemVer version for installation planning: {version}",
                data={
                    "summary": {
                        "version": version,
                        "mode": mode,
                        "valid_version": False,
                        "preliminary": True,
                        **_security_summary(),
                    }
                },
                findings=[
                    Finding(
                        id="INSTALL_VERSION_INVALID",
                        message="Installation planning requires a SemVer-compatible version.",
                        severity=Severity.ERROR,
                    )
                ],
            )

        artifact_info = _artifact_info(self.root, mode, version, self.options.artifact)
        if artifact_info.get("blocked"):
            return CommandResult(
                command="install plan",
                ok=False,
                exit_code=ExitCode.ERROR,
                message=artifact_info["block_message"],
                data={
                    "summary": {
                        "version": version,
                        "mode": mode,
                        "artifact": artifact_info,
                        "preliminary": True,
                        **_security_summary(),
                    }
                },
                findings=[
                    Finding(
                        id=artifact_info["block_id"],
                        message=artifact_info["block_message"],
                        severity=Severity.ERROR,
                    )
                ],
            )

        plans = _plans(version=version, python_executable=self.options.python_executable)
        selected_modes = ["editable", "wheel", "zip", "desktop-bridge"] if mode == "all" else [mode]
        selected_plans = [plans[item] for item in selected_modes]
        decision_matrix = _decision_matrix()

        plan = {
            "schema_version": "1.0.0",
            "plan_id": f"INSTALL-PLAN-{version}-{mode}",
            "release_id": f"DEVPL-{version}",
            "release_version": version,
            "mode": mode,
            "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "selected_modes": selected_modes,
            "artifact": artifact_info,
            "decision_matrix": decision_matrix,
            "plans": selected_plans,
            "security": _security_summary(),
            "preconditions": [
                "Resolver workspace DevPilot antes de operar.",
                "Usar Python 3.12 recomendado o Python compatible definido por pyproject.toml.",
                "Ejecutar packaging y release verify antes de instalar desde wheel o ZIP.",
                "Conservar outputs y dist como artefactos regenerables fuera del control de código fuente.",
            ],
            "limitations": [
                "FUNC-SPRINT-82 implementa estrategia de instalación y plan dry-run; no instala paquetes automáticamente.",
                "No implementa auto-update, servicios persistentes, instalación como servicio del sistema ni distribución remota.",
                "No reemplaza pruebas de instalación aislada completas; estas deben evolucionar en sprints posteriores.",
            ],
        }

        summary = {
            "version": version,
            "schema_version": "1.0.0",
            "preliminary": True,
            "mode": mode,
            "selected_modes_total": len(selected_modes),
            "decision_options_total": len(decision_matrix),
            "plan_steps_total": sum(len(item["steps"]) for item in selected_plans),
            "artifact_mode": mode in _ARTIFACT_MODES,
            "artifact_expected": artifact_info.get("expected"),
            "artifact_exists": artifact_info.get("exists"),
            "dry_run_default": True,
            "execute_supported": False,
            "installer_preliminary": True,
            "editable_install_documented": True,
            "wheel_install_documented": True,
            "zip_install_documented": True,
            "desktop_bridge_documented": True,
            "admin_privileges_required": False,
            "auto_update_enabled": False,
            "persistent_services_installed": False,
            **_security_summary(),
        }

        return CommandResult(
            command="install plan",
            ok=True,
            exit_code=ExitCode.PASS,
            message="Local installation strategy and dry-run plan generated.",
            data={
                "summary": summary,
                "install_plan": plan,
                "notes": [
                    "FUNC-SPRINT-82 keeps installation plan-only to avoid hidden local mutations.",
                    "Wheel and ZIP installation paths are documented and can be verified from local artifacts.",
                    "Desktop packaging remains a bridge strategy; no desktop installer is built in this sprint.",
                ],
            },
            findings=[
                Finding(
                    id="INSTALL_PLAN_CREATED",
                    message="Local installation plan was generated without executing installation steps.",
                    severity=Severity.INFO,
                    metadata={"mode": mode, "version": version, "selected_modes": selected_modes},
                )
            ],
        )


def _effective_version(root: Path, explicit: str | None) -> str:
    if explicit:
        return explicit
    pyproject_path = root / "pyproject.toml"
    if pyproject_path.exists():
        with pyproject_path.open("rb") as handle:
            data = tomllib.load(handle)
        version = ((data.get("project") or {}).get("version") or "").strip()
        if version:
            return version
    return "0.1.0"


def _artifact_info(root: Path, mode: str, version: str, artifact: str | None) -> dict[str, Any]:
    if mode == "all":
        return {
            "expected": False,
            "provided": artifact,
            "exists": artifact is not None and _safe_exists(root, artifact),
            "note": "Mode all documents all installation paths; specific artifact validation is performed with mode wheel or zip.",
        }
    if mode == "editable" or mode == "desktop-bridge":
        return {
            "expected": False,
            "provided": artifact,
            "exists": artifact is not None and _safe_exists(root, artifact),
            "note": f"Mode {mode} does not require a release artifact for planning.",
        }

    default_artifact = (
        f"dist/devpilot_local-{version}-py3-none-any.whl"
        if mode == "wheel"
        else f"dist/release/devpilot-local-{version}-source.zip"
    )
    artifact_value = artifact or default_artifact
    resolved = (root / artifact_value).resolve()
    try:
        resolved.relative_to(root)
    except ValueError:
        return {
            "expected": True,
            "provided": artifact_value,
            "exists": False,
            "blocked": True,
            "block_id": "INSTALL_ARTIFACT_OUTSIDE_WORKSPACE",
            "block_message": "Installation artifact path must remain inside the DevPilot workspace.",
        }

    expected_suffix = ".whl" if mode == "wheel" else ".zip"
    if resolved.suffix != expected_suffix:
        return {
            "expected": True,
            "provided": artifact_value,
            "exists": resolved.exists(),
            "blocked": True,
            "block_id": "INSTALL_ARTIFACT_KIND_MISMATCH",
            "block_message": f"Install mode {mode} expects a {expected_suffix} artifact.",
        }

    return {
        "expected": True,
        "provided": artifact_value,
        "path": str(resolved.relative_to(root)).replace("\\", "/"),
        "exists": resolved.exists(),
        "kind": mode,
        "note": "Artifact is not required to exist for dry-run planning, but must exist before manual installation.",
    }


def _safe_exists(root: Path, artifact: str) -> bool:
    try:
        return (root / artifact).resolve().relative_to(root) is not None and (root / artifact).resolve().exists()
    except ValueError:
        return False


def _security_summary() -> dict[str, bool]:
    return {
        "network_required": False,
        "external_api_used": False,
        "publishes_artifacts": False,
        "deploys_artifacts": False,
        "git_tagging_performed": False,
        "signing_performed": False,
        "source_mutations_performed": False,
        "runtime_state_mutated": False,
    }


def _decision_matrix() -> list[dict[str, Any]]:
    return [
        {
            "mode": "editable",
            "status": "recommended-for-development",
            "source": "workspace",
            "use_case": "Desarrollo local y validación rápida.",
            "pros": ["Iteración rápida", "No requiere artefacto dist", "Compatible con pytest"],
            "cons": ["No representa instalación final de usuario", "Depende del árbol fuente"],
            "pass_conditions": ["venv local", "pip install -e .[dev]", "pytest/quality gate PASS"],
            "block_conditions": ["requiere admin", "descarga obligatoria sin alternativa local"],
        },
        {
            "mode": "wheel",
            "status": "recommended-for-local-release-candidate",
            "source": "dist/devpilot_local-<version>-py3-none-any.whl",
            "use_case": "Instalación local desde artefacto Python generado.",
            "pros": ["Artefacto estándar Python", "Alineado con packaging", "Verificable por checksum"],
            "cons": ["Primera versión de wheel", "No cubre Desktop shell"],
            "pass_conditions": ["package build PASS", "release verify PASS", "pip install artifact local"],
            "block_conditions": ["artefacto inexistente", "checksum/smoke fallido"],
        },
        {
            "mode": "zip",
            "status": "supported-for-source-distribution",
            "source": "dist/release/devpilot-local-<version>-source.zip",
            "use_case": "Entrega de fuente limpia reproducible.",
            "pros": ["Auditable", "Incluye docs/tests", "Compatible con revisión manual"],
            "cons": ["Requiere instalación manual posterior", "Mayor tamaño"],
            "pass_conditions": ["ZIP limpio", "sin outputs/runtime/caches", "release verify PASS"],
            "block_conditions": ["incluye secretos", "incluye runtime state"],
        },
        {
            "mode": "desktop-bridge",
            "status": "planned-not-built",
            "source": "Fase F Web UI local y decisión Desktop diferida.",
            "use_case": "Puente arquitectónico para futuro shell desktop o instalador visual.",
            "pros": ["No duplica UI Web", "Mantiene Desktop diferido", "Reduce riesgo temprano"],
            "cons": ["No entrega instalador desktop", "Requiere fase futura"],
            "pass_conditions": ["documentar relación con Fase F", "sin servicios persistentes"],
            "block_conditions": ["instala servicio", "requiere privilegios elevados sin ADR"],
        },
    ]


def _plans(*, version: str, python_executable: str) -> dict[str, dict[str, Any]]:
    py = python_executable
    return {
        "editable": {
            "mode": "editable",
            "dry_run": True,
            "description": "Instalación local editable para desarrollo y validación.",
            "steps": [
                {"order": 1, "command": "py -3.12 -m venv .venv", "purpose": "Crear entorno virtual local."},
                {"order": 2, "command": ".\\.venv\\Scripts\\Activate.ps1", "purpose": "Activar entorno en PowerShell."},
                {"order": 3, "command": f"{py} -m pip install --upgrade pip", "purpose": "Actualizar pip dentro del entorno."},
                {"order": 4, "command": f"{py} -m pip install -e .[dev]", "purpose": "Instalar DevPilot en modo editable."},
                {"order": 5, "command": f"{py} -m devpilot_core --version", "purpose": "Smoke CLI mínimo."},
                {"order": 6, "command": f"{py} -m pytest -q", "purpose": "Validar regresión local."},
            ],
        },
        "wheel": {
            "mode": "wheel",
            "dry_run": True,
            "description": "Instalación local desde wheel generado por packaging.",
            "steps": [
                {"order": 1, "command": f"{py} -m devpilot_core package build --kind all --version {version} --execute --json --write-report", "purpose": "Generar wheel/sdist/ZIP local."},
                {"order": 2, "command": f"{py} -m devpilot_core release verify --artifact dist/release/devpilot-local-{version}-source.zip --json --write-report", "purpose": "Verificar artefacto fuente y checksums."},
                {"order": 3, "command": "py -3.12 -m venv .venv-install-smoke", "purpose": "Crear entorno aislado de smoke install."},
                {"order": 4, "command": ".\\.venv-install-smoke\\Scripts\\Activate.ps1", "purpose": "Activar entorno aislado."},
                {"order": 5, "command": f"{py} -m pip install dist/devpilot_local-{version}-py3-none-any.whl", "purpose": "Instalar wheel local."},
                {"order": 6, "command": f"{py} -m devpilot_core --version", "purpose": "Validar CLI instalado."},
            ],
        },
        "zip": {
            "mode": "zip",
            "dry_run": True,
            "description": "Instalación/revisión manual desde ZIP fuente limpio.",
            "steps": [
                {"order": 1, "command": f"{py} -m devpilot_core package build --kind repo-zip --version {version} --execute --json --write-report", "purpose": "Generar ZIP fuente limpio."},
                {"order": 2, "command": f"{py} -m devpilot_core release verify --artifact dist/release/devpilot-local-{version}-source.zip --json --write-report", "purpose": "Verificar integridad del ZIP."},
                {"order": 3, "command": "Expand-Archive -Path dist\\release\\devpilot-local-0.1.0-source.zip -DestinationPath .\\install-smoke -Force", "purpose": "Extraer en carpeta controlada."},
                {"order": 4, "command": "cd .\\install-smoke", "purpose": "Entrar al workspace extraído."},
                {"order": 5, "command": "py -3.12 -m venv .venv", "purpose": "Crear entorno local del ZIP extraído."},
                {"order": 6, "command": f"{py} -m pip install -e .[dev]", "purpose": "Instalar desde fuente extraída."},
            ],
        },
        "desktop-bridge": {
            "mode": "desktop-bridge",
            "dry_run": True,
            "description": "Puente documental hacia futuro shell desktop sin implementarlo todavía.",
            "steps": [
                {"order": 1, "command": f"{py} -m devpilot_core api serve --host 127.0.0.1 --port 8787 --dry-run --json", "purpose": "Validar API local en modo seguro."},
                {"order": 2, "command": "npm --prefix ui/web test", "purpose": "Validar Web UI local existente."},
                {"order": 3, "command": "No desktop installer is built in FUNC-SPRINT-82.", "purpose": "Mantener Desktop diferido sin duplicar Fase F."},
            ],
        },
    }
