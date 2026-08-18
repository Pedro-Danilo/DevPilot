from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity, exit_code_for_findings
from devpilot_core.policy import configured_external_workspace_roots

from .project_entry_contracts import (
    GitSourceKind,
    ProjectEntryContractService,
    ProjectEntryMode,
    ProjectIntake,
    stable_sha256,
)

ENVIRONMENT_DISCOVERY_SCHEMA_ID = "SCHEMA-DEVPL-GSDLC-03-B-ENVIRONMENT-DISCOVERY-REPORT-V1"
BOOTSTRAP_PLAN_SCHEMA_ID = "SCHEMA-DEVPL-GSDLC-03-B-BOOTSTRAP-PLAN-V1"
BOOTSTRAP_PLANNING_CATALOG_SCHEMA_ID = "SCHEMA-DEVPL-GSDLC-03-B-BOOTSTRAP-PLANNING-CATALOG-V1"

DEFAULT_BOOTSTRAP_PLANNING_CATALOG = ".devpilot/workspaces/bootstrap_planning_catalog.json"
DEFAULT_TIMEOUT_SECONDS = 3.0

_VERSION_PATTERN = re.compile(r"(?P<version>\d+(?:\.\d+){1,3})")
_SECRET_ENV_NAME = re.compile(r"(?:TOKEN|SECRET|PASSWORD|PASSWD|API[_-]?KEY|AUTHORIZATION|COOKIE)", re.IGNORECASE)


@dataclass(frozen=True)
class ToolProbeSpec:
    tool_id: str
    minimum_version: str
    executable_names: tuple[str, ...]
    version_args: tuple[str, ...]
    declared_minimum_version: str | None = None
    compatibility_policy: str = "strict-version"
    required_capabilities: tuple[str, ...] = ()
    authority_source: str = "technology-catalog"


def parse_version_tuple(value: str) -> tuple[int, ...]:
    match = _VERSION_PATTERN.search(str(value))
    if not match:
        return ()
    return tuple(int(part) for part in match.group("version").split("."))


def version_meets_minimum(actual: str, minimum: str) -> bool:
    actual_parts = parse_version_tuple(actual)
    minimum_parts = parse_version_tuple(minimum)
    if not actual_parts or not minimum_parts:
        return False
    width = max(len(actual_parts), len(minimum_parts))
    return actual_parts + (0,) * (width - len(actual_parts)) >= minimum_parts + (0,) * (width - len(minimum_parts))


def sanitized_environment_keys() -> list[str]:
    """Return only non-sensitive environment key names used for diagnostics.

    GSDLC-03-B explicitly forbids an environment dump. The discovery report
    therefore never returns values and excludes secret-like key names entirely.
    """

    allow = {"OS", "PROCESSOR_ARCHITECTURE", "COMSPEC", "SystemRoot", "WINDIR", "HOME", "USERPROFILE"}
    return sorted(key for key in os.environ if key in allow and not _SECRET_ENV_NAME.search(key))


