from __future__ import annotations

import difflib
import hashlib
import json
import re
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity, exit_code_for_findings
from devpilot_core.policy import SecretGuard
from devpilot_core.validators.frontmatter import parse_frontmatter_text, validate_frontmatter_document

from .workspace_documents_service import WorkspaceDocumentsApplicationService

EDITABLE_EXTENSIONS = (".md", ".json", ".yaml", ".yml")
MAX_PROPOSAL_BYTES = 262_144
MAX_DIFF_BYTES = 524_288
MAX_PLANS = 64
PLAN_TTL_SECONDS = 1800
PLAN_ID_PATTERN = re.compile(r"^eplan_[0-9a-f]{32}$")
SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
_YAML_UNSUPPORTED = re.compile(r"(^|\s)(?:&[A-Za-z0-9_.-]+|\*[A-Za-z0-9_.-]+|![A-Za-z0-9_.:/-]+)(?:\s|$)")


class WorkspaceEditPlanApplicationService:
    """UOC-004 source-non-mutating document edit planning facade.

    The service accepts only opaque document ids resolved through the existing
    WorkspaceDocumentsApplicationService. It validates a proposed Markdown/JSON/
    conservative-YAML edit, binds the proposal to the current source SHA-256,
    creates a deterministic immutable plan and returns a complete unified diff.

    It never writes source documents, never stages Git, never applies a patch and
    never executes arbitrary shell. UOC-005 owns approval/apply/rollback.
    """

    def __init__(
        self,
        platform_root: Path,
        *,
        documents: WorkspaceDocumentsApplicationService | None = None,
    ) -> None:
        self.platform_root = Path(platform_root).resolve()
        self.documents = documents or WorkspaceDocumentsApplicationService(self.platform_root)
        self.secret_guard = SecretGuard(self.platform_root)
        self._plans: dict[str, dict[str, Any]] = {}

    def plan(
        self,
        *,
        document_id: str,
        document_sha_before: str,
        proposed_content: str,
    ) -> CommandResult:
        started = time.perf_counter()
        document_id = str(document_id or "").strip()
        base_sha = str(document_sha_before or "").strip().lower()
        if not document_id:
            return _blocked("workspace edit plan", "UOC004_DOCUMENT_ID_REQUIRED", "An opaque document_id is required.")
        if not SHA256_PATTERN.fullmatch(base_sha):
            return _blocked("workspace edit plan", "UOC004_BASE_SHA_REQUIRED", "document_sha_before must be a lowercase SHA-256 value.")

        read = self.documents.read_document(document_id)
        if not read.ok:
            return _from_dependency("workspace edit plan", read, "UOC004_DOCUMENT_READ_BLOCK")
        document = (read.data or {}).get("document")
        if not isinstance(document, dict):
            return _blocked("workspace edit plan", "UOC004_DOCUMENT_RESOURCE_BLOCK", "Document service did not return a usable resource.")

        relative_path = str(document.get("relative_path") or "")
        extension = str(document.get("extension") or "").lower()
        current_sha = str(document.get("sha256") or "").lower()
        current_content = str(document.get("content") or "")
        if extension not in EDITABLE_EXTENSIONS:
            return _blocked(
                "workspace edit plan",
                "UOC004_EXTENSION_NOT_EDITABLE_BLOCK",
                "UOC-004 only plans edits for Markdown, JSON and YAML documents.",
                path=relative_path,
                metadata={"extension": extension, "editable_extensions": list(EDITABLE_EXTENSIONS)},
            )
        if current_sha != base_sha:
            return _blocked(
                "workspace edit plan",
                "UOC004_STALE_BASE_BLOCK",
                "The document changed after the editor loaded it; refresh before planning.",
                path=relative_path,
                metadata={"document_sha_before": base_sha, "current_sha256": current_sha},
            )

        if not isinstance(proposed_content, str):
            proposed_content = str(proposed_content)
        proposed_bytes = proposed_content.encode("utf-8")
        if len(proposed_bytes) > MAX_PROPOSAL_BYTES:
            return _blocked(
                "workspace edit plan",
                "UOC004_PROPOSAL_SIZE_BLOCK",
                "Proposed content exceeds the UOC-004 bounded edit budget.",
                path=relative_path,
                metadata={"proposal_bytes": len(proposed_bytes), "maximum_bytes": MAX_PROPOSAL_BYTES},
            )
        if proposed_content == current_content:
            return _result(
                "workspace edit plan",
                [Finding("UOC004_EMPTY_DIFF_FAIL", "The proposal does not change the document.", Severity.FAIL, path=relative_path)],
                data={"summary": _summary(relative_path, current_sha, current_sha, mutations=False)},
            )

        secret_decision = self.secret_guard.scan_text(proposed_content, subject=relative_path)
        if secret_decision.effect.value == "block":
            return _blocked(
                "workspace edit plan",
                "UOC004_SECRET_DRAFT_BLOCK",
                "SecretGuard detected secret-like material; the proposal is not eligible for planning or session draft persistence.",
                path=relative_path,
                metadata={"guard_rule": secret_decision.rule_id, "redactions": secret_decision.metadata.get("redactions", 0)},
            )

        validation_findings, validation = self._validate_content(
            extension=extension,
            relative_path=relative_path,
            current_content=current_content,
            proposed_content=proposed_content,
        )
        if any(item.severity in {Severity.FAIL, Severity.BLOCK, Severity.ERROR} for item in validation_findings):
            return _result(
                "workspace edit plan",
                validation_findings,
                data={
                    "summary": _summary(relative_path, current_sha, hashlib.sha256(proposed_bytes).hexdigest(), mutations=False),
                    "validation": validation,
                    "safety": _safety(),
                },
            )

        diff_text = _unified_diff(relative_path, current_content, proposed_content)
        diff_bytes = diff_text.encode("utf-8")
        if not diff_text.strip():
            return _result(
                "workspace edit plan",
                [Finding("UOC004_EMPTY_DIFF_FAIL", "The proposal generated no unified diff.", Severity.FAIL, path=relative_path)],
                data={"summary": _summary(relative_path, current_sha, hashlib.sha256(proposed_bytes).hexdigest(), mutations=False)},
            )
        if len(diff_bytes) > MAX_DIFF_BYTES:
            return _blocked(
                "workspace edit plan",
                "UOC004_DIFF_SIZE_BLOCK",
                "The complete unified diff exceeds the UOC-004 rendering budget; planning fails closed rather than truncating it.",
                path=relative_path,
                metadata={"diff_bytes": len(diff_bytes), "maximum_bytes": MAX_DIFF_BYTES},
            )

        proposed_sha = hashlib.sha256(proposed_bytes).hexdigest()
        diff_sha = hashlib.sha256(diff_bytes).hexdigest()
        change_stats = _diff_stats(diff_text)
        risk = _risk_assessment(relative_path, extension, current_content, proposed_content, change_stats)
        created_at = _now()
        expires_at = (datetime.now(timezone.utc) + timedelta(seconds=PLAN_TTL_SECONDS)).replace(microsecond=0).isoformat().replace("+00:00", "Z")
        immutable_core = {
            "schema_id": "devpilot.post_h_eval_002.uoc_004.edit_plan.v1",
            "workspace_id": (read.data or {}).get("ui_workspace_context", {}).get("active_workspace_id"),
            "document": {
                "document_id": document_id,
                "relative_path": relative_path,
                "extension": extension,
                "document_sha_before": current_sha,
                "proposed_sha256": proposed_sha,
                "size_before_bytes": len(current_content.encode("utf-8")),
                "size_after_bytes": len(proposed_bytes),
            },
            "proposed_content": proposed_content,
            "diff": {
                "format": "unified",
                "content": diff_text,
                "sha256": diff_sha,
                "bytes": len(diff_bytes),
                **change_stats,
                "truncated": False,
            },
            "validation": validation,
            "risk": risk,
            "policy": {
                "plan_generation_allowed": True,
                "source_write_enabled": False,
                "apply_available_in_uoc_004": False,
                "approval_required_for_apply": True,
                "future_apply_sprint": "UOC-005",
                "optimistic_concurrency_required": True,
                "base_hash_bound": True,
            },
            "preview": {
                "mode": "safe-markdown" if extension == ".md" else ("structured-json" if extension == ".json" else "safe-yaml-text"),
                "content_sha256": proposed_sha,
            },
            "patch_evidence": {
                "filename": f"{document_id}-{proposed_sha[:12]}.patch",
                "sha256": diff_sha,
                "executed": False,
                "source_mutated": False,
            },
            "expires_after_seconds": PLAN_TTL_SECONDS,
            "preliminary": True,
            "safety": _safety(),
        }
        plan_hash = _canonical_hash(immutable_core)
        plan_id = f"eplan_{plan_hash[:32]}"
        plan = {
            **immutable_core,
            "plan_id": plan_id,
            "plan_hash": plan_hash,
            "created_at": created_at,
            "expires_at": expires_at,
        }
        self._plans[plan_id] = plan
        while len(self._plans) > MAX_PLANS:
            self._plans.pop(next(iter(self._plans)))

        findings = [
            *validation_findings,
            Finding(
                "UOC004_EDIT_PLAN_PASS",
                "Immutable source-non-mutating edit plan and complete diff were generated.",
                Severity.INFO,
                path=relative_path,
                metadata={"plan_id": plan_id, "risk_level": risk["level"], "diff_sha256": diff_sha},
            ),
        ]
        if risk["level"] == "high":
            findings.append(Finding("UOC004_EDIT_PLAN_HIGH_RISK_WARNING", "The proposal is high risk and will require governed approval before any future apply.", Severity.WARNING, path=relative_path))
        elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
        return CommandResult(
            command="workspace edit plan",
            ok=True,
            exit_code=ExitCode.PASS,
            message="Immutable UOC-004 edit plan is ready for review; no source write occurred.",
            data={
                "summary": {
                    **_summary(relative_path, current_sha, proposed_sha, mutations=False),
                    "plan_id": plan_id,
                    "plan_hash": plan_hash,
                    "risk_level": risk["level"],
                    "diff_bytes": len(diff_bytes),
                    "elapsed_ms": elapsed_ms,
                    "draft_persistence": "browser-sessionStorage-manual-only",
                    "apply_enabled": False,
                    "approval_required_for_future_apply": True,
                    "preliminary": True,
                },
                "plan": plan,
                "safety": _safety(),
            },
            findings=findings,
        )

    def get_plan(self, *, plan_id: str) -> CommandResult:
        plan, findings = self._resolve_plan(plan_id)
        if plan is None:
            return _result("workspace edit plan status", findings)
        return CommandResult(
            "workspace edit plan status",
            True,
            ExitCode.PASS,
            "Immutable edit plan is available in local process memory.",
            data={"summary": {"plan_id": plan_id, "expired": False, "source_write_enabled": False, "preliminary": True}, "plan": plan, "safety": _safety()},
            findings=[*findings, Finding("UOC004_EDIT_PLAN_STATUS_PASS", "Edit plan is available and not expired.", Severity.INFO)],
        )

    def recheck(self, *, plan_id: str, plan_hash: str) -> CommandResult:
        plan, findings = self._resolve_plan(plan_id)
        if plan is None:
            return _result("workspace edit plan recheck", findings)
        if str(plan_hash or "") != str(plan.get("plan_hash") or ""):
            findings.append(Finding("UOC004_PLAN_HASH_MISMATCH_BLOCK", "Supplied plan hash does not match the immutable plan.", Severity.BLOCK))
            return _result("workspace edit plan recheck", findings)

        document = plan["document"]
        read = self.documents.read_document(str(document["document_id"]))
        if not read.ok:
            return _from_dependency("workspace edit plan recheck", read, "UOC004_RECHECK_DOCUMENT_READ_BLOCK")
        current = (read.data or {}).get("document") or {}
        current_sha = str(current.get("sha256") or "")
        stale = current_sha != str(document.get("document_sha_before") or "")
        if stale:
            findings.append(
                Finding(
                    "UOC004_OPTIMISTIC_CONCURRENCY_STALE_BLOCK",
                    "The source document changed after the immutable plan was created.",
                    Severity.BLOCK,
                    path=str(document.get("relative_path") or ""),
                    metadata={"document_sha_before": document.get("document_sha_before"), "current_sha256": current_sha},
                )
            )
        else:
            findings.append(Finding("UOC004_OPTIMISTIC_CONCURRENCY_PASS", "The source hash still matches the immutable plan base.", Severity.INFO, path=str(document.get("relative_path") or "")))
        return CommandResult(
            "workspace edit plan recheck",
            ok=not stale,
            exit_code=ExitCode.PASS if not stale else ExitCode.BLOCK,
            message="Optimistic concurrency recheck passed." if not stale else "Optimistic concurrency recheck blocked a stale plan.",
            data={
                "summary": {
                    "plan_id": plan_id,
                    "plan_hash": plan_hash,
                    "stale": stale,
                    "document_sha_before": document.get("document_sha_before"),
                    "current_sha256": current_sha,
                    "source_write_enabled": False,
                    "mutations_performed": False,
                    "preliminary": True,
                },
                "plan": plan,
                "safety": _safety(),
            },
            findings=findings,
        )

    def _resolve_plan(self, plan_id: str) -> tuple[dict[str, Any] | None, list[Finding]]:
        plan_id = str(plan_id or "").strip()
        if not PLAN_ID_PATTERN.fullmatch(plan_id):
            return None, [Finding("UOC004_PLAN_ID_BLOCK", "Edit plan id is invalid or not opaque.", Severity.BLOCK)]
        plan = self._plans.get(plan_id)
        if not plan:
            return None, [Finding("UOC004_PLAN_NOT_FOUND_BLOCK", "Edit plan is not available in this process; regenerate it from the current source.", Severity.BLOCK)]
        expires_at = _parse_utc(str(plan.get("expires_at") or ""))
        if expires_at is None or datetime.now(timezone.utc) >= expires_at:
            self._plans.pop(plan_id, None)
            return None, [Finding("UOC004_PLAN_EXPIRED_BLOCK", "Edit plan expired and must be regenerated.", Severity.BLOCK)]
        return plan, []

    def _validate_content(
        self,
        *,
        extension: str,
        relative_path: str,
        current_content: str,
        proposed_content: str,
    ) -> tuple[list[Finding], dict[str, Any]]:
        findings: list[Finding] = []
        details: dict[str, Any] = {"extension": extension, "syntax": "PASS", "frontmatter": "not-applicable"}

        if extension == ".json":
            try:
                parsed = json.loads(proposed_content)
                details["json_type"] = type(parsed).__name__
            except json.JSONDecodeError as exc:
                findings.append(Finding("UOC004_JSON_SYNTAX_FAIL", "Proposed JSON is invalid.", Severity.FAIL, path=relative_path, metadata={"line": exc.lineno, "column": exc.colno}))
                details["syntax"] = "FAIL"
        elif extension == ".md":
            if proposed_content.count("```") % 2:
                findings.append(Finding("UOC004_MARKDOWN_FENCE_FAIL", "Proposed Markdown contains an unclosed fenced code block.", Severity.FAIL, path=relative_path))
                details["syntax"] = "FAIL"
            current_fm = parse_frontmatter_text(current_content, path=Path(relative_path))
            proposed_fm = parse_frontmatter_text(proposed_content, path=Path(relative_path))
            if current_fm.has_frontmatter and not proposed_fm.has_frontmatter:
                findings.append(Finding("UOC004_FRONTMATTER_REMOVED_FAIL", "Existing Markdown frontmatter cannot be silently removed by an edit plan.", Severity.FAIL, path=relative_path))
                details["frontmatter"] = "FAIL"
            elif proposed_fm.has_frontmatter:
                fm_result = validate_frontmatter_document(proposed_fm, root=None, strict=False)
                details["frontmatter"] = "PASS" if fm_result.ok else "FAIL"
                details["frontmatter_fields"] = sorted(k for k in proposed_fm.frontmatter if not k.startswith("__parse_error_line_"))
                for item in fm_result.findings:
                    severity = item.severity if item.severity in {Severity.FAIL, Severity.BLOCK, Severity.ERROR} else Severity.WARNING
                    findings.append(Finding(f"UOC004_{item.id}", item.message, severity, path=relative_path, metadata=item.metadata))
                if current_fm.has_frontmatter:
                    before_id = str(current_fm.frontmatter.get("doc_id") or "")
                    after_id = str(proposed_fm.frontmatter.get("doc_id") or "")
                    if before_id and after_id and before_id != after_id:
                        findings.append(Finding("UOC004_DOCUMENT_IDENTITY_CHANGE_WARNING", "Proposal changes frontmatter doc_id; this is high-risk metadata drift.", Severity.WARNING, path=relative_path, metadata={"before": before_id, "after": after_id}))
        else:
            yaml_findings = _validate_yaml_subset(proposed_content, relative_path)
            findings.extend(yaml_findings)
            details["syntax"] = "PASS" if not any(x.severity in {Severity.FAIL, Severity.BLOCK, Severity.ERROR} for x in yaml_findings) else "FAIL"
            details["yaml_profile"] = "dependency-free-conservative-subset"

        if not findings:
            findings.append(Finding("UOC004_EDIT_SYNTAX_PASS", "Proposed content passed UOC-004 pre-apply syntax checks.", Severity.INFO, path=relative_path))
        details["ok"] = not any(item.severity in {Severity.FAIL, Severity.BLOCK, Severity.ERROR} for item in findings)
        return findings, details


