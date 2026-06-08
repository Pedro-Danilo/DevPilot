from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity

WORKSPACE_DIR_NAME = ".devpilot"
PROJECT_FILE_NAME = "project.yaml"
DEFAULT_PROJECT_ID = "devpilot-local"
DEFAULT_PROJECT_NAME = "DevPilot Local"
DEFAULT_PROJECT_TYPE = "agent-assisted-sdlc"
DEFAULT_SCHEMA_VERSION = "1.0"

ROOT_MARKER_FILES = ("pyproject.toml",)
ROOT_MARKER_DIRS = ("docs",)


@dataclass(frozen=True)
class WorkspacePaths:
    """Resolved local paths that define a DevPilot workspace.

    FUNC-SPRINT-08 introduces `.devpilot/` as the minimum local workspace
    boundary. The object keeps all important paths together so commands,
    tests and future policy guards can reason from the same contract.
    """

    root: Path
    workspace_dir: Path
    project_file: Path
    docs_dir: Path
    standards_dir: Path
    outputs_dir: Path
    reports_dir: Path
    traces_dir: Path

    def to_dict(self) -> dict[str, str]:
        return {
            "root": ".",
            "workspace_dir": _relative(self.workspace_dir, self.root),
            "project_file": _relative(self.project_file, self.root),
            "docs_dir": _relative(self.docs_dir, self.root),
            "standards_dir": _relative(self.standards_dir, self.root),
            "outputs_dir": _relative(self.outputs_dir, self.root),
            "reports_dir": _relative(self.reports_dir, self.root),
            "traces_dir": _relative(self.traces_dir, self.root),
        }


@dataclass(frozen=True)
class WorkspaceInitPlan:
    """Dry-run/execute plan for workspace initialization."""

    paths: WorkspacePaths
    project_id: str
    project_name: str
    project_type: str
    miasi_required: bool = True
    standards: tuple[str, str] = ("MIPSoftware", "MIASI")
    would_create_workspace_dir: bool = False
    would_create_project_file: bool = False
    already_initialized: bool = False
    project_yaml: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "project_id": self.project_id,
            "project_name": self.project_name,
            "project_type": self.project_type,
            "miasi_required": self.miasi_required,
            "standards": list(self.standards),
            "paths": self.paths.to_dict(),
            "would_create_workspace_dir": self.would_create_workspace_dir,
            "would_create_project_file": self.would_create_project_file,
            "already_initialized": self.already_initialized,
            "project_yaml_preview": self.project_yaml,
        }


@dataclass(frozen=True)
class WorkspaceStatus:
    """Current status of a DevPilot workspace."""

    paths: WorkspacePaths
    initialized: bool
    docs_present: bool
    standards_present: bool
    precode_checklist_present: bool
    outputs_present: bool
    reports_present: bool
    traces_present: bool
    project_metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def ready(self) -> bool:
        return self.initialized and self.docs_present and self.standards_present and self.precode_checklist_present

    def summary(self) -> dict[str, Any]:
        return {
            "initialized": self.initialized,
            "ready": self.ready,
            "docs_present": self.docs_present,
            "standards_present": self.standards_present,
            "precode_checklist_present": self.precode_checklist_present,
            "outputs_present": self.outputs_present,
            "reports_present": self.reports_present,
            "traces_present": self.traces_present,
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "paths": self.paths.to_dict(),
            "summary": self.summary(),
            "project_metadata": self.project_metadata,
        }


