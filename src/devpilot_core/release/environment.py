from __future__ import annotations

import json
import os
import platform
import re
import sys
import tomllib
from dataclasses import dataclass
from datetime import datetime, timezone
from importlib import metadata as importlib_metadata
from pathlib import Path
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.release.reproducibility_policy import DEFAULT_POLICY_PATH, ReleaseReproducibilityPolicyValidator

_SENSITIVE_KEY_RE = re.compile(
    r"(secret|token|api[_-]?key|password|passwd|pwd|credential|authorization|client[_-]?secret|private[_-]?key|database[_-]?url|connection[_-]?string)",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class ReleaseEnvironmentSnapshotOptions:
    """Options for POST-H-017-B redacted environment snapshot generation.

    The builder is intentionally local/read-only. It does not read `.env` files,
    does not include environment variable values and does not execute package
    managers, network calls, shell commands or external APIs. `write_report=True`
    writes generated evidence only under `outputs/release/`.
    """

    write_report: bool = False
    policy_path: Path | str = DEFAULT_POLICY_PATH
    output_json: Path | str = Path("outputs/release/environment_snapshot.json")
    output_markdown: Path | str = Path("outputs/release/environment_snapshot.md")
    dependency_limit: int = 200


class ReleaseEnvironmentSnapshotBuilder:
    """Build a redacted local environment snapshot for release reproducibility.

    POST-H-017-B captures enough local diagnostics to understand the release
    candidate environment without leaking secrets: Python/runtime metadata,
    platform metadata, local project manifest presence and declared dependency
    names. It never reads `.env*` files or secret values.
    """

    def __init__(self, root: Path, *, options: ReleaseEnvironmentSnapshotOptions | None = None) -> None:
        self.root = Path(root).resolve()
        self.options = options or ReleaseEnvironmentSnapshotOptions()

    def build(self) -> CommandResult:
        policy_result = ReleaseReproducibilityPolicyValidator(self.root, policy_path=self.options.policy_path).run()
        findings: list[Finding] = []
        if not policy_result.ok:
            findings.extend(policy_result.findings)
            summary = self._summary(
                snapshot=None,
                reports_written=False,
                blocking_findings_total=len(policy_result.findings) or 1,
                findings_total=len(policy_result.findings) or 1,
            )
            return CommandResult(
                command="release environment-snapshot",
                ok=False,
                exit_code=ExitCode.BLOCK,
                message="Release environment snapshot blocked by reproducibility policy.",
                data={"summary": summary, "policy": policy_result.data.get("summary")},
                findings=findings,
            )

        policy_payload = dict((policy_result.data or {}).get("policy") or {})
        blocked_key_patterns = list(((policy_payload.get("environment_snapshot_policy") or {}).get("blocked_key_patterns") or []))
        if not blocked_key_patterns:
            blocked_key_patterns = ["SECRET", "TOKEN", "KEY", "PASSWORD", "CREDENTIAL"]

        redacted_key_markers = self._redacted_env_key_markers()
        dependency_snapshot = self._dependency_snapshot()
        snapshot = {
            "schema_version": "1.0",
            "schema_id": "SCHEMA-DEVPL-RELEASE-ENVIRONMENT-SNAPSHOT-V1",
            "snapshot_id": "devpilot-release-environment-snapshot",
            "created_by": "POST-H-017-B",
            "status": "implemented-initial",
            "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
            "python": self._python_info(),
            "platform": self._platform_info(),
            "package_managers": self._package_managers(),
            "project_files": self._project_files(),
            "dependencies": dependency_snapshot,
            "diagnostics": {
                "allows_local_diagnosis": True,
                "dependency_sources_read": dependency_snapshot["sources"],
                "env_file_paths_detected": self._env_file_presence(),
                "env_file_contents_read": False,
                "environment_values_read": False,
                "package_manager_processes_executed": False,
                "network_diagnostics_executed": False,
            },
            "redaction": {
                "env_files_read": False,
                "secret_values_read": False,
                "secret_values_included": False,
                "redacted_keys": redacted_key_markers,
                "blocked_key_patterns": blocked_key_patterns,
            },
            "safety": {
                "local_first": True,
                "dry_run": True,
                "network_used": False,
                "external_api_used": False,
                "mutations_performed": False,
                "source_mutations_performed": False,
                "secrets_included": False,
                "remote_execution_used": False,
                "connector_write_used": False,
                "plugin_execution_used": False,
                "env_files_read": False,
                "secret_values_read": False,
            },
            "preliminary": True,
        }

        reports: dict[str, str] = {}
        reports_written = False
        if self.options.write_report:
            reports = self._write_outputs(snapshot)
            reports_written = True

        summary = self._summary(
            snapshot=snapshot,
            reports_written=reports_written,
            findings_total=1,
            blocking_findings_total=0,
        )
        data: dict[str, Any] = {
            "summary": summary,
            "snapshot": snapshot,
            "notes": [
                "POST-H-017-B captures a local redacted environment snapshot only; pack generation and verification are later micro-sprints.",
                "The builder reads local project manifests but never reads .env files, secret values, network resources or external APIs.",
            ],
        }
        if reports:
            data["reports"] = reports
        findings.append(
            Finding(
                "RELEASE_ENVIRONMENT_SNAPSHOT_CREATED",
                "Redacted release environment snapshot was generated without reading .env files or secret values.",
                Severity.INFO,
                metadata=summary,
            )
        )
        return CommandResult(
            command="release environment-snapshot",
            ok=True,
            exit_code=ExitCode.PASS,
            message="Release environment snapshot generated.",
            data=data,
            findings=findings,
        )

    def _python_info(self) -> dict[str, str]:
        executable_kind = "venv-python" if sys.prefix != getattr(sys, "base_prefix", sys.prefix) else "python"
        return {
            "version": platform.python_version(),
            "implementation": platform.python_implementation(),
            "executable_kind": executable_kind,
        }

    def _platform_info(self) -> dict[str, str]:
        return {
            "system": platform.system() or "unknown",
            "release": platform.release() or "",
            "machine": platform.machine() or "",
        }

    def _package_managers(self) -> dict[str, str | None]:
        return {
            "pip": self._metadata_version("pip"),
            "npm": None,
            "node": None,
        }

    def _project_files(self) -> dict[str, bool]:
        return {
            "pyproject_toml": (self.root / "pyproject.toml").is_file(),
            "ui_package_json": (self.root / "ui" / "web" / "package.json").is_file(),
            "ui_package_lock": (self.root / "ui" / "web" / "package-lock.json").is_file(),
        }

    def _dependency_snapshot(self) -> dict[str, Any]:
        pyproject_dependencies: list[dict[str, str]] = []
        pyproject_optional: list[dict[str, Any]] = []
        pyproject_build: list[dict[str, str]] = []
        node_dependencies: list[dict[str, str]] = []
        sources: list[str] = []

        pyproject_path = self.root / "pyproject.toml"
        if pyproject_path.is_file():
            sources.append("pyproject.toml")
            try:
                pyproject = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
            except tomllib.TOMLDecodeError:
                pyproject = {}
            project = pyproject.get("project") if isinstance(pyproject.get("project"), dict) else {}
            for dep in project.get("dependencies") or []:
                pyproject_dependencies.append(_dependency_name_record(str(dep), ecosystem="pypi", scope="runtime"))
            optional = project.get("optional-dependencies") if isinstance(project.get("optional-dependencies"), dict) else {}
            for group, deps in sorted(optional.items()):
                names = [_dependency_name_record(str(dep), ecosystem="pypi", scope=str(group)) for dep in deps or []]
                pyproject_optional.append({"group": str(group), "dependencies": names[: self.options.dependency_limit]})
            build_system = pyproject.get("build-system") if isinstance(pyproject.get("build-system"), dict) else {}
            for dep in build_system.get("requires") or []:
                pyproject_build.append(_dependency_name_record(str(dep), ecosystem="pypi", scope="build"))

        package_json_path = self.root / "ui" / "web" / "package.json"
        if package_json_path.is_file():
            sources.append("ui/web/package.json")
            try:
                package_json = json.loads(package_json_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                package_json = {}
            for scope, field in (("runtime", "dependencies"), ("dev", "devDependencies")):
                values = package_json.get(field) if isinstance(package_json.get(field), dict) else {}
                for name in sorted(values):
                    node_dependencies.append({"name": str(name), "ecosystem": "npm", "scope": scope})

        all_records = [
            *pyproject_dependencies,
            *pyproject_build,
            *node_dependencies,
            *(item for group in pyproject_optional for item in group.get("dependencies", [])),
        ]
        unique_names = sorted({record["name"] for record in all_records if record.get("name")})[: self.options.dependency_limit]
        return {
            "sources": sources,
            "python_runtime": pyproject_dependencies[: self.options.dependency_limit],
            "python_optional_groups": pyproject_optional,
            "python_build": pyproject_build[: self.options.dependency_limit],
            "node_declared": node_dependencies[: self.options.dependency_limit],
            "dependency_names": unique_names,
            "python_runtime_dependencies_total": len(pyproject_dependencies),
            "python_optional_groups_total": len(pyproject_optional),
            "python_build_dependencies_total": len(pyproject_build),
            "node_declared_dependencies_total": len(node_dependencies),
            "dependencies_total": len(unique_names),
            "dependency_values_redacted": True,
        }

    def _redacted_env_key_markers(self) -> list[str]:
        # Read only environment variable names, never values. Return a generic
        # marker instead of the real names to avoid leaking operational details.
        sensitive_names_detected = any(_SENSITIVE_KEY_RE.search(str(key)) for key in os.environ.keys())
        return ["<redacted-sensitive-env-key>"] if sensitive_names_detected else []

    def _env_file_presence(self) -> list[dict[str, Any]]:
        # Existence checks only; contents are never opened.
        result = []
        for relative in (".env", ".env.local", ".env.dev", ".env.test"):
            result.append({"path": relative, "exists": (self.root / relative).exists(), "contents_read": False})
        return result

    def _metadata_version(self, package: str) -> str | None:
        try:
            return importlib_metadata.version(package)
        except importlib_metadata.PackageNotFoundError:
            return None

    def _write_outputs(self, snapshot: dict[str, Any]) -> dict[str, str]:
        json_path = self.root / self.options.output_json
        md_path = self.root / self.options.output_markdown
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(json.dumps(snapshot, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        md_path.write_text(self.render_markdown(snapshot), encoding="utf-8")
        return {"json": str(self.options.output_json).replace("\\", "/"), "markdown": str(self.options.output_markdown).replace("\\", "/")}

    def render_markdown(self, snapshot: dict[str, Any]) -> str:
        summary = {
            "snapshot_id": snapshot.get("snapshot_id"),
            "created_by": snapshot.get("created_by"),
            "python": snapshot.get("python", {}).get("version"),
            "platform": snapshot.get("platform", {}).get("system"),
            "dependencies_total": snapshot.get("dependencies", {}).get("dependencies_total"),
            "secrets_included": snapshot.get("safety", {}).get("secrets_included"),
            "env_files_read": snapshot.get("redaction", {}).get("env_files_read"),
            "network_used": snapshot.get("safety", {}).get("network_used"),
        }
        lines = [
            "# Release environment snapshot",
            "",
            "Estado: `implemented-initial`.",
            "",
            "Este reporte fue generado por POST-H-017-B como evidencia local redactada. No contiene valores de secretos ni contenido de archivos `.env`.",
            "",
            "## Resumen",
            "",
        ]
        for key, value in summary.items():
            lines.append(f"- `{key}`: `{value}`")
        lines.extend([
            "",
            "## Seguridad",
            "",
            "- `local_first`: `true`",
            "- `dry_run`: `true`",
            "- `network_used`: `false`",
            "- `external_api_used`: `false`",
            "- `secret_values_read`: `false`",
            "- `secrets_included`: `false`",
            "",
            "Limitación: este snapshot no ejecuta package managers ni verifica checksums; esas capacidades quedan para POST-H-017-C/D/E.",
            "",
        ])
        return "\n".join(lines)

    def _summary(self, *, snapshot: dict[str, Any] | None, reports_written: bool, findings_total: int, blocking_findings_total: int) -> dict[str, Any]:
        dependencies = (snapshot or {}).get("dependencies") if isinstance(snapshot, dict) else {}
        return {
            "created_by": "POST-H-017-B",
            "status": "implemented-initial",
            "preliminary": True,
            "schema_id": "SCHEMA-DEVPL-RELEASE-ENVIRONMENT-SNAPSHOT-V1",
            "snapshot_id": (snapshot or {}).get("snapshot_id"),
            "python_version": ((snapshot or {}).get("python") or {}).get("version"),
            "platform_system": ((snapshot or {}).get("platform") or {}).get("system"),
            "dependencies_total": (dependencies or {}).get("dependencies_total", 0),
            "dependency_sources_total": len((dependencies or {}).get("sources") or []),
            "env_files_read": False,
            "secret_values_read": False,
            "secrets_included": False,
            "local_first": True,
            "read_only": True,
            "dry_run": True,
            "network_used": False,
            "external_api_used": False,
            "shell_used": False,
            "package_manager_processes_executed": False,
            "mutations_performed": False,
            "source_mutations_performed": False,
            "remote_execution_enabled": False,
            "connector_write_enabled": False,
            "plugin_execution_enabled": False,
            "reports_written": reports_written,
            "output_json": str(self.options.output_json).replace("\\", "/") if reports_written else None,
            "output_markdown": str(self.options.output_markdown).replace("\\", "/") if reports_written else None,
            "findings_total": findings_total,
            "blocking_findings_total": blocking_findings_total,
        }


def _dependency_name_record(raw: str, *, ecosystem: str, scope: str) -> dict[str, str]:
    name = _parse_dependency_name(raw)
    return {"name": name, "ecosystem": ecosystem, "scope": scope}


def _parse_dependency_name(raw: str) -> str:
    # Basic PEP 508/npm-compatible name extraction. Version specifiers and URLs
    # are deliberately omitted from the environment snapshot to reduce leakage.
    cleaned = raw.strip()
    if not cleaned:
        return "unknown"
    if " @ " in cleaned:
        cleaned = cleaned.split(" @ ", 1)[0]
    match = re.match(r"^([A-Za-z0-9_.-]+)", cleaned)
    return match.group(1) if match else "unknown"
