from __future__ import annotations

import fnmatch
import hashlib
import io
import json
import subprocess
import tarfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.runtime_state.inventory import RuntimeStateInventoryBuilder, RuntimeStateInventoryOptions
from devpilot_core.runtime_state.models import RuntimeStatePolicy, utc_now_iso
from devpilot_core.runtime_state.policy import RuntimeStatePolicyLoader

POST_H_008_E_CREATED_BY = "POST-H-008-E"
RUNTIME_STATE_HYGIENE_SCHEMA_ID = "SCHEMA-DEVPL-RUNTIME-STATE-HYGIENE-REPORT-V1"
RUNTIME_STATE_HYGIENE_REPORT_ID = "devpilot-runtime-state-hygiene-report"
RUNTIME_STATE_HYGIENE_CONTRACT = "RuntimeStateHygieneReport"

DEFAULT_HYGIENE_JSON = Path("outputs/reports/runtime_state_hygiene_report.json")
DEFAULT_HYGIENE_MARKDOWN = Path("outputs/reports/runtime_state_hygiene_report.md")

# Release/archive hygiene is intentionally stricter than the current minimal
# package builder: this gate centralizes runtime-state exclusions so package,
# audit-pack and manual ZIP workflows can converge on the same policy.
BASE_FORBIDDEN_ARCHIVE_PATTERNS: tuple[str, ...] = (
    ".git/",
    ".venv/",
    "venv/",
    "node_modules/",
    "ui/web/node_modules/",
    "dist/",
    "build/",
    "__pycache__/",
    ".pytest_cache/",
    ".mypy_cache/",
    ".ruff_cache/",
    ".tox/",
    ".nox/",
    ".cache/",
    "*.pyc",
    "*.pyo",
    ".devpilot/devpilot.db",
    ".devpilot/*.db",
    ".devpilot/*.db-*",
    ".devpilot/backups/",
    ".devpilot/agent_sessions/",
    ".devpilot/providers.yaml",
    "outputs/",
)

SOURCE_ARCHIVE_ROOTS: tuple[str, ...] = (
    ".devpilot/",
    ".github/",
    "docs/",
    "evals/",
    "patches/",
    "scripts/",
    "src/",
    "tests/",
    "ui/",
)

SOURCE_ARCHIVE_ROOT_FILES: tuple[str, ...] = (
    ".env.example",
    ".gitignore",
    "README.md",
    "devpilot_bootstrap_manifest.json",
    "pyproject.toml",
    "safe.patch",
)


@dataclass(frozen=True)
class RuntimeStateHygieneOptions:
    policy_path: str | Path = ".devpilot/runtime_state_policy.json"
    write_report: bool = False
    output_json: str | Path = DEFAULT_HYGIENE_JSON
    output_markdown: str | Path = DEFAULT_HYGIENE_MARKDOWN
    include_git_archive_check: bool = True


