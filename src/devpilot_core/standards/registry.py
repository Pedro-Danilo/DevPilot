from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity, exit_code_for_findings
from devpilot_core.standards.catalog import REQUIRED_PROJECT_ARTIFACTS, REQUIRED_STANDARDS, RequiredProjectArtifact, RequiredStandard
from devpilot_core.validators.artifact_profiles import ARTIFACT_PROFILES
from devpilot_core.validators.frontmatter import parse_frontmatter_file


@dataclass(frozen=True)
class StandardStatus:
    """Discovery result for one internal standard."""

    id: str
    title: str
    directory: str
    exists: bool
    required_files: list[dict[str, Any]]
    markdown_files: int
    json_files: int
    templates: int
    checklists: int
    schemas: int
    adrs: int
    status: str | None = None
    version: str | None = None

    @property
    def ok(self) -> bool:
        return self.exists and all(item["exists"] for item in self.required_files)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "directory": self.directory,
            "exists": self.exists,
            "ok": self.ok,
            "status": self.status,
            "version": self.version,
            "required_files": self.required_files,
            "counts": {
                "markdown_files": self.markdown_files,
                "json_files": self.json_files,
                "templates": self.templates,
                "checklists": self.checklists,
                "schemas": self.schemas,
                "adrs": self.adrs,
            },
        }


class StandardsRegistry:
    """Local registry for MIPSoftware and MIASI.

    The registry discovers versioned standards under `docs/standards`, checks
    whether their required files are present, and exposes the approved DevPilot
    project artifacts that those standards require.

    FUNC-SPRINT-04 deliberately keeps the registry local and deterministic:
    it reads files from disk only, does not call any external service, and does
    not require an LLM or API key.
    """

    def __init__(self, root: Path) -> None:
        self.root = root

    def discover_standard(self, standard: RequiredStandard) -> StandardStatus:
        directory = self.root / standard.directory
        exists = directory.exists() and directory.is_dir()
        required_files: list[dict[str, Any]] = []

        for rel in standard.required_files:
            path = directory / rel
            required_files.append(
                {
                    "path": f"{standard.directory}/{rel}".replace("\\", "/"),
                    "exists": path.exists() and path.is_file(),
                    "size_bytes": path.stat().st_size if path.exists() and path.is_file() else 0,
                }
            )

        markdown_files = len(list(directory.rglob("*.md"))) if exists else 0
        json_files = len(list(directory.rglob("*.json"))) if exists else 0
        templates = len(list((directory / "templates").glob("*.md"))) if (directory / "templates").exists() else 0
        checklists = len(list((directory / "checklists").glob("*.md"))) if (directory / "checklists").exists() else 0
        schemas = len(list((directory / "schemas").glob("*.json"))) if (directory / "schemas").exists() else 0
        adrs = len(list((directory / "adrs").glob("*.md"))) if (directory / "adrs").exists() else 0

        status: str | None = None
        version: str | None = None
        readme = directory / "README.md"
        if readme.exists() and readme.is_file():
            try:
                document = parse_frontmatter_file(readme)
                status = str(document.frontmatter.get("status", "") or "") or None
                version = str(document.frontmatter.get("version", "") or "") or None
            except Exception:
                # Frontmatter errors are reported by dedicated validators. The
                # registry must keep discovery robust and non-throwing.
                status = None
                version = None

        return StandardStatus(
            id=standard.id,
            title=standard.title,
            directory=standard.directory,
            exists=exists,
            required_files=required_files,
            markdown_files=markdown_files,
            json_files=json_files,
            templates=templates,
            checklists=checklists,
            schemas=schemas,
            adrs=adrs,
            status=status,
            version=version,
        )

    def discover_standards(self) -> list[StandardStatus]:
        return [self.discover_standard(standard) for standard in REQUIRED_STANDARDS]

    def project_artifact_status(self, artifact: RequiredProjectArtifact) -> dict[str, Any]:
        path = self.root / artifact.path
        return {
            "id": artifact.id,
            "path": artifact.path,
            "standard": artifact.standard,
            "purpose": artifact.purpose,
            "exists": path.exists() and path.is_file(),
            "size_bytes": path.stat().st_size if path.exists() and path.is_file() else 0,
        }

    def required_project_artifacts(self) -> list[dict[str, Any]]:
        return [self.project_artifact_status(artifact) for artifact in REQUIRED_PROJECT_ARTIFACTS]

    def validation_profiles(self) -> list[dict[str, Any]]:
        try:
            from devpilot_core.validation.artifact_profile_registry import ArtifactProfileRegistry

            profiles, _, fallback_used = ArtifactProfileRegistry(self.root).load_profiles(allow_fallback=True)
        except Exception:
            profiles = ARTIFACT_PROFILES
            fallback_used = True
        return [
            {
                "id": profile.id,
                "description": profile.description,
                "filename": profile.filename,
                "path_contains": list(profile.path_contains),
                "required_headings": list(profile.required_headings),
                "recommended_headings": list(profile.recommended_headings),
                "source": "python-fallback" if fallback_used else "docs/validation/artifact_profiles.json",
            }
            for profile in profiles
        ]


def build_standards_status_result(root: Path) -> CommandResult:
    """Build a normalized status report for the local standards registry."""

    registry = StandardsRegistry(root)
    standards = registry.discover_standards()
    project_artifacts = registry.required_project_artifacts()
    profiles = registry.validation_profiles()

    findings: list[Finding] = []

    for standard in standards:
        if not standard.exists:
            findings.append(
                Finding(
                    id="STANDARD_DIRECTORY_MISSING",
                    message=f"Required standard directory is missing: {standard.directory}",
                    severity=Severity.BLOCK,
                    path=standard.directory,
                    metadata={"standard": standard.id},
                )
            )
            continue

        for item in standard.required_files:
            if not item["exists"]:
                findings.append(
                    Finding(
                        id="STANDARD_REQUIRED_FILE_MISSING",
                        message=f"Required standard file is missing: {item['path']}",
                        severity=Severity.FAIL,
                        path=item["path"],
                        metadata={"standard": standard.id},
                    )
                )

    for artifact in project_artifacts:
        if not artifact["exists"]:
            findings.append(
                Finding(
                    id="PROJECT_REQUIRED_ARTIFACT_MISSING",
                    message=f"Required project artifact is missing: {artifact['path']}",
                    severity=Severity.FAIL,
                    path=artifact["path"],
                    metadata={"standard": artifact["standard"], "artifact_id": artifact["id"]},
                )
            )

    exit_code = exit_code_for_findings(findings)
    ok = exit_code == ExitCode.PASS

    return CommandResult(
        command="standards status",
        ok=ok,
        exit_code=exit_code,
        message="Standards registry status passed." if ok else "Standards registry status failed.",
        data={
            "standards_root": "docs/standards",
            "standards": [standard.to_dict() for standard in standards],
            "required_project_artifacts": project_artifacts,
            "validation_profiles": profiles,
            "summary": {
                "standards_total": len(standards),
                "standards_ok": sum(1 for standard in standards if standard.ok),
                "required_project_artifacts_total": len(project_artifacts),
                "required_project_artifacts_present": sum(1 for artifact in project_artifacts if artifact["exists"]),
                "validation_profiles_total": len(profiles),
            },
        },
        findings=findings,
    )
