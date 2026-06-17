from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
import tarfile
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity

_SEMVER_RE = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:[-+][0-9A-Za-z.-]+)?$")

_FORBIDDEN_MARKERS = [
    ".git/",
    ".venv/",
    "node_modules/",
    "outputs/",
    "dist/",
    "__pycache__/",
    ".pytest_cache/",
    ".devpilot/devpilot.db",
    ".devpilot/backups/",
    ".devpilot/providers.yaml",
    ".pyc",
    ".pyo",
]

_REQUIRED_SOURCE_ZIP_MARKERS = [
    "pyproject.toml",
    "README.md",
    "src/devpilot_core/__init__.py",
    "src/devpilot_core/__main__.py",
]


@dataclass(frozen=True)
class ReleaseChecksumOptions:
    """Options for FUNC-SPRINT-81 checksum generation.

    The checksum operation is read-only. It requires a real local artifact and
    computes cryptographic metadata without calling network, publishing or
    mutating source files.
    """

    artifact: str
    version: str | None = None


@dataclass(frozen=True)
class ReleaseSmokeTestOptions:
    """Options for FUNC-SPRINT-81 release smoke testing.

    Smoke testing validates the artifact container and executes minimal local
    CLI checks while preserving local-first execution boundaries.
    """

    artifact: str
    version: str | None = None
    timeout_seconds: int = 30


@dataclass(frozen=True)
class ReleaseVerifyOptions:
    """Options for FUNC-SPRINT-81 release verification.

    Release verification consolidates checksum evidence and smoke test evidence
    for one real local artifact. It does not publish, deploy, sign or tag Git.
    """

    artifact: str
    version: str | None = None
    timeout_seconds: int = 30


class ReleaseChecksumBuilder:
    """Generate SHA256 evidence for a real local release artifact."""

    def __init__(self, root: Path, *, options: ReleaseChecksumOptions) -> None:
        self.root = Path(root).resolve()
        self.options = options

    def build(self) -> CommandResult:
        artifact = _resolve_artifact(self.root, self.options.artifact)
        version = _effective_version(self.root, self.options.version)
        validation = _validate_artifact_path(self.root, artifact)
        if validation is not None:
            return validation
        if self.options.version is not None and not _SEMVER_RE.match(version):
            return _invalid_version_result("release checksum", version)

        metadata = _checksum_metadata(self.root, artifact)
        checksum = {
            "schema_version": "1.0.0",
            "checksum_id": f"CHECKSUM-{metadata['sha256'][:12]}",
            "release_id": f"DEVPL-{version}",
            "release_version": version,
            "artifact": metadata,
            "algorithms": {
                "sha256": metadata["sha256"],
            },
            "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "security": _security_flags(),
            "limitations": [
                "FUNC-SPRINT-81 calculates SHA256 locally and does not sign artifacts.",
                "Checksums verify integrity of local artifacts; they do not prove vulnerability-free or tamper-proof distribution.",
            ],
        }
        summary = {
            "version": version,
            "schema_version": "1.0.0",
            "preliminary": True,
            "artifact": metadata["path"],
            "artifact_exists": True,
            "artifact_size_bytes": metadata["size_bytes"],
            "artifact_kind": metadata["kind"],
            "sha256": metadata["sha256"],
            "sha256_generated": True,
            "network_used": False,
            "external_api_used": False,
            "publish_performed": False,
            "deploy_performed": False,
            "git_tagging_performed": False,
            "source_mutations_performed": False,
            "reports_written": False,
        }
        return CommandResult(
            command="release checksum",
            ok=True,
            exit_code=ExitCode.PASS,
            message="Release artifact checksum generated.",
            data={
                "summary": summary,
                "checksum": checksum,
                "notes": [
                    "FUNC-SPRINT-81 introduces local SHA256 release integrity evidence.",
                    "The command requires a real local artifact and never calls network or external APIs.",
                ],
            },
            findings=[
                Finding(
                    "RELEASE_CHECKSUM_CREATED",
                    "SHA256 checksum was generated for a real local release artifact.",
                    Severity.INFO,
                    metadata={"artifact": metadata["path"], "sha256": metadata["sha256"]},
                )
            ],
        )