class RuntimeStateHygieneGate:
    """POST-H-008-E runtime-state hygiene and release archive gate.

    The gate is read-only for source/runtime files. It composes the POST-H-008
    policy and inventory with an archive cleanliness check. When a Git checkout
    is available it inspects `git archive HEAD` in memory; when .git metadata is
    absent (for example inside a delivered clean ZIP) it performs the same
    exclusion logic against a deterministic source-archive plan.
    """

    def __init__(self, root: Path, options: RuntimeStateHygieneOptions | None = None) -> None:
        self.root = Path(root).resolve()
        self.options = options or RuntimeStateHygieneOptions()

    def run(self) -> CommandResult:
        try:
            policy = RuntimeStatePolicyLoader(self.root, self.options.policy_path).load()
            inventory_result = RuntimeStateInventoryBuilder(
                self.root,
                RuntimeStateInventoryOptions(policy_path=self.options.policy_path, write_report=False),
            ).run()
            inventory = (inventory_result.data or {}).get("inventory") or {}
            report = self.build_report(policy=policy, inventory=inventory)
        except Exception as exc:
            finding = Finding(
                "RUNTIME_STATE_HYGIENE_ERROR",
                f"Runtime-state hygiene gate could not be evaluated: {exc}",
                Severity.ERROR,
            )
            return CommandResult(
                "runtime-state hygiene",
                False,
                ExitCode.ERROR,
                "Runtime-state hygiene gate failed with an unexpected error.",
                data={"summary": {"created_by": POST_H_008_E_CREATED_BY, "preliminary": True}},
                findings=[finding],
            )

        reports: dict[str, str] = {}
        if self.options.write_report:
            json_display = _rel(self.root, self.root / self.options.output_json)
            markdown_display = _rel(self.root, self.root / self.options.output_markdown)
            report["summary"]["reports_written"] = True
            report["summary"]["output_json"] = json_display
            report["summary"]["output_markdown"] = markdown_display
            reports = self._write_reports(report)
        else:
            report["summary"]["reports_written"] = False
            report["summary"]["output_json"] = None
            report["summary"]["output_markdown"] = None

        findings = _findings_from_report(report)
        blocking = [finding for finding in findings if finding.severity in {Severity.FAIL, Severity.BLOCK, Severity.ERROR}]
        ok = not blocking
        return CommandResult(
            "runtime-state hygiene",
            ok,
            ExitCode.PASS if ok else _exit_code_from_findings(blocking),
            "Runtime-state hygiene gate passed." if ok else "Runtime-state hygiene gate found blocking release/archive issues.",
            data={"summary": report["summary"], "hygiene": report, "reports": reports},
            findings=findings,
        )

    def build_report(self, *, policy: RuntimeStatePolicy, inventory: dict[str, Any]) -> dict[str, Any]:
        must_exclude = _must_exclude_patterns(policy)
        policy_checks = self._policy_checks(policy)
        inventory_checks = self._inventory_checks(inventory)
        source_archive_plan = self._source_archive_plan(policy=policy, inventory=inventory, must_exclude=must_exclude)
        git_archive_check = self._git_archive_check(policy=policy, inventory=inventory, must_exclude=must_exclude)

        blocking_reasons: list[str] = []
        for check in policy_checks:
            if not check["ok"] and check["severity"] in {"block", "error", "fail"}:
                blocking_reasons.append(check["id"])
        if inventory_checks["versioned_runtime_artifacts_total"] > 0:
            blocking_reasons.append("RUNTIME_STATE_VERSIONED_ARTIFACTS")
        if source_archive_plan["forbidden_entries_total"] > 0:
            blocking_reasons.append("SOURCE_ARCHIVE_FORBIDDEN_ENTRIES")
        if source_archive_plan["runtime_entries_total"] > 0:
            blocking_reasons.append("SOURCE_ARCHIVE_RUNTIME_ENTRIES")
        if git_archive_check["checked"]:
            if git_archive_check["forbidden_entries_total"] > 0:
                blocking_reasons.append("GIT_ARCHIVE_FORBIDDEN_ENTRIES")
            if git_archive_check["runtime_entries_total"] > 0:
                blocking_reasons.append("GIT_ARCHIVE_RUNTIME_ENTRIES")
            if not git_archive_check["ok"]:
                blocking_reasons.append("GIT_ARCHIVE_CHECK_FAILED")

        archive_clean = (
            source_archive_plan["clean"]
            and (not git_archive_check["checked"] or git_archive_check["clean"])
        )
        quality_gate_ready = not blocking_reasons
        summary = {
            "created_by": POST_H_008_E_CREATED_BY,
            "status": "implemented-initial",
            "preliminary": True,
            "dry_run": True,
            "read_only": True,
            "quality_gate_ready": quality_gate_ready,
            "runtime_state_hygiene_passed": quality_gate_ready,
            "release_archive_clean": archive_clean,
            "source_archive_plan_checked": source_archive_plan["checked"],
            "source_archive_plan_clean": source_archive_plan["clean"],
            "git_archive_required": bool(policy.zip_hygiene.get("git_archive_required", False)),
            "git_archive_available": git_archive_check["available"],
            "git_archive_checked": git_archive_check["checked"],
            "git_archive_clean": git_archive_check["clean"],
            "git_metadata_available": bool(inventory.get("summary", {}).get("git_metadata_available", False)),
            "versioned_runtime_artifacts_total": inventory_checks["versioned_runtime_artifacts_total"],
            "runtime_archive_entries_total": source_archive_plan["runtime_entries_total"] + (git_archive_check["runtime_entries_total"] if git_archive_check["checked"] else 0),
            "forbidden_archive_entries_total": source_archive_plan["forbidden_entries_total"] + (git_archive_check["forbidden_entries_total"] if git_archive_check["checked"] else 0),
            "must_exclude_total": len(must_exclude),
            "blocking_reasons_total": len(set(blocking_reasons)),
            "network_used": False,
            "external_api_used": False,
            "mutations_performed": False,
            "source_mutations_performed": False,
            "destructive_cleanup_performed": False,
            "cleanup_execution_enabled": False,
            "export_execution_enabled": False,
            "remote_execution_enabled": False,
            "connector_write_enabled": False,
            "plugin_execution_enabled": False,
        }
        return {
            "schema_version": "1.0",
            "schema_id": RUNTIME_STATE_HYGIENE_SCHEMA_ID,
            "report_id": RUNTIME_STATE_HYGIENE_REPORT_ID,
            "created_by": POST_H_008_E_CREATED_BY,
            "status": "implemented-initial",
            "generated_at_utc": utc_now_iso(),
            "policy_id": policy.policy_id,
            "policy_path": _rel(self.root, self.root / self.options.policy_path),
            "must_exclude": must_exclude,
            "policy_checks": policy_checks,
            "inventory_checks": inventory_checks,
            "source_archive_plan": source_archive_plan,
            "git_archive_check": git_archive_check,
            "summary": summary,
            "safety": {
                "read_only": True,
                "dry_run_default": True,
                "network_used": False,
                "external_api_used": False,
                "mutations_performed": False,
                "source_mutations_performed": False,
                "destructive_cleanup_performed": False,
                "remote_execution_enabled": False,
                "connector_write_enabled": False,
                "plugin_execution_enabled": False,
                "release_archive_artifacts_written": False,
            },
            "notes": [
                "POST-H-008-E blocks release/archive readiness when runtime artifacts are versioned or included in source archive candidates.",
                "When .git metadata is present, git archive HEAD is inspected in memory and no archive is written.",
                "When .git metadata is absent, the gate evaluates a deterministic source-archive plan so clean delivered ZIPs remain verifiable.",
                "This is an implemented-initial gate; signing/encryption and stronger DLP remain future hardening work.",
            ],
        }

    def _policy_checks(self, policy: RuntimeStatePolicy) -> list[dict[str, Any]]:
        must_exclude = _must_exclude_patterns(policy)
        required = ["outputs/", ".devpilot/devpilot.db", ".devpilot/agent_sessions/"]
        checks: list[dict[str, Any]] = []
        for item in required:
            ok = item in must_exclude
            checks.append({
                "id": f"MUST_EXCLUDE_{_slug(item)}",
                "ok": ok,
                "severity": "info" if ok else "block",
                "path": item,
                "message": f"zip_hygiene.must_exclude {'contains' if ok else 'is missing'} {item}",
            })
        git_archive_required = bool(policy.zip_hygiene.get("git_archive_required", False))
        checks.append({
            "id": "GIT_ARCHIVE_REQUIRED",
            "ok": git_archive_required,
            "severity": "info" if git_archive_required else "block",
            "message": "zip_hygiene.git_archive_required is enabled." if git_archive_required else "zip_hygiene.git_archive_required must be enabled.",
        })
        runtime_allowed = bool(policy.zip_hygiene.get("runtime_artifacts_allowed_in_release_zip", False))
        checks.append({
            "id": "RUNTIME_ARTIFACTS_FORBIDDEN_IN_RELEASE_ZIP",
            "ok": not runtime_allowed,
            "severity": "info" if not runtime_allowed else "block",
            "message": "Runtime artifacts are forbidden in release/source ZIPs." if not runtime_allowed else "Runtime artifacts are allowed in release ZIP policy, which is not acceptable.",
        })
        return checks

    def _inventory_checks(self, inventory: dict[str, Any]) -> dict[str, Any]:
        summary = inventory.get("summary") or {}
        artifacts = inventory.get("artifacts") if isinstance(inventory.get("artifacts"), list) else []
        versioned = [item for item in artifacts if item.get("git_tracked") and not item.get("versionable")]
        return {
            "inventory_available": bool(inventory),
            "git_metadata_available": bool(summary.get("git_metadata_available", False)),
            "artifacts_total": int(summary.get("artifacts_total", len(artifacts)) or 0),
            "runtime_artifacts_total": int(summary.get("runtime_artifacts_total", 0) or 0),
            "versioned_runtime_artifacts_total": int(summary.get("versioned_runtime_artifacts_total", len(versioned)) or 0),
            "versioned_runtime_paths": sorted(str(item.get("path")) for item in versioned if item.get("path"))[:50],
            "blocking_violations_total": int(summary.get("blocking_violations_total", 0) or 0),
            "warnings_total": int(summary.get("warnings_total", 0) or 0),
        }

    def _source_archive_plan(self, *, policy: RuntimeStatePolicy, inventory: dict[str, Any], must_exclude: list[str]) -> dict[str, Any]:
        all_files = sorted(_iter_source_archive_candidates(self.root))
        included: list[str] = []
        excluded: list[dict[str, Any]] = []
        forbidden_included: list[dict[str, Any]] = []
        runtime_included: list[dict[str, Any]] = []
        artifacts_by_path = _runtime_artifact_map(inventory)
        for rel in all_files:
            matches = _matching_patterns(rel, must_exclude)
            if matches:
                excluded.append({"path": rel, "reason": "must-exclude", "patterns": matches})
                continue
            included.append(rel)
            forbidden_matches = _matching_patterns(rel, must_exclude)
            if forbidden_matches:
                forbidden_included.append({"path": rel, "patterns": forbidden_matches})
            artifact = artifacts_by_path.get(rel)
            if artifact and _is_nonversionable_runtime_artifact(artifact):
                runtime_included.append({"path": rel, "class_id": artifact.get("class_id"), "classification": artifact.get("classification")})
        digest = hashlib.sha256("\n".join(included).encode("utf-8")).hexdigest()
        return {
            "checked": True,
            "strategy": "deterministic-source-archive-plan",
            "clean": not forbidden_included and not runtime_included,
            "included_files_total": len(included),
            "excluded_files_total": len(excluded),
            "forbidden_entries_total": len(forbidden_included),
            "runtime_entries_total": len(runtime_included),
            "included_files_sha256": digest,
            "forbidden_entries": forbidden_included[:100],
            "runtime_entries": runtime_included[:100],
            "excluded_samples": excluded[:100],
        }

    def _git_archive_check(self, *, policy: RuntimeStatePolicy, inventory: dict[str, Any], must_exclude: list[str]) -> dict[str, Any]:
        git_dir = self.root / ".git"
        if not self.options.include_git_archive_check:
            return _git_archive_skipped(available=git_dir.exists(), reason="disabled-by-options")
        if not git_dir.exists():
            return _git_archive_skipped(available=False, reason="git-metadata-unavailable")
        completed = subprocess.run(
            ["git", "archive", "--format=tar", "HEAD"],
            cwd=self.root,
            capture_output=True,
            check=False,
        )
        if completed.returncode != 0:
            return {
                **_git_archive_skipped(available=True, reason="git-archive-command-failed"),
                "ok": False,
                "stderr_tail": completed.stderr.decode("utf-8", errors="replace")[-500:],
            }
        try:
            with tarfile.open(fileobj=io.BytesIO(completed.stdout), mode="r:") as archive:
                names = sorted(name for name in archive.getnames() if name and not name.endswith("/"))
        except tarfile.TarError as exc:
            return {
                **_git_archive_skipped(available=True, reason="git-archive-tar-parse-failed"),
                "ok": False,
                "stderr_tail": str(exc),
            }
        artifacts_by_path = _runtime_artifact_map(inventory)
        forbidden = []
        runtime = []
        for name in names:
            rel = _normalize_rel(name)
            matches = _matching_patterns(rel, must_exclude)
            if matches:
                forbidden.append({"path": rel, "patterns": matches})
            artifact = artifacts_by_path.get(rel)
            if artifact and _is_nonversionable_runtime_artifact(artifact):
                runtime.append({"path": rel, "class_id": artifact.get("class_id"), "classification": artifact.get("classification")})
        digest = hashlib.sha256("\n".join(_normalize_rel(name) for name in names).encode("utf-8")).hexdigest()
        return {
            "available": True,
            "checked": True,
            "ok": True,
            "clean": not forbidden and not runtime,
            "strategy": "git-archive-head-in-memory",
            "entries_total": len(names),
            "entries_sha256": digest,
            "forbidden_entries_total": len(forbidden),
            "runtime_entries_total": len(runtime),
            "forbidden_entries": forbidden[:100],
            "runtime_entries": runtime[:100],
            "reason": None,
        }

    def _write_reports(self, report: dict[str, Any]) -> dict[str, str]:
        json_path = self.root / self.options.output_json
        markdown_path = self.root / self.options.output_markdown
        json_path.parent.mkdir(parents=True, exist_ok=True)
        markdown_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
        markdown_path.write_text(render_runtime_state_hygiene_markdown(report), encoding="utf-8")
        return {"json": _rel(self.root, json_path), "markdown": _rel(self.root, markdown_path)}