def _validate_yaml_subset(text: str, relative_path: str) -> list[Finding]:
    """Conservative dependency-free YAML validation for the initial UOC-004 editor.

    The project intentionally has no PyYAML dependency. This validator accepts
    the scalar/list/mapping subset already used by DevPilot configuration and
    blocks advanced YAML features rather than pretending to parse them.
    """
    findings: list[Finding] = []
    if "\t" in text:
        findings.append(Finding("UOC004_YAML_TAB_FAIL", "YAML proposal contains tab indentation; spaces are required.", Severity.FAIL, path=relative_path))
    for number, raw in enumerate(text.replace("\r\n", "\n").split("\n"), start=1):
        stripped = raw.strip()
        if not stripped or stripped.startswith("#") or stripped in {"---", "..."}:
            continue
        if _YAML_UNSUPPORTED.search(stripped) or stripped.startswith("<<:"):
            findings.append(Finding("UOC004_YAML_ADVANCED_FEATURE_BLOCK", "Advanced YAML anchors, aliases, tags or merge keys are outside the initial UOC-004 safe subset.", Severity.BLOCK, path=relative_path, metadata={"line": number}))
            continue
        if re.search(r":\s*[|>][+-]?\s*$", stripped):
            findings.append(Finding("UOC004_YAML_MULTILINE_BLOCK", "Block scalar YAML is outside the initial UOC-004 safe subset.", Severity.BLOCK, path=relative_path, metadata={"line": number}))
            continue
        content = stripped[2:].strip() if stripped.startswith("- ") else stripped
        if content.startswith("- "):
            content = content[2:].strip()
        if ":" not in content and not stripped.startswith("- "):
            findings.append(Finding("UOC004_YAML_STRUCTURE_FAIL", "YAML line is not a supported mapping/list entry.", Severity.FAIL, path=relative_path, metadata={"line": number}))
        if raw.rstrip() != raw:
            # trailing whitespace is not syntax-invalid; keep it as a warning.
            findings.append(Finding("UOC004_YAML_TRAILING_WHITESPACE_WARNING", "YAML proposal contains trailing whitespace.", Severity.WARNING, path=relative_path, metadata={"line": number}))
        if not _balanced_inline_syntax(content):
            findings.append(Finding("UOC004_YAML_INLINE_SYNTAX_FAIL", "YAML proposal contains unbalanced quotes/brackets.", Severity.FAIL, path=relative_path, metadata={"line": number}))
    return findings


