from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.policy.secrets import SecretGuard
from devpilot_core.runtime_state.inventory import RuntimeStateInventoryBuilder, RuntimeStateInventoryOptions
from devpilot_core.runtime_state.models import utc_now_iso
from devpilot_core.runtime_state.policy import DEFAULT_RUNTIME_STATE_POLICY, RuntimeStatePolicyLoader

RUNTIME_STATE_EXPORT_MANIFEST_SCHEMA_ID = "SCHEMA-DEVPL-RUNTIME-STATE-EXPORT-MANIFEST-V1"
RUNTIME_STATE_EXPORT_ID = "devpilot-runtime-state-export"
POST_H_008_D_CREATED_BY = "POST-H-008-D"
DEFAULT_RUNTIME_EXPORT_ROOT = Path("outputs/runtime_exports")
_MANIFEST_NAME = "runtime_state_export_manifest.json"
_CHECKSUMS_NAME = "checksums.sha256"
_METADATA_ONLY_SUFFIX = ".metadata.json"
_TEXT_SUFFIXES = {".json", ".jsonl", ".md", ".txt", ".csv", ".yaml", ".yml", ".toml", ".log"}
_METADATA_ONLY_CLASSES = {"local-db"}
_RAW_PAYLOAD_KEYS = {
    "prompt",
    "prompts",
    "raw_prompt",
    "raw_prompts",
    "rendered_prompt",
    "rendered_prompts",
    "completion",
    "completions",
    "raw_output",
    "raw_outputs",
    "model_output",
    "model_outputs",
    "llm_output",
    "llm_outputs",
    "response_text",
    "input_text",
    "output_text",
}
_RAW_TEXT_LINE_PATTERN = re.compile(
    r"(?im)^.*\b(raw[_-]?prompt|raw[_-]?output|rendered[_-]?prompt|llm[_-]?output|model[_-]?output|completion)\b.*$"
)


@dataclass(frozen=True)
class RuntimeStateExportOptions:
    policy_path: str | Path = DEFAULT_RUNTIME_STATE_POLICY
    dry_run: bool = True
    execute: bool = False
    output: str | Path | None = None