def render_runtime_state_hygiene_markdown(report: dict[str, Any]) -> str:
    summary = report.get("summary", {})
    source = report.get("source_archive_plan", {})
    git = report.get("git_archive_check", {})
    lines = [
        "# Runtime state hygiene report",
        "",
        f"- Created by: `{report.get('created_by')}`",
        f"- Status: `{report.get('status')}`",
        f"- Generated at UTC: `{report.get('generated_at_utc')}`",
        f"- Runtime hygiene passed: `{summary.get('runtime_state_hygiene_passed')}`",
        f"- Release archive clean: `{summary.get('release_archive_clean')}`",
        f"- Versioned runtime artifacts: `{summary.get('versioned_runtime_artifacts_total')}`",
        f"- Forbidden archive entries: `{summary.get('forbidden_archive_entries_total')}`",
        f"- Runtime archive entries: `{summary.get('runtime_archive_entries_total')}`",
        "",
        "## Source archive plan",
        "",
        f"- Strategy: `{source.get('strategy')}`",
        f"- Clean: `{source.get('clean')}`",
        f"- Included files: `{source.get('included_files_total')}`",
        f"- Excluded files: `{source.get('excluded_files_total')}`",
        "",
        "## Git archive HEAD",
        "",
        f"- Available: `{git.get('available')}`",
        f"- Checked: `{git.get('checked')}`",
        f"- Clean: `{git.get('clean')}`",
        f"- Strategy: `{git.get('strategy')}`",
        f"- Reason: `{git.get('reason')}`",
        "",
        "## Safety",
        "",
        "```json",
        json.dumps(report.get("safety", {}), indent=2, ensure_ascii=False, sort_keys=True),
        "```",
        "",
        "## Notes",
        "",
    ]
    for note in report.get("notes", []):
        lines.append(f"- {note}")
    return "\n".join(lines) + "\n"


