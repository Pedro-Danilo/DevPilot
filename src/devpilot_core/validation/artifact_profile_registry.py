from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.schemas import SchemaValidator
from devpilot_core.validators.artifact_profiles import ARTIFACT_PROFILES, GENERIC_MARKDOWN_PROFILE, ArtifactProfile

DEFAULT_ARTIFACT_PROFILES_PATH = "docs/validation/artifact_profiles.json"


class ArtifactProfileRegistry:
    """Load Markdown artifact validation profiles from versioned JSON data.

    FUNC-SPRINT-24 reduces hardcoding by introducing
    `docs/validation/artifact_profiles.json` as the primary source for profile
    selection. The original Python profiles remain a safe fallback during the
    migration window, so readiness and artifact validation do not break when the
    JSON catalog is temporarily unavailable or invalid.

    The registry does not validate document semantics. It only loads and selects
    profile metadata used by the existing Markdown artifact validator.
    """

    def __init__(self, root: Path, catalog_path: str | Path = DEFAULT_ARTIFACT_PROFILES_PATH) -> None:
        self.root = Path(root)
        self.catalog_path = Path(catalog_path)

    @property
    def resolved_catalog_path(self) -> Path:
        return self.root / self.catalog_path

    def load_payload(self) -> dict[str, Any]:
        return json.loads(self.resolved_catalog_path.read_text(encoding="utf-8"))

    def load_profiles(self, *, allow_fallback: bool = True) -> tuple[tuple[ArtifactProfile, ...], ArtifactProfile, bool]:
        """Return profiles, generic profile and whether fallback was used."""

        try:
            payload = self.load_payload()
            profiles = tuple(self._profile_from_dict(item) for item in payload.get("profiles", []))
            generic = self._profile_from_dict(payload.get("generic_profile", {}))
            if not profiles:
                raise ValueError("artifact_profiles.json must contain at least one profile")
            return profiles, generic, False
        except Exception:
            if not allow_fallback:
                raise
            return ARTIFACT_PROFILES, GENERIC_MARKDOWN_PROFILE, True

    def select(self, path: Path) -> ArtifactProfile:
        """Select the most specific profile for one Markdown artifact path."""

        profiles, generic, _ = self.load_profiles(allow_fallback=True)
        normalized_path = self._normalize_path(path)
        path_name = Path(normalized_path).name

        for profile in profiles:
            if profile.filename and profile.filename != path_name:
                continue
            if all(fragment in normalized_path for fragment in profile.path_contains):
                return profile

        for profile in profiles:
            if profile.filename is not None:
                continue
            if all(fragment in normalized_path for fragment in profile.path_contains):
                return profile

        return generic

    def status(self) -> CommandResult:
        """Validate and summarize the data-driven artifact profile registry."""

        findings: list[Finding] = []
        path_display = str(self.catalog_path).replace("\\", "/")
        if not self.resolved_catalog_path.exists():
            findings.append(Finding(id="ARTIFACT_PROFILE_CATALOG_MISSING", message="Artifact profile catalog is missing.", severity=Severity.BLOCK, path=path_display))
            return self._result(False, ExitCode.BLOCK, "Artifact profile catalog is missing.", {}, findings)

        schema_result = SchemaValidator(self.root).validate(schema="ArtifactProfiles", instance=self.resolved_catalog_path)
        findings.extend(schema_result.findings)
        if not schema_result.ok:
            return self._result(False, schema_result.exit_code, "Artifact profile catalog failed schema validation.", {"schema_result": schema_result.to_dict()}, findings)

        try:
            profiles, generic, fallback_used = self.load_profiles(allow_fallback=False)
        except Exception as exc:
            findings.append(Finding(id="ARTIFACT_PROFILE_CATALOG_INVALID", message=f"Artifact profile catalog could not be loaded: {exc}", severity=Severity.ERROR, path=path_display))
            return self._result(False, ExitCode.ERROR, "Artifact profile catalog could not be loaded.", {}, findings)

        profile_ids = [profile.id for profile in profiles]
        duplicate_ids = sorted(item for item, count in Counter(profile_ids).items() if count > 1)
        for profile_id in duplicate_ids:
            findings.append(Finding(id="ARTIFACT_PROFILE_DUPLICATE_ID", message=f"Duplicate artifact profile id detected: {profile_id}", severity=Severity.BLOCK, metadata={"profile_id": profile_id}))

        python_ids = {profile.id for profile in ARTIFACT_PROFILES}
        json_ids = set(profile_ids)
        missing_from_json = sorted(python_ids - json_ids)
        extra_in_json = sorted(json_ids - python_ids)
        for profile_id in missing_from_json:
            findings.append(Finding(id="ARTIFACT_PROFILE_MISSING_FROM_JSON", message=f"Python profile is missing from JSON catalog: {profile_id}", severity=Severity.BLOCK, metadata={"profile_id": profile_id}))

        for profile_id in extra_in_json:
            findings.append(Finding(id="ARTIFACT_PROFILE_EXTRA_IN_JSON", message=f"JSON profile has no Python fallback counterpart: {profile_id}", severity=Severity.WARNING, metadata={"profile_id": profile_id}))

        blocking = any(f.severity in {Severity.FAIL, Severity.BLOCK, Severity.ERROR} for f in findings)
        data = {
            "summary": {
                "catalog_path": path_display,
                "profiles_total": len(profiles),
                "python_profiles_total": len(ARTIFACT_PROFILES),
                "generic_profile_id": generic.id,
                "duplicate_ids": duplicate_ids,
                "missing_from_json": missing_from_json,
                "extra_in_json": extra_in_json,
                "fallback_used": fallback_used,
                "preliminary": True,
            },
            "profiles": [self._profile_to_dict(profile) for profile in profiles],
            "generic_profile": self._profile_to_dict(generic),
            "notes": [
                "FUNC-SPRINT-24 uses JSON artifact profiles as primary data.",
                "Python artifact_profiles.py remains a conservative fallback during migration.",
            ],
        }
        if not blocking:
            findings.append(Finding(id="ARTIFACT_PROFILE_REGISTRY_PASS", message="Artifact profile registry passed compatibility validation.", severity=Severity.INFO, metadata=data["summary"]))
        return CommandResult(
            command="artifact profile registry",
            ok=not blocking,
            exit_code=ExitCode.PASS if not blocking else ExitCode.BLOCK,
            message="Artifact profile registry passed." if not blocking else "Artifact profile registry blocked.",
            data=data,
            findings=findings,
        )

    def _result(self, ok: bool, exit_code: ExitCode, message: str, data: dict[str, Any], findings: list[Finding]) -> CommandResult:
        payload = dict(data or {})
        payload.setdefault("summary", {"catalog_path": str(self.catalog_path).replace("\\", "/"), "preliminary": True})
        return CommandResult(command="artifact profile registry", ok=ok, exit_code=exit_code, message=message, data=payload, findings=findings)

    def _normalize_path(self, path: Path) -> str:
        candidate = path
        try:
            candidate = path.resolve().relative_to(self.root.resolve())
        except ValueError:
            candidate = path
        return str(candidate).replace("\\", "/")

    @staticmethod
    def _profile_from_dict(item: dict[str, Any]) -> ArtifactProfile:
        return ArtifactProfile(
            id=str(item.get("id", "")).strip(),
            description=str(item.get("description", "")).strip(),
            filename=item.get("filename") if item.get("filename") not in {"", None} else None,
            path_contains=tuple(str(value) for value in item.get("path_contains", [])),
            required_headings=tuple(str(value) for value in item.get("required_headings", [])),
            recommended_headings=tuple(str(value) for value in item.get("recommended_headings", [])),
        )

    @staticmethod
    def _profile_to_dict(profile: ArtifactProfile) -> dict[str, Any]:
        return {
            "id": profile.id,
            "description": profile.description,
            "filename": profile.filename,
            "path_contains": list(profile.path_contains),
            "required_headings": list(profile.required_headings),
            "recommended_headings": list(profile.recommended_headings),
        }