class RuntimeStateExporter:
    """Export redacted runtime evidence without leaking raw prompts, outputs or secrets.

    POST-H-008-D is intentionally local-only and conservative. Dry-run builds an
    export plan and performs no writes. Execute mode requires an explicit output
    path under ``outputs/runtime_exports/`` and writes sanitized text/JSON
    evidence, a manifest and a checksum file. Non-redactable binary artifacts
    such as the local SQLite DB are represented as metadata-only entries.
    """

    def __init__(self, root: Path, options: RuntimeStateExportOptions | None = None) -> None:
        self.root = Path(root).resolve()
        self.options = options or RuntimeStateExportOptions()
        self.secret_guard = SecretGuard()

    def run(self) -> CommandResult:
        findings: list[Finding] = []
        if self.options.dry_run and self.options.execute:
            finding = Finding(
                id="RUNTIME_STATE_EXPORT_MODE_CONFLICT",
                message="Use either --dry-run or --execute, not both.",
                severity=Severity.BLOCK,
            )
            return CommandResult(
                command="runtime-state export",
                ok=False,
                exit_code=ExitCode.BLOCK,
                message="Runtime-state export blocked by mode conflict.",
                data={"summary": self._base_summary(dry_run=True, execute_requested=True, execution_blocked=True)},
                findings=[finding],
            )

        execute = bool(self.options.execute)
        dry_run = not execute
        output_validation = self._validate_output(execute=execute)
        if output_validation is not None:
            return output_validation

        try:
            manifest = self._build_manifest(dry_run=dry_run, execute=execute)
        except Exception as exc:
            finding = Finding(
                id="RUNTIME_STATE_EXPORT_ERROR",
                message=f"Runtime-state export could not be prepared: {exc}",
                severity=Severity.ERROR,
            )
            return CommandResult(
                command="runtime-state export",
                ok=False,
                exit_code=ExitCode.ERROR,
                message="Runtime-state export failed.",
                data={"summary": self._base_summary(dry_run=dry_run, execute_requested=execute, execution_blocked=True)},
                findings=[finding],
            )

        if execute:
            findings.extend(self._write_export(manifest))
        else:
            manifest.pop("_payloads", None)

        summary = manifest["summary"]
        blocking = [finding for finding in findings if finding.severity in {Severity.BLOCK, Severity.ERROR, Severity.FAIL}]
        if blocking:
            summary["execution_blocked"] = True
            summary["export_execution_enabled"] = False
            return CommandResult(
                command="runtime-state export",
                ok=False,
                exit_code=_exit_code_from_findings(blocking),
                message="Runtime-state export blocked by safety findings.",
                data={"summary": summary, "manifest": manifest},
                findings=findings,
            )

        if execute:
            findings.append(
                Finding(
                    id="RUNTIME_STATE_EXPORT_PASS",
                    message="Runtime-state evidence export completed with manifest, checksums and redaction controls.",
                    severity=Severity.INFO,
                    path=summary.get("output_path"),
                    metadata={"files_exported_total": summary.get("files_exported_total", 0), "redactions_total": summary.get("redactions_total", 0)},
                )
            )
        else:
            findings.append(
                Finding(
                    id="RUNTIME_STATE_EXPORT_DRY_RUN_PASS",
                    message="Runtime-state export dry-run completed without writing files.",
                    severity=Severity.INFO,
                    metadata={"planned_entries_total": summary.get("planned_entries_total", 0)},
                )
            )

        return CommandResult(
            command="runtime-state export",
            ok=True,
            exit_code=ExitCode.PASS,
            message="Runtime-state export completed." if execute else "Runtime-state export dry-run completed.",
            data={"summary": summary, "manifest": manifest},
            findings=findings,
        )

    def _build_manifest(self, *, dry_run: bool, execute: bool) -> dict[str, Any]:
        policy = RuntimeStatePolicyLoader(self.root, self.options.policy_path).load()
        inventory = RuntimeStateInventoryBuilder(
            self.root,
            RuntimeStateInventoryOptions(policy_path=self.options.policy_path, include_source_of_truth_artifacts=False),
        ).build_inventory(policy)
        now = utc_now_iso()
        entries: list[dict[str, Any]] = []
        payloads: list[tuple[str, bytes]] = []
        redactions_total = 0
        raw_payload_fields_removed_total = 0
        metadata_only_total = 0
        skipped_total = 0

        for artifact in inventory.get("artifacts", []):
            if not artifact.get("export_allowed", False):
                skipped_total += 1
                continue
            rel_path = str(artifact.get("path", "")).replace("\\", "/")
            if not rel_path or artifact.get("source_of_truth", False):
                skipped_total += 1
                continue
            source_path = (self.root / rel_path).resolve()
            if not _is_relative_to(source_path, self.root) or not source_path.exists() or not source_path.is_file():
                skipped_total += 1
                continue
            entry, payload = self._prepare_entry(artifact, source_path, rel_path)
            redactions_total += int(entry.get("redactions_total", 0))
            raw_payload_fields_removed_total += int(entry.get("raw_payload_fields_removed", 0))
            metadata_only_total += 1 if entry.get("metadata_only") else 0
            entries.append(entry)
            if payload is not None:
                payloads.append((entry["export_path"], payload))

        export_id = _stable_export_id(entries, now)
        output_path = self._resolved_output_path(export_id=export_id) if execute else self._planned_output_path(export_id=export_id)
        checksums = {entry["export_path"]: entry["export_sha256"] for entry in entries if not entry.get("metadata_only")}
        manifest = {
            "schema_version": "1.0",
            "schema_id": RUNTIME_STATE_EXPORT_MANIFEST_SCHEMA_ID,
            "export_id": export_id,
            "created_by": POST_H_008_D_CREATED_BY,
            "status": "implemented-initial",
            "generated_at_utc": now,
            "policy_path": _rel(self.root, self.root / self.options.policy_path),
            "inventory_id": inventory.get("inventory_id"),
            "output_path": output_path,
            "dry_run": dry_run,
            "execute_requested": execute,
            "entries": entries,
            "checksums": checksums,
            "summary": {
                **self._base_summary(dry_run=dry_run, execute_requested=execute, execution_blocked=False),
                "output_path": output_path,
                "planned_entries_total": len(entries),
                "files_exported_total": 0,
                "metadata_only_total": metadata_only_total,
                "skipped_non_exportable_total": skipped_total,
                "redactions_total": redactions_total,
                "raw_payload_fields_removed_total": raw_payload_fields_removed_total,
                "checksums_total": len(checksums),
                "manifest_written": False,
                "checksums_written": False,
                "raw_prompts_exported": False,
                "raw_outputs_exported": False,
                "secrets_exported": False,
                "local_db_raw_exported": False,
                "auditpack_optional_source_ready": True,
            },
            "safety": {
                "dry_run_default": True,
                "execute_requires_explicit_output": True,
                "redaction_required_for_sensitive_artifacts": True,
                "no_raw_prompts": True,
                "no_raw_outputs": True,
                "secretguard_enabled": True,
                "local_db_metadata_only": True,
                "network_used": False,
                "external_api_used": False,
                "remote_execution_enabled": False,
                "connector_write_enabled": False,
                "plugin_execution_enabled": False,
                "source_mutations_performed": False,
            },
            "notes": [
                "POST-H-008-D exports runtime evidence locally only.",
                "Sensitive JSON/JSONL artifacts are recursively redacted and raw prompt/output fields are removed.",
                "Binary or non-redactable sensitive artifacts are exported as metadata-only entries, not raw payloads.",
                "This manifest can be consumed by future auditpack/release hygiene flows; full gate integration remains POST-H-008-E.",
            ],
            "_payloads": payloads,
        }
        return manifest

    def _prepare_entry(self, artifact: dict[str, Any], source_path: Path, rel_path: str) -> tuple[dict[str, Any], bytes | None]:
        class_id = str(artifact.get("class_id", ""))
        source_size = source_path.stat().st_size
        source_sha = _sha256_file(source_path)
        metadata_only = class_id in _METADATA_ONLY_CLASSES or not _is_text_like(source_path)
        redactions = 0
        raw_removed = 0
        redacted = False
        payload: bytes | None = None
        export_path = f"evidence/{_safe_export_path(rel_path)}"

        if metadata_only:
            export_path = f"metadata/{_safe_export_path(rel_path)}{_METADATA_ONLY_SUFFIX}"
            metadata_payload = {
                "original_path": rel_path,
                "class_id": class_id,
                "classification": artifact.get("classification"),
                "source_size_bytes": source_size,
                "source_sha256": source_sha,
                "metadata_only": True,
                "raw_payload_exported": False,
                "reason": "Artifact is binary or requires a dedicated export/redaction workflow; raw bytes were not exported.",
            }
            payload = json.dumps(metadata_payload, indent=2, ensure_ascii=False, sort_keys=True).encode("utf-8")
            redacted = True
        else:
            raw = source_path.read_bytes()
            suffix = source_path.suffix.lower()
            if suffix == ".json":
                payload_obj = json.loads(raw.decode("utf-8", errors="replace") or "{}")
                sanitized, raw_removed = _remove_raw_payload_fields(payload_obj)
                redaction = self.secret_guard.redact(sanitized)
                redactions = redaction.redactions
                payload = json.dumps(redaction.value, indent=2, ensure_ascii=False, sort_keys=True).encode("utf-8") + b"\n"
                redacted = redactions > 0 or raw_removed > 0 or bool(artifact.get("redaction_required", False))
            elif suffix == ".jsonl":
                text = raw.decode("utf-8", errors="replace")
                lines: list[str] = []
                for line in text.splitlines():
                    if not line.strip():
                        continue
                    try:
                        obj = json.loads(line)
                        sanitized, removed = _remove_raw_payload_fields(obj)
                        raw_removed += removed
                        redaction = self.secret_guard.redact(sanitized)
                        redactions += redaction.redactions
                        lines.append(json.dumps(redaction.value, ensure_ascii=False, sort_keys=True))
                    except json.JSONDecodeError:
                        sanitized_text, removed = _remove_raw_payload_lines(line)
                        raw_removed += removed
                        redaction = self.secret_guard.redact(sanitized_text)
                        redactions += redaction.redactions
                        lines.append(str(redaction.value))
                payload = ("\n".join(lines) + "\n").encode("utf-8")
                redacted = redactions > 0 or raw_removed > 0 or bool(artifact.get("redaction_required", False))
            else:
                text = raw.decode("utf-8", errors="replace")
                sanitized_text, raw_removed = _remove_raw_payload_lines(text)
                redaction = self.secret_guard.redact(sanitized_text)
                redactions = redaction.redactions
                payload = str(redaction.value).encode("utf-8")
                redacted = redactions > 0 or raw_removed > 0 or bool(artifact.get("redaction_required", False))

        assert payload is not None
        export_sha = hashlib.sha256(payload).hexdigest()
        entry = {
            "original_path": rel_path,
            "export_path": export_path,
            "class_id": class_id,
            "classification": artifact.get("classification"),
            "source_size_bytes": source_size,
            "exported_size_bytes": len(payload),
            "source_sha256": source_sha,
            "export_sha256": export_sha,
            "redacted": redacted,
            "redactions_total": redactions,
            "raw_payload_fields_removed": raw_removed,
            "raw_prompt_exported": False,
            "raw_output_exported": False,
            "secret_scan_passed": True,
            "metadata_only": metadata_only,
            "checksum_algorithm": "sha256",
        }
        return entry, payload

    def _write_export(self, manifest: dict[str, Any]) -> list[Finding]:
        findings: list[Finding] = []
        output_dir = (self.root / str(manifest["output_path"])).resolve()
        output_dir.mkdir(parents=True, exist_ok=True)
        payloads: list[tuple[str, bytes]] = list(manifest.pop("_payloads", []))
        for export_path, payload in payloads:
            target = (output_dir / export_path).resolve()
            if not _is_relative_to(target, output_dir):
                findings.append(Finding("RUNTIME_STATE_EXPORT_PATH_ESCAPE", "Refused to write export payload outside output directory.", Severity.BLOCK, path=export_path))
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(payload)
        checksums_text = "".join(f"{sha}  {path}\n" for path, sha in sorted(manifest.get("checksums", {}).items()))
        (output_dir / _CHECKSUMS_NAME).write_text(checksums_text, encoding="utf-8")
        manifest["summary"]["files_exported_total"] = len(payloads)
        manifest["summary"]["manifest_written"] = True
        manifest["summary"]["checksums_written"] = True
        manifest["summary"]["mutations_performed"] = True
        manifest["summary"]["export_execution_enabled"] = True
        manifest["safety"]["mutations_performed"] = True
        manifest["manifest_path"] = _rel(self.root, output_dir / _MANIFEST_NAME)
        manifest["checksums_path"] = _rel(self.root, output_dir / _CHECKSUMS_NAME)
        (output_dir / _MANIFEST_NAME).write_text(json.dumps(manifest, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
        return findings

    def _base_summary(self, *, dry_run: bool, execute_requested: bool, execution_blocked: bool = False) -> dict[str, Any]:
        return {
            "created_by": POST_H_008_D_CREATED_BY,
            "status": "implemented-initial",
            "preliminary": True,
            "dry_run": dry_run,
            "execute_requested": execute_requested,
            "execution_blocked": execution_blocked,
            "export_execution_enabled": False,
            "redaction_execution_enabled": True,
            "cleanup_execution_enabled": False,
            "network_used": False,
            "external_api_used": False,
            "mutations_performed": False,
            "destructive_cleanup_performed": False,
            "source_mutations_performed": False,
        }

    def _planned_output_path(self, *, export_id: str) -> str:
        if self.options.output:
            return str(Path(self.options.output)).replace("\\", "/")
        return (DEFAULT_RUNTIME_EXPORT_ROOT / export_id).as_posix()

    def _resolved_output_path(self, *, export_id: str) -> str:
        return self._planned_output_path(export_id=export_id)

    def _validate_output(self, *, execute: bool) -> CommandResult | None:
        if not execute:
            return None
        if self.options.output is None:
            finding = Finding(
                id="RUNTIME_STATE_EXPORT_OUTPUT_REQUIRED",
                message="--execute requires explicit --output under outputs/runtime_exports/.",
                severity=Severity.BLOCK,
            )
            return CommandResult(
                command="runtime-state export",
                ok=False,
                exit_code=ExitCode.BLOCK,
                message="Runtime-state export blocked because output path is required.",
                data={"summary": self._base_summary(dry_run=True, execute_requested=True, execution_blocked=True)},
                findings=[finding],
            )
        output = Path(self.options.output)
        normalized = output.as_posix().rstrip("/")
        if output.is_absolute():
            try:
                rel = output.resolve().relative_to(self.root)
                normalized = rel.as_posix().rstrip("/")
            except ValueError:
                normalized = output.as_posix().rstrip("/")
        if not normalized.startswith("outputs/runtime_exports/"):
            finding = Finding(
                id="RUNTIME_STATE_EXPORT_OUTPUT_OUTSIDE_RUNTIME_EXPORTS",
                message="Export output must be under outputs/runtime_exports/ to keep runtime evidence out of source-of-truth paths.",
                severity=Severity.BLOCK,
                path=normalized,
            )
            return CommandResult(
                command="runtime-state export",
                ok=False,
                exit_code=ExitCode.BLOCK,
                message="Runtime-state export blocked by output path policy.",
                data={"summary": self._base_summary(dry_run=True, execute_requested=True, execution_blocked=True)},
                findings=[finding],
            )
        return None


def render_runtime_state_export_manifest_markdown(payload: dict[str, Any]) -> str:
    summary = payload.get("summary", {})
    entries = payload.get("entries", [])
    lines = [
        "# Runtime state export manifest",
        "",
        f"Export ID: `{payload.get('export_id', '')}`",
        f"Generated at UTC: `{payload.get('generated_at_utc', '')}`",
        f"Created by: `{payload.get('created_by', '')}`",
        f"Status: `{payload.get('status', '')}`",
        f"Output path: `{payload.get('output_path', '')}`",
        "",
        "## Summary",
        "",
        f"- Dry-run: `{summary.get('dry_run', True)}`",
        f"- Execute requested: `{summary.get('execute_requested', False)}`",
        f"- Planned entries total: `{summary.get('planned_entries_total', 0)}`",
        f"- Files exported total: `{summary.get('files_exported_total', 0)}`",
        f"- Redactions total: `{summary.get('redactions_total', 0)}`",
        f"- Raw payload fields removed: `{summary.get('raw_payload_fields_removed_total', 0)}`",
        f"- Raw prompts exported: `{summary.get('raw_prompts_exported', False)}`",
        f"- Raw outputs exported: `{summary.get('raw_outputs_exported', False)}`",
        "",
        "## Entries",
        "",
        "| Original path | Export path | Class | Redacted | Metadata-only | SHA256 |",
        "|---|---|---|---:|---:|---|",
    ]
    for entry in entries[:200]:
        lines.append(
            f"| `{entry.get('original_path', '')}` | `{entry.get('export_path', '')}` | `{entry.get('class_id', '')}` | "
            f"{entry.get('redacted', False)} | {entry.get('metadata_only', False)} | `{entry.get('export_sha256', '')}` |"
        )
    if len(entries) > 200:
        lines.append(f"| ... | ... | ... | ... | ... | {len(entries) - 200} additional entries omitted from Markdown view; JSON contains the full manifest. |")
    lines.extend([
        "",
        "## Safety",
        "",
        "The export is local-only. Sensitive JSON/JSONL evidence is redacted recursively, raw prompt/output fields are removed, and non-redactable binary state is represented as metadata-only evidence.",
        "",
    ])
    return "\n".join(lines)


def _remove_raw_payload_fields(value: Any) -> tuple[Any, int]:
    if isinstance(value, dict):
        result: dict[Any, Any] = {}
        removed = 0
        for key, item in value.items():
            if _is_raw_payload_key(str(key)):
                removed += 1
                continue
            sanitized, child_removed = _remove_raw_payload_fields(item)
            result[key] = sanitized
            removed += child_removed
        return result, removed
    if isinstance(value, list):
        result = []
        removed = 0
        for item in value:
            sanitized, child_removed = _remove_raw_payload_fields(item)
            result.append(sanitized)
            removed += child_removed
        return result, removed
    return value, 0


def _remove_raw_payload_lines(text: str) -> tuple[str, int]:
    matches = list(_RAW_TEXT_LINE_PATTERN.finditer(text))
    if not matches:
        return text, 0
    return _RAW_TEXT_LINE_PATTERN.sub("[REDACTED_RAW_PAYLOAD_LINE]", text), len(matches)


def _is_raw_payload_key(key: str) -> bool:
    normalized = key.strip().lower().replace("-", "_")
    return normalized in _RAW_PAYLOAD_KEYS


def _is_text_like(path: Path) -> bool:
    return path.suffix.lower() in _TEXT_SUFFIXES


def _safe_export_path(path: str) -> str:
    return path.replace("\\", "/").replace("../", "__/").lstrip("/")


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _stable_export_id(entries: list[dict[str, Any]], generated_at: str) -> str:
    base = json.dumps(
        {"generated_at_utc": generated_at, "entries": [(entry.get("original_path"), entry.get("export_sha256")) for entry in entries]},
        sort_keys=True,
        ensure_ascii=False,
    ).encode("utf-8")
    return f"runtime-export-{hashlib.sha256(base).hexdigest()[:12]}"


def _rel(root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def _exit_code_from_findings(findings: list[Finding]) -> ExitCode:
    severities = {finding.severity for finding in findings}
    if Severity.ERROR in severities:
        return ExitCode.ERROR
    if Severity.BLOCK in severities:
        return ExitCode.BLOCK
    if Severity.FAIL in severities:
        return ExitCode.FAIL
    return ExitCode.PASS
