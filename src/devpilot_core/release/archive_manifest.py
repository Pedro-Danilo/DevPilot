from __future__ import annotations

import hashlib
import io
import json
import subprocess
import tarfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.release.reproducibility_policy import DEFAULT_POLICY_PATH, ReleaseReproducibilityPolicyValidator

SOURCE_ARCHIVE_ROOTS = (
    ".devpilot",
    "docs",
    "evals",
    "src",
    "tests",
    "ui",
)

SOURCE_ARCHIVE_ROOT_FILES = (
    ".gitignore",
    "README.md",
    "pyproject.toml",
)

CRITICAL_ARTIFACTS = (
    "README.md",
    "pyproject.toml",
    ".devpilot/project_state.json",
    ".devpilot/release/reproducibility_policy.json",
    ".devpilot/testing/test_contract_registry.json",
    ".devpilot/testing/test_contract_registry_v2.json",
    "docs/05_operations/runbook.md",
    "docs/05_operations/release_reproducibility_runbook.md",
    "docs/backlogs/POST-H-017_release_reproducibility_pack.md",
    "docs/release/CHANGELOG.md",
    "docs/schemas/schema_catalog.json",
    "docs/schemas/release_reproducibility_pack.schema.json",
    "docs/schemas/release_environment_snapshot.schema.json",
    "docs/schemas/release_source_archive_manifest.schema.json",
    "docs/schemas/release_reproducibility_verification.schema.json",
    "src/devpilot_core/cli.py",
    "src/devpilot_core/release/archive_manifest.py",
    "src/devpilot_core/release/environment.py",
    "src/devpilot_core/release/reproducibility_pack.py",
    "src/devpilot_core/release/reproducibility_policy.py",
    "src/devpilot_core/release/reproducibility_verify.py",
    "tests/test_post_h_017_release_reproducibility_pack.py",
    "tests/test_post_h_017_reproducibility_verify.py",
    "ui/web/package.json",
)


@dataclass(frozen=True)
class SourceArchiveManifestOptions:
    """Options for POST-H-017-C source archive manifest generation.

    The builder is local-first and read-only with respect to project sources.
    `write_report=True` writes generated evidence under `outputs/release/`.
    Test code may inject `archive_entries_override` to validate blocking cases
    without requiring a Git checkout in the delivered clean ZIP.
    """

    write_report: bool = False
    policy_path: Path | str = DEFAULT_POLICY_PATH
    output_json: Path | str = Path("outputs/release/source_archive_manifest.json")
    output_markdown: Path | str = Path("outputs/release/source_archive_manifest.md")
    output_checksums: Path | str = Path("outputs/release/source_archive_checksums.sha256")
    archive_entries_override: tuple[str, ...] | None = None
    include_files: bool = True


