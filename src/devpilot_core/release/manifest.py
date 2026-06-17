from __future__ import annotations

import json
import re
import subprocess
import sys
import tomllib
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity

_SEMVER_RE = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:[-+][0-9A-Za-z.-]+)?$")

_FORBIDDEN_RELEASE_MARKERS = [
    ".git/",
    ".venv/",
    "node_modules/",
    "outputs/",
    "__pycache__/",
    ".pytest_cache/",
    ".devpilot/devpilot.db",
    ".devpilot/backups/",
    ".pyc",
    ".pyo",
]

_COMPONENT_PATHS = [
    "src/devpilot_core",
    "tests",
    "docs",
    ".devpilot/miasi",
    ".github/workflows/devpilot-ci.yml",
    "ui/web",
    "pyproject.toml",
    "README.md",
]

_RELEASE_EVIDENCE_COMMANDS = [
    {
        "id": "TESTS-PYTEST-FULL",
        "command": "python -m pytest -q",
        "required_for_release": True,
        "status": "declared_required_not_executed_by_manifest",
        "reason": "Release manifest generation must remain deterministic and fast; pytest evidence is produced by CI/local verification.",
    },
    {
        "id": "QUALITY-GATE-CI",
        "command": "python -m devpilot_core quality-gate run --profile ci --json",
        "required_for_release": True,
        "status": "declared_required_not_executed_by_manifest",
        "reason": "The manifest references the required gate; executing the gate remains an explicit release-readiness step.",
    },
    {
        "id": "WEB-UI-SMOKE",
        "command": "npm --prefix ui/web test",
        "required_for_release": True,
        "status": "declared_required_not_executed_by_manifest",
        "reason": "Node execution is intentionally explicit and not hidden behind manifest generation.",
    },
]

_EXPECTED_RELEASE_ARTIFACTS = [
    {
        "id": "REL-MANIFEST-V1",
        "path": "outputs/reports/release_manifest.json",
        "kind": "release-manifest-report",
        "implemented_in": "FUNC-SPRINT-77",
        "status": "implemented-initial",
    },
    {
        "id": "REL-MANIFEST-MD",
        "path": "outputs/reports/release_manifest.md",
        "kind": "release-manifest-report",
        "implemented_in": "FUNC-SPRINT-77",
        "status": "implemented-initial",
    },
    {
        "id": "CHANGELOG-MD",
        "path": "outputs/reports/release_changelog.md",
        "kind": "human-readable-changelog",
        "implemented_in": "FUNC-SPRINT-78",
        "status": "implemented-initial",
    },
    {
        "id": "PKG-CLEAN-ZIP",
        "path": "dist/release/devpilot-local-<version>-source.zip",
        "kind": "clean-source-package",
        "implemented_in": "FUNC-SPRINT-79",
        "status": "implemented-initial",
    },
    {
        "id": "PKG-WHEEL",
        "path": "dist/devpilot_local-<version>-py3-none-any.whl",
        "kind": "python-wheel",
        "implemented_in": "FUNC-SPRINT-79",
        "status": "implemented-initial",
    },
    {
        "id": "PKG-SDIST",
        "path": "dist/devpilot-local-<version>.tar.gz",
        "kind": "python-sdist",
        "implemented_in": "FUNC-SPRINT-79",
        "status": "implemented-initial",
    },
    {
        "id": "PKG-BUILD-REPORT",
        "path": "outputs/reports/package_build.json",
        "kind": "package-build-report",
        "implemented_in": "FUNC-SPRINT-79",
        "status": "implemented-initial",
    },
    {
        "id": "SBOM-CYCLONEDX",
        "path": "outputs/reports/sbom.json",
        "kind": "sbom",
        "implemented_in": "FUNC-SPRINT-80",
        "status": "implemented-initial",
    },
    {
        "id": "CHECKSUMS-SHA256",
        "path": "outputs/reports/checksums.sha256",
        "kind": "checksums",
        "implemented_in": "FUNC-SPRINT-81",
        "status": "implemented-initial",
    },
    {
        "id": "RELEASE-SMOKE-TEST",
        "path": "outputs/reports/release_smoke_test.json",
        "kind": "release-smoke-test-report",
        "implemented_in": "FUNC-SPRINT-81",
        "status": "implemented-initial",
    },
    {
        "id": "RELEASE-VERIFICATION",
        "path": "outputs/reports/release_verification.json",
        "kind": "release-verification-report",
        "implemented_in": "FUNC-SPRINT-81",
        "status": "implemented-initial",
    },
    {
        "id": "INSTALL-PLAN",
        "path": "outputs/reports/install_plan.json",
        "kind": "installation-plan-report",
        "implemented_in": "FUNC-SPRINT-82",
        "status": "implemented-initial",
    },
    {
        "id": "BACKUP-MANIFEST",
        "path": ".devpilot/backups/<backup-id>.manifest.json",
        "kind": "local-backup-manifest",
        "implemented_in": "FUNC-SPRINT-83",
        "status": "implemented-initial",
    },
    {
        "id": "BACKUP-REPORT",
        "path": "outputs/reports/backup_create.json",
        "kind": "backup-create-report",
        "implemented_in": "FUNC-SPRINT-83",
        "status": "implemented-initial",
    },
    {
        "id": "RESTORE-PLAN",
        "path": "outputs/reports/backup_restore.json",
        "kind": "backup-restore-plan-report",
        "implemented_in": "FUNC-SPRINT-83",
        "status": "implemented-initial",
    },
    {
        "id": "UPGRADE-CHECK",
        "path": "outputs/reports/upgrade_check.json",
        "kind": "upgrade-check-report",
        "implemented_in": "FUNC-SPRINT-83",
        "status": "implemented-initial",
    },
]


