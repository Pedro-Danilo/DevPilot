from __future__ import annotations

import hashlib
import json
import os
import subprocess
import tomllib
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.release.manifest import ReleaseManifestBuilder, ReleaseManifestOptions
from devpilot_core.release.artifact_manifest import ReleaseArtifactManifestBuilder, ReleaseArtifactManifestOptions
from devpilot_core.schemas.validator import SchemaValidator
from devpilot_core.release.package_builder import PackageBuildBuilder, PackageBuildOptions
from devpilot_core.release.reproducibility_pack import ReleaseReproducibilityPackBuilder, ReleaseReproducibilityPackOptions
from devpilot_core.release.sbom import ReleaseSbomBuilder
from devpilot_core.release.source_zip_policy import SourceZipPolicyOptions, SourceZipReleasePolicyValidator

RELEASE_PACKAGE_ROLES = {"owner", "release-manager"}
RUNTIME_DIR = Path("outputs/runtime/gsdlc11b_release_package")
RELEASE_DIR = Path("outputs/release/gsdlc11b")


@dataclass(frozen=True)
class GitAuthority:
    commit: str
    tree: str
    branch: str
    dirty_tracked: bool

    def to_dict(self) -> dict[str, Any]:
        return {"commit": self.commit, "tree": self.tree, "branch": self.branch, "dirty_tracked": self.dirty_tracked}