class SourceArchiveManifestBuilder:
    """Build POST-H-017-C evidence for source archive contents and checksums."""

    def __init__(self, root: Path, *, options: SourceArchiveManifestOptions | None = None) -> None:
        self.root = Path(root).resolve()
        self.options = options or SourceArchiveManifestOptions()

    def build(self) -> CommandResult:
        policy_result = ReleaseReproducibilityPolicyValidator(self.root, policy_path=self.options.policy_path).run()
        if not policy_result.ok:
            return CommandResult(
                command="release source-archive-manifest",
                ok=False,
                exit_code=ExitCode.BLOCK,
                message="Release source archive manifest blocked by reproducibility policy.",
                data={"summary": self._summary(None, reports_written=False, findings_total=len(policy_result.findings) or 1, blocking_findings_total=len(policy_result.findings) or 1)},
                findings=policy_result.findings,
            )

        policy = dict((policy_result.data or {}).get("policy") or {})
        forbidden_patterns = _normal_patterns(policy.get("forbidden_archive_entries") or policy.get("critical_exclusions") or [])
        exclusions = _normal_patterns(policy.get("critical_exclusions") or [])
        archive = self._archive_entries()
        included_files = archive["entries"]
        forbidden_entries = _matched_entries(included_files, forbidden_patterns)
        checksums = self._critical_artifact_checksums(included_files)
        manifest = {
            "schema_version": "1.0",
            "schema_id": "SCHEMA-DEVPL-RELEASE-SOURCE-ARCHIVE-MANIFEST-V1",
            "manifest_id": "devpilot-release-source-archive-manifest",
            "created_by": "POST-H-017-C",
            "status": "implemented-initial",
            "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
            "archive": {
                "method": archive["method"],
                "git_metadata_available": archive["git_metadata_available"],
                "git_archive_checked": archive["git_archive_checked"],
                "fallback_used": archive["fallback_used"],
                "entries_total": len(included_files),
                "entries_sha256": _list_digest(included_files),
                "entries": included_files if self.options.include_files else [],
            },
            "exclusions": {
                "critical_exclusions": exclusions,
                "forbidden_archive_entries": forbidden_patterns,
                "forbidden_entries_detected": forbidden_entries,
                "forbidden_entries_total": len(forbidden_entries),
            },
            "critical_artifacts": {
                "required": list(CRITICAL_ARTIFACTS),
                "present_total": len([item for item in checksums if item["exists"]]),
                "missing_total": len([item for item in checksums if not item["exists"]]),
                "sha256": checksums,
                "checksums_sha256": _checksums_digest(checksums),
            },
            "safety": {
                "local_first": True,
                "dry_run": True,
                "read_only": True,
                "network_used": False,
                "external_api_used": False,
                "remote_execution_used": False,
                "connector_write_used": False,
                "plugin_execution_used": False,
                "mutations_performed": False,
                "source_mutations_performed": False,
                "secrets_included": False,
                "env_files_read": False,
                "secret_values_read": False,
            },
            "preliminary": True,
        }

        reports: dict[str, str] = {}
        if self.options.write_report:
            reports = self._write_outputs(manifest, checksums)

        blocking = len(forbidden_entries)
        summary = self._summary(manifest, reports_written=bool(reports), findings_total=1, blocking_findings_total=blocking)
        finding = Finding(
            "RELEASE_SOURCE_ARCHIVE_FORBIDDEN_ENTRIES"
            if blocking
            else "RELEASE_SOURCE_ARCHIVE_MANIFEST_CREATED",
            "Source archive manifest includes forbidden runtime/build/cache entries."
            if blocking
            else "Source archive manifest and critical artifact checksums were generated.",
            Severity.BLOCK if blocking else Severity.INFO,
            metadata=summary,
        )
        data: dict[str, Any] = {
            "summary": summary,
            "manifest": manifest,
            "notes": [
                "POST-H-017-C produces source archive evidence and critical artifact checksums only.",
                "The local verifier and release-reproducibility quality gate remain POST-H-017-D/E scope.",
            ],
        }
        if reports:
            data["reports"] = reports
        return CommandResult(
            command="release source-archive-manifest",
            ok=blocking == 0,
            exit_code=ExitCode.PASS if blocking == 0 else ExitCode.BLOCK,
            message="Release source archive manifest generated." if blocking == 0 else "Release source archive manifest blocked by forbidden entries.",
            data=data,
            findings=[finding],
        )

    def _archive_entries(self) -> dict[str, Any]:
        if self.options.archive_entries_override is not None:
            return {
                "method": "test-override",
                "git_metadata_available": False,
                "git_archive_checked": False,
                "fallback_used": False,
                "entries": sorted({_normalize_rel(value) for value in self.options.archive_entries_override if value}),
            }

        git_archive = self._git_archive_head_entries()
        if git_archive is not None:
            git_archive["entries"] = _filter_source_archive_entries(git_archive["entries"])
            return git_archive
        return {
            "method": "deterministic-source-archive-plan",
            "git_metadata_available": False,
            "git_archive_checked": False,
            "fallback_used": True,
            "entries": _iter_source_archive_candidates(self.root),
        }

    def _git_archive_head_entries(self) -> dict[str, Any] | None:
        if not (self.root / ".git").exists():
            return None
        completed = subprocess.run(
            ["git", "archive", "--format=tar", "HEAD"],
            cwd=self.root,
            capture_output=True,
            check=False,
        )
        if completed.returncode != 0:
            return None
        try:
            with tarfile.open(fileobj=io.BytesIO(completed.stdout), mode="r:") as archive:
                entries = sorted(_normalize_rel(name) for name in archive.getnames() if name and not name.endswith("/"))
        except tarfile.TarError:
            return None
        return {
            "method": "git-archive-head-in-memory",
            "git_metadata_available": True,
            "git_archive_checked": True,
            "fallback_used": False,
            "entries": entries,
        }

    def _critical_artifact_checksums(self, included_files: list[str]) -> list[dict[str, Any]]:
        included = set(included_files)
        checksums: list[dict[str, Any]] = []
        for relative in CRITICAL_ARTIFACTS:
            path = self.root / relative
            exists = path.is_file()
            checksums.append(
                {
                    "path": relative,
                    "exists": exists,
                    "included_in_archive": relative in included,
                    "sha256": _sha256_file(path) if exists else None,
                    "size_bytes": path.stat().st_size if exists else None,
                }
            )
        return checksums

    def _write_outputs(self, manifest: dict[str, Any], checksums: list[dict[str, Any]]) -> dict[str, str]:
        json_path = self.root / self.options.output_json
        md_path = self.root / self.options.output_markdown
        checksum_path = self.root / self.options.output_checksums
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        md_path.write_text(self.render_markdown(manifest), encoding="utf-8")
        checksum_path.write_text(_render_checksums(checksums), encoding="utf-8")
        return {
            "json": str(self.options.output_json).replace("\\", "/"),
            "markdown": str(self.options.output_markdown).replace("\\", "/"),
            "checksums": str(self.options.output_checksums).replace("\\", "/"),
        }

    def render_markdown(self, manifest: dict[str, Any]) -> str:
        summary = self._summary(manifest, reports_written=False, findings_total=1, blocking_findings_total=manifest["exclusions"]["forbidden_entries_total"])
        lines = [
            "# Release source archive manifest",
            "",
            "Estado: `implemented-initial`.",
            "",
            "Este reporte fue generado por POST-H-017-C como evidencia local de archivos fuente y checksums críticos.",
            "",
            "## Resumen",
            "",
        ]
        for key, value in summary.items():
            lines.append(f"- `{key}`: `{value}`")
        lines.extend(
            [
                "",
                "## Seguridad",
                "",
                "- `local_first`: `true`",
                "- `dry_run`: `true`",
                "- `network_used`: `false`",
                "- `external_api_used`: `false`",
                "- `secrets_included`: `false`",
                "",
                "Limitación: el verifier local y el quality gate release-reproducibility quedan para POST-H-017-D/E.",
                "",
            ]
        )
        return "\n".join(lines)

    def _summary(self, manifest: dict[str, Any] | None, *, reports_written: bool, findings_total: int, blocking_findings_total: int) -> dict[str, Any]:
        archive = (manifest or {}).get("archive") if isinstance(manifest, dict) else {}
        exclusions = (manifest or {}).get("exclusions") if isinstance(manifest, dict) else {}
        artifacts = (manifest or {}).get("critical_artifacts") if isinstance(manifest, dict) else {}
        return {
            "created_by": "POST-H-017-C",
            "status": "implemented-initial",
            "preliminary": True,
            "schema_id": "SCHEMA-DEVPL-RELEASE-SOURCE-ARCHIVE-MANIFEST-V1",
            "manifest_id": (manifest or {}).get("manifest_id") if isinstance(manifest, dict) else None,
            "archive_method": (archive or {}).get("method"),
            "git_metadata_available": bool((archive or {}).get("git_metadata_available")),
            "git_archive_checked": bool((archive or {}).get("git_archive_checked")),
            "fallback_used": bool((archive or {}).get("fallback_used")),
            "included_files_total": int((archive or {}).get("entries_total") or 0),
            "forbidden_entries_total": int((exclusions or {}).get("forbidden_entries_total") or 0),
            "critical_artifacts_present_total": int((artifacts or {}).get("present_total") or 0),
            "critical_artifacts_missing_total": int((artifacts or {}).get("missing_total") or 0),
            "checksums_generated": bool((artifacts or {}).get("sha256")),
            "local_first": True,
            "read_only": True,
            "dry_run": True,
            "network_used": False,
            "external_api_used": False,
            "shell_used": False,
            "mutations_performed": False,
            "source_mutations_performed": False,
            "remote_execution_enabled": False,
            "connector_write_enabled": False,
            "plugin_execution_enabled": False,
            "secrets_included": False,
            "reports_written": reports_written,
            "output_json": str(self.options.output_json).replace("\\", "/") if reports_written else None,
            "output_markdown": str(self.options.output_markdown).replace("\\", "/") if reports_written else None,
            "output_checksums": str(self.options.output_checksums).replace("\\", "/") if reports_written else None,
            "findings_total": findings_total,
            "blocking_findings_total": blocking_findings_total,
        }