class ReleaseSmokeTestBuilder:
    """Run minimal local smoke checks against a release artifact."""

    def __init__(self, root: Path, *, options: ReleaseSmokeTestOptions) -> None:
        self.root = Path(root).resolve()
        self.options = options

    def build(self) -> CommandResult:
        artifact = _resolve_artifact(self.root, self.options.artifact)
        version = _effective_version(self.root, self.options.version)
        validation = _validate_artifact_path(self.root, artifact)
        if validation is not None:
            return validation
        if self.options.version is not None and not _SEMVER_RE.match(version):
            return _invalid_version_result("release smoke-test", version)

        artifact_metadata = _checksum_metadata(self.root, artifact)
        container_result = _inspect_artifact_container(self.root, artifact)
        cli_result = _run_cli_version_smoke(self.root, timeout_seconds=self.options.timeout_seconds)
        checks = [container_result, cli_result]
        failed = [item for item in checks if not item["ok"]]

        smoke = {
            "schema_version": "1.0.0",
            "smoke_test_id": f"SMOKE-{_safe_version(version)}-{artifact_metadata['sha256'][:12]}",
            "release_id": f"DEVPL-{version}",
            "release_version": version,
            "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "artifact": artifact_metadata,
            "checks": checks,
            "security": _security_flags(),
            "limitations": [
                "FUNC-SPRINT-81 smoke testing validates local artifact structure and minimal CLI execution only.",
                "It is not a full install/upgrade test; installer and upgrade validation are planned for later Fase G sprints.",
            ],
        }
        summary = {
            "version": version,
            "schema_version": "1.0.0",
            "preliminary": True,
            "artifact": artifact_metadata["path"],
            "artifact_exists": True,
            "artifact_kind": artifact_metadata["kind"],
            "checks_total": len(checks),
            "checks_passed": len(checks) - len(failed),
            "checks_failed": len(failed),
            "container_check_passed": container_result["ok"],
            "cli_version_check_passed": cli_result["ok"],
            "exit_codes_observed": True,
            "network_used": False,
            "external_api_used": False,
            "publish_performed": False,
            "deploy_performed": False,
            "git_tagging_performed": False,
            "source_mutations_performed": False,
            "reports_written": False,
        }
        findings = [
            Finding(
                "RELEASE_SMOKE_TEST_PASS" if not failed else "RELEASE_SMOKE_TEST_FAIL",
                "Release smoke test passed." if not failed else "Release smoke test failed because one or more checks failed.",
                Severity.INFO if not failed else Severity.ERROR,
                metadata={"artifact": artifact_metadata["path"], "checks_failed": len(failed)},
            )
        ]
        return CommandResult(
            command="release smoke-test",
            ok=not failed,
            exit_code=ExitCode.PASS if not failed else ExitCode.FAIL,
            message="Release smoke test passed." if not failed else "Release smoke test failed.",
            data={"summary": summary, "smoke_test": smoke},
            findings=findings,
        )


