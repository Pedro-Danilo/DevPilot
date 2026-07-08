from __future__ import annotations

import json
import re
import sys
import zipfile
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter
from typing import Any

from devpilot_core import __version__
from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity

DEFAULT_LOCAL_INSTALL_SMOKE_REPORT_JSON = Path("outputs/reports/local_install_smoke_report.json")
DEFAULT_LOCAL_INSTALL_SMOKE_REPORT_MARKDOWN = Path("outputs/reports/local_install_smoke_report.md")
_FORBIDDEN_PACKAGE_PREFIXES = (
    "outputs/",
    ".git/",
    ".venv/",
    "venv/",
    ".pytest_cache/",
    "__pycache__/",
    "node_modules/",
    "ui/web/node_modules/",
    "ui/web/dist/",
    "dist/",
    "build/",
    ".devpilot/devpilot.db",
    ".devpilot/providers.yaml",
)
_REQUIRED_GITIGNORE_MARKERS = (
    "outputs/",
    ".venv/",
    "__pycache__/",
    ".pytest_cache/",
    ".devpilot/*.db",
    ".devpilot/providers.yaml",
    "ui/web/node_modules/",
    "ui/web/dist/",
)
_REQUIRED_OPERATOR_COMMANDS = (
    "python -m devpilot_core --version",
    "python -m devpilot_core project-state validate --json",
    "python -m devpilot_core docs-governance validate --json",
    "python -m devpilot_core schema list --json",
    "python -m devpilot_core test-contracts validate --json",
    "python -m devpilot_core test-contracts validate-v2 --json",
    "python -m devpilot_core industrial-readiness production-ready-local-final --json --write-report",
    "python -m devpilot_core api token --json",
    "python -m devpilot_core api serve --host 127.0.0.1 --port 8787 --execute",
    "npm --prefix ui/web test",
    "npm --prefix ui/web run dev -- --host 127.0.0.1 --port 5173",
    "python -m devpilot_core release-candidate ui-api-smoke --base-url http://127.0.0.1:8787 --json --write-report",
)
_REQUIRED_DOC_MARKERS = (
    "py -3.12 -m venv .venv",
    "python -m pip install -e .[dev]",
    "release-candidate install-smoke",
    "npm --prefix ui/web test",
    "127.0.0.1",
)
_REQUIRED_CLI_SOURCE_MARKERS = (
    "release-candidate",
    "evidence-freshness",
    "profile",
    "ui-api-smoke",
    "install-smoke",
)


@dataclass(frozen=True)
class LocalInstallSmokeOptions:
    output_json: str = str(DEFAULT_LOCAL_INSTALL_SMOKE_REPORT_JSON)
    output_markdown: str = str(DEFAULT_LOCAL_INSTALL_SMOKE_REPORT_MARKDOWN)
    candidate_zip: str | None = None
    write_report: bool = False