def _findings_from_report(report: dict[str, Any]) -> list[Finding]:
    findings: list[Finding] = []
    for check in report.get("policy_checks", []):
        severity = Severity(check.get("severity", "info"))
        findings.append(Finding(check.get("id", "RUNTIME_STATE_POLICY_CHECK"), check.get("message", "Runtime policy check."), severity, path=check.get("path")))
    inventory = report.get("inventory_checks", {})
    if inventory.get("versioned_runtime_artifacts_total", 0) > 0:
        findings.append(Finding(
            "RUNTIME_STATE_VERSIONED_ARTIFACTS_BLOCK",
            "Runtime artifacts are tracked/versioned and must be removed before release/archive readiness.",
            Severity.BLOCK,
            metadata={"paths": inventory.get("versioned_runtime_paths", [])},
        ))
    source = report.get("source_archive_plan", {})
    if source.get("forbidden_entries_total", 0) > 0:
        findings.append(Finding(
            "SOURCE_ARCHIVE_FORBIDDEN_ENTRIES_BLOCK",
            "Deterministic source archive plan includes forbidden runtime/build/cache entries.",
            Severity.BLOCK,
            metadata={"entries": source.get("forbidden_entries", [])[:25]},
        ))
    if source.get("runtime_entries_total", 0) > 0:
        findings.append(Finding(
            "SOURCE_ARCHIVE_RUNTIME_ENTRIES_BLOCK",
            "Deterministic source archive plan includes non-versionable runtime artifacts.",
            Severity.BLOCK,
            metadata={"entries": source.get("runtime_entries", [])[:25]},
        ))
    git = report.get("git_archive_check", {})
    if git.get("checked"):
        if git.get("forbidden_entries_total", 0) > 0:
            findings.append(Finding(
                "GIT_ARCHIVE_FORBIDDEN_ENTRIES_BLOCK",
                "git archive HEAD includes forbidden runtime/build/cache entries.",
                Severity.BLOCK,
                metadata={"entries": git.get("forbidden_entries", [])[:25]},
            ))
        if git.get("runtime_entries_total", 0) > 0:
            findings.append(Finding(
                "GIT_ARCHIVE_RUNTIME_ENTRIES_BLOCK",
                "git archive HEAD includes non-versionable runtime artifacts.",
                Severity.BLOCK,
                metadata={"entries": git.get("runtime_entries", [])[:25]},
            ))
        if not git.get("ok", True):
            findings.append(Finding(
                "GIT_ARCHIVE_CHECK_ERROR",
                "git archive HEAD check failed.",
                Severity.ERROR,
                metadata={"reason": git.get("reason"), "stderr_tail": git.get("stderr_tail")},
            ))
    else:
        findings.append(Finding(
            "GIT_ARCHIVE_CHECK_SKIPPED",
            "git archive HEAD was not inspected because Git metadata is unavailable or disabled; source archive plan was checked instead.",
            Severity.WARNING,
            metadata={"reason": git.get("reason")},
        ))
    if not any(f.severity in {Severity.BLOCK, Severity.ERROR, Severity.FAIL} for f in findings):
        findings.append(Finding(
            "RUNTIME_STATE_HYGIENE_PASS",
            "Runtime-state hygiene and release archive checks passed.",
            Severity.INFO,
            metadata={"release_archive_clean": report.get("summary", {}).get("release_archive_clean")},
        ))
    return findings


