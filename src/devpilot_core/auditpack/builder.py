from __future__ import annotations

import hashlib
import json
import re
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.identity import IdentityRegistry, IdentityRegistryOptions, RbacCheckInput
from devpilot_core.policy import PathGuard, SecretGuard
from devpilot_core.policy.decisions import PolicyEffect

_AUDITPACK_DIR = Path("outputs/auditpacks")
_MANIFEST_NAME = "audit-pack-manifest.json"
_DEFAULT_ACTOR = "local-owner"

_FORBIDDEN_EXACT = {
    ".devpilot/devpilot.db",
    ".devpilot/providers.yaml",
    ".env",
}
_FORBIDDEN_PARTS = {
    ".git",
    ".venv",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    "dist",
}
_FORBIDDEN_PREFIXES = (
    "outputs/auditpacks/",
    ".devpilot/agent_sessions/",
    ".devpilot/backups/",
)
_SECRET_SUFFIXES = (".pem", ".key", ".p12", ".pfx")
_TEXT_SUFFIXES = {
    ".md",
    ".txt",
    ".json",
    ".yaml",
    ".yml",
    ".toml",
    ".csv",
    ".sha256",
    ".example",
}


@dataclass(frozen=True)
class AuditPackBuildOptions:
    """Options for FUNC-SPRINT-96 audit pack creation.

    Audit packs are local collaboration artifacts. The builder writes a ZIP under
    ``outputs/auditpacks`` and intentionally excludes runtime DBs, env files,
    provider secrets, agent sessions, build outputs and VCS internals. The pack
    contains checksummed evidence only: manifests, changelog, audit docs, selected
    MIASI/registry metadata and optional local reports when present.
    """

    actor: str | None = _DEFAULT_ACTOR
    output_dir: str = "outputs/auditpacks"
    include_reports: bool = True
    include_runtime_db: bool = False
    confirm_include_runtime_db: bool = False


@dataclass(frozen=True)
class AuditPackVerifyOptions:
    """Options for local audit pack integrity verification."""

    path: str