class EnvironmentDiscoveryService:
    """Read-only environment discovery and deterministic bootstrap planning.

    The service may inspect executable metadata, filesystem metadata and bounded
    Git status. It does not create files/directories, install tools, mutate Git,
    use network, call external APIs or inspect the paused pilot repository.
    """

    def __init__(
        self,
        platform_root: Path,
        *,
        allowed_roots: Iterable[Path] | None = None,
        timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
        planning_catalog_path: str | Path = DEFAULT_BOOTSTRAP_PLANNING_CATALOG,
    ) -> None:
        self.platform_root = Path(platform_root).resolve()
        self.allowed_roots = tuple(
            Path(item).resolve()
            for item in (allowed_roots if allowed_roots is not None else configured_external_workspace_roots())
        )
        self.timeout_seconds = max(0.1, min(float(timeout_seconds), 15.0))
        self.contracts = ProjectEntryContractService(self.platform_root, allowed_roots=self.allowed_roots)
        planning_path = Path(planning_catalog_path)
        self.planning_catalog_path = planning_path if planning_path.is_absolute() else self.platform_root / planning_path

    def load_planning_catalog(self) -> dict[str, Any]:
        return json.loads(self.planning_catalog_path.read_text(encoding="utf-8"))

    def discover(self, payload: Mapping[str, Any]) -> CommandResult:
        intake_payload = _unwrap_intake(payload)
        validated = self.contracts.validate_intake(intake_payload)
        if not validated.ok:
            return CommandResult(
                command="project entry environment discovery",
                ok=False,
                exit_code=validated.exit_code,
                message="Environment discovery blocked because ProjectIntake validation failed.",
                data={
                    "validation": validated.to_dict(),
                    "writes_performed": False,
                    "network_used": False,
                    "external_api_used": False,
                    "environment_values_exposed": False,
                },
                findings=validated.findings,
            )

        intake = ProjectIntake.from_mapping(intake_payload)
        technology_catalog = self.contracts.load_catalog()
        requirements = self._requirements_for(technology_catalog, intake.entry_mode)
        tools: list[dict[str, Any]] = []
        findings: list[Finding] = []
        selected: dict[str, dict[str, Any]] = {}

        node_probe: dict[str, Any] | None = None
        for requirement in requirements:
            tool_id = str(requirement["tool_id"])
            if tool_id == "npm":
                continue
            spec = self._tool_spec(tool_id, str(requirement["minimum_version"]), entry_mode=intake.entry_mode)
            probe = self._probe_tool(spec)
            tools.append(probe)
            selected[tool_id] = probe
            if tool_id == "node":
                node_probe = probe
            findings.extend(self._tool_findings(probe))

        npm_requirement = next((item for item in requirements if item.get("tool_id") == "npm"), None)
        if npm_requirement is not None:
            npm_probe = self._probe_npm(
                minimum_version=str(npm_requirement["minimum_version"]),
                node_probe=node_probe,
            )
            tools.append(npm_probe)
            selected["npm"] = npm_probe
            findings.extend(self._tool_findings(npm_probe))

        target = Path(intake.target_root).expanduser().resolve(strict=False)
        filesystem = self._filesystem_discovery(target, intake.entry_mode)
        git = self._git_discovery(intake, selected.get("git"))
        if git.get("status") == "BLOCK":
            findings.append(
                Finding(
                    "PROJECT_ENTRY_GIT_DISCOVERY_BLOCK",
                    str(git.get("message") or "Git discovery blocked."),
                    Severity.BLOCK,
                    metadata={"entry_mode": intake.entry_mode.value, "reason": git.get("reason")},
                )
            )

        report_core = {
            "schema_id": ENVIRONMENT_DISCOVERY_SCHEMA_ID,
            "schema_version": "1.0",
            "report_version": "1.0.0",
            "entry_mode": intake.entry_mode.value,
            "source_intake_hash": stable_sha256(intake.to_mapping()),
            "target": {
                "root": str(target),
                "exists": target.exists(),
                "collision_state": filesystem["collision_state"],
            },
            "tools": sorted(tools, key=lambda item: item["tool_id"]),
            "filesystem": filesystem,
            "git": git,
            "environment": {
                "values_exposed": False,
                "safe_key_names": sanitized_environment_keys(),
                "path_value_exposed": False,
            },
            "alternatives": self._alternatives(tools),
            "safety": {
                "read_only": True,
                "writes_performed": False,
                "network_used": False,
                "external_api_used": False,
                "installers_executed": False,
                "arbitrary_shell_used": False,
                "environment_dumped": False,
                "secret_values_exposed": False,
                "pilot_workspace_accessed": False,
            },
        }
        report = {**report_core, "discovery_fingerprint": stable_sha256(_stable_discovery_projection(report_core))}
        if not findings:
            findings.append(
                Finding(
                    "PROJECT_ENTRY_ENVIRONMENT_DISCOVERY_PASS",
                    "Required local prerequisites were discovered read-only and meet the planning contract.",
                    Severity.INFO,
                )
            )
        return _result(
            "project entry environment discovery",
            findings,
            data={"report": report, "writes_performed": False},
            pass_message="Environment discovery passed; no filesystem/Git mutation or installer execution occurred.",
            block_message="Environment discovery blocked; no installer or mutation was attempted.",
        )

    def build_bootstrap_plan(self, payload: Mapping[str, Any]) -> CommandResult:
        intake_payload = _unwrap_intake(payload)
        discovery = self.discover(intake_payload)
        if not discovery.ok:
            return CommandResult(
                command="project entry bootstrap plan",
                ok=False,
                exit_code=discovery.exit_code,
                message="Bootstrap planning blocked because environment discovery did not satisfy prerequisites.",
                data={
                    "discovery": discovery.to_dict(),
                    "writes_performed": False,
                    "network_used": False,
                    "execution_enabled": False,
                },
                findings=discovery.findings,
            )

        creation = self.contracts.build_creation_plan(intake_payload)
        if not creation.ok:
            return CommandResult(
                command="project entry bootstrap plan",
                ok=False,
                exit_code=creation.exit_code,
                message="Bootstrap planning blocked because ProjectCreationPlan could not be built.",
                data={"creation_plan": creation.to_dict(), "writes_performed": False},
                findings=creation.findings,
            )

        intake = ProjectIntake.from_mapping(intake_payload)
        creation_plan = creation.data["plan"]
        discovery_report = discovery.data["report"]
        planning_catalog = self.load_planning_catalog()
        profile = _profile_binding(planning_catalog, str(creation_plan["stack"]["profile_id"]))
        if profile is None:
            finding = Finding(
                "PROJECT_ENTRY_BOOTSTRAP_PROFILE_BINDING_BLOCK",
                "BootstrapPlanningCatalog has no unique binding for the selected technology profile.",
                Severity.BLOCK,
            )
            return _result(
                "project entry bootstrap plan",
                [finding],
                data={"writes_performed": False, "execution_enabled": False},
                pass_message="",
                block_message="Bootstrap plan blocked.",
            )

        target = str(creation_plan["target"]["root"])
        create_mode = intake.entry_mode is ProjectEntryMode.CREATE_NEW
        directories = _render_path_rows(target, profile.get("directories", []), row_type="directory") if create_mode else []
        files = _render_file_rows(target, profile.get("files", [])) if create_mode else []
        dependency_jobs = self._dependency_jobs(intake, profile)
        git_operations = self._git_operations(intake, creation_plan)
        registration = {
            "operation_id": "workspace.register",
            "target_root": target,
            "workspace_id": intake.project_id,
            "writes": True,
            "network_required": False,
            "approval_required": True,
            "execution_status": "planned-only",
        }

        plan_without_hash: dict[str, Any] = {
            "schema_id": BOOTSTRAP_PLAN_SCHEMA_ID,
            "schema_version": "1.0",
            "plan_version": "1.0.0",
            "planning_only": True,
            "execution_enabled": False,
            "entry_mode": intake.entry_mode.value,
            "project_id": intake.project_id,
            "source_intake_hash": creation_plan["source_intake_hash"],
            "source_creation_plan_hash": creation_plan["plan_hash"],
            "source_discovery_fingerprint": discovery_report["discovery_fingerprint"],
            "target_root": target,
            "directories": directories,
            "files": files,
            "git_operations": git_operations,
            "venv": {
                "operation_id": "python.venv.create",
                "path": str(Path(target) / ".venv"),
                "required": create_mode,
                "writes": create_mode,
                "network_required": False,
                "approval_required": create_mode,
                "execution_status": "planned-only" if create_mode else "not-applicable-until-source-inspection",
            },
            "dependency_jobs": dependency_jobs,
            "workspace_registration": registration,
            "network": {
                "required_by_plan": any(bool(row["network_required"]) for row in dependency_jobs + git_operations),
                "runtime_network_used": False,
                "silent_network_allowed": False,
                "remote_git_disabled_by_default": True,
            },
            "approval": {
                "required_for_execute": True,
                "approval_requested": False,
                "bound_to_plan_hash": True,
                "human_session_required": True,
            },
            "expected_side_effects": _expected_side_effects(directories, files, git_operations, dependency_jobs, registration),
            "rollback_steps": _rollback_steps(intake.entry_mode),
            "missing_tool_alternatives": discovery_report.get("alternatives", []),
            "safety": {
                "read_only_planning": True,
                "writes_performed": False,
                "network_used": False,
                "external_api_used": False,
                "installers_executed": False,
                "arbitrary_shell_used": False,
                "pilot_workspace_accessed": False,
                "credentials_included": False,
            },
        }
        plan = {**plan_without_hash, "plan_hash": stable_sha256(plan_without_hash)}
        return CommandResult(
            command="project entry bootstrap plan",
            ok=True,
            exit_code=ExitCode.PASS,
            message="Deterministic bootstrap plan built from typed discovery; no side effects were executed.",
            data={
                "discovery": discovery_report,
                "creation_plan": creation_plan,
                "bootstrap_plan": plan,
                "ui_projection": _ui_projection(plan, discovery_report),
                "writes_performed": False,
            },
            findings=[
                Finding(
                    "PROJECT_ENTRY_BOOTSTRAP_PLAN_PASS",
                    "Bootstrap plan is stable, explicit about side effects, approval and network, and remains non-executable in GSDLC-03-B.",
                    Severity.INFO,
                )
            ],
        )

    def _requirements_for(self, catalog: Mapping[str, Any], mode: ProjectEntryMode) -> list[dict[str, Any]]:
        return [
            dict(item)
            for item in catalog.get("tool_requirements", [])
            if mode.value in item.get("required_for", [])
        ]

    def _tool_spec(self, tool_id: str, minimum_version: str, *, entry_mode: ProjectEntryMode) -> ToolProbeSpec:
        executable_names = {
            "python": ("python.exe", "python") if os.name == "nt" else ("python3", "python"),
            "node": ("node.exe", "node") if os.name == "nt" else ("node",),
            "git": ("git.exe", "git") if os.name == "nt" else ("git",),
        }.get(tool_id, (tool_id,))
        declared = str(minimum_version)
        effective = declared
        policy = "strict-version"
        capabilities: tuple[str, ...] = ()
        authority_source = "technology-catalog"
        planning_catalog = self.load_planning_catalog()
        for rule in planning_catalog.get("tool_compatibility", []):
            if (
                str(rule.get("tool_id")) == tool_id
                and entry_mode.value in rule.get("scope", [])
                and str(rule.get("declared_minimum_version")) == declared
            ):
                effective = str(rule.get("effective_minimum_version") or declared)
                policy = str(rule.get("policy") or "strict-version")
                capabilities = tuple(str(item) for item in rule.get("required_capabilities", []))
                authority_source = "bootstrap-planning-catalog-successor"
                break
        return ToolProbeSpec(
            tool_id,
            effective,
            tuple(executable_names),
            ("--version",),
            declared_minimum_version=declared,
            compatibility_policy=policy,
            required_capabilities=capabilities,
            authority_source=authority_source,
        )

    def _probe_tool(self, spec: ToolProbeSpec) -> dict[str, Any]:
        if spec.tool_id == "python":
            path = Path(sys.executable).resolve()
            candidates = [path]
        else:
            candidates = _find_executable_candidates(spec.executable_names)

        if not candidates:
            return _tool_row(spec, status="missing", candidates=[], selected=None, version=None, message="Executable not found in bounded PATH discovery.")
        if len(candidates) > 1:
            return _tool_row(spec, status="ambiguous", candidates=candidates, selected=None, version=None, message="More than one executable candidate was discovered; selection is fail-closed.")

        selected = candidates[0]
        result = _run_read_only([str(selected), *spec.version_args], timeout_seconds=self.timeout_seconds)
        if result["status"] != "PASS":
            return _tool_row(spec, status=result["status"].lower(), candidates=candidates, selected=selected, version=None, message=result["message"])

        version = _extract_version(result["stdout"] or result["stderr"])
        status = "ready" if version and version_meets_minimum(version, spec.minimum_version) else "version-too-old-or-unparseable"
        return _tool_row(spec, status=status, candidates=candidates, selected=selected, version=version, message="Read-only version probe completed.")

    def _probe_npm(self, *, minimum_version: str, node_probe: Mapping[str, Any] | None) -> dict[str, Any]:
        spec = ToolProbeSpec(
            "npm",
            minimum_version,
            ("npm.cmd", "npm") if os.name == "nt" else ("npm",),
            ("--version",),
            declared_minimum_version=minimum_version,
            compatibility_policy="strict-version",
            authority_source="selected-node-distribution",
        )
        node_path = (
            Path(str(node_probe.get("selected_path"))).resolve()
            if node_probe and node_probe.get("status") == "ready" and node_probe.get("selected_path")
            else None
        )

        # Primary authority: npm shipped with the already-selected Node distribution.
        # Wrapper multiplicity in PATH (npm, npm.cmd, duplicate shims) is diagnostic
        # only and must not create a false ambiguity when they front the same Node.
        if node_path is not None:
            cli = _locate_npm_cli_from_node(node_path)
            if cli is not None:
                result = _run_read_only([str(node_path), str(cli), "--version"], timeout_seconds=self.timeout_seconds)
                version = _extract_version(result["stdout"] or result["stderr"]) if result["status"] == "PASS" else None
                status = "ready" if version and version_meets_minimum(version, minimum_version) else (
                    "version-too-old-or-unparseable" if result["status"] == "PASS" else result["status"].lower()
                )
                row = _tool_row(
                    spec,
                    status=status,
                    candidates=[cli],
                    selected=cli,
                    version=version,
                    message="npm capability resolved from the selected Node distribution without cmd.exe.",
                )
                row["execution_mode"] = "node+npm-cli.js"
                row["native_cli_path"] = str(cli)
                return row

        wrappers = _find_executable_candidates(spec.executable_names)
        if not wrappers:
            return _tool_row(spec, status="missing", candidates=[], selected=None, version=None, message="npm capability was not found.")

        canonical: dict[str, Path] = {}
        for wrapper in wrappers:
            cli = _locate_npm_cli(wrapper, node_path)
            if cli is not None:
                canonical[os.path.normcase(str(cli.resolve()))] = cli.resolve()
        if len(canonical) != 1 or node_path is None:
            return _tool_row(
                spec,
                status="ambiguous" if len(canonical) > 1 or len(wrappers) > 1 else "wrapper-without-native-cli",
                candidates=list(canonical.values()) or wrappers,
                selected=None,
                version=None,
                message="npm wrappers could not be reduced to one native npm-cli.js bound to the selected Node distribution.",
            )

        cli = next(iter(canonical.values()))
        result = _run_read_only([str(node_path), str(cli), "--version"], timeout_seconds=self.timeout_seconds)
        version = _extract_version(result["stdout"] or result["stderr"]) if result["status"] == "PASS" else None
        status = "ready" if version and version_meets_minimum(version, minimum_version) else (
            "version-too-old-or-unparseable" if result["status"] == "PASS" else result["status"].lower()
        )
        row = _tool_row(spec, status=status, candidates=[cli], selected=cli, version=version, message=result["message"])
        row["execution_mode"] = "node+npm-cli.js"
        row["native_cli_path"] = str(cli)
        return row

    @staticmethod
    def _tool_findings(probe: Mapping[str, Any]) -> list[Finding]:
        if probe.get("status") == "ready":
            return []
        return [
            Finding(
                "PROJECT_ENTRY_REQUIRED_TOOL_BLOCK",
                f"Required tool {probe.get('tool_id')} is not ready: {probe.get('status')}.",
                Severity.BLOCK,
                metadata={
                    "tool_id": probe.get("tool_id"),
                    "status": probe.get("status"),
                    "candidates_total": probe.get("candidates_total"),
                    "minimum_version": probe.get("minimum_version"),
                },
            )
        ]

    def _filesystem_discovery(self, target: Path, mode: ProjectEntryMode) -> dict[str, Any]:
        anchor = _nearest_existing_ancestor(target)
        usage = shutil.disk_usage(anchor)
        return {
            "anchor_path": str(anchor),
            "free_bytes": int(usage.free),
            "total_bytes": int(usage.total),
            "readable": os.access(anchor, os.R_OK),
            "writable_advisory": os.access(anchor, os.W_OK),
            "executable_or_traversable": os.access(anchor, os.X_OK),
            "write_probe_performed": False,
            "collision_state": _collision_state(target, mode),
        }

    def _git_discovery(self, intake: ProjectIntake, git_probe: Mapping[str, Any] | None) -> dict[str, Any]:
        if intake.entry_mode is ProjectEntryMode.CREATE_NEW:
            return {"status": "NOT_APPLICABLE", "reason": "CREATE_NEW has no pre-existing Git worktree to inspect.", "writes_performed": False}
        inspect_root = Path(intake.target_root)
        if intake.entry_mode is ProjectEntryMode.IMPORT_GIT and intake.git_source_kind is GitSourceKind.LOCAL_PATH:
            inspect_root = Path(intake.git_source_location or "")
        elif intake.entry_mode is ProjectEntryMode.IMPORT_GIT and intake.git_source_kind is GitSourceKind.REMOTE_URL:
            return {
                "status": "PLAN_ONLY_REMOTE",
                "reason": "Remote source is not contacted during GSDLC-03-B discovery.",
                "writes_performed": False,
                "network_used": False,
            }

        if not inspect_root.exists():
            return {"status": "BLOCK", "reason": "git-inspection-root-missing", "message": "Git inspection root does not exist.", "writes_performed": False}
        if not git_probe or git_probe.get("status") != "ready" or not git_probe.get("selected_path"):
            return {"status": "BLOCK", "reason": "git-tool-not-ready", "message": "Git executable is not ready.", "writes_performed": False}

        git = str(git_probe["selected_path"])
        inside = _run_read_only([git, "-C", str(inspect_root), "rev-parse", "--is-inside-work-tree"], timeout_seconds=self.timeout_seconds)
        if inside["status"] != "PASS" or inside["returncode"] != 0 or inside["stdout"].strip().lower() != "true":
            return {"status": "BLOCK", "reason": "not-a-git-worktree", "message": "Selected OPEN/IMPORT source is not a Git worktree.", "writes_performed": False}
        head = _run_read_only([git, "-C", str(inspect_root), "rev-parse", "HEAD"], timeout_seconds=self.timeout_seconds)
        status = _run_read_only_bytes([git, "-C", str(inspect_root), "status", "--porcelain=v1", "-z"], timeout_seconds=self.timeout_seconds)
        if head["status"] != "PASS" or status["status"] != "PASS":
            return {"status": "BLOCK", "reason": "git-read-failed", "message": "Bounded Git read failed.", "writes_performed": False}
        entries = [item for item in status["stdout_bytes"].split(b"\0") if item]
        return {
            "status": "PASS",
            "root": str(inspect_root.resolve(strict=False)),
            "head": head["stdout"].strip(),
            "dirty": bool(entries),
            "status_entries_total": len(entries),
            "status_payload_exposed": False,
            "writes_performed": False,
        }

    @staticmethod
    def _alternatives(tools: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
        return [
            {
                "tool_id": row["tool_id"],
                "status": row["status"],
                "action": "Install or select a supported local tool explicitly, then rerun discovery. DevPilot will not run an installer.",
            }
            for row in tools
            if row.get("status") != "ready"
        ]

    @staticmethod
    def _dependency_jobs(intake: ProjectIntake, profile: Mapping[str, Any]) -> list[dict[str, Any]]:
        if intake.entry_mode is not ProjectEntryMode.CREATE_NEW:
            return []
        rows = []
        for item in profile.get("dependency_jobs", []):
            rows.append(
                {
                    "job_id": item["job_id"],
                    "operation_id": item["operation_id"],
                    "ecosystem": item["ecosystem"],
                    "manifest_path": str(Path(intake.target_root) / item["manifest_path"]),
                    "dependency_set_id": item["dependency_set_id"],
                    "lock_resolution_required_before_execute": bool(item.get("lock_resolution_required_before_execute", True)),
                    "writes": True,
                    "network_required": bool(item.get("network_required", True)),
                    "approval_required": True,
                    "execution_status": "planned-only",
                }
            )
        return rows

    @staticmethod
    def _git_operations(intake: ProjectIntake, creation_plan: Mapping[str, Any]) -> list[dict[str, Any]]:
        rows = [item for item in creation_plan.get("typed_operations", []) if str(item.get("category")) == "git"]
        result = []
        for item in rows:
            row = dict(item)
            row["execution_status"] = "planned-only"
            if item["operation_id"] == "git.clone.remote":
                row["remote_execution_enabled"] = False
                row["network_approval_required"] = True
            result.append(row)
        return result


def _unwrap_intake(payload: Mapping[str, Any]) -> Mapping[str, Any]:
    value = payload.get("intake") if isinstance(payload, Mapping) else None
    return value if isinstance(value, Mapping) else payload


def _find_executable_candidates(names: Sequence[str]) -> list[Path]:
    """Return every distinct executable candidate visible through PATH.

    ``shutil.which`` only returns the first match and therefore cannot prove
    that executable selection is unambiguous. GSDLC-03-B deliberately scans
    every PATH entry and fails closed when two distinct candidates are visible.
    The function does not execute or mutate anything.
    """

    path_entries = [Path(item) for item in os.environ.get("PATH", "").split(os.pathsep) if item.strip()]
    pathext = [item.lower() for item in os.environ.get("PATHEXT", ".COM;.EXE;.BAT;.CMD").split(os.pathsep) if item]
    candidates: list[Path] = []
    seen: set[str] = set()

    def add(candidate: Path) -> None:
        try:
            if not candidate.is_file():
                return
            if os.name != "nt" and not os.access(candidate, os.X_OK):
                return
            resolved = candidate.resolve()
        except OSError:
            return
        key = os.path.normcase(str(resolved))
        if key not in seen:
            seen.add(key)
            candidates.append(resolved)

    for raw_name in names:
        name_path = Path(raw_name)
        if name_path.is_absolute():
            add(name_path)
            continue
        suffix = name_path.suffix.lower()
        variants = [raw_name]
        if os.name == "nt" and not suffix:
            variants.extend(raw_name + ext for ext in pathext)
        for directory in path_entries:
            for variant in variants:
                add(directory / variant)

    return candidates


def _locate_npm_cli_from_node(node_path: Path) -> Path | None:
    roots = [node_path.parent, node_path.parent.parent]
    relative_candidates = (
        Path("node_modules/npm/bin/npm-cli.js"),
        Path("node_modules/npm/bin/npm-cli.cjs"),
        Path("../lib/node_modules/npm/bin/npm-cli.js"),
    )
    for root in roots:
        for rel in relative_candidates:
            candidate = (root / rel)
            if candidate.is_file():
                return candidate.resolve()
    return None


def _locate_npm_cli(npm_wrapper: Path, node_path: Path | None) -> Path | None:
    if node_path is not None:
        from_node = _locate_npm_cli_from_node(node_path)
        if from_node is not None:
            return from_node
    roots = []
    if node_path is not None:
        roots.extend([node_path.parent, node_path.parent.parent])
    roots.extend([npm_wrapper.parent, npm_wrapper.parent.parent])
    relative_candidates = (
        Path("node_modules/npm/bin/npm-cli.js"),
        Path("node_modules/npm/bin/npm-cli.cjs"),
        Path("npm/node_modules/npm/bin/npm-cli.js"),
    )
    for root in roots:
        for rel in relative_candidates:
            candidate = root / rel
            if candidate.is_file():
                return candidate.resolve()
    return None


def _run_read_only(argv: Sequence[str], *, timeout_seconds: float) -> dict[str, Any]:
    try:
        completed = subprocess.run(
            list(argv),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            shell=False,
            timeout=timeout_seconds,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return {"status": "TIMEOUT", "returncode": 124, "stdout": "", "stderr": "", "message": "Read-only probe timed out."}
    except OSError as exc:
        return {"status": "START_ERROR", "returncode": 127, "stdout": "", "stderr": "", "message": f"Read-only probe could not start: {exc.__class__.__name__}."}
    return {
        "status": "PASS" if completed.returncode == 0 else "FAIL",
        "returncode": completed.returncode,
        "stdout": completed.stdout.strip(),
        "stderr": completed.stderr.strip(),
        "message": "Read-only probe completed." if completed.returncode == 0 else "Read-only probe returned non-zero.",
    }


def _run_read_only_bytes(argv: Sequence[str], *, timeout_seconds: float) -> dict[str, Any]:
    try:
        completed = subprocess.run(
            list(argv),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=False,
            timeout=timeout_seconds,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return {"status": "TIMEOUT", "returncode": 124, "stdout_bytes": b"", "message": "Read-only probe timed out."}
    except OSError as exc:
        return {"status": "START_ERROR", "returncode": 127, "stdout_bytes": b"", "message": f"Read-only probe could not start: {exc.__class__.__name__}."}
    return {
        "status": "PASS" if completed.returncode == 0 else "FAIL",
        "returncode": completed.returncode,
        "stdout_bytes": completed.stdout,
        "message": "Read-only binary probe completed." if completed.returncode == 0 else "Read-only binary probe returned non-zero.",
    }


def _extract_version(text: str) -> str | None:
    match = _VERSION_PATTERN.search(str(text))
    return match.group("version") if match else None


def _tool_row(
    spec: ToolProbeSpec,
    *,
    status: str,
    candidates: Sequence[Path],
    selected: Path | None,
    version: str | None,
    message: str,
) -> dict[str, Any]:
    declared = spec.declared_minimum_version or spec.minimum_version
    return {
        "tool_id": spec.tool_id,
        "minimum_version": spec.minimum_version,
        "declared_minimum_version": declared,
        "effective_minimum_version": spec.minimum_version,
        "meets_declared_minimum": bool(version and version_meets_minimum(version, declared)),
        "compatibility_policy": spec.compatibility_policy,
        "required_capabilities": list(spec.required_capabilities),
        "authority_source": spec.authority_source,
        "status": status,
        "candidates_total": len(candidates),
        "candidate_paths": [str(item) for item in candidates],
        "selected_path": str(selected) if selected else None,
        "version": version,
        "meets_minimum": bool(version and version_meets_minimum(version, spec.minimum_version)),
        "probe_mode": "typed-read-only",
        "shell_used": False,
        "message": message,
    }


def _nearest_existing_ancestor(path: Path) -> Path:
    current = path
    while not current.exists() and current != current.parent:
        current = current.parent
    return current if current.exists() else Path.cwd()


def _collision_state(target: Path, mode: ProjectEntryMode) -> str:
    if not target.exists():
        return "absent"
    if not target.is_dir():
        return "file-collision"
    if any(target.iterdir()):
        return "non-empty-directory" if mode is not ProjectEntryMode.OPEN_EXISTING else "existing-directory"
    return "empty-directory"


def _stable_discovery_projection(report: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "entry_mode": report["entry_mode"],
        "source_intake_hash": report["source_intake_hash"],
        "target": {"root": report["target"]["root"], "collision_state": report["target"]["collision_state"]},
        "tools": [
            {
                "tool_id": row["tool_id"],
                "status": row["status"],
                "selected_path": row.get("selected_path"),
                "version": row.get("version"),
                "minimum_version": row.get("minimum_version"),
            }
            for row in report["tools"]
        ],
        "git": {
            "status": report["git"].get("status"),
            "head": report["git"].get("head"),
            "dirty": report["git"].get("dirty"),
        },
    }


def _profile_binding(catalog: Mapping[str, Any], profile_id: str) -> Mapping[str, Any] | None:
    rows = [item for item in catalog.get("profiles", []) if item.get("profile_id") == profile_id]
    return rows[0] if len(rows) == 1 else None


def _render_path_rows(target: str, rows: Sequence[Mapping[str, Any]], *, row_type: str) -> list[dict[str, Any]]:
    result = []
    for item in rows:
        rel = str(item["relative_path"])
        result.append(
            {
                "relative_path": rel,
                "absolute_path": str(Path(target) / rel) if rel not in {"", "."} else target,
                "type": row_type,
                "writes": True,
                "source": item.get("source", "bootstrap-planning-catalog"),
            }
        )
    return result


def _render_file_rows(target: str, rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    result = []
    for item in rows:
        rel = str(item["relative_path"])
        result.append(
            {
                "relative_path": rel,
                "absolute_path": str(Path(target) / rel),
                "type": "file",
                "template_id": item["template_id"],
                "writes": True,
                "content_materialized": False,
            }
        )
    return result


def _expected_side_effects(
    directories: Sequence[Mapping[str, Any]],
    files: Sequence[Mapping[str, Any]],
    git_operations: Sequence[Mapping[str, Any]],
    dependency_jobs: Sequence[Mapping[str, Any]],
    registration: Mapping[str, Any],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    rows.extend({"kind": "directory-create", "subject": item["relative_path"], "declared": True} for item in directories)
    rows.extend({"kind": "file-create", "subject": item["relative_path"], "declared": True} for item in files)
    rows.extend({"kind": "git-operation", "subject": item["operation_id"], "declared": True} for item in git_operations)
    rows.extend({"kind": "dependency-job", "subject": item["job_id"], "declared": True} for item in dependency_jobs)
    rows.append({"kind": "workspace-registration", "subject": registration["workspace_id"], "declared": True})
    return rows


def _rollback_steps(mode: ProjectEntryMode) -> list[dict[str, Any]]:
    if mode is ProjectEntryMode.OPEN_EXISTING:
        return [
            {"step": 1, "action_id": "workspace.registration.rollback", "scope": "registration-only", "planned_only": True},
        ]
    return [
        {"step": 1, "action_id": "workspace.registration.rollback", "scope": "registration-only", "planned_only": True},
        {"step": 2, "action_id": "dependency.jobs.compensate", "scope": "planned-jobs", "planned_only": True},
        {"step": 3, "action_id": "workspace.target.cleanup-created-only", "scope": "created-by-bootstrap-only", "planned_only": True},
    ]


def _ui_projection(plan: Mapping[str, Any], discovery: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "projection_version": "1.0.0",
        "read_only": True,
        "execution_enabled": False,
        "entry_mode": plan["entry_mode"],
        "project_id": plan["project_id"],
        "plan_hash": plan["plan_hash"],
        "discovery_fingerprint": plan["source_discovery_fingerprint"],
        "tools": [
            {"tool_id": row["tool_id"], "status": row["status"], "version": row.get("version")}
            for row in discovery["tools"]
        ],
        "steps": [
            {
                "operation_id": row["operation_id"],
                "network_required": bool(row.get("network_required", False)),
                "approval_required": bool(row.get("approval_required", False)),
                "execution_status": row.get("execution_status", "planned-only"),
            }
            for row in plan["git_operations"] + plan["dependency_jobs"] + [plan["workspace_registration"]]
        ],
        "network_required": plan["network"]["required_by_plan"],
        "approval_required": plan["approval"]["required_for_execute"],
        "writes_performed": False,
    }


def _result(
    command: str,
    findings: list[Finding],
    *,
    data: dict[str, Any],
    pass_message: str,
    block_message: str,
) -> CommandResult:
    blocking = [item for item in findings if item.severity in {Severity.BLOCK, Severity.FAIL, Severity.ERROR}]
    ok = not blocking
    return CommandResult(
        command=command,
        ok=ok,
        exit_code=ExitCode.PASS if ok else exit_code_for_findings(findings, default_ok=False),
        message=pass_message if ok else block_message,
        data=data,
        findings=findings,
    )
