from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.policy import PathGuard, PolicyEffect, configured_external_workspace_roots
from devpilot_core.workspace.project_entry_contracts import GitSourceKind, ProjectEntryMode, ProjectIntake, stable_sha256

BOOTSTRAP_EXECUTION_SCHEMA_ID = "SCHEMA-DEVPL-GSDLC-03-D-BOOTSTRAP-EXECUTION-V1"
BOOTSTRAP_ROLLBACK_SCHEMA_ID = "SCHEMA-DEVPL-GSDLC-03-D-BOOTSTRAP-ROLLBACK-V1"
GSDLC03D_GIT_MIN_VERSION = (2, 33, 0)
GSDLC03D_GIT_MIN_VERSION_TEXT = "2.33.0"

STAGES = (
    "target-root",
    "structure-templates",
    "git",
    "venv",
    "dependency-jobs",
    "workspace-metadata",
    "workspace-register",
    "verify",
)

_TEMPLATE_CONTENT = {
    "common.gitignore": ".venv/\nnode_modules/\n__pycache__/\n*.pyc\n.env\n.devpilot/bootstrap-execution.json\n.devpilot/workspace-registration.json\n",
    "frontend.react-typescript.package": json.dumps(
        {
            "name": "devpilot-created-frontend",
            "private": True,
            "version": "0.1.0",
            "type": "module",
            "scripts": {"dev": "vite", "build": "tsc --noEmit && vite build"},
            "dependencies": {"react": "^18.3.1", "react-dom": "^18.3.1"},
            "devDependencies": {"typescript": "^5.6.0", "vite": "^6.0.0"},
        },
        indent=2,
        sort_keys=True,
    )
    + "\n",
    "frontend.react-typescript.tsconfig": json.dumps(
        {
            "compilerOptions": {
                "target": "ES2020",
                "module": "ESNext",
                "moduleResolution": "Bundler",
                "strict": True,
                "jsx": "react-jsx",
                "skipLibCheck": True,
            },
            "include": ["src"],
        },
        indent=2,
        sort_keys=True,
    )
    + "\n",
    "frontend.react-typescript.main": "export const bootstrapMessage = 'DevPilot project bootstrap';\n",
    "backend.fastapi-python.requirements": "fastapi>=0.115,<1\nuvicorn>=0.30,<1\n",
    "backend.fastapi-python.main": "from fastapi import FastAPI\n\napp = FastAPI(title='DevPilot Project')\n\n@app.get('/health')\ndef health() -> dict[str, str]:\n    return {'status': 'ok'}\n",
    "standards.mipsoftware": "# MIPSoftware\n\nProyecto inicializado por DevPilot bajo contrato GSDLC-03-D.\n",
    "standards.miasi": "# MIASI\n\nControles locales, deny-by-default y aprobación humana obligatoria.\n",
}


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _sha_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _run(argv: list[str], *, cwd: Path, timeout: int = 120) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(argv, cwd=cwd, capture_output=True, check=False, timeout=timeout, shell=False)


def _parse_git_version(text: str) -> tuple[int, int, int] | None:
    # Examples: "git version 2.33.0.windows.2", "git version 2.45.1".
    tokens = (text or "").strip().split()
    candidate = tokens[-1] if tokens else ""
    numeric = candidate.split(".")
    values: list[int] = []
    for part in numeric:
        digits = "".join(ch for ch in part if ch.isdigit())
        if not digits:
            break
        values.append(int(digits))
        if len(values) == 3:
            break
    if len(values) < 2:
        return None
    while len(values) < 3:
        values.append(0)
    return tuple(values[:3])  # type: ignore[return-value]


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.resolve(strict=False).relative_to(root.resolve(strict=False))
        return True
    except ValueError:
        return False