def _balanced_inline_syntax(value: str) -> bool:
    single = double = False
    escaped = False
    stack: list[str] = []
    pairs = {"]": "[", "}": "{"}
    for char in value:
        if escaped:
            escaped = False
            continue
        if char == "\\" and double:
            escaped = True
            continue
        if char == "'" and not double:
            single = not single
            continue
        if char == '"' and not single:
            double = not double
            continue
        if single or double:
            continue
        if char in "[{":
            stack.append(char)
        elif char in "]}":
            if not stack or stack.pop() != pairs[char]:
                return False
    return not single and not double and not stack


def _unified_diff(relative_path: str, before: str, after: str) -> str:
    before_lines = before.replace("\r\n", "\n").splitlines(keepends=True)
    after_lines = after.replace("\r\n", "\n").splitlines(keepends=True)
    return "".join(
        difflib.unified_diff(
            before_lines,
            after_lines,
            fromfile=f"a/{relative_path}",
            tofile=f"b/{relative_path}",
            lineterm="\n",
            n=3,
        )
    )


def _diff_stats(diff_text: str) -> dict[str, int]:
    additions = deletions = hunks = 0
    for line in diff_text.splitlines():
        if line.startswith("@@"):
            hunks += 1
        elif line.startswith("+") and not line.startswith("+++"):
            additions += 1
        elif line.startswith("-") and not line.startswith("---"):
            deletions += 1
    return {"additions": additions, "deletions": deletions, "hunks": hunks, "changed_lines": additions + deletions}