class ReleaseVerifyBuilder:
    """Consolidate release checksum and smoke-test evidence."""

    def __init__(self, root: Path, *, options: ReleaseVerifyOptions) -> None:
        self.root = Path(root).resolve()
        self.options = options

    def build(self) -> CommandResult:
        checksum_result = ReleaseChecksumBuilder(
            self.root,
            options=ReleaseChecksumOptions(artifact=self.options.artifact, version=self.options.version),
        ).build()
        smoke_result = ReleaseSmokeTestBuilder(
            self.root,
            options=ReleaseSmokeTestOptions(
                artifact=self.options.artifact,
                version=self.options.version,
                timeout_seconds=self.options.timeout_seconds,
            ),
        ).build()
        version = ((checksum_result.data or {}).get("summary") or {}).get("version") or _effective_version(self.root, self.options.version)
        checksum_summary = (checksum_result.data or {}).get("summary") or {}
        smoke_summary = (smoke_result.data or {}).get("summary") or {}
        ok = checksum_result.ok and smoke_result.ok
        verification = {
            "schema_version": "1.0.0",
            "verification_id": f"VERIFY-{_safe_version(version)}-{(checksum_summary.get('sha256') or 'missing')[:12]}",
            "release_id": f"DEVPL-{version}",
            "release_version": version,
            "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "artifact": checksum_summary.get("artifact") or smoke_summary.get("artifact") or _to_posix(Path(self.options.artifact)),
            "checksum": (checksum_result.data or {}).get("checksum"),
            "smoke_test": (smoke_result.data or {}).get("smoke_test"),
            "subresults": {
                "checksum_ok": checksum_result.ok,
                "checksum_exit_code": int(checksum_result.exit_code),
                "smoke_test_ok": smoke_result.ok,
                "smoke_test_exit_code": int(smoke_result.exit_code),
            },
            "security": _security_flags(),
            "limitations": [
                "FUNC-SPRINT-81 verifies a real local artifact but does not publish, deploy, sign or tag Git.",
                "Smoke testing is a baseline local check; full install, upgrade and rollback validation are separate future sprints.",
            ],
        }
        summary = {
            "version": version,
            "schema_version": "1.0.0",
            "preliminary": True,
            "artifact": verification["artifact"],
            "artifact_exists": checksum_summary.get("artifact_exists", False),
            "sha256_generated": bool(checksum_summary.get("sha256_generated")),
            "sha256": checksum_summary.get("sha256"),
            "smoke_test_passed": smoke_result.ok,
            "checksum_passed": checksum_result.ok,
            "subchecks_total": 2,
            "subchecks_passed": int(checksum_result.ok) + int(smoke_result.ok),
            "subchecks_failed": 2 - (int(checksum_result.ok) + int(smoke_result.ok)),
            "release_verified": ok,
            "exit_codes_observed": bool(smoke_summary.get("exit_codes_observed")),
            "network_used": False,
            "external_api_used": False,
            "publish_performed": False,
            "deploy_performed": False,
            "git_tagging_performed": False,
            "source_mutations_performed": False,
            "reports_written": False,
        }
        findings = [
            Finding(
                "RELEASE_VERIFICATION_PASS" if ok else "RELEASE_VERIFICATION_BLOCKED",
                "Release verification passed for the local artifact." if ok else "Release verification did not pass for the local artifact.",
                Severity.INFO if ok else Severity.BLOCK,
                metadata={"artifact": verification["artifact"], "release_verified": ok},
            )
        ]
        return CommandResult(
            command="release verify",
            ok=ok,
            exit_code=ExitCode.PASS if ok else ExitCode.BLOCK,
            message="Release verification passed." if ok else "Release verification blocked.",
            data={
                "summary": summary,
                "release_verification": verification,
                "notes": [
                    "FUNC-SPRINT-81 consolidates local checksum and smoke-test evidence.",
                    "The command verifies a real local artifact and does not ignore subprocess exit codes.",
                ],
            },
            findings=findings,
        )


def _effective_version(root: Path, override: str | None) -> str:
    if override:
        return override
    pyproject = root / "pyproject.toml"
    if not pyproject.is_file():
        return "0.0.0"
    try:
        import tomllib

        payload = tomllib.loads(pyproject.read_text(encoding="utf-8"))
        version = (payload.get("project") or {}).get("version")
        return str(version or "0.0.0")
    except Exception:
        return "0.0.0"


def _resolve_artifact(root: Path, artifact: str) -> Path:
    candidate = Path(artifact)
    if not candidate.is_absolute():
        candidate = root / candidate
    return candidate.resolve()


