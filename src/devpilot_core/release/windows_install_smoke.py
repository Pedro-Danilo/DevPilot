from __future__ import annotations

import json
import platform
import re
import shutil
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter
from typing import Any

from devpilot_core import __version__
from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity

DEFAULT_WINDOWS_INSTALL_SMOKE_REPORT_JSON = Path("outputs/reports/windows_install_smoke_report.json")
DEFAULT_WINDOWS_INSTALL_SMOKE_REPORT_MARKDOWN = Path("outputs/reports/windows_install_smoke_report.md")

_SUPPORTED_MODES = {"editable", "wheel", "zip"}
_REQUIRED_GUIDE_MARKERS = (
    "POST-H-027-D",
    "py -3.12 -m venv .venv",
    ".venv\\Scripts\\Activate.ps1",
    "python -m pip install -e .[dev]",
    "python -m devpilot_core install windows-smoke --mode editable --json --write-report",
    "python -m devpilot_core install windows-smoke --mode wheel",
    "python -m devpilot_core install windows-smoke --mode zip",
    "python -m devpilot_core release artifact-manifest --version 0.1.0 --verify-checksums --json --write-report",
    "python -m devpilot_core api token --json",
    "127.0.0.1",
    "npm --prefix ui/web test",
    "ExecutionPolicy",
    "node_modules",
    "outputs/",
    "dist/",
    ".venv/",
)
_REQUIRED_MINIMAL_CLI_MARKERS = (
    "python -m devpilot_core --version",
    "python -m devpilot_core schema list --json",
    "python -m devpilot_core project-state validate --json",
    "python -m devpilot_core docs-governance validate --json",
    "python -m devpilot_core release artifact-manifest --version 0.1.0 --verify-checksums --json --write-report",
)
_FORBIDDEN_GUIDE_MARKERS = (
    "--host 0.0.0.0",
    "allow_origins=[\"*\"]",
    "CORS wildcard enabled",
    "Set-ExecutionPolicy Unrestricted",
)


@dataclass(frozen=True)
class WindowsInstallSmokeOptions:
    mode: str = "editable"
    version: str = "0.1.0"
    artifact: str | None = None
    output_json: str = str(DEFAULT_WINDOWS_INSTALL_SMOKE_REPORT_JSON)
    output_markdown: str = str(DEFAULT_WINDOWS_INSTALL_SMOKE_REPORT_MARKDOWN)
    write_report: bool = False


