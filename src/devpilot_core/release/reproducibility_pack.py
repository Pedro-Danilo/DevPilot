from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.release.archive_manifest import SourceArchiveManifestBuilder, SourceArchiveManifestOptions
from devpilot_core.release.environment import ReleaseEnvironmentSnapshotBuilder, ReleaseEnvironmentSnapshotOptions
from devpilot_core.release.reproducibility_policy import ReleaseReproducibilityPolicyValidator
from devpilot_core.release.reproducibility_verify import ReleaseReproducibilityVerifier, ReleaseReproducibilityVerifyOptions

DEFAULT_PACK_JSON = Path("outputs/release/reproducibility_pack.json")
DEFAULT_PACK_MARKDOWN = Path("outputs/release/reproducibility_pack.md")


@dataclass(frozen=True)
class ReleaseReproducibilityPackOptions:
    """Options for POST-H-017-E local release reproducibility pack generation."""

    write_report: bool = False
    verify_after_build: bool = False
    require_clean_git: bool = False
    output_json: Path | str = DEFAULT_PACK_JSON
    output_markdown: Path | str = DEFAULT_PACK_MARKDOWN


class ReleaseReproducibilityPackBuilder:
    """Generate a local dry-run ReleaseReproducibilityPack and optional verifier evidence.

    POST-H-017-E intentionally produces local evidence only. It writes under
    ``outputs/release`` when requested, never publishes, deploys, tags, signs
    remotely, calls network services, reads secrets or mutates source files.
    """

    def __init__(self, root: Path, *, options: ReleaseReproducibilityPackOptions | None = None) -> None:
        self.root = Path(root).resolve()
        self.options = options or ReleaseReproducibilityPackOptions()

    def build(self) -> CommandResult:
        findings: list[Finding] = []
        policy_result = ReleaseReproducibilityPolicyValidator(self.root).run()
        findings.extend(_prefixed_findings(policy_result.findings, prefix="POLICY"))
        if not policy_result.ok:
            return self._blocked("Release reproducibility pack blocked by policy.", findings)

        environment_result = ReleaseEnvironmentSnapshotBuilder(
            self.root,
            options=ReleaseEnvironmentSnapshotOptions(write_report=self.options.write_report),
        ).build()
        findings.extend(_prefixed_findings(environment_result.findings, prefix="ENVIRONMENT"))
        if not environment_result.ok:
            return self._blocked("Release reproducibility pack blocked by environment snapshot.", findings)

        source_archive_result = SourceArchiveManifestBuilder(
            self.root,
            options=SourceArchiveManifestOptions(write_report=self.options.write_report),
        ).build()
        findings.extend(_prefixed_findings(source_archive_result.findings, prefix="SOURCE_ARCHIVE"))
        if not source_archive_result.ok:
            return self._blocked("Release reproducibility pack blocked by source archive manifest.", findings)

        git_state = _git_state(self.root)
        if git_state["dirty"] is True and self.options.require_clean_git:
            findings.append(
                Finding(
                    "RELEASE_REPRODUCIBILITY_PACK_DIRTY_REPO",
                    "Current Git checkout is dirty; DevPilot will not declare a reproducible release pack.",
                    Severity.BLOCK,
                    metadata=git_state,
                )
            )
            return self._blocked("Release reproducibility pack blocked by dirty Git state.", findings)
        if git_state["dirty"] is True:
            findings.append(
                Finding(
                    "RELEASE_REPRODUCIBILITY_PACK_DIRTY_REPO_ADVISORY",
                    "Current Git checkout is dirty; generated pack remains implemented-initial and must not be promoted as verified-local.",
                    Severity.WARNING,
                    metadata=git_state,
                )
            )

        pack = self._pack(git_state)
        reports: dict[str, str] = {}
        if self.options.write_report:
            reports = self._write_outputs(pack)

        verifier_result: CommandResult | None = None
        if self.options.verify_after_build and self.options.write_report:
            verifier_result = ReleaseReproducibilityVerifier(
                self.root,
                options=ReleaseReproducibilityVerifyOptions(pack=self.options.output_json, write_report=True),
            ).verify()
            findings.extend(_prefixed_findings(verifier_result.findings, prefix="VERIFIER"))

        blocking = _blocking_findings(findings)
        summary = self._summary(
            pack=pack,
            reports=reports,
            verifier_result=verifier_result,
            findings_total=len(findings),
            blocking_findings_total=len(blocking),
        )
        data: dict[str, Any] = {
            "summary": summary,
            "pack": pack,
            "notes": [
                "POST-H-017-E generates a local dry-run reproducibility pack and can verify it immediately.",
                "The pack is implemented-initial evidence, not publication, deployment, remote signature, SLSA attestation or supply-chain certification.",
            ],
        }
        if reports:
            data["reports"] = reports
        if verifier_result is not None:
            data["verification"] = verifier_result.to_dict()

        ok = not blocking and (verifier_result.ok if verifier_result is not None else True)
        return CommandResult(
            command="release reproducibility-pack",
            ok=ok,
            exit_code=ExitCode.PASS if ok else ExitCode.BLOCK,
            message="Release reproducibility pack generated." if ok else "Release reproducibility pack generation blocked.",
            data=data,
            findings=findings
            or [
                Finding(
                    "RELEASE_REPRODUCIBILITY_PACK_CREATED",
                    "Local release reproducibility pack was generated.",
                    Severity.INFO,
                    metadata=summary,
                )
            ],
        )

    def _pack(self, git_state: dict[str, Any]) -> dict[str, Any]:
        return {
            "schema_version": "1.0",
            "schema_id": "SCHEMA-DEVPL-RELEASE-REPRODUCIBILITY-PACK-V1",
            "pack_id": f"devpilot-release-reproducibility-{datetime.now(timezone.utc).strftime('%Y%m%d')}",
            "created_by": "POST-H-017-A",
            "status": "implemented-initial",
            "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
            "git": {
                "commit": git_state["commit"] or "HEAD",
                "branch": git_state["branch"],
                "dirty": False,
                "archive_method": "source-archive-manifest",
                "source_archive_required": True,
                "git_metadata_required": True,
            },
            "validation": {
                "pytest_summary": "not-run-in-pack",
                "quality_gate_hardening": "not-run-in-pack",
                "test_contracts": "not-run-in-pack",
                "test_contracts_v2": "not-run-in-pack",
                "docs_governance": "not-run-in-pack",
                "industrial_readiness": "not-run-in-pack",
            },
            "artifacts": {
                "changelog": "docs/release/CHANGELOG.md",
                "manifest": "outputs/reports/release_manifest.json",
                "sbom": "outputs/reports/sbom.json",
                "checksums": "outputs/release/source_archive_checksums.sha256",
                "environment_snapshot": "outputs/release/environment_snapshot.json",
                "source_archive_manifest": "outputs/release/source_archive_manifest.json",
            },
            "exclusions": [
                "outputs/",
                ".devpilot/devpilot.db",
                ".devpilot/agent_sessions/",
                ".venv/",
                "node_modules/",
            ],
            "policy": {
                "policy_id": "devpilot-release-reproducibility-policy",
                "policy_path": ".devpilot/release/reproducibility_policy.json",
                "runtime_artifacts_forbidden": True,
                "dirty_repo_blocks_reproducible_release": True,
                "secret_free_required": True,
                "dry_run_only": True,
            },
            "safety": {
                "local_first": True,
                "dry_run": True,
                "published": False,
                "deployed": False,
                "network_used": False,
                "external_api_used": False,
                "remote_execution_used": False,
                "connector_write_used": False,
                "plugin_execution_used": False,
                "mutations_performed": False,
                "source_mutations_performed": False,
                "secrets_included": False,
            },
            "preliminary": True,
        }

    def _write_outputs(self, pack: dict[str, Any]) -> dict[str, str]:
        json_path = _resolve(self.root, self.options.output_json)
        markdown_path = _resolve(self.root, self.options.output_markdown)
        _ensure_inside_root(self.root, json_path)
        _ensure_inside_root(self.root, markdown_path)
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(json.dumps(pack, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        markdown_path.write_text(_render_markdown(pack), encoding="utf-8")
        return {
            "json": _display(self.root, json_path),
            "markdown": _display(self.root, markdown_path),
        }

    def _summary(
        self,
        *,
        pack: dict[str, Any],
        reports: dict[str, str],
        verifier_result: CommandResult | None,
        findings_total: int,
        blocking_findings_total: int,
    ) -> dict[str, Any]:
        verification_summary = dict((verifier_result.data or {}).get("summary") or {}) if verifier_result else {}
        return {
            "created_by": "POST-H-017-E",
            "status": "implemented-initial",
            "preliminary": True,
            "pack_id": pack["pack_id"],
            "pack_status": pack["status"],
            "schema_id": pack["schema_id"],
            "pack_written": bool(reports),
            "output_json": reports.get("json"),
            "output_markdown": reports.get("markdown"),
            "verify_after_build": verifier_result is not None,
            "current_git_dirty_advisory": pack.get("git", {}).get("dirty") is False and bool(_git_state(self.root).get("dirty")),
            "require_clean_git": self.options.require_clean_git,
            "release_reproducibility_verified": bool(verification_summary.get("release_reproducibility_verified")) if verifier_result else False,
            "forbidden_entries_total": verification_summary.get("forbidden_entries_total"),
            "checksum_mismatches_total": verification_summary.get("checksum_mismatches_total"),
            "checksum_missing_files_total": verification_summary.get("checksum_missing_files_total"),
            "findings_total": findings_total,
            "blocking_findings_total": blocking_findings_total,
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
        }

    def _blocked(self, message: str, findings: list[Finding]) -> CommandResult:
        return CommandResult(
            command="release reproducibility-pack",
            ok=False,
            exit_code=ExitCode.BLOCK,
            message=message,
            data={
                "summary": {
                    "created_by": "POST-H-017-E",
                    "status": "implemented-initial",
                    "preliminary": True,
                    "pack_written": False,
                    "findings_total": len(findings),
                    "blocking_findings_total": len(_blocking_findings(findings)),
                    "network_used": False,
                    "external_api_used": False,
                    "source_mutations_performed": False,
                }
            },
            findings=findings,
        )


def _git_state(root: Path) -> dict[str, Any]:
    if not (root / ".git").exists():
        return {"git_metadata_available": False, "commit": "HEAD", "branch": None, "dirty": False}
    commit = subprocess.run(["git", "rev-parse", "--verify", "HEAD"], cwd=root, text=True, capture_output=True, check=False)
    branch = subprocess.run(["git", "branch", "--show-current"], cwd=root, text=True, capture_output=True, check=False)
    status = subprocess.run(["git", "status", "--porcelain"], cwd=root, text=True, capture_output=True, check=False)
    return {
        "git_metadata_available": commit.returncode == 0,
        "commit": commit.stdout.strip() if commit.returncode == 0 else "HEAD",
        "branch": branch.stdout.strip() if branch.returncode == 0 and branch.stdout.strip() else None,
        "dirty": bool(status.stdout.strip()) if status.returncode == 0 else True,
    }


def _prefixed_findings(findings: list[Finding], *, prefix: str) -> list[Finding]:
    return [
        Finding(
            id=f"{prefix}_{finding.id}",
            message=finding.message,
            severity=finding.severity,
            path=finding.path,
            metadata=finding.metadata,
        )
        for finding in findings
    ]


def _blocking_findings(findings: list[Finding]) -> list[Finding]:
    return [finding for finding in findings if finding.severity in {Severity.BLOCK, Severity.ERROR, Severity.FAIL}]


def _resolve(root: Path, value: Path | str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else root / path


def _display(root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def _ensure_inside_root(root: Path, path: Path) -> None:
    path.resolve().relative_to(root.resolve())


def _render_markdown(pack: dict[str, Any]) -> str:
    git = pack.get("git") or {}
    artifacts = pack.get("artifacts") or {}
    return "\n".join(
        [
            "# Release reproducibility pack",
            "",
            "Estado: `implemented-initial`.",
            "",
            "## Resumen",
            "",
            f"- `pack_id`: `{pack.get('pack_id')}`",
            f"- `status`: `{pack.get('status')}`",
            f"- `commit`: `{git.get('commit')}`",
            f"- `dirty`: `{git.get('dirty')}`",
            "",
            "## Artefactos",
            "",
            *[f"- `{key}`: `{value}`" for key, value in artifacts.items()],
            "",
            "## Límites",
            "",
            "- Evidencia local dry-run; no publica, no despliega y no firma remoto.",
            "- No sustituye una attestation supply-chain ni una certificación SLSA.",
            "",
        ]
    )