def _validate_artifact_path(root: Path, artifact: Path) -> CommandResult | None:
    try:
        artifact.relative_to(root)
    except ValueError:
        return CommandResult(
            command="release artifact validation",
            ok=False,
            exit_code=ExitCode.BLOCK,
            message="Release artifact must be inside the project workspace.",
            data={"summary": {"artifact": str(artifact), "artifact_exists": artifact.is_file(), "preliminary": True}},
            findings=[Finding("RELEASE_ARTIFACT_OUTSIDE_WORKSPACE", "Artifact path is outside the workspace.", Severity.BLOCK)],
        )
    if not artifact.is_file():
        return CommandResult(
            command="release artifact validation",
            ok=False,
            exit_code=ExitCode.BLOCK,
            message="Release artifact does not exist or is not a file.",
            data={"summary": {"artifact": _to_posix(artifact.relative_to(root)), "artifact_exists": False, "preliminary": True}},
            findings=[Finding("RELEASE_ARTIFACT_MISSING", "Artifact must exist before release verification.", Severity.BLOCK)],
        )
    return None


def _invalid_version_result(command: str, version: str) -> CommandResult:
    return CommandResult(
        command=command,
        ok=False,
        exit_code=ExitCode.ERROR,
        message="Release verification failed because the version is invalid.",
        data={"summary": {"version": version, "valid_version": False, "preliminary": True}},
        findings=[Finding("RELEASE_VERSION_INVALID", "Release version must follow SemVer.", Severity.ERROR, metadata={"version": version})],
    )


def _checksum_metadata(root: Path, artifact: Path) -> dict[str, Any]:
    data = artifact.read_bytes()
    return {
        "path": _to_posix(artifact.relative_to(root)),
        "name": artifact.name,
        "kind": _artifact_kind(artifact),
        "size_bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
    }


def _artifact_kind(path: Path) -> str:
    name = path.name.lower()
    if name.endswith(".whl"):
        return "python-wheel"
    if name.endswith(".tar.gz"):
        return "python-sdist"
    if name.endswith(".zip"):
        return "zip"
    return "file"


def _inspect_artifact_container(root: Path, artifact: Path) -> dict[str, Any]:
    kind = _artifact_kind(artifact)
    if kind in {"zip", "python-wheel"}:
        return _inspect_zip_artifact(root, artifact, kind)
    if kind == "python-sdist":
        return _inspect_tar_artifact(root, artifact)
    return {
        "id": "artifact-container",
        "ok": False,
        "exit_code": 1,
        "message": "Unsupported artifact format for release smoke test.",
        "metadata": {"artifact": _to_posix(artifact.relative_to(root)), "kind": kind},
    }


def _inspect_zip_artifact(root: Path, artifact: Path, kind: str) -> dict[str, Any]:
    try:
        with zipfile.ZipFile(artifact, "r") as archive:
            corrupt = archive.testzip()
            names = sorted(archive.namelist())
    except zipfile.BadZipFile as exc:
        return {
            "id": "artifact-container",
            "ok": False,
            "exit_code": 1,
            "message": "ZIP artifact is not readable.",
            "metadata": {"error": str(exc), "artifact": _to_posix(artifact.relative_to(root))},
        }
    forbidden = [name for name in names if _contains_forbidden_marker(name)]
    required_missing = []
    if kind == "zip":
        required_missing = [marker for marker in _REQUIRED_SOURCE_ZIP_MARKERS if marker not in names]
    elif kind == "python-wheel":
        required_missing = [] if any(name.endswith(".dist-info/WHEEL") for name in names) and any(name.endswith(".dist-info/METADATA") for name in names) else ["*.dist-info/WHEEL", "*.dist-info/METADATA"]
    ok = corrupt is None and not forbidden and not required_missing
    return {
        "id": "artifact-container",
        "ok": ok,
        "exit_code": 0 if ok else 1,
        "message": "Artifact container integrity and safety checks passed." if ok else "Artifact container smoke checks failed.",
        "metadata": {
            "artifact": _to_posix(artifact.relative_to(root)),
            "kind": kind,
            "entries_total": len(names),
            "corrupt_entry": corrupt,
            "forbidden_entries_total": len(forbidden),
            "forbidden_entries_sample": forbidden[:20],
            "required_missing": required_missing,
        },
    }