@dataclass(frozen=True)
class ReleaseManifestOptions:
    """Options for creating the local release manifest.

    FUNC-SPRINT-77 deliberately creates metadata and evidence references only.
    Packaging and SBOM are implemented as initial local baselines; checksums and smoke verification are implemented initially in FUNC-SPRINT-81; installation planning is implemented initially in FUNC-SPRINT-82; backup/restore/upgrade planning is implemented initially in FUNC-SPRINT-83. Signing and publication remain future/out-of-scope capabilities.
    """

    version: str
    channel: str = "local-candidate"
    include_git: bool = True


class ReleaseManifestBuilder:
    """Build a deterministic, local-first release manifest for DevPilot.

    The builder does not call the network, does not invoke external model APIs,
    does not publish packages and does not mutate source files. Optional report
    writing is handled by the CLI through the standard ReportEngine.
    """

    def __init__(self, root: Path, *, options: ReleaseManifestOptions) -> None:
        self.root = Path(root).resolve()
        self.options = options

    def build(self) -> CommandResult:
        findings: list[Finding] = []
        if not _SEMVER_RE.match(self.options.version):
            findings.append(
                Finding(
                    "RELEASE_VERSION_INVALID",
                    "Release version must follow SemVer MAJOR.MINOR.PATCH, optionally with prerelease/build metadata.",
                    Severity.ERROR,
                    metadata={"version": self.options.version},
                )
            )
            return CommandResult(
                command="release manifest",
                ok=False,
                exit_code=ExitCode.ERROR,
                message="Release manifest generation failed because the version is invalid.",
                data={"summary": self._summary_template(valid_version=False)},
                findings=findings,
            )

        project = self._project_metadata()
        git = self._git_metadata() if self.options.include_git else self._git_disabled_metadata()
        components = self._components()
        release_manifest = {
            "schema_version": "1.0.0",
            "manifest_id": f"REL-MANIFEST-{_safe_release_id(self.options.version)}",
            "release_id": f"DEVPL-{self.options.version}",
            "release_version": self.options.version,
            "release_channel": self.options.channel,
            "release_status": "candidate-local",
            "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "generator": {
                "component": "devpilot_core.release.ReleaseManifestBuilder",
                "sprint": "FUNC-SPRINT-77",
                "preliminary": True,
            },
            "project": project,
            "git": git,
            "components": components,
            "evidence": {
                "required_commands": _RELEASE_EVIDENCE_COMMANDS,
                "quality_gate_profile": "ci",
                "pytest_required": True,
                "web_ui_smoke_required": True,
                "execution_policy": "manifest generation declares evidence requirements but does not execute tests/gates implicitly",
            },
            "expected_release_artifacts": _EXPECTED_RELEASE_ARTIFACTS,
            "exclusions": {
                "forbidden_markers": _FORBIDDEN_RELEASE_MARKERS,
                "runtime_state_excluded": True,
                "secrets_excluded": True,
                "outputs_excluded_from_source_package": True,
            },
            "security": {
                "network_used": False,
                "external_api_used": False,
                "publish_performed": False,
                "deploy_performed": False,
                "source_mutations_performed": False,
                "secrets_embedded": False,
            },
            "limitations": [
                "FUNC-SPRINT-77 does not build release packages.",
                "FUNC-SPRINT-78 provides the human-readable changelog; FUNC-SPRINT-79 provides initial local packaging; FUNC-SPRINT-80 provides initial SBOM baseline; checksum verification remains later.",
                "FUNC-SPRINT-77 does not calculate checksums or perform vulnerability scanning.",
                "FUNC-SPRINT-77 does not tag Git, sign artifacts, publish packages or deploy.",
                "Release readiness still requires running pytest, quality-gate ci and Web UI smoke commands explicitly.",
            ],
        }
        findings.append(
            Finding(
                "RELEASE_MANIFEST_CREATED",
                "Release manifest metadata was created without network, publication or source mutation.",
                Severity.INFO,
                metadata={"version": self.options.version, "release_id": release_manifest["release_id"]},
            )
        )
        summary = {
            **self._summary_template(valid_version=True),
            "release_id": release_manifest["release_id"],
            "release_status": release_manifest["release_status"],
            "components_total": len(components),
            "expected_artifacts_total": len(_EXPECTED_RELEASE_ARTIFACTS),
            "evidence_commands_total": len(_RELEASE_EVIDENCE_COMMANDS),
            "is_git_repo": git.get("is_git_repo"),
            "git_metadata_available": git.get("metadata_available"),
            "network_used": False,
            "external_api_used": False,
            "mutations_performed": False,
            "source_mutations_performed": False,
            "reports_written": False,
            "preliminary": True,
        }
        return CommandResult(
            command="release manifest",
            ok=True,
            exit_code=ExitCode.PASS,
            message="Release manifest generated.",
            data={
                "summary": summary,
                "release_manifest": release_manifest,
                "notes": [
                    "FUNC-SPRINT-77 introduces release metadata and manifest generation only.",
                    "Packaging, SBOM, checksums, smoke verification, installation planning and backup/upgrade planning now have local initial implementations; signing, tagging and publication remain out of scope.",
                    "Run pytest, quality-gate ci and Web UI smoke separately to produce release readiness evidence.",
                ],
            },
            findings=findings,
        )

    def _summary_template(self, *, valid_version: bool) -> dict[str, Any]:
        return {
            "version": self.options.version,
            "valid_version": valid_version,
            "channel": self.options.channel,
            "schema_version": "1.0.0",
            "dry_run": True,
            "preliminary": True,
        }

    def _project_metadata(self) -> dict[str, Any]:
        pyproject = self.root / "pyproject.toml"
        metadata: dict[str, Any] = {
            "name": "unknown",
            "pyproject_path": "pyproject.toml",
            "pyproject_exists": pyproject.exists(),
            "python_executable": sys.executable,
        }
        if not pyproject.exists():
            return metadata
        try:
            data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
        except tomllib.TOMLDecodeError as exc:
            metadata["pyproject_parse_error"] = str(exc)
            return metadata
        project = data.get("project", {}) if isinstance(data, dict) else {}
        if isinstance(project, dict):
            metadata["name"] = project.get("name", "unknown")
            metadata["declared_version"] = project.get("version")
            metadata["requires_python"] = project.get("requires-python")
            metadata["optional_dependency_groups"] = sorted((project.get("optional-dependencies") or {}).keys())
        return metadata

    def _git_metadata(self) -> dict[str, Any]:
        metadata: dict[str, Any] = {
            "is_git_repo": False,
            "metadata_available": False,
            "branch": None,
            "commit": None,
            "dirty": None,
            "error": None,
        }
        if not (self.root / ".git").exists():
            return metadata
        metadata["is_git_repo"] = True
        try:
            branch = _run_git(self.root, ["rev-parse", "--abbrev-ref", "HEAD"])
            commit = _run_git(self.root, ["rev-parse", "HEAD"])
            status = _run_git(self.root, ["status", "--porcelain"])
        except RuntimeError as exc:
            metadata["error"] = str(exc)
            return metadata
        metadata.update({"metadata_available": True, "branch": branch, "commit": commit, "dirty": bool(status.strip())})
        return metadata

    def _git_disabled_metadata(self) -> dict[str, Any]:
        return {"is_git_repo": False, "metadata_available": False, "disabled_by_option": True}

    def _components(self) -> list[dict[str, Any]]:
        return [self._component_record(path) for path in _COMPONENT_PATHS]

    def _component_record(self, relative_path: str) -> dict[str, Any]:
        path = self.root / relative_path
        if path.is_dir():
            files = [item for item in path.rglob("*") if item.is_file() and not _is_forbidden_for_manifest(item, self.root)]
            return {
                "path": relative_path,
                "kind": "directory",
                "exists": True,
                "files_total": len(files),
                "size_bytes": sum(item.stat().st_size for item in files),
            }
        if path.is_file():
            return {"path": relative_path, "kind": "file", "exists": True, "size_bytes": path.stat().st_size}
        return {"path": relative_path, "kind": "missing", "exists": False, "size_bytes": 0}


def _run_git(root: Path, args: list[str]) -> str:
    completed = subprocess.run(["git", *args], cwd=root, text=True, capture_output=True, check=False, timeout=5)
    if completed.returncode != 0:
        raise RuntimeError((completed.stderr or completed.stdout or "git command failed").strip())
    return completed.stdout.strip()


def _safe_release_id(version: str) -> str:
    return re.sub(r"[^0-9A-Za-z.-]+", "-", version).upper()


def _is_forbidden_for_manifest(path: Path, root: Path) -> bool:
    rel = str(path.resolve().relative_to(root.resolve())).replace("\\", "/")
    return any(marker in rel for marker in _FORBIDDEN_RELEASE_MARKERS)