class WindowsInstallSmokeRunner:
    """POST-H-027-D Windows operator install smoke.

    The runner is a local-first, schema-backed preflight for the Windows install
    recipe. It does not create venvs, run pip, run npm, open sockets, publish,
    deploy, require administrator privileges or mutate source files. Instead it
    verifies that the Windows operator path is explicit and executable by the
    operator: editable/wheel/ZIP commands are documented, local artifacts remain
    inside the workspace, core CLI/API localhost invariants are present, and
    frontend prerequisites are classified as advisory rather than blocking Python
    package validation.
    """

    def __init__(self, root: Path, options: WindowsInstallSmokeOptions | None = None) -> None:
        self.root = Path(root).resolve()
        self.options = options or WindowsInstallSmokeOptions()

    def run(self) -> CommandResult:
        started = perf_counter()
        checks: list[dict[str, Any]] = []
        findings: list[Finding] = []
        mode = self.options.mode

        install_guide = self._read_text("docs/05_operations/install_guide.md")
        runbook = self._read_text("docs/05_operations/runbook.md")
        readme = self._read_text("README.md")
        cli_source = self._read_text("src/devpilot_core/cli.py")
        api_security = self._read_text("src/devpilot_core/interfaces/api/security.py")
        docs_bundle = "\n".join((install_guide, runbook, readme))

        self._mode_check(mode, checks, findings)
        artifact_info = self._artifact_check(mode, checks, findings)
        self._python_prereq_check(checks)
        self._pip_venv_recipe_check(install_guide, checks, findings)
        self._guide_content_check(install_guide, checks, findings)
        self._minimal_cli_recipe_check(docs_bundle, cli_source, checks, findings)
        self._api_localhost_check(docs_bundle, api_security, checks, findings)
        self._frontend_prereq_check(install_guide, checks, findings)
        self._runtime_exclusion_check(docs_bundle, checks, findings)
        self._safety_policy_check(checks, findings)

        blocking = [finding for finding in findings if finding.severity in {Severity.BLOCK, Severity.ERROR, Severity.FAIL}]
        decision = "PASS" if not blocking else "BLOCK"
        duration_ms = round((perf_counter() - started) * 1000, 3)
        checks_passed = sum(1 for item in checks if item["status"] == "pass")
        checks_advisory = sum(1 for item in checks if item["status"] == "advisory")
        checks_failed = sum(1 for item in checks if item["status"] == "block")

        report = {
            "schema_version": "1.0",
            "schema_id": "SCHEMA-DEVPL-WINDOWS-INSTALL-SMOKE-REPORT-V1",
            "report_id": f"windows-install-smoke-post_h_027_d-{mode}",
            "created_by": "POST-H-027-D",
            "status": "implemented-initial",
            "generated_at_utc": self._now(),
            "scope": "windows-local-install-smoke",
            "mode": mode,
            "release_version": self.options.version,
            "artifact": artifact_info,
            "environment": {
                "os_name": platform.system() or "unknown",
                "platform": platform.platform(),
                "windows_host_detected": platform.system().lower() == "windows",
                "python_executable": _normalize_path(sys.executable),
                "python_version": platform.python_version(),
                "devpilot_version": __version__,
                "npm_available": shutil.which("npm") is not None,
                "node_available": shutil.which("node") is not None,
            },
            "checks_total": len(checks),
            "checks_passed_total": checks_passed,
            "checks_advisory_total": checks_advisory,
            "checks_failed_total": checks_failed,
            "critical_checks_failed_total": sum(1 for item in checks if item["critical"] and item["status"] == "block"),
            "checks": checks,
            "summary": {
                "decision": decision,
                "created_by": "POST-H-027-D",
                "preliminary": True,
                "scope": "windows-local-install-smoke",
                "mode": mode,
                "release_version": self.options.version,
                "guide_has_editable_flow": _contains_all(install_guide, ["python -m pip install -e .[dev]", "--mode editable"]),
                "guide_has_wheel_flow": "--mode wheel" in install_guide and "devpilot_local-0.1.0-py3-none-any.whl" in install_guide,
                "guide_has_zip_flow": "--mode zip" in install_guide and "devpilot-local-0.1.0-source.zip" in install_guide,
                "core_cli_smoke_documented": _contains_all(docs_bundle, _REQUIRED_MINIMAL_CLI_MARKERS),
                "artifact_required": artifact_info["required"],
                "artifact_exists": artifact_info["exists"],
                "frontend_prereq_advisory": any(item["check_id"] == "frontend-npm-prereq" and item["status"] == "advisory" for item in checks),
                "admin_required": False,
                "network_used": False,
                "external_api_used": False,
                "publish_performed": False,
                "deploy_performed": False,
                "pip_executed": False,
                "npm_executed": False,
                "socket_opened": False,
                "remote_execution_enabled": False,
                "connector_write_enabled": False,
                "plugin_execution_enabled": False,
                "source_mutations": False,
                "reports_written": bool(self.options.write_report),
            },
            "safety": {
                "local_first": True,
                "read_only": not self.options.write_report,
                "dry_run": True,
                "admin_required": False,
                "network_used": False,
                "external_api_used": False,
                "publish_performed": False,
                "deploy_performed": False,
                "pip_executed": False,
                "npm_executed": False,
                "socket_opened": False,
                "remote_execution_enabled": False,
                "connector_write_enabled": False,
                "plugin_execution_enabled": False,
                "source_mutations": False,
                "reports_written": bool(self.options.write_report),
            },
            "limitations": [
                "POST-H-027-D validates the Windows operator install recipe and local artifact preconditions; it does not create MSI installers, services or auto-update flows.",
                "The smoke does not install Python, Node or dependencies automatically; missing frontend tooling is classified as advisory for the Python core path.",
                "Upgrade/rollback dry-run remains POST-H-027-E scope.",
            ],
            "preliminary": True,
        }

        data: dict[str, Any] = {
            "summary": report["summary"],
            "report": report,
            "reports": {},
            "notes": [
                "Windows install smoke is local-first and dry-run by design.",
                "Core Python checks remain independent from optional Web UI npm prerequisites.",
            ],
        }
        if self.options.write_report:
            data["reports"] = self._write_outputs(report)
            report["summary"]["reports_written"] = True
            report["safety"]["reports_written"] = True
            data["summary"] = report["summary"]

        return CommandResult(
            command="install windows-smoke",
            ok=decision == "PASS",
            exit_code=ExitCode.PASS if decision == "PASS" else ExitCode.BLOCK,
            message="Windows install smoke passed." if decision == "PASS" else "Windows install smoke blocked.",
            data=data,
            findings=findings,
        )

    def _mode_check(self, mode: str, checks: list[dict[str, Any]], findings: list[Finding]) -> None:
        ok = mode in _SUPPORTED_MODES
        self._record(checks, "windows-install-mode-supported", ok, "Windows install smoke mode is supported.", category="input", critical=True, metadata={"mode": mode, "supported_modes": sorted(_SUPPORTED_MODES)})
        if not ok:
            findings.append(Finding("WINDOWS_INSTALL_MODE_UNSUPPORTED", f"Unsupported Windows install smoke mode: {mode}.", Severity.ERROR, metadata={"mode": mode}))

    def _artifact_check(self, mode: str, checks: list[dict[str, Any]], findings: list[Finding]) -> dict[str, Any]:
        default_artifact = {
            "wheel": f"dist/devpilot_local-{self.options.version}-py3-none-any.whl",
            "zip": f"dist/release/devpilot-local-{self.options.version}-source.zip",
        }.get(mode)
        artifact = self.options.artifact or default_artifact
        info = {
            "required": mode in {"wheel", "zip"},
            "provided": _normalize_path(artifact) if artifact else None,
            "resolved": None,
            "exists": False,
            "inside_workspace": True,
            "kind": mode if mode in {"wheel", "zip"} else "editable",
            "expected_suffix": ".whl" if mode == "wheel" else ".zip" if mode == "zip" else None,
        }
        if not artifact:
            self._record(checks, "windows-install-artifact-not-required", True, "Editable mode does not require a built release artifact.", category="artifact", critical=True, metadata=info)
            return info

        normalized = _normalize_path(artifact)
        artifact_path = _workspace_path(self.root, artifact)
        info["resolved"] = _normalize_path(_relative_or_absolute(self.root, artifact_path))
        try:
            artifact_path.relative_to(self.root)
        except ValueError:
            info["inside_workspace"] = False
            self._record(checks, "windows-install-artifact-inside-workspace", False, "Install artifact must stay inside the workspace.", category="artifact", critical=True, metadata=info)
            findings.append(Finding("WINDOWS_INSTALL_ARTIFACT_OUTSIDE_WORKSPACE", "Windows install smoke artifact path must stay inside the workspace.", Severity.BLOCK, path=normalized))
            return info

        exists = artifact_path.exists()
        suffix_ok = artifact_path.name.endswith(str(info["expected_suffix"])) if info["expected_suffix"] else True
        info["exists"] = exists
        self._record(checks, "windows-install-artifact-local-supported", (not info["required"] or (exists and suffix_ok)), "Required local install artifact exists and has the expected suffix.", category="artifact", critical=True, metadata=info)
        if info["required"] and not exists:
            findings.append(Finding("WINDOWS_INSTALL_ARTIFACT_MISSING", "Windows install smoke requires the selected local artifact to exist.", Severity.BLOCK, path=normalized, metadata=info))
        elif info["required"] and not suffix_ok:
            findings.append(Finding("WINDOWS_INSTALL_ARTIFACT_SUFFIX_UNSUPPORTED", "Windows install artifact has an unsupported suffix for the selected mode.", Severity.BLOCK, path=normalized, metadata=info))
        return info

    def _python_prereq_check(self, checks: list[dict[str, Any]]) -> None:
        version_ok = sys.version_info >= (3, 11)
        self._record(checks, "python-version-compatible", version_ok, "Python version is compatible with the local DevPilot operator smoke.", category="environment", critical=True, metadata={"python_version": platform.python_version(), "recommended": "3.12", "minimum": "3.11"})

    def _pip_venv_recipe_check(self, install_guide: str, checks: list[dict[str, Any]], findings: list[Finding]) -> None:
        markers = ["py -3.12 -m venv .venv", ".venv\\Scripts\\Activate.ps1", "python -m pip install --upgrade pip", "python -m pip install -e .[dev]"]
        ok = _contains_all(install_guide, markers)
        self._record(checks, "windows-venv-pip-recipe-documented", ok, "Windows venv activation and pip install recipe are documented.", category="docs", critical=True, metadata={"missing_markers": [item for item in markers if item not in install_guide]})
        if not ok:
            findings.append(Finding("WINDOWS_INSTALL_GUIDE_VENV_PIP_RECIPE_MISSING", "Windows install guide is missing venv/pip recipe markers.", Severity.BLOCK, path="docs/05_operations/install_guide.md"))

    def _guide_content_check(self, install_guide: str, checks: list[dict[str, Any]], findings: list[Finding]) -> None:
        missing = [item for item in _REQUIRED_GUIDE_MARKERS if item not in install_guide]
        forbidden = [item for item in _FORBIDDEN_GUIDE_MARKERS if item in install_guide]
        ok = not missing and not forbidden
        self._record(checks, "windows-install-guide-contract", ok, "Windows install guide contains required operator flow and no unsafe host/CORS/execution-policy recommendations.", category="docs", critical=True, metadata={"missing_markers": missing, "forbidden_markers": forbidden})
        if missing:
            findings.append(Finding("WINDOWS_INSTALL_GUIDE_REQUIRED_MARKERS_MISSING", "Windows install guide is missing required POST-H-027-D markers.", Severity.BLOCK, path="docs/05_operations/install_guide.md", metadata={"missing_markers": missing}))
        if forbidden:
            findings.append(Finding("WINDOWS_INSTALL_GUIDE_UNSAFE_MARKERS", "Windows install guide contains unsafe Windows/API recommendations.", Severity.BLOCK, path="docs/05_operations/install_guide.md", metadata={"forbidden_markers": forbidden}))

    def _minimal_cli_recipe_check(self, docs_bundle: str, cli_source: str, checks: list[dict[str, Any]], findings: list[Finding]) -> None:
        docs_missing = [item for item in _REQUIRED_MINIMAL_CLI_MARKERS if item not in docs_bundle]
        source_markers = ["windows-smoke", "artifact-manifest", "python-artifact-verify", "source-zip-policy"]
        source_missing = [item for item in source_markers if item not in cli_source]
        ok = not docs_missing and not source_missing
        self._record(checks, "core-cli-smoke-contract-documented", ok, "Core CLI smoke commands are documented and routed in CLI source.", category="cli", critical=True, metadata={"docs_missing": docs_missing, "source_missing": source_missing})
        if docs_missing or source_missing:
            findings.append(Finding("WINDOWS_INSTALL_CORE_CLI_SMOKE_CONTRACT_INCOMPLETE", "Windows install smoke core CLI contract is incomplete.", Severity.BLOCK, metadata={"docs_missing": docs_missing, "source_missing": source_missing}))

    def _api_localhost_check(self, docs_bundle: str, api_security: str, checks: list[dict[str, Any]], findings: list[Finding]) -> None:
        required = ["python -m devpilot_core api token --json", "127.0.0.1", "release-candidate ui-api-smoke"]
        forbidden = ["--host 0.0.0.0", "allow_origins=[\"*\"]"]
        ok = _contains_all(docs_bundle, required) and "127.0.0.1" in api_security and not any(item in docs_bundle for item in forbidden)
        self._record(checks, "api-localhost-token-contract", ok, "Windows flow documents API token and localhost-only host posture without wildcard CORS.", category="security", critical=True, metadata={"required_missing": [item for item in required if item not in docs_bundle], "forbidden_present": [item for item in forbidden if item in docs_bundle]})
        if not ok:
            findings.append(Finding("WINDOWS_INSTALL_API_LOCALHOST_CONTRACT_INCOMPLETE", "Windows install smoke requires localhost-only API/token documentation.", Severity.BLOCK, path="docs/05_operations/install_guide.md"))

    def _frontend_prereq_check(self, install_guide: str, checks: list[dict[str, Any]], findings: list[Finding]) -> None:
        npm_available = shutil.which("npm") is not None
        package_json = self.root / "ui/web/package.json"
        smoke_script = self.root / "ui/web/scripts/smoke-test.mjs"
        documented = "npm --prefix ui/web test" in install_guide
        ok = documented and package_json.exists() and smoke_script.exists()
        status_ok = ok and npm_available
        if status_ok:
            self._record(checks, "frontend-npm-prereq", True, "npm Web UI smoke prerequisite is available and documented.", category="frontend", critical=False, metadata={"npm_available": True, "package_json_exists": True, "smoke_script_exists": True})
            return
        severity = Severity.WARNING
        self._record(checks, "frontend-npm-prereq", "advisory", "Frontend npm smoke is optional for Python core install and is classified as advisory when prerequisites are absent.", category="frontend", critical=False, metadata={"npm_available": npm_available, "package_json_exists": package_json.exists(), "smoke_script_exists": smoke_script.exists(), "documented": documented})
        findings.append(Finding("WINDOWS_INSTALL_FRONTEND_PREREQ_ADVISORY", "Web UI npm smoke prerequisite is advisory for the Python core Windows install path.", severity, metadata={"npm_available": npm_available, "documented": documented}))

    def _runtime_exclusion_check(self, docs_bundle: str, checks: list[dict[str, Any]], findings: list[Finding]) -> None:
        markers = ["node_modules", "outputs/", "dist/", ".venv/", ".pytest_cache", "__pycache__"]
        missing = [item for item in markers if item not in docs_bundle]
        ok = not missing
        self._record(checks, "runtime-artifact-exclusions-documented", ok, "Windows guide/runbook document runtime artifact exclusions from version control.", category="docs", critical=True, metadata={"missing_markers": missing})
        if missing:
            findings.append(Finding("WINDOWS_INSTALL_RUNTIME_EXCLUSIONS_MISSING", "Windows install documentation must state runtime artifacts are not versioned.", Severity.BLOCK, path="docs/05_operations/install_guide.md", metadata={"missing_markers": missing}))

    def _safety_policy_check(self, checks: list[dict[str, Any]], findings: list[Finding]) -> None:
        ok = True
        self._record(checks, "windows-install-no-go-safety", ok, "Windows smoke does not require admin, network, publish, deploy, sockets, remote execution, connector write or plugin execution.", category="safety", critical=True, metadata={"admin_required": False, "network_used": False, "external_api_used": False, "publish_performed": False, "deploy_performed": False, "socket_opened": False})

    def _record(
        self,
        checks: list[dict[str, Any]],
        check_id: str,
        ok_or_status: bool | str,
        reason: str,
        *,
        category: str,
        critical: bool,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        if isinstance(ok_or_status, str):
            status = ok_or_status
        else:
            status = "pass" if ok_or_status else "block"
        checks.append({
            "check_id": check_id,
            "category": category,
            "status": status,
            "critical": critical,
            "reason": reason,
            "metadata": metadata or {},
        })

    def _read_text(self, rel_path: str) -> str:
        path = self.root / rel_path
        if not path.exists():
            return ""
        return path.read_text(encoding="utf-8")

    def _write_outputs(self, report: dict[str, Any]) -> dict[str, str]:
        json_rel = _normalize_path(self.options.output_json)
        markdown_rel = _normalize_path(self.options.output_markdown)
        json_path = _workspace_path(self.root, self.options.output_json)
        markdown_path = _workspace_path(self.root, self.options.output_markdown)
        json_path.parent.mkdir(parents=True, exist_ok=True)
        markdown_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        markdown_path.write_text(_markdown_report(report), encoding="utf-8")
        return {"json": json_rel, "markdown": markdown_rel}

    @staticmethod
    def _now() -> str:
        return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _workspace_path(root: Path, rel_or_abs: str) -> Path:
    value = str(rel_or_abs).replace("\\", "/")
    path = Path(value)
    if path.is_absolute():
        return path
    return (root / path).resolve()


def _normalize_path(value: str | Path | None) -> str | None:
    if value is None:
        return None
    return str(value).replace("\\", "/")


def _relative_or_absolute(root: Path, path: Path) -> Path | str:
    try:
        return path.relative_to(root)
    except ValueError:
        return path


def _contains_all(text: str, markers: list[str] | tuple[str, ...]) -> bool:
    return all(marker in text for marker in markers)


def _markdown_report(report: dict[str, Any]) -> str:
    summary = report["summary"]
    lines = [
        "# POST-H-027-D — Windows install smoke report",
        "",
        f"- Decision: `{summary['decision']}`",
        f"- Mode: `{summary['mode']}`",
        f"- Release version: `{summary['release_version']}`",
        f"- Checks: {report['checks_passed_total']} pass / {report['checks_advisory_total']} advisory / {report['checks_failed_total']} block",
        f"- Network used: `{summary['network_used']}`",
        f"- External API used: `{summary['external_api_used']}`",
        f"- Admin required: `{summary['admin_required']}`",
        "",
        "## Checks",
        "",
    ]
    for check in report["checks"]:
        lines.append(f"- `{check['check_id']}`: **{check['status']}** — {check['reason']}")
    lines.extend([
        "",
        "## Limitations",
        "",
    ])
    for item in report["limitations"]:
        lines.append(f"- {item}")
    return "\n".join(lines) + "\n"