def _iter_source_archive_candidates(root: Path) -> list[str]:
    candidates: list[str] = []
    for file_name in SOURCE_ARCHIVE_ROOT_FILES:
        path = root / file_name
        if path.is_file():
            candidates.append(file_name)
    for prefix in SOURCE_ARCHIVE_ROOTS:
        base = root / prefix
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if path.is_file() and not _is_source_archive_excluded(_rel(root, path)):
                candidates.append(_rel(root, path))
    return sorted(set(candidates))


def _filter_source_archive_entries(entries: list[str]) -> list[str]:
    return sorted({_normalize_rel(entry) for entry in entries if entry and not _is_source_archive_excluded(entry)})


def _is_source_archive_excluded(path: str) -> bool:
    normalized = _normalize_rel(path)
    parts = set(normalized.split("/"))
    if parts & {"__pycache__", ".pytest_cache", "node_modules", ".venv", "dist", "outputs"}:
        return True
    return any(
        normalized == marker.rstrip("/") or normalized.startswith(marker)
        for marker in (
            ".devpilot/backups/",
            ".devpilot/agent_sessions/",
            ".devpilot/devpilot.db",
        )
    )


def _matched_entries(entries: list[str], patterns: list[str]) -> list[dict[str, Any]]:
    matches = []
    for entry in entries:
        matched = [pattern for pattern in patterns if _matches_pattern(entry, pattern)]
        if matched:
            matches.append({"path": entry, "patterns": matched})
    return matches


