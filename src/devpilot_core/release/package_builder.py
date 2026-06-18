from __future__ import annotations

import base64
import hashlib
import json
import re
import tarfile
import tomllib
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity

_SEMVER_RE = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:[-+][0-9A-Za-z.-]+)?$")
_SUPPORTED_KINDS = {"repo-zip", "python", "all"}

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
    ".devpilot/agent_sessions/",
    ".devpilot/providers.yaml",
    ".pyc",
    ".pyo",
]

_SECRET_MARKERS = (
    "private_key",
    "id_rsa",
)

_REPO_ZIP_NAME_TEMPLATE = "devpilot-local-{version}-source.zip"
_SDIST_NAME_TEMPLATE = "devpilot-local-{version}.tar.gz"
_WHEEL_NAME_TEMPLATE = "devpilot_local-{version}-py3-none-any.whl"


@dataclass(frozen=True)
class PackageBuildOptions:
    """Options for FUNC-SPRINT-79 local packaging.

    Packaging is local-first and dry-run-first. By default it produces a build
    plan and audit metadata only. Passing ``execute=True`` writes artifacts
    under ``dist/`` and still does not publish, deploy, tag Git or call network.
    """

    version: str
    kind: str = "repo-zip"
    execute: bool = False
    output_dir: str = "dist"