def _safe_tree(root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not root.exists():
        return rows
    for path in sorted(root.rglob("*"), key=lambda p: p.as_posix().lower()):
        if ".venv" in path.parts or ".git" in path.parts:
            continue
        if path.is_file():
            rows.append(
                {
                    "path": path.relative_to(root).as_posix(),
                    "sha256": _sha_file(path),
                    "bytes": path.stat().st_size,
                }
            )
    return rows


def _render_project_yaml(intake: ProjectIntake) -> str:
    return (
        "schema_version: '1.0'\n"
        f"project_id: {intake.project_id}\n"
        f"project_name: {json.dumps(intake.project_name, ensure_ascii=False)}\n"
        "project_type: agent-assisted-sdlc\n"
        "miasi_required: true\n"
        "standards:\n"
        "  - MIPSoftware\n"
        "  - MIASI\n"
    )


def _render_readme(intake: ProjectIntake) -> str:
    return (
        f"# {intake.project_name}\n\n"
        "Workspace materializado por DevPilot mediante GSDLC-03-D.\n\n"
        f"- project_id: `{intake.project_id}`\n"
        f"- entry_mode: `{intake.entry_mode.value}`\n"
        "- bootstrap: approval-bound / local-first\n"
    )


@dataclass(frozen=True)
class BootstrapExecutionInput:
    intake: Mapping[str, Any]
    bootstrap_plan: Mapping[str, Any]
    plan_hash: str
    preimage_hash: str
    approval_id: str
    actor_id: str
    role_at_decision: str
    fault_stage: str | None = None
    dependency_mode: str = "defer-network"


class ProjectBootstrapExecutor:
    """Typed, bounded and rollback-capable GSDLC-03-D workspace executor.

    This core class assumes policy/approval authorization has already passed at
    the ApplicationService boundary. It still independently enforces path scope,
    typed stages, no shell interpolation and no network by default.
    """

    def __init__(self, platform_root: Path, *, allowed_roots: tuple[Path, ...] | None = None) -> None:
        self.platform_root = Path(platform_root).resolve()
        self.allowed_roots = tuple(
            Path(item).resolve()
            for item in (allowed_roots if allowed_roots is not None else configured_external_workspace_roots())
        )
        self.path_guard = PathGuard(self.platform_root, allowed_external_roots=self.allowed_roots)

    def execute(self, data: BootstrapExecutionInput) -> CommandResult:
        started = time.perf_counter()
        try:
            intake = ProjectIntake.from_mapping(data.intake)
        except (ValueError, TypeError) as exc:
            return self._block("PROJECT_BOOTSTRAP_INTAKE_BLOCK", f"Bootstrap intake is invalid: {exc}")

        if data.fault_stage and data.fault_stage not in STAGES:
            return self._block(
                "PROJECT_BOOTSTRAP_FAULT_STAGE_INVALID",
                "Fault injection stage is not supported.",
                {"fault_stage": data.fault_stage, "supported": list(STAGES)},
            )
        if data.dependency_mode not in {"defer-network", "offline-cache"}:
            return self._block(
                "PROJECT_BOOTSTRAP_DEPENDENCY_MODE_BLOCK",
                "Dependency mode must be defer-network or offline-cache.",
            )

        plan = dict(data.bootstrap_plan)
        if str(plan.get("plan_hash") or "") != data.plan_hash:
            return self._block("PROJECT_BOOTSTRAP_PLAN_HASH_MISMATCH", "Bootstrap plan hash does not match the approved plan.")
        if str(plan.get("project_id") or "") != intake.project_id:
            return self._block("PROJECT_BOOTSTRAP_PROJECT_BINDING_BLOCK", "Bootstrap plan is bound to a different project_id.")
        if str(plan.get("entry_mode") or "") != intake.entry_mode.value:
            return self._block("PROJECT_BOOTSTRAP_MODE_BINDING_BLOCK", "Bootstrap plan is bound to a different entry mode.")

        target = Path(intake.target_root).expanduser().resolve(strict=False)
        decision = self.path_guard.evaluate(target, action="write")
        if decision.effect in {PolicyEffect.BLOCK, PolicyEffect.DENY}:
            return self._block(
                "PROJECT_BOOTSTRAP_TARGET_SCOPE_BLOCK",
                decision.reason,
                {"target": str(target), "policy": decision.to_dict()},
            )
        if _is_relative_to(target, self.platform_root) or _is_relative_to(self.platform_root, target):
            return self._block("PROJECT_BOOTSTRAP_PLATFORM_OVERLAP_BLOCK", "Bootstrap target must not overlap the DevPilot platform repository.")

        if intake.entry_mode is ProjectEntryMode.IMPORT_GIT and intake.git_source_kind is GitSourceKind.REMOTE_URL:
            return self._block(
                "PROJECT_BOOTSTRAP_REMOTE_GIT_DISABLED",
                "Remote Git execution remains disabled-by-default in GSDLC-03-D; local import is the acceptance authority.",
            )

        created_target = False
        created_paths: list[Path] = []
        stages: list[dict[str, Any]] = []
        rollback: dict[str, Any] | None = None
        git_exclude_backup: tuple[Path, bool, bytes] | None = None

        def stage_start(stage_id: str) -> dict[str, Any]:
            row = {
                "stage": stage_id,
                "status": "RUNNING",
                "started_at": _utcnow(),
                "before": {"target_exists": target.exists()},
                "rollback_action": "remove-created-target" if created_target else "remove-created-paths-only",
            }
            stages.append(row)
            return row

        def stage_finish(row: dict[str, Any], *, status: str = "PASS", **extra: Any) -> None:
            row.update(status=status, completed_at=_utcnow(), after={"target_exists": target.exists()}, **extra)

        def maybe_fault(stage_id: str) -> None:
            if data.fault_stage == stage_id:
                raise RuntimeError(f"fault-injection:{stage_id}")

        try:
            row = stage_start("target-root")
            if intake.entry_mode in {ProjectEntryMode.CREATE_NEW, ProjectEntryMode.IMPORT_GIT}:
                if target.exists():
                    raise RuntimeError("target-collision")
                target.mkdir(parents=True, exist_ok=False)
                created_target = True
            else:
                if not target.is_dir():
                    raise RuntimeError("open-target-missing")
            stage_finish(row, created_target=created_target)
            maybe_fault("target-root")

            row = stage_start("structure-templates")
            if intake.entry_mode is ProjectEntryMode.CREATE_NEW:
                for item in plan.get("directories", []):
                    rel = str(item.get("relative_path") or "")
                    self._mkdir(target, rel, created_paths)
                for item in plan.get("files", []):
                    rel = str(item.get("relative_path") or "")
                    template_id = str(item.get("template_id") or "")
                    content = self._template_content(template_id, intake)
                    self._write_new(target, rel, content.encode("utf-8"), created_paths)
            stage_finish(row, files_total=len(plan.get("files", [])) if intake.entry_mode is ProjectEntryMode.CREATE_NEW else 0)
            maybe_fault("structure-templates")

            row = stage_start("git")
            git_result = self._git_stage(intake, target, created_paths)
            stage_finish(row, git=git_result)
            maybe_fault("git")

            row = stage_start("venv")
            venv_result = self._venv_stage(plan, target, created_paths)
            stage_finish(row, venv=venv_result)
            maybe_fault("venv")

            row = stage_start("dependency-jobs")
            deps = self._dependency_stage(plan, target, mode=data.dependency_mode)
            stage_finish(row, dependency_jobs=deps)
            maybe_fault("dependency-jobs")

            row = stage_start("workspace-metadata")
            if intake.entry_mode in {ProjectEntryMode.OPEN_EXISTING, ProjectEntryMode.IMPORT_GIT}:
                git_exclude_backup = self._ensure_git_exclude(target, ".devpilot/")
            metadata_dir = target / ".devpilot"
            if not metadata_dir.exists():
                metadata_dir.mkdir(parents=True)
                created_paths.append(metadata_dir)
            project_file = metadata_dir / "project.yaml"
            if not project_file.exists():
                project_file.write_text(_render_project_yaml(intake), encoding="utf-8")
                created_paths.append(project_file)
            execution_seed = {
                "schema_id": BOOTSTRAP_EXECUTION_SCHEMA_ID,
                "project_id": intake.project_id,
                "entry_mode": intake.entry_mode.value,
                "target_root": str(target),
                "plan_hash": data.plan_hash,
                "preimage_hash": data.preimage_hash,
                "approval_id": data.approval_id,
                "actor_id": data.actor_id,
                "role_at_decision": data.role_at_decision,
                "network_used": False,
                "external_api_used": False,
                "arbitrary_shell_used": False,
            }
            seed_path = metadata_dir / "bootstrap-execution.json"
            seed_path.write_text(json.dumps(execution_seed, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            if seed_path not in created_paths:
                created_paths.append(seed_path)
            stage_finish(row, metadata_files=[".devpilot/project.yaml", ".devpilot/bootstrap-execution.json"])
            maybe_fault("workspace-metadata")

            row = stage_start("workspace-register")
            registration_path = target / ".devpilot" / "workspace-registration.json"
            registration = {
                "schema_id": "devpilot.gsdlc03d.workspace_registration.v1",
                "workspace_id": intake.project_id,
                "project_id": intake.project_id,
                "root_path": str(target),
                "status": "registered-local",
                "default_effect": "deny",
                "network_allowed": False,
                "external_api_allowed": False,
                "registered_at": _utcnow(),
                "registration_scope": "target-local",
            }
            existed_registration = registration_path.exists()
            if existed_registration:
                existing = json.loads(registration_path.read_text(encoding="utf-8"))
                if existing.get("workspace_id") != intake.project_id or Path(str(existing.get("root_path"))).resolve(strict=False) != target:
                    raise RuntimeError("registration-conflict")
            else:
                registration_path.write_text(json.dumps(registration, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
                created_paths.append(registration_path)
            stage_finish(row, registration=registration, idempotent_existing=existed_registration)
            maybe_fault("workspace-register")

            row = stage_start("verify")
            verify = self._verify(intake, plan, target, deps)
            if not verify["ok"]:
                raise RuntimeError("verification-failed:" + ",".join(verify["failures"]))
            stage_finish(row, verification=verify)
            maybe_fault("verify")

        except Exception as exc:
            rollback = self._rollback(
                target,
                created_target=created_target,
                created_paths=created_paths,
                reason=str(exc),
                git_exclude_backup=git_exclude_backup,
            )
            duration_ms = round((time.perf_counter() - started) * 1000, 2)
            return CommandResult(
                command="project bootstrap execute",
                ok=False,
                exit_code=ExitCode.BLOCK,
                message="Bootstrap transaction failed and rollback was executed.",
                data={
                    "execution": {
                        "schema_id": BOOTSTRAP_EXECUTION_SCHEMA_ID,
                        "status": "ROLLED-BACK" if rollback["rollback_ok"] else "ROLLBACK-BLOCKED",
                        "project_id": intake.project_id,
                        "target_root": str(target),
                        "plan_hash": data.plan_hash,
                        "preimage_hash": data.preimage_hash,
                        "approval_id": data.approval_id,
                        "stages": stages,
                        "rollback": rollback,
                        "duration_ms": duration_ms,
                        "network_used": False,
                        "external_api_used": False,
                        "writes_outside_workspace": 0,
                    }
                },
                findings=[
                    Finding(
                        "PROJECT_BOOTSTRAP_EXECUTION_ROLLED_BACK" if rollback["rollback_ok"] else "PROJECT_BOOTSTRAP_ROLLBACK_BLOCK",
                        "Fault/transaction failure was compensated without external writes." if rollback["rollback_ok"] else "Rollback could not prove clean compensation.",
                        Severity.BLOCK,
                        metadata={"reason": str(exc), "rollback_ok": rollback["rollback_ok"]},
                    )
                ],
            )

        duration_ms = round((time.perf_counter() - started) * 1000, 2)
        execution = {
            "schema_id": BOOTSTRAP_EXECUTION_SCHEMA_ID,
            "schema_version": "1.0",
            "status": "PASS",
            "project_id": intake.project_id,
            "entry_mode": intake.entry_mode.value,
            "target_root": str(target),
            "plan_hash": data.plan_hash,
            "preimage_hash": data.preimage_hash,
            "approval_id": data.approval_id,
            "actor_id": data.actor_id,
            "role_at_decision": data.role_at_decision,
            "stages": stages,
            "verification": self._verify(intake, plan, target, deps),
            "target_inventory": _safe_tree(target),
            "network_used": False,
            "external_api_used": False,
            "arbitrary_shell_used": False,
            "writes_outside_workspace": 0,
            "pilot_workspace_accessed": False,
            "dependency_mode": data.dependency_mode,
            "duration_ms": duration_ms,
            "completed_at": _utcnow(),
        }
        execution["execution_hash"] = stable_sha256(execution)
        manifest = target / ".devpilot" / "bootstrap-execution.json"
        manifest.write_text(json.dumps(execution, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        return CommandResult(
            command="project bootstrap execute",
            ok=True,
            exit_code=ExitCode.PASS,
            message="Approved project bootstrap completed inside the authorized workspace.",
            data={"execution": execution},
            findings=[
                Finding(
                    "PROJECT_BOOTSTRAP_EXECUTION_PASS",
                    "Bootstrap execution completed with typed stages, local-only writes and verified postconditions.",
                    Severity.INFO,
                    path=str(target),
                )
            ],
        )

    def _mkdir(self, target: Path, relative: str, created_paths: list[Path]) -> None:
        path = self._target_path(target, relative)
        if not path.exists():
            path.mkdir(parents=True, exist_ok=False)
            created_paths.append(path)

    def _write_new(self, target: Path, relative: str, content: bytes, created_paths: list[Path]) -> None:
        path = self._target_path(target, relative)
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            raise RuntimeError(f"planned-file-collision:{relative}")
        path.write_bytes(content)
        created_paths.append(path)

    def _target_path(self, target: Path, relative: str) -> Path:
        rel = Path(relative)
        if rel.is_absolute() or ".." in rel.parts:
            raise RuntimeError(f"unsafe-relative-path:{relative}")
        path = (target / rel).resolve(strict=False)
        if not _is_relative_to(path, target):
            raise RuntimeError(f"path-escape:{relative}")
        return path

    def _template_content(self, template_id: str, intake: ProjectIntake) -> str:
        if template_id == "common.readme":
            return _render_readme(intake)
        if template_id == "devpilot.project-metadata":
            return _render_project_yaml(intake)
        if template_id not in _TEMPLATE_CONTENT:
            raise RuntimeError(f"template-not-implemented:{template_id}")
        return _TEMPLATE_CONTENT[template_id]

    def _git_stage(self, intake: ProjectIntake, target: Path, created_paths: list[Path]) -> dict[str, Any]:
        git = shutil.which("git")
        if not git:
            raise RuntimeError("git-not-found")
        version_probe = _run([git, "--version"], cwd=target.parent if target.parent.exists() else self.platform_root)
        version_text = version_probe.stdout.decode("utf-8", "replace").strip() if version_probe.returncode == 0 else ""
        version = _parse_git_version(version_text)
        if version is None or version < GSDLC03D_GIT_MIN_VERSION:
            raise RuntimeError(
                f"git-version-unsupported:{version_text or 'unparseable'};minimum={GSDLC03D_GIT_MIN_VERSION_TEXT}"
            )
        if intake.entry_mode is ProjectEntryMode.CREATE_NEW:
            cp = _run([git, "init"], cwd=target)
            if cp.returncode:
                raise RuntimeError("git-init-failed:" + cp.stderr.decode("utf-8", "replace")[-400:])
            return {"operation_id": "git.init", "status": "PASS", "network_used": False, "git_version": version_text, "effective_minimum_version": GSDLC03D_GIT_MIN_VERSION_TEXT}
        if intake.entry_mode is ProjectEntryMode.OPEN_EXISTING:
            inside = _run([git, "rev-parse", "--is-inside-work-tree"], cwd=target)
            if inside.returncode or inside.stdout.decode("utf-8", "replace").strip().lower() != "true":
                raise RuntimeError("open-existing-not-git")
            return {"operation_id": "workspace.inspect", "status": "PASS", "network_used": False, "git_version": version_text, "effective_minimum_version": GSDLC03D_GIT_MIN_VERSION_TEXT}
        if intake.git_source_kind is not GitSourceKind.LOCAL_PATH:
            raise RuntimeError("remote-git-disabled")
        source = Path(intake.git_source_location or "").expanduser().resolve(strict=True)
        if not source.is_dir():
            raise RuntimeError("local-import-source-missing")
        source_guard = self.path_guard.evaluate(source, action="read")
        if source_guard.effect in {PolicyEffect.BLOCK, PolicyEffect.DENY}:
            raise RuntimeError("local-import-source-outside-allowed-roots")
        # Target was created empty at target-root stage; clone requires absence.
        target.rmdir()
        cp = _run([git, "clone", "--local", "--no-hardlinks", str(source), str(target)], cwd=target.parent, timeout=120)
        if cp.returncode:
            target.mkdir(parents=True, exist_ok=True)
            raise RuntimeError("git-local-import-failed:" + cp.stderr.decode("utf-8", "replace")[-400:])
        return {"operation_id": "git.import.local", "status": "PASS", "network_used": False, "source": str(source), "git_version": version_text, "effective_minimum_version": GSDLC03D_GIT_MIN_VERSION_TEXT}

    def _venv_stage(self, plan: Mapping[str, Any], target: Path, created_paths: list[Path]) -> dict[str, Any]:
        spec = plan.get("venv") if isinstance(plan.get("venv"), Mapping) else {}
        if not bool(spec.get("required")):
            return {"operation_id": "python.venv.create", "status": "NOT-APPLICABLE", "network_used": False}
        path = target / ".venv"
        if path.exists():
            raise RuntimeError("venv-collision")
        cp = _run([sys.executable, "-m", "venv", str(path)], cwd=target, timeout=180)
        if cp.returncode:
            raise RuntimeError("venv-create-failed:" + cp.stderr.decode("utf-8", "replace")[-400:])
        created_paths.append(path)
        py = path / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        if not py.is_file():
            raise RuntimeError("venv-python-missing")
        return {
            "operation_id": "python.venv.create",
            "status": "PASS",
            "path": str(path),
            "python": str(py),
            "network_used": False,
        }

    def _dependency_stage(self, plan: Mapping[str, Any], target: Path, *, mode: str) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for job in plan.get("dependency_jobs", []):
            network_required = bool(job.get("network_required"))
            if network_required and mode == "defer-network":
                rows.append(
                    {
                        "job_id": str(job.get("job_id")),
                        "operation_id": str(job.get("operation_id")),
                        "status": "DEFERRED-NETWORK-POLICY",
                        "network_required": True,
                        "network_used": False,
                        "reason": "Dependency installation remains disabled until an explicit network/cache plan is approved.",
                    }
                )
                continue
            if network_required and mode == "offline-cache":
                rows.append(
                    {
                        "job_id": str(job.get("job_id")),
                        "operation_id": str(job.get("operation_id")),
                        "status": "DEFERRED-CACHE-NOT-BOUND",
                        "network_required": True,
                        "network_used": False,
                        "reason": "No lock/cache authority is bound in the GSDLC-03-B plan; executor refuses to guess packages.",
                    }
                )
                continue
            rows.append(
                {
                    "job_id": str(job.get("job_id")),
                    "operation_id": str(job.get("operation_id")),
                    "status": "NOT-REQUIRED",
                    "network_required": False,
                    "network_used": False,
                }
            )
        return rows

    def _verify(self, intake: ProjectIntake, plan: Mapping[str, Any], target: Path, deps: list[dict[str, Any]]) -> dict[str, Any]:
        failures: list[str] = []
        if not target.is_dir():
            failures.append("target-missing")
        project_file = target / ".devpilot" / "project.yaml"
        if not project_file.is_file():
            failures.append("project-metadata-missing")
        registration = target / ".devpilot" / "workspace-registration.json"
        if not registration.is_file():
            failures.append("registration-missing")
        git = shutil.which("git")
        git_clean = False
        if git and target.exists():
            inside = _run([git, "rev-parse", "--is-inside-work-tree"], cwd=target)
            if inside.returncode == 0 and inside.stdout.decode("utf-8", "replace").strip().lower() == "true":
                status = _run([git, "status", "--porcelain=v1", "-z"], cwd=target)
                git_clean = status.returncode == 0 and not [x for x in status.stdout.split(b"\0") if x]
        if intake.entry_mode is ProjectEntryMode.OPEN_EXISTING:
            # OPEN may already have user files and is only registered; clean Git is still required by current 03-B contract.
            if not git_clean:
                failures.append("git-not-clean")
        elif intake.entry_mode is ProjectEntryMode.IMPORT_GIT:
            # Local clone remains clean because target-local DevPilot metadata is excluded via .git/info/exclude
            # before it is materialized. The exclude preimage is restored if the transaction rolls back.
            git_clean = self._git_clean(target)
            if not git_clean:
                failures.append("git-not-clean")
        else:
            # CREATE_NEW writes generated files after git init. Stage a deterministic initial local commit so the resulting workspace is clean.
            self._ensure_git_identity_and_commit(target)
            git_clean = self._git_clean(target)
            if not git_clean:
                failures.append("git-not-clean")

        venv_required = bool((plan.get("venv") or {}).get("required"))
        venv_ok = True
        if venv_required:
            py = target / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
            venv_ok = py.is_file()
            if not venv_ok:
                failures.append("venv-missing")

        deps_compliant = all(str(row.get("status")) in {"DEFERRED-NETWORK-POLICY", "DEFERRED-CACHE-NOT-BOUND", "NOT-REQUIRED"} for row in deps)
        if not deps_compliant:
            failures.append("dependency-policy")

        return {
            "ok": not failures,
            "failures": failures,
            "git_clean": git_clean,
            "venv_required": venv_required,
            "venv_ok": venv_ok,
            "dependencies_compliant_with_network_policy": deps_compliant,
            "writes_outside_workspace": 0,
            "network_used": False,
        }

    def _ensure_git_exclude(self, target: Path, line: str) -> tuple[Path, bool, bytes] | None:
        info = target / ".git" / "info"
        if not info.is_dir():
            return None
        exclude = info / "exclude"
        existed = exclude.exists()
        original = exclude.read_bytes() if existed else b""
        text = original.decode("utf-8", errors="replace")
        if line not in {row.strip() for row in text.splitlines()}:
            with exclude.open("a", encoding="utf-8", newline="\n") as fh:
                if text and not text.endswith(("\n", "\r")):
                    fh.write("\n")
                fh.write(line + "\n")
        return (exclude, existed, original)

    def _ensure_git_identity_and_commit(self, target: Path) -> None:
        git = shutil.which("git")
        if not git:
            raise RuntimeError("git-not-found")
        # Local-only identity; never touches global Git config.
        commands = [
            [git, "config", "user.email", "devpilot-bootstrap@example.invalid"],
            [git, "config", "user.name", "DevPilot Bootstrap"],
            [git, "add", "--all"],
        ]
        for argv in commands:
            cp = _run(argv, cwd=target)
            if cp.returncode:
                raise RuntimeError("git-initial-commit-prepare-failed")
        diff = _run([git, "diff", "--cached", "--quiet"], cwd=target)
        if diff.returncode == 1:
            cp = _run([git, "commit", "-m", "Initial DevPilot bootstrap"], cwd=target)
            if cp.returncode:
                raise RuntimeError("git-initial-commit-failed:" + cp.stderr.decode("utf-8", "replace")[-400:])

    def _git_clean(self, target: Path) -> bool:
        git = shutil.which("git")
        if not git:
            return False
        status = _run([git, "status", "--porcelain=v1", "-z"], cwd=target)
        return status.returncode == 0 and not [x for x in status.stdout.split(b"\0") if x]

    def _rollback(
        self,
        target: Path,
        *,
        created_target: bool,
        created_paths: list[Path],
        reason: str,
        git_exclude_backup: tuple[Path, bool, bytes] | None = None,
    ) -> dict[str, Any]:
        actions: list[dict[str, Any]] = []
        ok = True
        if created_target:
            try:
                if target.exists():
                    shutil.rmtree(target)
                actions.append({"action": "remove-created-target", "status": "PASS", "path": str(target)})
            except Exception as exc:
                ok = False
                actions.append({"action": "remove-created-target", "status": "BLOCK", "error": str(exc)})
        else:
            for path in sorted(set(created_paths), key=lambda p: len(p.parts), reverse=True):
                try:
                    if path.is_file() or path.is_symlink():
                        path.unlink(missing_ok=True)
                    elif path.is_dir() and path.exists():
                        path.rmdir()
                    actions.append({"action": "remove-created-path", "status": "PASS", "path": str(path)})
                except Exception as exc:
                    ok = False
                    actions.append({"action": "remove-created-path", "status": "BLOCK", "path": str(path), "error": str(exc)})
            if git_exclude_backup is not None:
                exclude, existed, original = git_exclude_backup
                try:
                    if existed:
                        exclude.write_bytes(original)
                    else:
                        exclude.unlink(missing_ok=True)
                    actions.append({"action": "restore-git-info-exclude", "status": "PASS", "path": str(exclude)})
                except Exception as exc:
                    ok = False
                    actions.append({"action": "restore-git-info-exclude", "status": "BLOCK", "path": str(exclude), "error": str(exc)})
        residue = target.exists() if created_target else False
        if created_target and residue:
            ok = False
        return {
            "schema_id": BOOTSTRAP_ROLLBACK_SCHEMA_ID,
            "rollback_ok": ok,
            "reason": reason,
            "created_target": created_target,
            "actions": actions,
            "target_residue": residue,
            "writes_outside_workspace": 0,
            "completed_at": _utcnow(),
        }

    @staticmethod
    def _block(finding_id: str, message: str, metadata: Mapping[str, Any] | None = None) -> CommandResult:
        return CommandResult(
            command="project bootstrap execute",
            ok=False,
            exit_code=ExitCode.BLOCK,
            message=message,
            data={"execution": {"status": "BLOCK", "writes_outside_workspace": 0, "network_used": False}},
            findings=[Finding(finding_id, message, Severity.BLOCK, metadata=dict(metadata or {}))],
        )