class AuditPackBuilder:
    """Build and verify governed local audit packs for offline collaboration.

    The implementation is intentionally metadata-first and local-only. It does
    not upload artifacts, does not call cloud services, does not read secrets and
    does not include runtime SQLite state unless a future ADR introduces a
    stronger export policy. In FUNC-SPRINT-96, even explicit DB export flags are
    blocked to keep the first version conservative.
    """

    def __init__(self, root: Path) -> None:
        self.root = Path(root).resolve()
        self.path_guard = PathGuard(self.root)
        self.secret_guard = SecretGuard()

    def build(self, options: AuditPackBuildOptions | None = None) -> CommandResult:
        options = options or AuditPackBuildOptions()
        findings: list[Finding] = []
        rbac_result = self._rbac_check(options.actor, action="audit-pack.build", subject="audit-pack")
        if not rbac_result.ok:
            return rbac_result
        if options.include_runtime_db:
            finding = Finding(
                "AUDIT_PACK_RUNTIME_DB_EXPORT_BLOCKED",
                "Runtime DB export is blocked in the implemented-initial audit pack builder; export only evidence metadata.",
                Severity.BLOCK,
                path=".devpilot/devpilot.db",
                metadata={"include_runtime_db": True, "confirm_include_runtime_db": bool(options.confirm_include_runtime_db)},
            )
            return CommandResult(
                "audit-pack build",
                False,
                ExitCode.BLOCK,
                "Audit pack build blocked because runtime DB export is not enabled in Sprint 96.",
                data={"summary": self._base_summary(options, entries_total=0, files_included=0, blocked_findings_total=1)},
                findings=[finding],
            )

        candidates = self._collect_candidates(include_reports=options.include_reports)
        entries: list[dict[str, Any]] = []
        payloads: list[tuple[str, bytes]] = []
        redactions_total = 0

        for rel in candidates:
            absolute = self.root / rel
            decision = self.path_guard.evaluate(rel, action="read")
            if decision.effect == PolicyEffect.BLOCK:
                findings.append(decision.to_finding())
                continue
            blocked_reason = _blocked_reason(rel)
            if blocked_reason:
                findings.append(Finding("AUDIT_PACK_FORBIDDEN_PATH_EXCLUDED", "Audit pack excluded a forbidden runtime/secret/build path.", Severity.WARNING, path=rel, metadata={"reason": blocked_reason}))
                continue
            if not absolute.exists() or not absolute.is_file():
                continue
            try:
                raw = absolute.read_bytes()
            except OSError as exc:
                findings.append(Finding("AUDIT_PACK_FILE_READ_ERROR", "Audit pack could not read a candidate evidence file.", Severity.FAIL, path=rel, metadata={"error": str(exc)}))
                continue
            redacted = False
            if _is_text_like(absolute):
                text = raw.decode("utf-8", errors="replace")
                redaction = self.secret_guard.redact(text)
                if redaction.changed:
                    redactions_total += redaction.redactions
                    raw = (
                        f"# Redacted audit-pack artifact\n\n"
                        f"Original path: {rel}\n"
                        f"Redactions: {redaction.redactions}\n"
                        "Raw content was not exported because SecretGuard detected secret-like material.\n"
                    ).encode("utf-8")
                    redacted = True
                    findings.append(Finding("AUDIT_PACK_SECRET_REDACTED", "SecretGuard redacted secret-like content before audit pack export.", Severity.WARNING, path=rel, metadata={"redactions": redaction.redactions, "raw_secret_not_exported": True}))
            arcname = rel
            sha = hashlib.sha256(raw).hexdigest()
            entries.append({"path": arcname, "size_bytes": len(raw), "sha256": sha, "kind": _entry_kind(arcname), "source": "repo", "secret_scan_passed": True, "redacted": redacted})
            payloads.append((arcname, raw))

        blocking_findings = [finding for finding in findings if finding.severity in {Severity.FAIL, Severity.BLOCK, Severity.ERROR}]
        if blocking_findings:
            summary = self._base_summary(options, entries_total=len(candidates), files_included=len(payloads), blocked_findings_total=len(blocking_findings))
            summary["redactions_total"] = redactions_total
            return CommandResult("audit-pack build", False, _exit_code_from_findings(blocking_findings), "Audit pack build blocked by safety findings.", data={"summary": summary, "entries": entries}, findings=findings)

        pack_id = _pack_id(entries)
        output_dir = (self.root / options.output_dir).resolve()
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"{pack_id}.zip"
        manifest = self._manifest(pack_id=pack_id, actor=options.actor or _DEFAULT_ACTOR, entries=entries)
        manifest_bytes = json.dumps(manifest, indent=2, ensure_ascii=False, sort_keys=True).encode("utf-8")
        with zipfile.ZipFile(output_path, mode="w", compression=zipfile.ZIP_DEFLATED) as archive:
            for arcname, raw in sorted(payloads, key=lambda item: item[0]):
                archive.writestr(arcname, raw)
            archive.writestr(_MANIFEST_NAME, manifest_bytes)
        zip_sha = _sha256_file(output_path)
        summary = self._base_summary(options, entries_total=len(candidates), files_included=len(payloads), blocked_findings_total=0)
        summary.update({
            "pack_id": pack_id,
            "pack_path": _to_posix(output_path.relative_to(self.root)),
            "pack_sha256": zip_sha,
            "manifest_embedded": True,
            "manifest_entries_total": len(entries),
            "redactions_total": redactions_total,
            "secrets_exported": False,
            "runtime_db_exported": False,
            "providers_local_exported": False,
            "external_api_used": False,
            "network_used": False,
            "mutations_performed": True,
            "source_mutations_performed": False,
        })
        findings.append(Finding("AUDIT_PACK_BUILD_PASS", "Audit pack built with manifest and checksums without exporting secrets or runtime DB.", Severity.INFO, path=summary["pack_path"], metadata={"pack_sha256": zip_sha, "files_included": len(payloads)}))
        return CommandResult("audit-pack build", True, ExitCode.PASS, "Audit pack built successfully.", data={"summary": summary, "manifest": manifest}, findings=findings)

    def verify(self, options: AuditPackVerifyOptions) -> CommandResult:
        findings: list[Finding] = []
        input_path = Path(options.path)
        absolute = input_path if input_path.is_absolute() else self.root / input_path
        absolute = absolute.resolve()
        try:
            rel = _to_posix(absolute.relative_to(self.root))
        except ValueError:
            finding = Finding("AUDIT_PACK_PATH_OUTSIDE_ROOT_BLOCKED", "Audit pack verification path is outside the governed workspace root.", Severity.BLOCK, path=str(input_path))
            return CommandResult("audit-pack verify", False, ExitCode.BLOCK, "Audit pack verification blocked by PathGuard.", data={"summary": {"path": str(input_path), "path_allowed": False, "preliminary": True}}, findings=[finding])
        decision = self.path_guard.evaluate(rel, action="read")
        if decision.effect == PolicyEffect.BLOCK:
            return CommandResult("audit-pack verify", False, ExitCode.BLOCK, "Audit pack verification blocked by PathGuard.", data={"summary": {"path": rel, "path_allowed": False, "preliminary": True}}, findings=[decision.to_finding()])
        summary: dict[str, Any] = {
            "path": rel,
            "exists": absolute.exists(),
            "zip_valid": False,
            "manifest_present": False,
            "entries_total": 0,
            "entries_verified": 0,
            "checksum_mismatches": 0,
            "forbidden_paths_total": 0,
            "secret_findings_total": 0,
            "runtime_db_exported": False,
            "providers_local_exported": False,
            "network_used": False,
            "external_api_used": False,
            "mutations_performed": False,
            "preliminary": True,
        }
        if not absolute.exists() or not absolute.is_file():
            findings.append(Finding("AUDIT_PACK_MISSING", "Audit pack ZIP does not exist.", Severity.BLOCK, path=rel))
            return CommandResult("audit-pack verify", False, ExitCode.BLOCK, "Audit pack does not exist.", data={"summary": summary}, findings=findings)
        try:
            with zipfile.ZipFile(absolute, mode="r") as archive:
                names = set(archive.namelist())
                summary["zip_valid"] = True
                if _MANIFEST_NAME not in names:
                    findings.append(Finding("AUDIT_PACK_MANIFEST_MISSING", "Audit pack manifest is missing.", Severity.BLOCK, path=rel))
                else:
                    summary["manifest_present"] = True
                    manifest = json.loads(archive.read(_MANIFEST_NAME).decode("utf-8"))
                    entries = manifest.get("entries") if isinstance(manifest, dict) else None
                    if not isinstance(entries, list):
                        findings.append(Finding("AUDIT_PACK_MANIFEST_INVALID", "Audit pack manifest entries are invalid.", Severity.BLOCK, path=_MANIFEST_NAME))
                        entries = []
                    summary["entries_total"] = len(entries)
                    for entry in entries:
                        entry_path = str(entry.get("path", ""))
                        expected_sha = str(entry.get("sha256", ""))
                        if not entry_path or entry_path not in names:
                            findings.append(Finding("AUDIT_PACK_ENTRY_MISSING", "Manifest entry is missing from ZIP.", Severity.BLOCK, path=entry_path or _MANIFEST_NAME))
                            continue
                        reason = _blocked_reason(entry_path)
                        if reason:
                            summary["forbidden_paths_total"] += 1
                            findings.append(Finding("AUDIT_PACK_FORBIDDEN_PATH_BLOCKED", "Audit pack contains a forbidden runtime/secret/build path.", Severity.BLOCK, path=entry_path, metadata={"reason": reason}))
                        raw = archive.read(entry_path)
                        actual_sha = hashlib.sha256(raw).hexdigest()
                        if expected_sha != actual_sha:
                            summary["checksum_mismatches"] += 1
                            findings.append(Finding("AUDIT_PACK_CHECKSUM_MISMATCH", "Audit pack entry checksum does not match manifest.", Severity.BLOCK, path=entry_path, metadata={"expected_sha256": expected_sha, "actual_sha256": actual_sha}))
                        else:
                            summary["entries_verified"] += 1
                        if _is_text_arcname(entry_path):
                            redaction = self.secret_guard.redact(raw.decode("utf-8", errors="replace"))
                            if redaction.changed:
                                summary["secret_findings_total"] += redaction.redactions
                                findings.append(Finding("AUDIT_PACK_SECRET_CONTENT_BLOCKED", "SecretGuard detected secret-like content inside audit pack.", Severity.BLOCK, path=entry_path, metadata={"redactions": redaction.redactions}))
                        if entry_path == ".devpilot/devpilot.db":
                            summary["runtime_db_exported"] = True
                        if entry_path == ".devpilot/providers.yaml":
                            summary["providers_local_exported"] = True
                for name in names:
                    reason = _blocked_reason(name)
                    if reason:
                        summary["forbidden_paths_total"] += 1
                        findings.append(Finding("AUDIT_PACK_FORBIDDEN_ZIP_MEMBER_BLOCKED", "Audit pack ZIP contains forbidden member not allowed by export policy.", Severity.BLOCK, path=name, metadata={"reason": reason}))
        except zipfile.BadZipFile:
            findings.append(Finding("AUDIT_PACK_ZIP_INVALID", "Audit pack is not a valid ZIP file.", Severity.BLOCK, path=rel))
        except json.JSONDecodeError as exc:
            findings.append(Finding("AUDIT_PACK_MANIFEST_JSON_INVALID", "Audit pack manifest JSON is invalid.", Severity.ERROR, path=_MANIFEST_NAME, metadata={"error": str(exc)}))
        except OSError as exc:
            findings.append(Finding("AUDIT_PACK_VERIFY_IO_ERROR", "Audit pack verification could not read ZIP content.", Severity.ERROR, path=rel, metadata={"error": str(exc)}))

        blocking = [finding for finding in findings if finding.severity in {Severity.FAIL, Severity.BLOCK, Severity.ERROR}]
        ok = not blocking and summary["zip_valid"] and summary["manifest_present"] and summary["entries_total"] == summary["entries_verified"]
        summary["blocking_findings_total"] = len(blocking)
        summary["pack_sha256"] = _sha256_file(absolute) if absolute.exists() and absolute.is_file() else None
        return CommandResult(
            "audit-pack verify",
            ok,
            ExitCode.PASS if ok else _exit_code_from_findings(blocking or findings),
            "Audit pack verification passed." if ok else "Audit pack verification failed or blocked.",
            data={"summary": summary},
            findings=findings or [Finding("AUDIT_PACK_VERIFY_PASS", "Audit pack manifest, checksums and export policy verified.", Severity.INFO, path=rel, metadata={"entries_verified": summary["entries_verified"]})],
        )

    def _collect_candidates(self, *, include_reports: bool) -> list[str]:
        candidates: set[str] = set()
        fixed = [
            "README.md",
            "pyproject.toml",
            ".devpilot/project.yaml",
            ".devpilot/policy.yaml",
            ".devpilot/providers.yaml.example",
            ".devpilot/miasi/agent_registry.json",
            ".devpilot/miasi/tool_registry.json",
            ".devpilot/miasi/policy_matrix.json",
            ".devpilot/connectors/connector_registry.json",
            ".devpilot/plugins/plugin_registry.json",
            ".devpilot/workspaces/workspace_registry.json",
            ".devpilot/identity/identity_registry.json",
            "docs/devpilot_backlog_fase_H_capacidades_avanzadas.md",
            "docs/functional_backlog_after_precode.md",
            "docs/release/CHANGELOG.md",
            "docs/05_operations/runbook.md",
            "docs/05_operations/audit_pack_runbook.md",
            "docs/schemas/schema_catalog.json",
            "docs/schemas/audit_pack_manifest.schema.json",
        ]
        candidates.update(path for path in fixed if (self.root / path).exists())
        for pattern in ["docs/functional_sprint_*_manifest.json", "docs/audits/*.md", "evals/fixtures/*_eval_cases.json"]:
            for path in self.root.glob(pattern):
                if path.is_file():
                    candidates.add(_to_posix(path.relative_to(self.root)))
        if include_reports:
            for pattern in ["outputs/reports/*.json", "outputs/reports/*.md", "outputs/reports/*.sha256"]:
                for path in self.root.glob(pattern):
                    if path.is_file():
                        candidates.add(_to_posix(path.relative_to(self.root)))
        return sorted(candidates)

    def _manifest(self, *, pack_id: str, actor: str, entries: list[dict[str, Any]]) -> dict[str, Any]:
        return {
            "schema_version": "1.0",
            "schema_id": "SCHEMA-DEVPL-AUDIT-PACK-MANIFEST-V1",
            "pack_id": pack_id,
            "title": "DevPilot Local Audit Pack",
            "status": "implemented-initial",
            "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
            "generated_by_actor": actor,
            "sprint": "FUNC-SPRINT-96",
            "local_first": True,
            "cloud_export_used": False,
            "network_used": False,
            "external_api_used": False,
            "secrets_exported": False,
            "runtime_db_exported": False,
            "providers_local_exported": False,
            "entries_total": len(entries),
            "entries": entries,
            "checksums": {entry["path"]: entry["sha256"] for entry in entries},
            "notes": [
                "Implemented-initial audit pack for offline collaboration and review.",
                "No .env, local providers.yaml, runtime DB, agent sessions, VCS metadata, build artifacts or node_modules are exported.",
            ],
        }

    def _rbac_check(self, actor: str | None, *, action: str, subject: str) -> CommandResult:
        registry = IdentityRegistry(self.root, options=IdentityRegistryOptions(registry_path=".devpilot/identity/identity_registry.json"))
        result = registry.check(RbacCheckInput(actor_id=actor, action=action, permission="audit.pack.build", subject=subject, require_sensitive=False))
        # FUNC-SPRINT-96 must not be blocked by the coarse Sprint 95 permission
        # model when active local owner has wildcard permissions. Unknown actors
        # still fail closed through IdentityRegistry.
        if result.ok:
            return CommandResult("audit-pack rbac", True, ExitCode.PASS, "Audit pack actor is authorized.", data=result.data, findings=[Finding("AUDIT_PACK_RBAC_ALLOWED", "Local actor is authorized to build/verify audit packs.", Severity.INFO, metadata={"actor": actor or _DEFAULT_ACTOR})])
        return CommandResult("audit-pack build", False, result.exit_code, "Audit pack actor is not authorized.", data=result.data, findings=result.findings)

    def _base_summary(self, options: AuditPackBuildOptions, *, entries_total: int, files_included: int, blocked_findings_total: int) -> dict[str, Any]:
        return {
            "output_dir": options.output_dir,
            "entries_total": entries_total,
            "files_included": files_included,
            "include_reports": bool(options.include_reports),
            "include_runtime_db": bool(options.include_runtime_db),
            "blocked_findings_total": blocked_findings_total,
            "local_first": True,
            "cloud_export_used": False,
            "network_used": False,
            "external_api_used": False,
            "preliminary": True,
        }