class PackageBuildBuilder:
    """Build or plan DevPilot release packages in a reproducible, safe way.

    The builder supports a clean repository ZIP and minimal Python sdist/wheel
    artifacts using only the Python standard library. It intentionally avoids
    PyPI publication, external build services, Git tagging and network calls.
    """

    def __init__(self, root: Path, *, options: PackageBuildOptions) -> None:
        self.root = Path(root).resolve()
        self.options = options

    def build(self) -> CommandResult:
        findings: list[Finding] = []
        if not _SEMVER_RE.match(self.options.version):
            findings.append(
                Finding(
                    "PACKAGE_VERSION_INVALID",
                    "Package version must follow SemVer MAJOR.MINOR.PATCH, optionally with prerelease/build metadata.",
                    Severity.ERROR,
                    metadata={"version": self.options.version},
                )
            )
            return CommandResult(
                command="package build",
                ok=False,
                exit_code=ExitCode.ERROR,
                message="Package build failed because the version is invalid.",
                data={"summary": self._summary_template(valid_version=False)},
                findings=findings,
            )
        if self.options.kind not in _SUPPORTED_KINDS:
            findings.append(
                Finding(
                    "PACKAGE_KIND_UNSUPPORTED",
                    "Package kind must be one of repo-zip, python or all.",
                    Severity.ERROR,
                    metadata={"kind": self.options.kind, "supported": sorted(_SUPPORTED_KINDS)},
                )
            )
            return CommandResult(
                command="package build",
                ok=False,
                exit_code=ExitCode.ERROR,
                message="Package build failed because the kind is unsupported.",
                data={"summary": self._summary_template(valid_version=True)},
                findings=findings,
            )

        included, excluded = self._classified_source_files()
        secret_risks = [item for item in included if _looks_like_secret_path(item)]
        if secret_risks:
            findings.append(
                Finding(
                    "PACKAGE_SECRET_RISK_BLOCKED",
                    "Clean package build detected paths that look like secrets in the included file set.",
                    Severity.BLOCK,
                    metadata={"paths": secret_risks[:25], "total": len(secret_risks)},
                )
            )
            return CommandResult(
                command="package build",
                ok=False,
                exit_code=ExitCode.BLOCK,
                message="Package build blocked because included files may contain secrets.",
                data={"summary": self._summary_template(valid_version=True), "included_files": included, "excluded_files": excluded},
                findings=findings,
            )

        outputs: list[dict[str, Any]] = []
        if self.options.kind in {"repo-zip", "all"}:
            outputs.append(self._repo_zip_plan(included))
        if self.options.kind in {"python", "all"}:
            outputs.extend(self._python_package_plans(included))

        written: list[dict[str, Any]] = []
        if self.options.execute:
            for output in outputs:
                if output["id"] == "PKG-CLEAN-ZIP":
                    written.append(self._write_repo_zip(included, output["path"]))
                elif output["id"] == "PKG-SDIST":
                    written.append(self._write_sdist(included, output["path"]))
                elif output["id"] == "PKG-WHEEL":
                    written.append(self._write_wheel(output["path"]))

        package_build = {
            "schema_version": "1.0.0",
            "package_build_id": f"PKG-BUILD-{_safe_version(self.options.version)}-{self.options.kind}",
            "release_id": f"DEVPL-{self.options.version}",
            "release_version": self.options.version,
            "kind": self.options.kind,
            "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "generator": {
                "component": "devpilot_core.release.PackageBuildBuilder",
                "sprint": "FUNC-SPRINT-79",
                "preliminary": True,
            },
            "dry_run": not self.options.execute,
            "execute": self.options.execute,
            "outputs": outputs,
            "written_artifacts": written,
            "included_files": included,
            "excluded_files": excluded,
            "exclusions": {
                "forbidden_markers": _FORBIDDEN_MARKERS,
                "runtime_state_excluded": ".devpilot/devpilot.db" in excluded,
                "local_provider_config_excluded": ".devpilot/providers.yaml" in excluded,
                "outputs_excluded": any(item.startswith("outputs/") for item in excluded),
                "git_excluded": any(item.startswith(".git/") for item in excluded),
                "venv_excluded": any(item.startswith(".venv/") for item in excluded),
                "node_modules_excluded": any(item.startswith("node_modules/") or "/node_modules/" in item for item in excluded),
                "python_caches_excluded": any("__pycache__/" in item or item.endswith((".pyc", ".pyo")) for item in excluded),
            },
            "python_packaging": {
                "strategy": "stdlib-minimal-wheel-and-sdist",
                "build_dependency_required": False,
                "build_dependency_documented": True,
                "pyproject": self._project_metadata(),
            },
            "security": {
                "network_used": False,
                "external_api_used": False,
                "publish_performed": False,
                "deploy_performed": False,
                "git_tagging_performed": False,
                "source_mutations_performed": False,
                "secrets_embedded": False,
            },
            "limitations": [
                "FUNC-SPRINT-79 creates local artifacts only when --execute is used.",
                "The wheel/sdist builder is a first local implementation based on project metadata and source files.",
                "Publication, signing, SBOM, checksums and smoke-install verification remain later Fase G steps.",
            ],
        }
        summary = {
            **self._summary_template(valid_version=True),
            "kind": self.options.kind,
            "dry_run": not self.options.execute,
            "execute": self.options.execute,
            "outputs_total": len(outputs),
            "artifacts_written_total": len(written),
            "included_files_total": len(included),
            "excluded_files_total": len(excluded),
            "repo_zip_supported": self.options.kind in {"repo-zip", "all"},
            "python_package_supported": self.options.kind in {"python", "all"},
            "network_used": False,
            "external_api_used": False,
            "publish_performed": False,
            "deploy_performed": False,
            "source_mutations_performed": False,
            "reports_written": False,
            "preliminary": True,
        }
        findings.append(
            Finding(
                "PACKAGE_BUILD_READY" if not self.options.execute else "PACKAGE_BUILD_ARTIFACTS_CREATED",
                "Package build produced a clean local build plan" + (" and wrote local artifacts." if self.options.execute else "."),
                Severity.INFO,
                metadata={"version": self.options.version, "kind": self.options.kind, "outputs_total": len(outputs)},
            )
        )
        return CommandResult(
            command="package build",
            ok=True,
            exit_code=ExitCode.PASS,
            message="Package build completed." if self.options.execute else "Package build dry-run completed.",
            data={
                "summary": summary,
                "package_build": package_build,
                "notes": [
                    "FUNC-SPRINT-79 introduces local clean packaging only.",
                    "Use --execute to write local artifacts under dist/; publication remains out of scope.",
                    "Outputs/reports are runtime evidence and must not be committed as source artifacts.",
                ],
            },
            findings=findings,
        )

    def _summary_template(self, *, valid_version: bool) -> dict[str, Any]:
        return {
            "version": self.options.version,
            "valid_version": valid_version,
            "schema_version": "1.0.0",
            "preliminary": True,
        }

    def _project_metadata(self) -> dict[str, Any]:
        pyproject = self.root / "pyproject.toml"
        metadata: dict[str, Any] = {"pyproject_path": "pyproject.toml", "pyproject_exists": pyproject.is_file()}
        if not pyproject.is_file():
            return metadata
        payload = tomllib.loads(pyproject.read_text(encoding="utf-8"))
        project = payload.get("project", {})
        build_system = payload.get("build-system", {})
        metadata.update(
            {
                "name": project.get("name"),
                "declared_version": project.get("version"),
                "requires_python": project.get("requires-python"),
                "dependencies": project.get("dependencies", []),
                "optional_dependency_groups": sorted((project.get("optional-dependencies") or {}).keys()),
                "build_backend": build_system.get("build-backend"),
                "build_requires": build_system.get("requires", []),
            }
        )
        return metadata

    def _classified_source_files(self) -> tuple[list[str], list[str]]:
        included: list[str] = []
        excluded: list[str] = []
        for path in sorted(self.root.rglob("*")):
            if not path.is_file():
                continue
            rel = _to_posix(path.relative_to(self.root))
            if _is_excluded(rel):
                excluded.append(rel)
            else:
                included.append(rel)
        return included, excluded

    def _repo_zip_plan(self, included: list[str]) -> dict[str, Any]:
        path = f"dist/release/{_REPO_ZIP_NAME_TEMPLATE.format(version=self.options.version)}"
        return {
            "id": "PKG-CLEAN-ZIP",
            "kind": "clean-source-zip",
            "path": path,
            "files_total": len(included),
            "status": "will-write" if self.options.execute else "planned-dry-run",
            "implemented_in": "FUNC-SPRINT-79",
        }

    def _python_package_plans(self, included: list[str]) -> list[dict[str, Any]]:
        package_files = [item for item in included if item.startswith("src/devpilot_core/") and item.endswith(".py")]
        return [
            {
                "id": "PKG-SDIST",
                "kind": "python-sdist",
                "path": f"dist/{_SDIST_NAME_TEMPLATE.format(version=self.options.version)}",
                "files_total": len(included),
                "status": "will-write" if self.options.execute else "planned-dry-run",
                "implemented_in": "FUNC-SPRINT-79",
            },
            {
                "id": "PKG-WHEEL",
                "kind": "python-wheel",
                "path": f"dist/{_WHEEL_NAME_TEMPLATE.format(version=self.options.version)}",
                "files_total": len(package_files),
                "status": "will-write" if self.options.execute else "planned-dry-run",
                "implemented_in": "FUNC-SPRINT-79",
            },
        ]

    def _write_repo_zip(self, included: list[str], relative_output: str) -> dict[str, Any]:
        output = self.root / relative_output
        output.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(output, mode="w", compression=zipfile.ZIP_DEFLATED) as archive:
            for rel in included:
                archive.write(self.root / rel, rel)
        return _artifact_metadata(self.root, output, "clean-source-zip")

    def _write_sdist(self, included: list[str], relative_output: str) -> dict[str, Any]:
        output = self.root / relative_output
        output.parent.mkdir(parents=True, exist_ok=True)
        root_name = f"devpilot-local-{self.options.version}"
        with tarfile.open(output, mode="w:gz", format=tarfile.PAX_FORMAT) as archive:
            for rel in included:
                archive.add(self.root / rel, arcname=f"{root_name}/{rel}")
        return _artifact_metadata(self.root, output, "python-sdist")

    def _write_wheel(self, relative_output: str) -> dict[str, Any]:
        output = self.root / relative_output
        output.parent.mkdir(parents=True, exist_ok=True)
        metadata = self._project_metadata()
        dist_info = f"devpilot_local-{self.options.version}.dist-info"
        records: list[tuple[str, bytes]] = []

        for path in sorted((self.root / "src" / "devpilot_core").rglob("*.py")):
            rel = _to_posix(path.relative_to(self.root / "src"))
            records.append((rel, path.read_bytes()))

        records.append((f"{dist_info}/METADATA", self._wheel_metadata(metadata).encode("utf-8")))
        records.append((f"{dist_info}/WHEEL", _wheel_file_text().encode("utf-8")))
        records.append((f"{dist_info}/top_level.txt", b"devpilot_core\n"))

        record_rows: list[str] = []
        with zipfile.ZipFile(output, mode="w", compression=zipfile.ZIP_DEFLATED) as archive:
            for arcname, content in records:
                archive.writestr(arcname, content)
                record_rows.append(f"{arcname},sha256={_urlsafe_sha256(content)},{len(content)}")
            record_path = f"{dist_info}/RECORD"
            record_rows.append(f"{record_path},,")
            archive.writestr(record_path, "\n".join(record_rows) + "\n")
        return _artifact_metadata(self.root, output, "python-wheel")

    def _wheel_metadata(self, project: dict[str, Any]) -> str:
        name = project.get("name") or "devpilot-local"
        summary = "Local-first agent-assisted SDLC personal platform"
        requires_python = project.get("requires_python") or ">=3.10"
        lines = [
            "Metadata-Version: 2.1",
            f"Name: {name}",
            f"Version: {self.options.version}",
            f"Summary: {summary}",
            f"Requires-Python: {requires_python}",
        ]
        for dep in project.get("dependencies") or []:
            lines.append(f"Requires-Dist: {dep}")
        return "\n".join(lines) + "\n"