class ReleasePackageJobApplicationService:
    """GSDLC-11-B typed local release-package orchestration.

    This service composes the existing PackageBuildBuilder, ReleaseManifest,
    SourceZip policy, SBOM and reproducibility verifier.  It never accepts shell
    text, never publishes, and writes only excluded runtime/release artifacts.
    """

    def __init__(self, platform_root: Path, *, context_resolver) -> None:
        self.root = Path(platform_root).resolve()
        self.context_resolver = context_resolver
        self.runtime_dir = self.root / RUNTIME_DIR
        self.release_dir = self.root / RELEASE_DIR

    def status(self, *, actor: str, actor_roles: Iterable[str], workspace_scopes: Iterable[str]) -> CommandResult:
        checked = self._authorize("release package status", actor_roles, workspace_scopes, require_release_role=False)
        if checked is not None:
            return checked
        receipt = self._read_json(self.runtime_dir / "job_result.json") or self._read_json(self.runtime_dir / "plan.json")
        return CommandResult(
            command="release package status",
            ok=True,
            exit_code=ExitCode.PASS,
            message="Release package status projected.",
            data={"release_package": receipt or {"state": "NOT_PLANNED"}, "safety": self._safety(mutated=False)},
            findings=[Finding("GSDLC11B_RELEASE_PACKAGE_STATUS_PASS", "Release package status is available from local governed evidence.", Severity.INFO)],
        )

    def plan(self, *, actor: str, actor_roles: Iterable[str], workspace_scopes: Iterable[str]) -> CommandResult:
        command = "release package plan"
        checked = self._authorize(command, actor_roles, workspace_scopes, require_release_role=True)
        if checked is not None:
            return checked
        authority = self._git_authority()
        if authority is None or authority.dirty_tracked:
            return self._block(command, "GSDLC11B_GIT_AUTHORITY_BLOCK", "Release package planning requires a clean tracked Git authority.")
        precondition = self._precondition()
        if precondition is not None:
            return precondition
        unsafe = self._unsafe_source_links()
        if unsafe:
            return self._block(command, "GSDLC11B_SOURCE_LINK_ESCAPE_BLOCK", "Release package planning blocks included symlink/junction/path-escape source entries.", {"entries": unsafe})
        version = self._project_version()
        dry = PackageBuildBuilder(self.root, options=PackageBuildOptions(version=version, kind="repo-zip", execute=False)).build()
        if not dry.ok:
            return self._wrap_block(command, dry, "GSDLC11B_PACKAGE_DRY_RUN_BLOCK")
        plan_core = {
            "schema_version": "1.0.0",
            "operation": "release.package.execute",
            "release_version": version,
            "source_authority": authority.to_dict(),
            "package_kind": "repo-zip",
            "expected_package_path": f"dist/release/devpilot-local-{version}-source.zip",
            "dry_run": True,
            "network_used": False,
            "external_api_used": False,
            "publish_performed": False,
            "deploy_performed": False,
            "arbitrary_shell_used": False,
        }
        plan_hash = _canonical_hash(plan_core)
        plan_id = f"GSDLC11B-PKG-{authority.commit[:12]}-{plan_hash[:12]}"
        plan = {**plan_core, "plan_id": plan_id, "plan_hash": plan_hash, "created_at_utc": _now()}
        self._write_json(self.runtime_dir / "plan.json", plan)
        return CommandResult(command=command, ok=True, exit_code=ExitCode.PASS, message="Release package dry-run plan created.", data={"plan": plan, "package_build": dry.data, "safety": self._safety(mutated=False)}, findings=[Finding("GSDLC11B_PACKAGE_PLAN_PASS", "Typed release package dry-run plan is commit/tree-bound.", Severity.INFO, metadata={"plan_id": plan_id, "commit": authority.commit, "tree": authority.tree})])

    def execute(self, *, actor: str, actor_roles: Iterable[str], workspace_scopes: Iterable[str], plan_id: str, plan_hash: str) -> CommandResult:
        command = "release package execute"
        checked = self._authorize(command, actor_roles, workspace_scopes, require_release_role=True)
        if checked is not None:
            return checked
        plan = self._read_json(self.runtime_dir / "plan.json")
        if not plan or plan.get("plan_id") != plan_id or plan.get("plan_hash") != plan_hash:
            return self._block(command, "GSDLC11B_PLAN_BINDING_BLOCK", "Execute requires the exact current typed package plan id/hash.")
        expected_core = {k: v for k, v in plan.items() if k not in {"plan_id", "plan_hash", "created_at_utc"}}
        if _canonical_hash(expected_core) != plan_hash:
            return self._block(command, "GSDLC11B_PLAN_HASH_BLOCK", "Stored package plan hash no longer matches its immutable content.")
        authority = self._git_authority()
        if authority is None or authority.dirty_tracked:
            return self._block(command, "GSDLC11B_GIT_AUTHORITY_BLOCK", "Release package execution requires a clean tracked Git authority.")
        if authority.commit != plan["source_authority"]["commit"] or authority.tree != plan["source_authority"]["tree"]:
            return self._block(command, "GSDLC11B_ARTIFACT_COMMIT_BINDING_BLOCK", "Git commit/tree changed after planning; package execution is stale.", {"planned": plan["source_authority"], "current": authority.to_dict()})
        unsafe = self._unsafe_source_links()
        if unsafe:
            return self._block(command, "GSDLC11B_SOURCE_LINK_ESCAPE_BLOCK", "Release package execution blocks included symlink/junction/path-escape source entries.", {"entries": unsafe})
        prior = self._read_json(self.runtime_dir / "job_result.json")
        if prior and prior.get("status") == "PASS" and prior.get("source_authority") == authority.to_dict() and self._receipt_artifacts_valid(prior):
            return CommandResult(command=command, ok=True, exit_code=ExitCode.PASS, message="Release package execution reused prior hash-bound PASS evidence.", data={"release_package": prior, "reused": True, "safety": self._safety(mutated=True)}, findings=[Finding("GSDLC11B_PACKAGE_EXECUTE_REUSED_PASS", "Existing commit-bound release package evidence remains intact; execution was not repeated.", Severity.INFO)])

        version = str(plan["release_version"])
        first = PackageBuildBuilder(self.root, options=PackageBuildOptions(version=version, kind="repo-zip", execute=True)).build()
        if not first.ok:
            return self._wrap_block(command, first, "GSDLC11B_PACKAGE_BUILD_BLOCK")
        artifact = _written_zip(first)
        if artifact is None:
            return self._block(command, "GSDLC11B_PACKAGE_ARTIFACT_MISSING_BLOCK", "Package builder did not produce the governed source ZIP.")
        package_path = self.root / str(artifact["path"])
        first_sha = _sha256_file(package_path)
        first_size = package_path.stat().st_size
        second = PackageBuildBuilder(self.root, options=PackageBuildOptions(version=version, kind="repo-zip", execute=True)).build()
        if not second.ok:
            return self._wrap_block(command, second, "GSDLC11B_PACKAGE_SECOND_DERIVATION_BLOCK")
        second_sha = _sha256_file(package_path)
        if first_sha != second_sha:
            return self._block(command, "GSDLC11B_PACKAGE_NONDETERMINISTIC_BLOCK", "Two equivalent source-package derivations produced different SHA-256 values.", {"first": first_sha, "second": second_sha})

        policy_result = SourceZipReleasePolicyValidator(self.root, SourceZipPolicyOptions(artifact=str(artifact["path"]), write_report=True)).run()
        if not policy_result.ok:
            return self._wrap_block(command, policy_result, "GSDLC11B_SOURCE_ZIP_POLICY_BLOCK")

        sbom1 = ReleaseSbomBuilder(self.root).build()
        if not sbom1.ok:
            return self._wrap_block(command, sbom1, "GSDLC11B_SBOM_BLOCK")
        sbom_payload1 = dict((sbom1.data or {}).get("sbom") or {})
        sbom2 = ReleaseSbomBuilder(self.root).build()
        sbom_payload2 = dict((sbom2.data or {}).get("sbom") or {})
        sbom_sem1 = _semantic_sbom(sbom_payload1)
        sbom_sem2 = _semantic_sbom(sbom_payload2)
        if _canonical_hash(sbom_sem1) != _canonical_hash(sbom_sem2):
            return self._block(command, "GSDLC11B_SBOM_NONDETERMINISTIC_BLOCK", "Equivalent SBOM derivations differ after permitted timestamp-noise normalization.")

        manifest1 = ReleaseManifestBuilder(self.root, options=ReleaseManifestOptions(version=version)).build()
        if not manifest1.ok:
            return self._wrap_block(command, manifest1, "GSDLC11B_RELEASE_MANIFEST_BLOCK")
        release_manifest = dict((manifest1.data or {}).get("release_manifest") or (manifest1.data or {}).get("manifest") or {})

        self.release_dir.mkdir(parents=True, exist_ok=True)
        sbom_path = self.root / "outputs/reports/sbom.json"
        release_manifest_path = self.root / "outputs/reports/release_manifest.json"
        sbom_path.parent.mkdir(parents=True, exist_ok=True)
        release_manifest_path.parent.mkdir(parents=True, exist_ok=True)
        sbom_path.write_text(json.dumps(sbom_payload1, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        release_manifest_path.write_text(json.dumps(release_manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

        sbom_schema = SchemaValidator(self.root).validate(schema="GSDLC11BSbomBaseline", instance=sbom_path)
        if not sbom_schema.ok:
            return self._wrap_block(command, sbom_schema, "GSDLC11B_SBOM_SCHEMA_BLOCK")

        base_manifest_result = ReleaseArtifactManifestBuilder(
            self.root,
            options=ReleaseArtifactManifestOptions(
                version=version,
                policy_path=".devpilot/release/gsdlc11b_artifact_manifest_policy.json",
                output_json="outputs/release/gsdlc11b/base_artifact_manifest.json",
                output_markdown="outputs/release/gsdlc11b/base_artifact_manifest.md",
                output_checksums="outputs/release/gsdlc11b/base_checksums.sha256",
                verify_checksums=True,
                write_report=True,
            ),
        ).build()
        if not base_manifest_result.ok:
            return self._wrap_block(command, base_manifest_result, "GSDLC11B_BASE_ARTIFACT_MANIFEST_BLOCK")
        base_manifest_path = self.root / "outputs/release/gsdlc11b/base_artifact_manifest.json"
        base_manifest_schema = SchemaValidator(self.root).validate(schema="ReleaseArtifactManifest", instance=base_manifest_path)
        if not base_manifest_schema.ok:
            return self._wrap_block(command, base_manifest_schema, "GSDLC11B_BASE_ARTIFACT_SCHEMA_BLOCK")

        repro = ReleaseReproducibilityPackBuilder(self.root, options=ReleaseReproducibilityPackOptions(write_report=True, verify_after_build=True, require_clean_git=True)).build()
        if not repro.ok:
            return self._wrap_block(command, repro, "GSDLC11B_REPRODUCIBILITY_VERIFIER_BLOCK")

        checksums = {
            str(artifact["path"]): first_sha,
            _rel(self.root, sbom_path): _sha256_file(sbom_path),
            _rel(self.root, release_manifest_path): _sha256_file(release_manifest_path),
            _rel(self.root, base_manifest_path): _sha256_file(base_manifest_path),
        }
        checksums_path = self.release_dir / "checksums.sha256"
        checksums_path.write_text("".join(f"{digest}  {path}\n" for path, digest in sorted(checksums.items())), encoding="utf-8")
        comparison = {
            "status": "PASS",
            "package_sha256_first": first_sha,
            "package_sha256_second": second_sha,
            "package_byte_reproducible": first_sha == second_sha,
            "sbom_semantic_sha256_first": _canonical_hash(sbom_sem1),
            "sbom_semantic_sha256_second": _canonical_hash(sbom_sem2),
            "sbom_semantically_reproducible": _canonical_hash(sbom_sem1) == _canonical_hash(sbom_sem2),
            "normalized_noise": ["generated_at_utc", "cyclonedx.metadata.timestamp"],
        }
        comparison_path = self.release_dir / "reproducibility_comparison.json"
        comparison_path.write_text(json.dumps(comparison, indent=2) + "\n", encoding="utf-8")

        artifact_manifest = {
            "schema_version": "1.0.0",
            "manifest_id": f"DEVPL-GSDLC-11-B-{authority.commit[:12]}",
            "status": "PASS",
            "generated_at_utc": _now(),
            "source_authority": authority.to_dict(),
            "artifact": {"path": str(artifact["path"]), "sha256": first_sha, "size_bytes": first_size, "file_count": int(artifact.get("files_total") or len((first.data or {}).get("package_build", {}).get("included_files", [])))},
            "included_files_total": len((first.data or {}).get("package_build", {}).get("included_files", [])),
            "excluded_files_total": len((first.data or {}).get("package_build", {}).get("excluded_files", [])),
            "exclusions": dict((first.data or {}).get("package_build", {}).get("exclusions") or {}),
            "checksums": {"path": _rel(self.root, checksums_path), "sha256": _sha256_file(checksums_path), "entries": checksums},
            "sbom": {"path": _rel(self.root, sbom_path), "sha256": _sha256_file(sbom_path), "format": "CycloneDX-compatible baseline", "coverage": "declared local dependencies only; no vulnerability/license certification", "schema_validation": "PASS"},
            "release_manifest": {"path": _rel(self.root, release_manifest_path), "sha256": _sha256_file(release_manifest_path)},
            "base_artifact_manifest": {"path": _rel(self.root, base_manifest_path), "sha256": _sha256_file(base_manifest_path), "schema_validation": "PASS", "checksums_verified": bool(((base_manifest_result.data or {}).get("manifest") or {}).get("checksums", {}).get("verified"))},
            "reproducibility": {"path": _rel(self.root, comparison_path), **comparison},
            "existing_stack": ["PackageBuildBuilder", "SourceZipReleasePolicyValidator", "ReleaseManifestBuilder", "ReleaseSbomBuilder", "ReleaseReproducibilityPackBuilder", "ReleaseReproducibilityVerifier"],
            "provenance": {"job_type": "release.package.execute", "actor": actor, "typed_operation": True, "arbitrary_shell": False},
            "safety": self._safety(mutated=True),
            "limitations": ["SBOM is an implemented local dependency inventory baseline, not SCA, vulnerability scanning, license certification or signed attestation.", "No publish, upload, signing, remote build or deploy is performed by GSDLC-11-B."],
        }
        manifest_path = self.release_dir / "release_artifact_manifest.json"
        manifest_path.write_text(json.dumps(artifact_manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        manifest_schema = SchemaValidator(self.root).validate(schema="GSDLC11BReleaseArtifactManifest", instance=manifest_path)
        if not manifest_schema.ok:
            return self._wrap_block(command, manifest_schema, "GSDLC11B_ARTIFACT_MANIFEST_SCHEMA_BLOCK")
        result = {**artifact_manifest, "artifacts": {"release_artifact_manifest": _rel(self.root, manifest_path), "package": str(artifact["path"]), "checksums": _rel(self.root, checksums_path), "sbom": _rel(self.root, sbom_path), "release_manifest": _rel(self.root, release_manifest_path), "base_artifact_manifest": _rel(self.root, base_manifest_path), "reproducibility_comparison": _rel(self.root, comparison_path)}, "job_log": {"events": ["plan-bound", "git-authority-revalidated", "package-derived-twice", "source-zip-policy-pass", "sbom-schema-pass", "base-artifact-manifest-pass", "reproducibility-verifier-pass", "checksums-written", "artifact-manifest-schema-pass"], "secrets_redacted": True}}
        self._write_json(self.runtime_dir / "job_result.json", result)
        return CommandResult(command=command, ok=True, exit_code=ExitCode.PASS, message="Commit-bound reproducible local release package generated and verified.", data={"release_package": result, "reused": False, "safety": self._safety(mutated=True)}, findings=[Finding("GSDLC11B_PACKAGE_EXECUTE_PASS", "Source package, SHA-256, SBOM and reproducibility evidence are commit/tree-bound and local-only.", Severity.INFO, metadata={"commit": authority.commit, "artifact_sha256": first_sha})])

    def _authorize(self, command: str, actor_roles: Iterable[str], workspace_scopes: Iterable[str], *, require_release_role: bool) -> CommandResult | None:
        context = self.context_resolver.resolve()
        if not context.configured or not context.valid or context.active_workspace_root is None or not context.active_workspace_id:
            return self._block(command, "GSDLC11B_PROJECT_CONTEXT_BLOCK", "Release package workbench requires a server-validated active project workspace.")
        scopes = {str(item) for item in workspace_scopes if str(item).strip()}
        workspace_id = str(context.active_workspace_id)
        if scopes and workspace_id not in scopes and "*" not in scopes:
            return self._block(command, "GSDLC11B_WORKSPACE_SCOPE_BLOCK", "Authenticated session is not scoped to the active workspace.")
        roles = {str(item).strip() for item in actor_roles if str(item).strip()}
        if require_release_role and not roles.intersection(RELEASE_PACKAGE_ROLES):
            return self._block(command, "GSDLC11B_RELEASE_ROLE_BLOCK", "Release package plan/execute requires owner or release-manager server-side role.")
        return None

    def _precondition(self) -> CommandResult | None:
        state = self._read_json(self.root / ".devpilot/project_state.json") or {}
        if state.get("gsdlc_11_a_status") != "CLOSED/PASS/WINDOWS-VALIDATED" or state.get("gsdlc_11_b_authorized") is not True:
            return self._block("release package plan", "GSDLC11B_PREDECESSOR_BLOCK", "GSDLC-11-B requires GSDLC-11-A CLOSED/PASS/WINDOWS-VALIDATED and explicit authorization.")
        if int(state.get("gsdlc_11_full_regression_budget_consumed") or 0) != 0:
            return self._block("release package plan", "GSDLC11B_FULL_BUDGET_BLOCK", "GSDLC-11-B must not consume the GSDLC-11 Full Regression budget.")
        return None

    def _git_authority(self) -> GitAuthority | None:
        def run(*args: str) -> str | None:
            completed = subprocess.run(["git", "-C", str(self.root), *args], capture_output=True, text=True, check=False)
            return completed.stdout.strip() if completed.returncode == 0 else None
        commit = run("rev-parse", "HEAD")
        tree = run("rev-parse", "HEAD^{tree}")
        branch = run("branch", "--show-current") or "DETACHED"
        status = run("status", "--porcelain", "--untracked-files=no")
        if not commit or not tree or status is None:
            return None
        return GitAuthority(commit=commit, tree=tree, branch=branch, dirty_tracked=bool(status.strip()))

    def _project_version(self) -> str:
        data = tomllib.loads((self.root / "pyproject.toml").read_text(encoding="utf-8"))
        return str((data.get("project") or {}).get("version") or "0.1.0")

    def _unsafe_source_links(self) -> list[dict[str, str]]:
        unsafe: list[dict[str, str]] = []
        excluded_parts = {".git", ".venv", "node_modules", "outputs", "dist", "__pycache__", ".pytest_cache"}
        root = self.root.resolve()
        for current, dirs, files in os.walk(self.root, followlinks=False):
            base = Path(current)
            for name in list(dirs) + list(files):
                path = base / name
                rel = path.relative_to(self.root).as_posix()
                if any(part in excluded_parts for part in Path(rel).parts):
                    continue
                junction = bool(getattr(os.path, "isjunction", lambda value: False)(path))
                if path.is_symlink() or junction:
                    unsafe.append({"path": rel, "reason": "symlink-or-junction"})
                    continue
                try:
                    path.resolve().relative_to(root)
                except (OSError, ValueError):
                    unsafe.append({"path": rel, "reason": "path-escape"})
        return sorted(unsafe, key=lambda row: row["path"])

    def _receipt_artifacts_valid(self, receipt: dict[str, Any]) -> bool:
        artifacts = receipt.get("artifacts") or {}
        manifest_rel = artifacts.get("release_artifact_manifest")
        if not manifest_rel:
            return False
        manifest = self._read_json(self.root / str(manifest_rel))
        if not manifest or manifest.get("status") != "PASS":
            return False
        for key in ("package", "checksums", "sbom", "release_manifest", "reproducibility_comparison"):
            rel = artifacts.get(key)
            if not rel or not (self.root / str(rel)).is_file():
                return False
        package = self.root / str(artifacts["package"])
        return _sha256_file(package) == str((receipt.get("artifact") or {}).get("sha256") or "")

    def _safety(self, *, mutated: bool) -> dict[str, Any]:
        return {"local_first": True, "network_used": False, "external_api_used": False, "publish_performed": False, "deploy_performed": False, "source_mutations_performed": False, "runtime_artifacts_written": mutated, "arbitrary_shell_used": False, "secrets_exposed": False}

    def _wrap_block(self, command: str, result: CommandResult, finding_id: str) -> CommandResult:
        return CommandResult(command=command, ok=False, exit_code=ExitCode.BLOCK, message=result.message, data={"upstream": result.to_dict(), "safety": self._safety(mutated=False)}, findings=[Finding(finding_id, result.message, Severity.BLOCK)])

    def _block(self, command: str, finding_id: str, message: str, metadata: dict[str, Any] | None = None) -> CommandResult:
        return CommandResult(command=command, ok=False, exit_code=ExitCode.BLOCK, message=message, data={"safety": self._safety(mutated=False)}, findings=[Finding(finding_id, message, Severity.BLOCK, metadata=metadata or {})])

    @staticmethod
    def _read_json(path: Path) -> dict[str, Any] | None:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None
        return payload if isinstance(payload, dict) else None

    @staticmethod
    def _write_json(path: Path, payload: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_name(path.name + ".tmp")
        tmp.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        tmp.replace(path)


def _written_zip(result: CommandResult) -> dict[str, Any] | None:
    build = dict((result.data or {}).get("package_build") or {})
    for row in build.get("written_artifacts") or []:
        if isinstance(row, dict) and row.get("kind") == "clean-source-zip":
            enriched = dict(row)
            included = build.get("included_files") or []
            enriched["files_total"] = len(included)
            return enriched
    return None


def _semantic_sbom(payload: dict[str, Any]) -> dict[str, Any]:
    value = json.loads(json.dumps(payload))
    value.pop("generated_at_utc", None)
    cyclonedx = value.get("cyclonedx")
    if isinstance(cyclonedx, dict) and isinstance(cyclonedx.get("metadata"), dict):
        cyclonedx["metadata"].pop("timestamp", None)
    return value


def _canonical_hash(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")).hexdigest()


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _rel(root: Path, path: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