def _blocked_reason(rel: str) -> str | None:
    rel = rel.replace("\\", "/").strip("/")
    path = PurePosixPath(rel)
    if rel in _FORBIDDEN_EXACT:
        return "forbidden-exact"
    if any(rel.startswith(prefix) for prefix in _FORBIDDEN_PREFIXES):
        return "forbidden-prefix"
    if any(part in _FORBIDDEN_PARTS for part in path.parts):
        return "forbidden-part"
    filename = path.name.lower()
    if filename == ".env" or (filename.startswith(".env.") and not filename.endswith(".example")):
        return "env-secret"
    if filename.endswith(_SECRET_SUFFIXES):
        return "secret-key-file"
    if any(part.lower() in {"secrets", ".secrets"} for part in path.parts):
        return "secrets-directory"
    return None


def _is_text_like(path: Path) -> bool:
    name = path.name.lower()
    if name.endswith((".yaml.example", ".yml.example")):
        return True
    if path.suffix.lower() in _TEXT_SUFFIXES:
        return True
    try:
        chunk = path.read_bytes()[:1024]
    except OSError:
        return False
    return b"\x00" not in chunk


def _is_text_arcname(name: str) -> bool:
    suffix = PurePosixPath(name).suffix.lower()
    return name.lower().endswith((".yaml.example", ".yml.example")) or suffix in _TEXT_SUFFIXES or name == _MANIFEST_NAME


def _entry_kind(path: str) -> str:
    if path.startswith("docs/audits/"):
        return "audit-document"
    if path.startswith("docs/functional_sprint_"):
        return "sprint-manifest"
    if path.startswith("outputs/reports/"):
        return "runtime-report"
    if path.startswith(".devpilot/"):
        return "governance-registry"
    if path.startswith("evals/fixtures/"):
        return "eval-fixture"
    return "documentation"


def _pack_id(entries: list[dict[str, Any]]) -> str:
    now = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    seed = "|".join(f"{entry['path']}:{entry['sha256']}" for entry in sorted(entries, key=lambda item: item["path"]))
    digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()[:8]
    return f"devpilot-audit-pack-{now}-{digest}"


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _exit_code_from_findings(findings: list[Finding]) -> ExitCode:
    severities = {finding.severity for finding in findings}
    if Severity.ERROR in severities:
        return ExitCode.ERROR
    if Severity.BLOCK in severities:
        return ExitCode.BLOCK
    if Severity.FAIL in severities:
        return ExitCode.FAIL
    return ExitCode.PASS


def _to_posix(path: Path) -> str:
    return path.as_posix()