def _risk_assessment(relative_path: str, extension: str, before: str, after: str, stats: dict[str, int]) -> dict[str, Any]:
    score = 0
    reasons: list[str] = []
    changed = int(stats.get("changed_lines", 0))
    if changed > 100:
        score += 3
        reasons.append("more-than-100-changed-lines")
    elif changed > 20:
        score += 2
        reasons.append("more-than-20-changed-lines")
    else:
        score += 1
        reasons.append("bounded-change")
    if extension in {".yaml", ".yml"}:
        score += 1
        reasons.append("configuration-format")
    path_lower = relative_path.lower()
    if any(token in path_lower for token in ("/security", "policy", "architecture")):
        score += 1
        reasons.append("governance-sensitive-path")
    before_fm = parse_frontmatter_text(before, path=Path(relative_path))
    after_fm = parse_frontmatter_text(after, path=Path(relative_path))
    if before_fm.has_frontmatter and after_fm.has_frontmatter and before_fm.frontmatter != after_fm.frontmatter:
        score += 1
        reasons.append("frontmatter-changed")
    level = "high" if score >= 4 else ("medium" if score >= 2 else "low")
    return {
        "level": level,
        "score": score,
        "reasons": reasons,
        "approval_required_for_apply": True,
        "apply_policy_deferred_to": "UOC-005",
        "source_write_enabled": False,
    }