def _exit_code_from_findings(findings: list[Finding]) -> ExitCode:
    severities = {finding.severity for finding in findings}
    if Severity.ERROR in severities:
        return ExitCode.ERROR
    if Severity.BLOCK in severities:
        return ExitCode.BLOCK
    if Severity.FAIL in severities:
        return ExitCode.FAIL
    return ExitCode.PASS


def _git_archive_skipped(*, available: bool, reason: str) -> dict[str, Any]:
    return {
        "available": available,
        "checked": False,
        "ok": True,
        "clean": True,
        "strategy": "git-archive-head-in-memory",
        "entries_total": 0,
        "entries_sha256": None,
        "forbidden_entries_total": 0,
        "runtime_entries_total": 0,
        "forbidden_entries": [],
        "runtime_entries": [],
        "reason": reason,
    }


def _must_exclude_patterns(policy: RuntimeStatePolicy) -> list[str]:
    raw = [str(item).replace("\\", "/") for item in policy.zip_hygiene.get("must_exclude", [])]
    combined = [*raw, *BASE_FORBIDDEN_ARCHIVE_PATTERNS]
    result: list[str] = []
    for item in combined:
        if item and item not in result:
            result.append(item)
    return result


def _iter_source_archive_candidates(root: Path) -> list[str]:
    candidates: list[str] = []
    for file_name in SOURCE_ARCHIVE_ROOT_FILES:
        path = root / file_name
        if path.exists() and path.is_file():
            candidates.append(file_name)
    for prefix in SOURCE_ARCHIVE_ROOTS:
        base = root / prefix
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if path.is_file():
                candidates.append(_rel(root, path))
    return sorted(set(candidates))