class WorkspaceManager:
    """Minimum local workspace manager for DevPilot.

    The manager is intentionally deterministic and dependency-free. It writes
    only `.devpilot/project.yaml` under the resolved project root and never
    overwrites an existing workspace file by default.
    """

    def __init__(self, root: Path) -> None:
        self.root = root.resolve()
        self.paths = WorkspacePaths(
            root=self.root,
            workspace_dir=self.root / WORKSPACE_DIR_NAME,
            project_file=self.root / WORKSPACE_DIR_NAME / PROJECT_FILE_NAME,
            docs_dir=self.root / "docs",
            standards_dir=self.root / "docs" / "standards",
            outputs_dir=self.root / "outputs",
            reports_dir=self.root / "outputs" / "reports",
            traces_dir=self.root / "outputs" / "traces",
        )

    @classmethod
    def discover(cls, start: Path | None = None) -> "WorkspaceManager":
        """Discover a DevPilot project root by walking upward from `start`.

        Priority is `.devpilot/project.yaml`; fallback is the current pre-code
        repository shape (`pyproject.toml` + `docs/`). If no marker is found,
        the starting directory is used. This fallback keeps bootstrap commands
        usable before workspace initialization.
        """

        base = (start or Path.cwd()).resolve()
        current = base if base.is_dir() else base.parent
        for candidate in (current, *current.parents):
            if (candidate / WORKSPACE_DIR_NAME / PROJECT_FILE_NAME).is_file():
                return cls(candidate)
            if all((candidate / marker).exists() for marker in ROOT_MARKER_FILES) and all(
                (candidate / marker).is_dir() for marker in ROOT_MARKER_DIRS
            ):
                return cls(candidate)
        return cls(current)

    def build_init_plan(
        self,
        *,
        project_id: str = DEFAULT_PROJECT_ID,
        project_name: str = DEFAULT_PROJECT_NAME,
        project_type: str = DEFAULT_PROJECT_TYPE,
    ) -> WorkspaceInitPlan:
        """Build a workspace initialization plan without writing files."""

        self._assert_inside_root(self.paths.workspace_dir)
        self._assert_inside_root(self.paths.project_file)
        project_yaml = render_project_yaml(project_id=project_id, project_name=project_name, project_type=project_type)
        already_initialized = self.paths.project_file.exists()
        return WorkspaceInitPlan(
            paths=self.paths,
            project_id=project_id,
            project_name=project_name,
            project_type=project_type,
            already_initialized=already_initialized,
            would_create_workspace_dir=not self.paths.workspace_dir.exists(),
            would_create_project_file=not already_initialized,
            project_yaml=project_yaml,
        )

    def init_workspace(
        self,
        *,
        execute: bool = False,
        project_id: str = DEFAULT_PROJECT_ID,
        project_name: str = DEFAULT_PROJECT_NAME,
        project_type: str = DEFAULT_PROJECT_TYPE,
    ) -> CommandResult:
        """Initialize `.devpilot/project.yaml` or return a dry-run plan."""

        plan = self.build_init_plan(project_id=project_id, project_name=project_name, project_type=project_type)
        data: dict[str, Any] = {"dry_run": not execute, "plan": plan.to_dict()}

        if plan.already_initialized and execute:
            return CommandResult(
                command="workspace init",
                ok=False,
                exit_code=ExitCode.BLOCK,
                message="Workspace already initialized; refusing to overwrite .devpilot/project.yaml.",
                data=data,
                findings=[
                    Finding(
                        id="WORKSPACE_ALREADY_INITIALIZED",
                        message=".devpilot/project.yaml already exists and DevPilot does not overwrite it by default.",
                        severity=Severity.BLOCK,
                        path=_relative(self.paths.project_file, self.root),
                    )
                ],
            )

        if not execute:
            return CommandResult(
                command="workspace init",
                ok=True,
                exit_code=ExitCode.PASS,
                message="Workspace initialization dry-run completed; no files were written.",
                data=data,
                findings=[
                    Finding(
                        id="WORKSPACE_ALREADY_INITIALIZED" if plan.already_initialized else "WORKSPACE_INIT_DRY_RUN",
                        message=(
                            ".devpilot/project.yaml already exists; dry-run reports current state without writing."
                            if plan.already_initialized
                            else "Dry-run only; no files were written."
                        ),
                        severity=Severity.INFO,
                        path=_relative(self.paths.project_file, self.root),
                    )
                ],
            )

        self.paths.workspace_dir.mkdir(parents=True, exist_ok=True)
        self.paths.project_file.write_text(plan.project_yaml, encoding="utf-8")
        data["created"] = {
            "workspace_dir": _relative(self.paths.workspace_dir, self.root),
            "project_file": _relative(self.paths.project_file, self.root),
        }
        return CommandResult(
            command="workspace init",
            ok=True,
            exit_code=ExitCode.PASS,
            message="Workspace initialized at .devpilot/project.yaml.",
            data=data,
            findings=[],
        )

    def status(self) -> CommandResult:
        """Return workspace status as a normalized command result."""

        status = WorkspaceStatus(
            paths=self.paths,
            initialized=self.paths.project_file.is_file(),
            docs_present=self.paths.docs_dir.is_dir(),
            standards_present=self.paths.standards_dir.is_dir(),
            precode_checklist_present=(self.paths.docs_dir / "checklists" / "checklist_pre_code.md").is_file(),
            outputs_present=self.paths.outputs_dir.exists(),
            reports_present=self.paths.reports_dir.exists(),
            traces_present=self.paths.traces_dir.exists(),
            project_metadata=parse_project_yaml_metadata(self.paths.project_file) if self.paths.project_file.is_file() else {},
        )
        findings: list[Finding] = []
        if not status.initialized:
            findings.append(
                Finding(
                    id="WORKSPACE_NOT_INITIALIZED",
                    message=".devpilot/project.yaml is missing. Run workspace init --execute to initialize it.",
                    severity=Severity.FAIL,
                    path=_relative(self.paths.project_file, self.root),
                )
            )
        for finding_id, present, path, message in (
            ("WORKSPACE_DOCS_MISSING", status.docs_present, self.paths.docs_dir, "docs/ directory is required for DevPilot workspace readiness."),
            (
                "WORKSPACE_STANDARDS_MISSING",
                status.standards_present,
                self.paths.standards_dir,
                "docs/standards/ directory is required for MIPSoftware/MIASI workspace readiness.",
            ),
            (
                "WORKSPACE_PRECODE_CHECKLIST_MISSING",
                status.precode_checklist_present,
                self.paths.docs_dir / "checklists" / "checklist_pre_code.md",
                "docs/checklists/checklist_pre_code.md is required for pre-code gate readiness.",
            ),
        ):
            if not present:
                findings.append(Finding(id=finding_id, message=message, severity=Severity.BLOCK, path=_relative(path, self.root)))

        ok = status.ready
        exit_code = ExitCode.PASS if ok else (ExitCode.BLOCK if any(f.severity == Severity.BLOCK for f in findings) else ExitCode.FAIL)
        return CommandResult(
            command="workspace status",
            ok=ok,
            exit_code=exit_code,
            message="Workspace status passed." if ok else "Workspace status requires attention.",
            data=status.to_dict(),
            findings=findings,
        )

    def _assert_inside_root(self, path: Path) -> None:
        try:
            path.resolve().relative_to(self.root)
        except ValueError as exc:
            raise ValueError("Workspace paths must remain inside the DevPilot project root.") from exc