def _inspect_tar_artifact(root: Path, artifact: Path) -> dict[str, Any]:
    try:
        with tarfile.open(artifact, "r:gz") as archive:
            members = [member.name for member in archive.getmembers()]
    except tarfile.TarError as exc:
        return {
            "id": "artifact-container",
            "ok": False,
            "exit_code": 1,
            "message": "Tar artifact is not readable.",
            "metadata": {"error": str(exc), "artifact": _to_posix(artifact.relative_to(root))},
        }
    forbidden = [name for name in members if _contains_forbidden_marker(_strip_top_level(name))]
    required_missing = [marker for marker in _REQUIRED_SOURCE_ZIP_MARKERS if not any(_strip_top_level(name) == marker for name in members)]
    ok = not forbidden and not required_missing
    return {
        "id": "artifact-container",
        "ok": ok,
        "exit_code": 0 if ok else 1,
        "message": "Tar artifact integrity and safety checks passed." if ok else "Tar artifact smoke checks failed.",
        "metadata": {
            "artifact": _to_posix(artifact.relative_to(root)),
            "kind": "python-sdist",
            "entries_total": len(members),
            "forbidden_entries_total": len(forbidden),
            "forbidden_entries_sample": forbidden[:20],
            "required_missing": required_missing,
        },
    }


def _run_cli_version_smoke(root: Path, *, timeout_seconds: int) -> dict[str, Any]:
    completed = subprocess.run(
        [sys.executable, "-m", "devpilot_core", "--version"],
        cwd=root,
        text=True,
        capture_output=True,
        timeout=timeout_seconds,
        check=False,
    )
    ok = completed.returncode == 0 and "devpilot-local" in completed.stdout
    return {
        "id": "cli-version",
        "ok": ok,
        "exit_code": completed.returncode,
        "message": "CLI version smoke command passed." if ok else "CLI version smoke command failed.",
        "metadata": {
            "command": "python -m devpilot_core --version",
            "stdout": completed.stdout.strip()[:200],
            "stderr": completed.stderr.strip()[:500],
            "timeout_seconds": timeout_seconds,
        },
    }


def _contains_forbidden_marker(name: str) -> bool:
    cleaned = name.replace("\\", "/")
    parts = PurePosixPath(cleaned).parts
    if any(part in {".git", ".venv", "node_modules", "outputs", "dist", "__pycache__", ".pytest_cache"} for part in parts):
        return True
    if cleaned.endswith((".pyc", ".pyo")):
        return True
    return cleaned in {".devpilot/devpilot.db", ".devpilot/providers.yaml"}


def _strip_top_level(name: str) -> str:
    parts = PurePosixPath(name.replace("\\", "/")).parts
    if len(parts) <= 1:
        return name.replace("\\", "/")
    return "/".join(parts[1:])


def _security_flags() -> dict[str, bool]:
    return {
        "network_used": False,
        "external_api_used": False,
        "publish_performed": False,
        "deploy_performed": False,
        "git_tagging_performed": False,
        "signing_performed": False,
        "source_mutations_performed": False,
    }


def checksum_line(result: CommandResult) -> str:
    """Return standard sha256sum text for checksum or verification results."""

    data = result.data or {}
    checksum = (data.get("checksum") or {}).get("artifact") or {}
    if not checksum:
        checksum = (((data.get("release_verification") or {}).get("checksum") or {}).get("artifact") or {})
    digest = checksum.get("sha256")
    path = checksum.get("path")
    if not digest or not path:
        return ""
    return f"{digest}  {path}\n"


def _safe_version(version: str) -> str:
    return re.sub(r"[^0-9A-Za-z_.-]+", "-", version)


def _to_posix(path: Path | str) -> str:
    return str(path).replace("\\", "/")