class LocalInstallSmokeRunner:
    """POST-H-026-D local install/run verification.

    The runner validates install/run readiness without creating virtual
    environments, calling pip, opening sockets or executing shell commands. It is
    a deterministic preflight that checks the local install recipe, package
    metadata, minimal CLI/API/UI command availability as versioned contracts and
    clean artifact hygiene. A candidate ZIP can be supplied for strict archive
    entry validation.
    """

    def __init__(self, root: Path, options: LocalInstallSmokeOptions | None = None) -> None:
        self.root = Path(root).resolve()
        self.options = options or LocalInstallSmokeOptions()

    def run(self) -> CommandResult:
        started = perf_counter()
        findings: list[Finding] = []
        checks: list[dict[str, Any]] = []

        pyproject = self._read_text("pyproject.toml")
        readme = self._read_text("README.md")
        runbook = self._read_text("docs/05_operations/runbook.md")
        backlog = self._read_text("docs/backlogs/POST-H-026_local_release_candidate_operator_verification.md")
        docs_bundle = "\n".join((readme, runbook, backlog))

        self._python_checks(pyproject, checks, findings)
        self._cli_contract_checks(checks, findings)
        self._frontend_checks(checks, findings)
        self._docs_checks(docs_bundle, checks, findings)
        self._artifact_hygiene_checks(checks, findings)
        self._no_go_claim_checks(checks, findings)

        blocking = [finding for finding in findings if finding.severity in {Severity.BLOCK, Severity.ERROR, Severity.FAIL}]
        decision = "PASS" if not blocking else "BLOCK"
        duration_ms = round((perf_counter() - started) * 1000, 3)
        checks_passed = sum(1 for check in checks if check["status"] == "pass")
        candidate_zip_checked = bool(self.options.candidate_zip)
        report = {
            "schema_version": "1.0",
            "schema_id": "SCHEMA-DEVPL-LOCAL-INSTALL-SMOKE-REPORT-V1",
            "report_id": "local-install-smoke-post_h_026_d",
            "created_by": "POST-H-026-D",
            "created_at": self._now(),
            "scope": "local-release-candidate",
            "decision": decision,
            "implemented_status": "implemented-initial",
            "execution_mode": "read-only-install-run-preflight",
            "candidate_zip": self.options.candidate_zip,
            "candidate_zip_checked": candidate_zip_checked,
            "checks_total": len(checks),
            "checks_passed_total": checks_passed,
            "checks_failed_total": len(checks) - checks_passed,
            "critical_checks_total": sum(1 for check in checks if check.get("critical") is True),
            "critical_checks_failed_total": sum(1 for check in checks if check.get("critical") is True and check["status"] != "pass"),
            "operator_commands_total": len(_REQUIRED_OPERATOR_COMMANDS),
            "operator_commands": list(_REQUIRED_OPERATOR_COMMANDS),
            "commands_executed": [],
            "checks": checks,
            "duration_ms": duration_ms,
            "safety": {
                "local_first": True,
                "read_only": True,
                "dry_run": True,
                "subprocess_executed": False,
                "pip_executed": False,
                "npm_executed": False,
                "socket_opened": False,
                "network_used": False,
                "external_api_used": False,
                "remote_execution_enabled": False,
                "connector_write_enabled": False,
                "plugin_execution_enabled": False,
                "mutations_performed": False,
                "source_mutations": False,
                "reports_written": self.options.write_report,
            },
            "summary": {
                "decision": decision,
                "created_by": "POST-H-026-D",
                "preliminary": True,
                "python_package_importable": self._check_status(checks, "python-package-importable"),
                "editable_install_documented": self._check_status(checks, "editable-install-documented"),
                "operator_checklist_documented": self._check_status(checks, "operator-checklist-documented"),
                "frontend_smoke_documented": self._check_status(checks, "frontend-local-smoke-documented"),
                "clean_package_policy_passed": self._check_status(checks, "clean-package-policy-configured") and self._check_status(checks, "candidate-zip-hygiene"),
                "candidate_zip_checked": candidate_zip_checked,
                "commands_executed": False,
                "reports_written": self.options.write_report,
                "network_used": False,
                "external_api_used": False,
                "mutations_performed": False,
                "source_mutations": False,
                "remote_execution_enabled": False,
                "connector_write_enabled": False,
                "plugin_execution_enabled": False,
            },
            "limitations": [
                "POST-H-026-D is a deterministic install/run preflight; it does not create virtual environments or execute pip/npm/subprocess commands.",
                "Strict archive-entry validation is performed when --candidate-zip is supplied; otherwise clean packaging is checked through source-controlled exclusion policy and operator documentation.",
                "Wheel/sdist reproducibility, OS matrix and upgrade/rollback packaging remain planned for POST-H-027.",
            ],
        }
        if self.options.write_report:
            self._write_report(report)

        if not blocking:
            findings.append(
                Finding(
                    "LOCAL_INSTALL_SMOKE_PASS",
                    "Local install/run preflight passed without executing installers, network calls or source mutations.",
                    Severity.INFO,
                    metadata={"checks_total": len(checks), "checks_passed_total": checks_passed, "candidate_zip_checked": candidate_zip_checked},
                )
            )
        return CommandResult(
            "release-candidate install-smoke",
            decision == "PASS",
            ExitCode.PASS if decision == "PASS" else ExitCode.BLOCK,
            "Local install smoke passed." if decision == "PASS" else "Local install smoke blocked.",
            data={"summary": report["summary"], "report": report, "reports": self._report_paths() if self.options.write_report else {}},
            findings=findings,
        )

    def _python_checks(self, pyproject: str, checks: list[dict[str, Any]], findings: list[Finding]) -> None:
        name = self._toml_value(pyproject, "name")
        version = self._toml_value(pyproject, "version")
        requires_python = self._toml_value(pyproject, "requires-python")
        backend = self._toml_value(pyproject, "build-backend")
        min_version = self._minimum_python(requires_python)
        current_ok = min_version is None or sys.version_info[:2] >= min_version
        metadata_ok = name == "devpilot-local" and bool(version) and version == __version__ and backend == "setuptools.build_meta"
        import_ok = bool(__version__) and (self.root / "src/devpilot_core/__main__.py").exists() and (self.root / "src/devpilot_core/cli.py").exists()
        self._record(checks, "python-version-supported", current_ok, f"Current Python {sys.version_info.major}.{sys.version_info.minor} satisfies requires-python={requires_python or 'unknown'}.", category="python", critical=True, metadata={"requires_python": requires_python, "current": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"})
        self._record(checks, "python-package-metadata", metadata_ok, "pyproject.toml exposes local package metadata and setuptools build backend.", category="python", critical=True, metadata={"name": name, "version": version, "package_version": __version__, "build_backend": backend})
        self._record(checks, "python-package-importable", import_ok, "devpilot_core package and python -m devpilot_core entrypoint are importable from the local source tree.", category="python", critical=True)
        if not current_ok:
            findings.append(Finding("LOCAL_INSTALL_PYTHON_VERSION_BLOCK", "Current Python does not satisfy pyproject requires-python.", Severity.BLOCK, path="pyproject.toml", metadata={"requires_python": requires_python}))
        if not metadata_ok:
            findings.append(Finding("LOCAL_INSTALL_PACKAGE_METADATA_BLOCK", "Local package metadata is incomplete or inconsistent with devpilot_core.__version__.", Severity.BLOCK, path="pyproject.toml", metadata={"name": name, "version": version, "package_version": __version__, "build_backend": backend}))
        if not import_ok:
            findings.append(Finding("LOCAL_INSTALL_PACKAGE_IMPORT_BLOCK", "devpilot_core package or module entrypoint is missing.", Severity.BLOCK, path="src/devpilot_core"))

    def _cli_contract_checks(self, checks: list[dict[str, Any]], findings: list[Finding]) -> None:
        cli_source = self._read_text("src/devpilot_core/cli.py")
        registry_source = self._read_text("src/devpilot_core/cli_registry/registry.py")
        profiles_payload = self._load_json(".devpilot/testing/test_profiles.json")
        profile = {}
        for item in profiles_payload.get("profiles", []) if isinstance(profiles_payload, dict) else []:
            if isinstance(item, dict) and item.get("profile_id") == "release-candidate-local":
                profile = item
                break
        missing_cli_markers = [marker for marker in _REQUIRED_CLI_SOURCE_MARKERS if marker not in cli_source]
        commands = profile.get("commands", []) if isinstance(profile, dict) else []
        pytest_targets = profile.get("pytest_targets", []) if isinstance(profile, dict) else []
        profile_ok = "release-candidate install-smoke" in commands and "tests/test_post_h_026_install_smoke.py" in pytest_targets
        registry_ok = "release-candidate" in registry_source and "test_post_h_026_install_smoke.py" in registry_source
        self._record(checks, "cli-release-candidate-commands-available", not missing_cli_markers, "Release-candidate CLI command family exposes install-smoke and prior RC commands.", category="cli", critical=True, metadata={"missing_markers": missing_cli_markers})
        self._record(checks, "rc-profile-includes-install-smoke", profile_ok, "release-candidate-local profile includes install-smoke command and tests.", category="cli", critical=True)
        self._record(checks, "cli-registry-includes-install-smoke-tests", registry_ok, "CLI registry metadata includes install-smoke recommended tests.", category="cli", critical=True)
        if missing_cli_markers:
            findings.append(Finding("LOCAL_INSTALL_CLI_COMMANDS_MISSING_BLOCK", "CLI source is missing required release-candidate install/run command markers.", Severity.BLOCK, path="src/devpilot_core/cli.py", metadata={"missing": missing_cli_markers}))
        if not profile_ok:
            findings.append(Finding("LOCAL_INSTALL_RC_PROFILE_MISSING_BLOCK", "release-candidate-local profile does not include install-smoke command/test coverage.", Severity.BLOCK, path=".devpilot/testing/test_profiles.json"))
        if not registry_ok:
            findings.append(Finding("LOCAL_INSTALL_CLI_REGISTRY_MISSING_BLOCK", "CLI registry metadata does not include install-smoke coverage.", Severity.BLOCK, path="src/devpilot_core/cli_registry/registry.py"))

    def _frontend_checks(self, checks: list[dict[str, Any]], findings: list[Finding]) -> None:
        package_path = self.root / "ui/web/package.json"
        try:
            package = json.loads(package_path.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError) as exc:
            package = {}
            findings.append(Finding("LOCAL_INSTALL_FRONTEND_PACKAGE_LOAD_BLOCK", "Web UI package.json could not be loaded.", Severity.BLOCK, path="ui/web/package.json", metadata={"error": str(exc)}))
        scripts = package.get("scripts", {}) if isinstance(package, dict) else {}
        test_ok = scripts.get("test") == "node scripts/smoke-test.mjs"
        dev_ok = "127.0.0.1" in str(scripts.get("dev", "")) and "5173" in str(scripts.get("dev", ""))
        smoke_exists = (self.root / "ui/web/scripts/smoke-test.mjs").exists()
        self._record(checks, "frontend-local-smoke-documented", test_ok and smoke_exists, "Web UI package exposes deterministic local smoke test.", category="frontend", critical=True, metadata={"test_script": scripts.get("test"), "smoke_script_exists": smoke_exists})
        self._record(checks, "frontend-local-dev-host", dev_ok, "Web UI dev script binds to 127.0.0.1:5173.", category="frontend", critical=True, metadata={"dev_script": scripts.get("dev")})
        if not (test_ok and smoke_exists):
            findings.append(Finding("LOCAL_INSTALL_FRONTEND_SMOKE_BLOCK", "Web UI local smoke script is missing or not configured.", Severity.BLOCK, path="ui/web/package.json"))
        if not dev_ok:
            findings.append(Finding("LOCAL_INSTALL_FRONTEND_HOST_BLOCK", "Web UI dev script must bind to localhost for RC install/run verification.", Severity.BLOCK, path="ui/web/package.json"))

    def _docs_checks(self, docs_bundle: str, checks: list[dict[str, Any]], findings: list[Finding]) -> None:
        missing_doc_markers = [marker for marker in _REQUIRED_DOC_MARKERS if marker not in docs_bundle]
        command_coverage = [command for command in _REQUIRED_OPERATOR_COMMANDS if self._command_marker(command) not in docs_bundle]
        self._record(checks, "editable-install-documented", "python -m pip install -e .[dev]" in docs_bundle, "Editable local install command is documented for operators.", category="docs", critical=True)
        self._record(checks, "operator-checklist-documented", not missing_doc_markers and not command_coverage, "Operator install/run checklist is documented without relying on conversational memory.", category="docs", critical=True, metadata={"missing_markers": missing_doc_markers, "missing_commands": command_coverage})
        if missing_doc_markers or command_coverage:
            findings.append(Finding("LOCAL_INSTALL_OPERATOR_DOCS_BLOCK", "README/runbook/backlog do not document the required local install/run checklist.", Severity.BLOCK, metadata={"missing_markers": missing_doc_markers, "missing_commands": command_coverage}))

    def _artifact_hygiene_checks(self, checks: list[dict[str, Any]], findings: list[Finding]) -> None:
        gitignore = self._read_text(".gitignore")
        missing_ignore = [marker for marker in _REQUIRED_GITIGNORE_MARKERS if marker not in gitignore]
        self._record(checks, "clean-package-policy-configured", not missing_ignore, "Source-controlled ignore policy excludes runtime artifacts from local release packages.", category="artifact", critical=True, metadata={"missing_ignore_markers": missing_ignore})
        if missing_ignore:
            findings.append(Finding("LOCAL_INSTALL_CLEAN_PACKAGE_POLICY_BLOCK", "Clean package exclusion policy is incomplete.", Severity.BLOCK, path=".gitignore", metadata={"missing": missing_ignore}))

        zip_ok = True
        violations: list[str] = []
        if self.options.candidate_zip:
            zip_path = self._resolve_existing(self.options.candidate_zip)
            try:
                with zipfile.ZipFile(zip_path) as archive:
                    for name in archive.namelist():
                        normalized = name.replace("\\", "/").lstrip("./")
                        if any(normalized == prefix.rstrip("/") or normalized.startswith(prefix) for prefix in _FORBIDDEN_PACKAGE_PREFIXES):
                            violations.append(normalized)
            except (OSError, zipfile.BadZipFile) as exc:
                zip_ok = False
                findings.append(Finding("LOCAL_INSTALL_CANDIDATE_ZIP_LOAD_BLOCK", "Candidate ZIP could not be inspected.", Severity.BLOCK, path=self._relative(zip_path), metadata={"error": str(exc)}))
            zip_ok = zip_ok and not violations
            if violations:
                findings.append(Finding("LOCAL_INSTALL_CANDIDATE_ZIP_RUNTIME_ARTIFACTS_BLOCK", "Candidate ZIP contains runtime artifacts that must not be packaged.", Severity.BLOCK, path=self._relative(zip_path), metadata={"violations": violations[:50], "violations_total": len(violations)}))
        self._record(checks, "candidate-zip-hygiene", zip_ok, "Candidate ZIP has no forbidden runtime entries when supplied; otherwise source policy is used.", category="artifact", critical=True, metadata={"candidate_zip_checked": bool(self.options.candidate_zip), "violations_total": len(violations), "violations": violations[:20]})

    def _no_go_claim_checks(self, checks: list[dict[str, Any]], findings: list[Finding]) -> None:
        state = self._load_json(".devpilot/project_state.json")
        forbidden_flags = {
            "remote_execution_enabled": state.get("remote_execution_enabled"),
            "connector_write_enabled": state.get("connector_write_enabled"),
            "plugin_execution_enabled": state.get("plugin_execution_enabled"),
            "post_h_026_remote_execution_enabled": state.get("post_h_026_remote_execution_enabled"),
            "post_h_026_connector_write_enabled": state.get("post_h_026_connector_write_enabled"),
            "post_h_026_plugin_execution_enabled": state.get("post_h_026_plugin_execution_enabled"),
            "post_h_026_external_apis_required": state.get("post_h_026_external_apis_required"),
        }
        unsafe = {key: value for key, value in forbidden_flags.items() if value is not False}
        claims = {
            "enterprise_ready_claimed": state.get("post_h_026_enterprise_ready_claimed"),
            "compliance_certified_claimed": state.get("post_h_026_compliance_certified_claimed"),
            "remote_ready_claimed": state.get("post_h_026_remote_ready_claimed"),
            "saas_ready_claimed": state.get("post_h_026_saas_ready_claimed"),
        }
        unsafe_claims = {key: value for key, value in claims.items() if value is not False}
        self._record(checks, "no-go-gates-remain-disabled", not unsafe, "Remote execution, connector write, plugin execution and external API no-go gates remain disabled.", category="security", critical=True, metadata={"unsafe_flags": unsafe})
        self._record(checks, "forbidden-claims-remain-false", not unsafe_claims, "Install smoke does not add enterprise/compliance/remote/SaaS claims.", category="security", critical=True, metadata={"unsafe_claims": unsafe_claims})
        if unsafe or unsafe_claims:
            findings.append(Finding("LOCAL_INSTALL_NO_GO_OR_CLAIMS_BLOCK", "Local install smoke detected enabled no-go gates or forbidden claims.", Severity.BLOCK, path=".devpilot/project_state.json", metadata={"unsafe_flags": unsafe, "unsafe_claims": unsafe_claims}))

    def _record(self, checks: list[dict[str, Any]], check_id: str, passed: bool, reason: str, *, category: str, critical: bool, metadata: dict[str, Any] | None = None) -> bool:
        checks.append({"check_id": check_id, "category": category, "status": "pass" if passed else "block", "critical": critical, "reason": reason, "metadata": metadata or {}})
        return passed

    def _check_status(self, checks: list[dict[str, Any]], check_id: str) -> bool:
        return any(check.get("check_id") == check_id and check.get("status") == "pass" for check in checks)

    def _read_text(self, relative_path: str) -> str:
        path = self.root / relative_path
        try:
            return path.read_text(encoding="utf-8", errors="replace")
        except FileNotFoundError:
            return ""

    def _load_json(self, relative_path: str) -> dict[str, Any]:
        path = self.root / relative_path
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            return payload if isinstance(payload, dict) else {}
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def _toml_value(self, text: str, key: str) -> str:
        match = re.search(rf"^\s*{re.escape(key)}\s*=\s*\"([^\"]+)\"", text, flags=re.MULTILINE)
        return match.group(1).strip() if match else ""

    def _minimum_python(self, requires_python: str) -> tuple[int, int] | None:
        match = re.search(r">=\s*([0-9]+)\.([0-9]+)", requires_python or "")
        if not match:
            return None
        return int(match.group(1)), int(match.group(2))

    def _command_marker(self, command: str) -> str:
        if command.startswith("python -m devpilot_core "):
            return command.replace("python -m devpilot_core ", "").split(" --", 1)[0]
        if command.startswith("npm --prefix ui/web"):
            return "npm --prefix ui/web"
        return command

    def _write_report(self, report: dict[str, Any]) -> None:
        json_path = self._resolve_output(self.options.output_json)
        markdown_path = self._resolve_output(self.options.output_markdown)
        json_path.parent.mkdir(parents=True, exist_ok=True)
        markdown_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        markdown_path.write_text(self._markdown(report), encoding="utf-8")

    def _markdown(self, report: dict[str, Any]) -> str:
        lines = [
            "# Local install smoke report",
            "",
            f"- Decision: `{report['decision']}`",
            f"- Scope: `{report['scope']}`",
            f"- Execution mode: `{report['execution_mode']}`",
            f"- Candidate ZIP checked: `{report['candidate_zip_checked']}`",
            f"- Checks: `{report['checks_passed_total']}/{report['checks_total']}`",
            f"- Commands executed: `{bool(report['commands_executed'])}`",
            f"- Network used: `{report['safety']['network_used']}`",
            "",
            "## Operator commands",
        ]
        lines.extend(f"- `{command}`" for command in report["operator_commands"])
        lines.extend(["", "## Checks"])
        lines.extend(f"- `{check['status']}` · `{check['check_id']}` · {check['reason']}" for check in report["checks"])
        lines.extend(["", "## Limitations"])
        lines.extend(f"- {item}" for item in report["limitations"])
        return "\n".join(lines) + "\n"

    def _report_paths(self) -> dict[str, str]:
        return {"json": self._relative(self._resolve_output(self.options.output_json)), "markdown": self._relative(self._resolve_output(self.options.output_markdown))}

    def _resolve_output(self, path: str | Path) -> Path:
        candidate = Path(path)
        if not candidate.is_absolute():
            candidate = self.root / candidate
        resolved = candidate.resolve()
        try:
            resolved.relative_to(self.root)
        except ValueError as exc:
            raise ValueError(f"Path escapes project root: {path}") from exc
        return resolved

    def _resolve_existing(self, path: str | Path) -> Path:
        candidate = Path(path)
        if not candidate.is_absolute():
            candidate = self.root / candidate
        return candidate.resolve()

    def _relative(self, path: Path) -> str:
        try:
            return str(path.resolve().relative_to(self.root)).replace("\\", "/")
        except ValueError:
            return str(path).replace("\\", "/")

    def _now(self) -> str:
        return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