def _is_excluded(rel: str) -> bool:
    rel = rel.replace("\\", "/")
    if rel in {".devpilot/devpilot.db", ".devpilot/providers.yaml"}:
        return True
    if rel.startswith((".devpilot/backups/", ".devpilot/agent_sessions/")):
        return True
    if rel.endswith((".pyc", ".pyo")):
        return True
    parts = rel.split("/")
    if any(part in {".git", ".venv", "node_modules", "outputs", "dist", "__pycache__", ".pytest_cache"} for part in parts):
        return True
    if rel.startswith("repo_DevPilot_Local_") and rel.endswith(".zip"):
        return True
    if _looks_like_secret_path(rel):
        return True
    return False


def _looks_like_secret_path(rel: str) -> bool:
    lower = rel.lower()
    filename = PurePosixPath(rel).name.lower()
    if filename == ".env" or (filename.startswith(".env.") and not filename.endswith(".example")):
        return True
    if filename.endswith((".pem", ".key", ".p12", ".pfx")):
        return True
    if any(part in {"secrets", ".secrets"} for part in PurePosixPath(rel).parts):
        return True
    return any(marker in lower for marker in _SECRET_MARKERS)


def _artifact_metadata(root: Path, path: Path, kind: str) -> dict[str, Any]:
    data = path.read_bytes()
    return {
        "kind": kind,
        "path": _to_posix(path.relative_to(root)),
        "size_bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
    }


def _wheel_file_text() -> str:
    return "\n".join(
        [
            "Wheel-Version: 1.0",
            "Generator: devpilot-core FUNC-SPRINT-79",
            "Root-Is-Purelib: true",
            "Tag: py3-none-any",
            "",
        ]
    )


def _urlsafe_sha256(content: bytes) -> str:
    digest = hashlib.sha256(content).digest()
    return base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")


def _safe_version(version: str) -> str:
    return re.sub(r"[^0-9A-Za-z_.-]+", "-", version)


def _to_posix(path: Path) -> str:
    return path.as_posix()