def _matches_pattern(path: str, pattern: str) -> bool:
    rel = _normalize_rel(path)
    normal = _normalize_rel(pattern).rstrip("/")
    if not normal:
        return False
    if pattern.endswith("/"):
        return rel == normal or rel.startswith(f"{normal}/")
    if normal.startswith("*."):
        return rel.endswith(normal[1:])
    return rel == normal or rel.startswith(f"{normal}/")


def _normal_patterns(raw: list[Any]) -> list[str]:
    return sorted({_normalize_rel(str(value)) for value in raw if str(value).strip()})


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _list_digest(values: list[str]) -> str:
    return hashlib.sha256("\n".join(sorted(values)).encode("utf-8")).hexdigest()


def _checksums_digest(records: list[dict[str, Any]]) -> str:
    lines = [f"{item['sha256']}  {item['path']}" for item in records if item.get("sha256")]
    return hashlib.sha256("\n".join(sorted(lines)).encode("utf-8")).hexdigest()


def _render_checksums(records: list[dict[str, Any]]) -> str:
    lines = [f"{item['sha256']}  {item['path']}" for item in records if item.get("sha256")]
    return "\n".join(lines) + ("\n" if lines else "")


def _normalize_rel(value: str) -> str:
    normalized = value.replace("\\", "/")
    while normalized.startswith("./"):
        normalized = normalized[2:]
    return normalized


def _rel(root: Path, path: Path) -> str:
    return _normalize_rel(str(path.resolve().relative_to(root)))