def render_project_yaml(
    *,
    project_id: str = DEFAULT_PROJECT_ID,
    project_name: str = DEFAULT_PROJECT_NAME,
    project_type: str = DEFAULT_PROJECT_TYPE,
) -> str:
    """Render the minimal dependency-free project.yaml contract."""

    return f'''schema_version: "{DEFAULT_SCHEMA_VERSION}"
project:
  id: "{_escape_yaml_string(project_id)}"
  name: "{_escape_yaml_string(project_name)}"
  type: "{_escape_yaml_string(project_type)}"
  owner: "Ordóñez"
standards:
  - "MIPSoftware"
  - "MIASI"
miasi:
  required: true
paths:
  docs: "docs"
  standards: "docs/standards"
  outputs: "outputs"
  reports: "outputs/reports"
  traces: "outputs/traces"
  policy: ".devpilot/policy.yaml"
  state: ".devpilot/devpilot.db"
  miasi_config: ".devpilot/miasi"
  agent_registry: ".devpilot/miasi/agent_registry.json"
  tool_registry: ".devpilot/miasi/tool_registry.json"
  policy_matrix: ".devpilot/miasi/policy_matrix.json"
  drafts: "outputs/drafts"
  eval_fixtures: "evals/fixtures"
  eval_outputs: "outputs/evals"
  providers_example: ".devpilot/providers.yaml.example"
  providers: ".devpilot/providers.yaml"
runtime:
  dry_run_default: true
  created_by: "FUNC-SPRINT-08"
  overwrite_policy: "refuse_by_default"
'''


def parse_project_yaml_metadata(path: Path) -> dict[str, Any]:
    """Parse the minimal fields DevPilot writes to project.yaml.

    This is not a general YAML parser. It intentionally supports only the
    deterministic shape generated by `render_project_yaml`, avoiding a runtime
    dependency until the project decides to formalize configuration parsing.
    """

    metadata: dict[str, Any] = {}
    if not path.is_file():
        return metadata
    current_section: str | None = None
    standards: list[str] = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.rstrip()
        if not line or line.lstrip().startswith("#"):
            continue
        if not line.startswith(" ") and line.endswith(":"):
            current_section = line[:-1]
            continue
        if not line.startswith(" ") and ":" in line:
            key, value = line.split(":", 1)
            metadata[key.strip()] = _parse_scalar(value.strip())
            current_section = None
            continue
        if current_section == "project" and line.startswith("  ") and ":" in line:
            key, value = line.split(":", 1)
            metadata[f"project_{key.strip()}"] = _parse_scalar(value.strip())
        elif current_section == "miasi" and line.startswith("  ") and ":" in line:
            key, value = line.split(":", 1)
            metadata[f"miasi_{key.strip()}"] = _parse_scalar(value.strip())
        elif current_section == "standards" and line.strip().startswith("-"):
            standards.append(str(_parse_scalar(line.strip()[1:].strip())))
    if standards:
        metadata["standards"] = standards
    return metadata


def _parse_scalar(value: str) -> Any:
    if value.lower() == "true":
        return True
    if value.lower() == "false":
        return False
    if len(value) >= 2 and value[0] == value[-1] == '"':
        return value[1:-1]
    return value


def _escape_yaml_string(value: str) -> str:
    return value.replace('\\', '\\\\').replace('"', '\\"')


def _relative(path: Path, root: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve())).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")