def _runtime_artifact_map(inventory: dict[str, Any]) -> dict[str, dict[str, Any]]:
    artifacts = inventory.get("artifacts") if isinstance(inventory.get("artifacts"), list) else []
    return {_normalize_rel(str(item.get("path"))): item for item in artifacts if isinstance(item, dict) and item.get("path")}


def _is_nonversionable_runtime_artifact(artifact: dict[str, Any]) -> bool:
    return not bool(artifact.get("source_of_truth")) and not bool(artifact.get("versionable"))


def _matching_patterns(path: str, patterns: list[str]) -> list[str]:
    rel = _normalize_rel(path)
    return [pattern for pattern in patterns if _matches_pattern(rel, pattern)]


def _matches_pattern(path: str, pattern: str) -> bool:
    rel = _normalize_rel(path)
    pat = pattern.replace("\\", "/").strip()
    if not pat:
        return False
    if pat.endswith("/"):
        prefix = pat.rstrip("/") + "/"
        return rel.startswith(prefix) or f"/{prefix}" in f"/{rel}"
    if "*" in pat or "?" in pat or "[" in pat:
        return fnmatch.fnmatch(rel, pat) or fnmatch.fnmatch(PurePosixPath(rel).name, pat)
    return rel == pat or rel.startswith(pat.rstrip("/") + "/")


def _normalize_rel(path: str) -> str:
    return path.replace("\\", "/").lstrip("./")


def _rel(root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _slug(value: str) -> str:
    return value.replace(".", "_").replace("/", "_").replace("*", "star").strip("_").upper()


__all__ = [
    "DEFAULT_HYGIENE_JSON",
    "DEFAULT_HYGIENE_MARKDOWN",
    "POST_H_008_E_CREATED_BY",
    "RUNTIME_STATE_HYGIENE_CONTRACT",
    "RUNTIME_STATE_HYGIENE_REPORT_ID",
    "RUNTIME_STATE_HYGIENE_SCHEMA_ID",
    "RuntimeStateHygieneGate",
    "RuntimeStateHygieneOptions",
    "render_runtime_state_hygiene_markdown",
]