def _summary(relative_path: str, before_sha: str, after_sha: str, *, mutations: bool) -> dict[str, Any]:
    return {
        "relative_path": relative_path,
        "document_sha_before": before_sha,
        "proposed_sha256": after_sha,
        "source_write_enabled": False,
        "mutations_performed": mutations,
        "external_api_used": False,
        "network_used": False,
        "preliminary": True,
    }


def _safety() -> dict[str, Any]:
    return {
        "local_first": True,
        "source_write_enabled": False,
        "auto_save_enabled": False,
        "patch_apply_enabled": False,
        "git_mutation_enabled": False,
        "arbitrary_shell_allowed": False,
        "external_api_required": False,
        "remote_execution_enabled": False,
        "connector_write_enabled": False,
        "plugin_execution_enabled": False,
        "draft_persistence": "browser-sessionStorage-manual-only",
        "preliminary": True,
    }


def _blocked(command: str, finding_id: str, message: str, *, path: str | None = None, metadata: dict[str, Any] | None = None) -> CommandResult:
    return CommandResult(
        command,
        False,
        ExitCode.BLOCK,
        message,
        data={"summary": {"source_write_enabled": False, "mutations_performed": False, "preliminary": True}, "safety": _safety()},
        findings=[Finding(finding_id, message, Severity.BLOCK, path=path, metadata=metadata or {})],
    )


def _result(command: str, findings: list[Finding], *, data: dict[str, Any] | None = None) -> CommandResult:
    exit_code = exit_code_for_findings(findings)
    ok = not any(item.severity in {Severity.FAIL, Severity.BLOCK, Severity.ERROR} for item in findings)
    return CommandResult(
        command,
        ok,
        ExitCode.PASS if ok else exit_code,
        "Edit planning check passed." if ok else "Edit planning check completed with blocking/failing findings.",
        data=data or {"safety": _safety()},
        findings=findings,
    )


def _from_dependency(command: str, dependency: CommandResult, finding_id: str) -> CommandResult:
    findings = list(dependency.findings)
    findings.append(Finding(finding_id, dependency.message, Severity.BLOCK))
    return CommandResult(command, False, ExitCode.BLOCK, dependency.message, data={"dependency": dependency.to_dict(), "safety": _safety()}, findings=findings)


def _canonical_hash(value: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")).hexdigest()


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _parse_utc(value: str) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed.astimezone(timezone.utc)
    except (TypeError, ValueError):
        return None
