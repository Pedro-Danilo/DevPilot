from __future__ import annotations

import difflib
import hashlib
import json
import os
import re
import shutil
import tempfile
import unicodedata
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from devpilot_core.approval.service import ApprovalCliInput, ApprovalService
from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.identity.auth_store import LocalAuthStore
from devpilot_core.policy import PolicyEngine, PolicyRequest, configured_external_workspace_roots
from devpilot_core.validators.frontmatter import parse_frontmatter_text

ADR_APPLY_ACTION = "filesystem.pre_code_architecture_adr_bundle_apply"
ADR_APPLY_TOOL = "workspace.edit.apply"
ZERO_SHA256 = "0" * 64
ADR_ROOT = Path("docs/02_architecture/adrs")
ARCH_PATH = Path("docs/02_architecture/architecture_document.md")
_ADR_HEADING = re.compile(r"^###\s+(ADR-\d{3})\s+[—-]\s+(.+?)\s*$", re.M)


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _sha_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _sha_text(text: str) -> str:
    normalized = str(text or "").replace("\r\n", "\n").replace("\r", "\n")
    return _sha_bytes(normalized.encode("utf-8"))


def _canonical_sha(value: Any) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return _sha_bytes(raw)


def _safe_slug(value: str) -> str:
    ascii_value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_value.lower()).strip("-")
    return slug[:64] or "decision"


def _unified_diff(path: str, before: str, after: str) -> str:
    return "".join(
        difflib.unified_diff(
            before.replace("\r\n", "\n").replace("\r", "\n").splitlines(keepends=True),
            after.replace("\r\n", "\n").replace("\r", "\n").splitlines(keepends=True),
            fromfile=f"a/{path}",
            tofile=f"b/{path}",
            n=3,
        )
    )


class ArchitectureAdrBundleService:
    """Governed companion lifecycle for C-02 standalone Architecture ADRs.

    The Architecture document remains the semantic authority for decisions already
    reviewed and frozen. This service only projects those exact embedded ADRs into
    standalone governed Markdown artifacts. Planning is source-non-mutating;
    apply is owner-approval-bound, exact-path allowlisted and all-or-nothing.
    """

    def __init__(self, platform_root: Path, *, approval_auth_store: LocalAuthStore | None = None) -> None:
        self.root = Path(platform_root).resolve()
        self.approvals = ApprovalService(self.root)
        self.approval_auth_store = approval_auth_store

    def projection(self, *, workspace_root: Path, workspace_id: str, state: dict[str, Any]) -> dict[str, Any]:
        arch = dict((state.get("stages") or {}).get("architecture") or {})
        derivation=arch.get("derivation") if isinstance(arch.get("derivation"),dict) else {}
        if str(arch.get("status") or "") != "FROZEN" or str(arch.get("mode") or "") != "DEVPL_MOCK" or not str(derivation.get("schema_id") or "").startswith("devpilot.gsdlc13c02"):
            return {"status": "NOT_APPLICABLE", "required": False, "ready": False, "adrs": []}
        runtime = dict(state.get("architecture_adr_bundle") or {})
        expected = self._expected_from_frozen(workspace_root=workspace_root, workspace_id=workspace_id, arch=arch)
        if isinstance(expected, CommandResult):
            return {
                "status": "BLOCK",
                "required": True,
                "ready": False,
                "message": expected.message,
                "findings": [x.to_dict() for x in expected.findings],
                "adrs": [],
            }
        parity = self._source_parity(workspace_root, expected["adrs"])
        # Exact source content is necessary but never sufficient: recovery must also prove
        # that a persisted APPROVED approval is bound to the immutable multi-file plan.
        receipt_applied = parity["all_exact"] and self._receipt_valid(workspace_id=workspace_id, expected=expected)
        if parity["all_exact"] and receipt_applied:
            status = "APPLIED"
            ready = True
        elif parity["all_exact"]:
            status = "BLOCK"
            ready = False
        else:
            status = str(runtime.get("status") or "REQUIRED")
            ready = False
        return {
            "schema_id": "devpilot.gsdlc13c02.architecture_adr_bundle_projection.v1",
            "status": status,
            "required": True,
            "ready": ready,
            "message": ("Standalone ADR files exist but no trusted approval-bound execution receipt/state proves their governed materialization." if parity["all_exact"] and not ready else None),
            "architecture_sha256": expected["architecture_sha256"],
            "architecture_approval_id": expected["architecture_approval_id"],
            "plan_id": runtime.get("plan_id"),
            "plan_hash": runtime.get("plan_hash"),
            "approval_id": runtime.get("approval_id"),
            "execution_id": runtime.get("execution_id"),
            "exact_paths": [x["relative_path"] for x in expected["adrs"]],
            "adrs": [
                {
                    "adr_id": x["adr_id"],
                    "title": x["title"],
                    "relative_path": x["relative_path"],
                    "proposed_sha256": x["proposed_sha256"],
                    "source_state": parity["states"].get(x["relative_path"]),
                }
                for x in expected["adrs"]
            ],
            "source_mutations_performed": False,
        }

    def prepare(self, *, workspace_root: Path, workspace_id: str, state: dict[str, Any], actor: str, actor_role: str) -> CommandResult:
        command = "guided pre-code architecture ADR bundle prepare"
        if actor_role != "owner":
            return self._block(command, "GSDLC13C02_ADR_OWNER_ROLE_BLOCK", "Only Owner can prepare the Architecture ADR companion plan.")
        arch = dict((state.get("stages") or {}).get("architecture") or {})
        derivation=arch.get("derivation") if isinstance(arch.get("derivation"),dict) else {}
        if str(arch.get("status") or "") != "FROZEN":
            return self._block(command, "GSDLC13C02_ADR_ARCHITECTURE_FROZEN_REQUIRED_BLOCK", "Architecture must be FROZEN before standalone ADR materialization can be planned.")
        if str(arch.get("mode") or "") != "DEVPL_MOCK" or not str(derivation.get("schema_id") or "").startswith("devpilot.gsdlc13c02"):
            return self._block(command, "GSDLC13C02_ADR_C02_DERIVATION_REQUIRED_BLOCK", "ADR companion materialization is bounded to the C-02 deterministic Architecture derivation; generic MANUAL/IMPORT lifecycle remains unchanged.")
        expected = self._expected_from_frozen(workspace_root=workspace_root, workspace_id=workspace_id, arch=arch)
        if isinstance(expected, CommandResult):
            return expected
        parity = self._source_parity(workspace_root, expected["adrs"])
        unknown = [p for p, s in parity["states"].items() if s == "DRIFT"]
        if unknown:
            return self._block(command, "GSDLC13C02_ADR_TARGET_DRIFT_BLOCK", "Existing ADR target content does not match the frozen Architecture projection.", metadata={"paths": unknown})
        if parity["all_exact"]:
            if not self._receipt_valid(workspace_id=workspace_id, expected=expected):
                return self._block(command, "GSDLC13C02_ADR_UNTRUSTED_EXISTING_SOURCE_BLOCK", "Standalone ADR files match the deterministic projection but no approval-bound execution receipt exists; DevPilot will not infer approval from content equality.")
            receipt=self._load_receipt(workspace_id)
            runtime = dict(state.get("architecture_adr_bundle") or {})
            runtime.update({"status": "APPLIED", "architecture_sha256": expected["architecture_sha256"], "architecture_approval_id": expected["architecture_approval_id"], "adrs": deepcopy(expected["adrs"]), "approval_id":receipt.get("approval_id"), "execution_id":receipt.get("execution_id"), "recovered_exact_source": True, "updated_at": _now()})
            state["architecture_adr_bundle"] = runtime
            return self._pass(command, "GSDLC13C02_ADR_ALREADY_APPLIED_PASS", "Standalone ADRs and approval-bound execution receipt match the frozen Architecture projection; idempotent state recovered.", {"architecture_adr_bundle": self._runtime_public(runtime), "source_mutations_performed": False})

        plan_core = {
            "schema_id": "devpilot.gsdlc13c02.architecture_adr_bundle_plan.v1",
            "workspace_id": workspace_id,
            "architecture_sha256": expected["architecture_sha256"],
            "architecture_approval_id": expected["architecture_approval_id"],
            "changes": [
                {
                    "adr_id": x["adr_id"],
                    "title": x["title"],
                    "relative_path": x["relative_path"],
                    "preimage_sha256": parity["preimages"][x["relative_path"]],
                    "postimage_sha256": x["proposed_sha256"],
                    "content": x["content"],
                    "diff": _unified_diff(x["relative_path"], parity["before_text"].get(x["relative_path"], ""), x["content"]),
                }
                for x in expected["adrs"]
            ],
            "exact_path_allowlist": [x["relative_path"] for x in expected["adrs"]],
            "source_mutations_performed": False,
            "network_used": False,
            "external_api_used": False,
        }
        plan_id = "adr-plan-" + _canonical_sha({k: v for k, v in plan_core.items() if k != "source_mutations_performed"})[:24]
        plan = {**plan_core, "plan_id": plan_id, "created_by": actor, "created_at": _now()}
        plan_hash = _canonical_sha({k: v for k, v in plan.items() if k != "plan_hash"})
        plan["plan_hash"] = plan_hash
        runtime = {
            "status": "PLANNED",
            "architecture_sha256": expected["architecture_sha256"],
            "architecture_approval_id": expected["architecture_approval_id"],
            "plan_id": plan_id,
            "plan_hash": plan_hash,
            "plan": plan,
            "approval_id": None,
            "execution_id": None,
            "adrs": deepcopy(expected["adrs"]),
            "updated_at": _now(),
        }
        state["architecture_adr_bundle"] = runtime
        return self._pass(command, "GSDLC13C02_ADR_PLAN_READY_PASS", "Immutable standalone ADR bundle plan created without mutating project source.", {"architecture_adr_bundle": self._runtime_public(runtime), "plan": self._plan_public(plan), "source_mutations_performed": False})

    def request_approval(self, *, workspace_root: Path, workspace_id: str, state: dict[str, Any], actor: str, actor_role: str, reason: str) -> CommandResult:
        command = "guided pre-code architecture ADR bundle approval request"
        if actor_role != "owner":
            return self._block(command, "GSDLC13C02_ADR_OWNER_ROLE_BLOCK", "Only Owner can request ADR materialization approval.")
        runtime = dict(state.get("architecture_adr_bundle") or {})
        plan = dict(runtime.get("plan") or {})
        if str(runtime.get("status") or "") not in {"PLANNED", "APPROVAL_PENDING"} or not plan:
            return self._block(command, "GSDLC13C02_ADR_PLAN_REQUIRED_BLOCK", "Prepare the immutable ADR bundle plan before requesting approval.")
        recheck = self._recheck(workspace_root=workspace_root, state=state, runtime=runtime)
        if not recheck.ok:
            return recheck
        plan_id = str(plan["plan_id"]); plan_hash = str(plan["plan_hash"])
        scope = {
            "actor_id": actor,
            "role_at_decision": "owner",
            "tool_id": ADR_APPLY_TOOL,
            "action": ADR_APPLY_ACTION,
            "action_id": ADR_APPLY_ACTION,
            "subject": plan_id,
            "subject_hash": plan_hash,
            "workspace_id": workspace_id,
            "exact_path_allowlist": list(plan["exact_path_allowlist"]),
            "interface": "ui",
            "scope_type": "pre-code-architecture-adr-bundle",
        }
        result = self.approvals.request(ApprovalCliInput(tool_id=ADR_APPLY_TOOL, action=ADR_APPLY_ACTION, subject=plan_id, actor=actor, reason=str(reason or "Approve materialization of standalone ADRs from frozen Architecture."), scope=json.dumps(scope, ensure_ascii=False, sort_keys=True), ttl_minutes=30, metadata={"source": "gsdlc-13-c-02", "interface": "ui", "plan_hash": plan_hash, "architecture_sha256": plan["architecture_sha256"]}))
        if not result.ok:
            return result
        approval = (result.data or {}).get("approval") if isinstance(result.data, dict) else None
        approval_id = str((approval or {}).get("approval_id") or (result.data or {}).get("approval_id") or "")
        if not approval_id:
            candidates = [v for v in (result.data or {}).values() if isinstance(v, dict) and str(v.get("approval_id") or "")]
            approval_id = str(candidates[0].get("approval_id")) if candidates else ""
        if not approval_id:
            return self._block(command, "GSDLC13C02_ADR_APPROVAL_ID_MISSING_BLOCK", "Approval store did not return an approval id.")
        runtime["status"] = "APPROVAL_PENDING"; runtime["approval_id"] = approval_id; runtime["updated_at"] = _now(); state["architecture_adr_bundle"] = runtime
        data = dict(result.data or {}); data["architecture_adr_bundle"] = self._runtime_public(runtime)
        return CommandResult(command, True, ExitCode.PASS, "ADR materialization approval request is exactly bound to the immutable multi-file plan.", data=data, findings=result.findings)

    def apply(self, *, workspace_root: Path, workspace_id: str, state: dict[str, Any], actor: str, actor_role: str) -> CommandResult:
        command = "guided pre-code architecture ADR bundle apply"
        if actor_role != "owner":
            return self._block(command, "GSDLC13C02_ADR_OWNER_ROLE_BLOCK", "Only Owner can apply the approved ADR materialization plan.")
        runtime = dict(state.get("architecture_adr_bundle") or {})
        plan = dict(runtime.get("plan") or {})
        approval_id = str(runtime.get("approval_id") or "")
        if not plan or not approval_id:
            return self._block(command, "GSDLC13C02_ADR_APPROVAL_REQUIRED_BLOCK", "ADR materialization requires an immutable plan and approval id.")
        recheck = self._recheck(workspace_root=workspace_root, state=state, runtime=runtime)
        if not recheck.ok:
            return recheck
        plan_id = str(plan["plan_id"]); plan_hash = str(plan["plan_hash"])
        scope = {
            "actor_id": actor,
            "role_at_decision": "owner",
            "tool_id": ADR_APPLY_TOOL,
            "action": ADR_APPLY_ACTION,
            "action_id": ADR_APPLY_ACTION,
            "subject": plan_id,
            "subject_hash": plan_hash,
            "workspace_id": workspace_id,
            "exact_path_allowlist": list(plan["exact_path_allowlist"]),
            "interface": "ui",
            "scope_type": "pre-code-architecture-adr-bundle",
        }
        policy = PolicyEngine(self.root, allowed_external_roots=configured_external_workspace_roots(), approval_auth_store=self.approval_auth_store).evaluate(PolicyRequest(action=ADR_APPLY_ACTION, path=str(workspace_root), text="\n".join(str(c.get("content") or "") for c in plan["changes"]), dry_run=False, approval_id=approval_id, tool_id=ADR_APPLY_TOOL, subject=plan_id, actor=actor, role_at_decision="owner", subject_hash=plan_hash, interface="ui", metadata=scope))
        if not policy.ok:
            return CommandResult(command, False, ExitCode.BLOCK, "Policy/RBAC/approval binding blocked ADR materialization.", data={"source_mutations_performed": False, "policy": policy.to_dict()}, findings=policy.findings)

        # The project-source write and the platform execution receipt are one bounded
        # transaction. If either side fails, source is restored to the preimage and an
        # existing receipt is restored as well. This prevents a surviving half-applied
        # state from forcing manual filesystem repair on the next run.
        execution_id = "adr-exec-" + _canonical_sha({"plan_hash": plan_hash, "approval_id": approval_id})[:24]
        applied_at = _now()
        receipt = {
            "schema_id": "devpilot.gsdlc13c02.architecture_adr_bundle_execution.v1",
            "execution_id": execution_id,
            "workspace_id": workspace_id,
            "plan_id": plan_id,
            "plan_hash": plan_hash,
            "approval_id": approval_id,
            "architecture_sha256": plan["architecture_sha256"],
            "paths": [{"relative_path": c["relative_path"], "sha256": c["postimage_sha256"]} for c in plan["changes"]],
            "atomic_all_or_nothing": True,
            "network_used": False,
            "external_api_used": False,
            "applied_at": applied_at,
        }
        receipt_path = self._receipt_path(workspace_id)
        receipt_before = receipt_path.read_bytes() if receipt_path.is_file() else None
        temps: list[tuple[Path, Path]] = []
        backups: list[tuple[Path, bytes | None]] = []
        try:
            # Prepare all postimages first. No project source changes before every temp
            # exists and matches the immutable plan hash.
            for change in plan["changes"]:
                target = (workspace_root / str(change["relative_path"])).resolve()
                try:
                    target.relative_to(workspace_root.resolve())
                except ValueError:
                    raise RuntimeError(f"target escaped workspace: {change['relative_path']}")
                if target.parent != (workspace_root / ADR_ROOT).resolve() or not target.parent.is_dir() or target.parent.is_symlink():
                    raise RuntimeError(f"governed ADR parent invalid: {change['relative_path']}")
                fd, raw_tmp = tempfile.mkstemp(prefix=f".{target.name}.", suffix=".tmp", dir=str(target.parent))
                tmp = Path(raw_tmp)
                with os.fdopen(fd, "wb") as handle:
                    handle.write(str(change["content"]).encode("utf-8")); handle.flush(); os.fsync(handle.fileno())
                if _sha_bytes(tmp.read_bytes()) != str(change["postimage_sha256"]):
                    raise RuntimeError(f"prepared temp hash mismatch: {change['relative_path']}")
                temps.append((target, tmp))

            for change, (target, tmp) in zip(plan["changes"], temps):
                before = target.read_bytes() if target.is_file() else None
                if before is not None and _sha_bytes(before) == str(change["postimage_sha256"]):
                    tmp.unlink(missing_ok=True)
                    continue
                backups.append((target, before))
                os.replace(tmp, target)
                if _sha_bytes(target.read_bytes()) != str(change["postimage_sha256"]):
                    raise RuntimeError(f"postimage hash mismatch: {change['relative_path']}")

            post = self._source_parity(workspace_root, [{"relative_path": c["relative_path"], "proposed_sha256": c["postimage_sha256"]} for c in plan["changes"]])
            if not post["all_exact"]:
                raise RuntimeError(f"ADR postimages do not match approved plan: {post['states']}")

            receipt_path.parent.mkdir(parents=True, exist_ok=True)
            self._atomic_json(receipt_path, receipt)
            if not self._receipt_valid(workspace_id=workspace_id, expected={
                "architecture_sha256": plan["architecture_sha256"],
                "adrs": [{"relative_path": c["relative_path"], "proposed_sha256": c["postimage_sha256"]} for c in plan["changes"]],
            }):
                raise RuntimeError("persisted ADR execution receipt is not bound to the approved immutable plan")
        except Exception as exc:
            # Compensating all-or-nothing restoration for the bounded source allowlist.
            for target, before in reversed(backups):
                try:
                    if before is None:
                        target.unlink(missing_ok=True)
                    else:
                        fd, raw_tmp = tempfile.mkstemp(prefix=f".{target.name}.rollback.", suffix=".tmp", dir=str(target.parent))
                        tmp = Path(raw_tmp)
                        with os.fdopen(fd, "wb") as handle:
                            handle.write(before); handle.flush(); os.fsync(handle.fileno())
                        os.replace(tmp, target)
                except Exception:
                    pass
            for _, tmp in temps:
                tmp.unlink(missing_ok=True)
            try:
                if receipt_before is None:
                    receipt_path.unlink(missing_ok=True)
                else:
                    fd, raw_tmp = tempfile.mkstemp(prefix=f".{receipt_path.name}.rollback.", suffix=".tmp", dir=str(receipt_path.parent))
                    tmp = Path(raw_tmp)
                    with os.fdopen(fd, "wb") as handle:
                        handle.write(receipt_before); handle.flush(); os.fsync(handle.fileno())
                    os.replace(tmp, receipt_path)
            except Exception:
                pass
            return self._block(command, "GSDLC13C02_ADR_ATOMIC_APPLY_BLOCK", "ADR materialization/receipt persistence failed and compensating restoration was attempted.", metadata={"error": str(exc), "paths": list(plan["exact_path_allowlist"])})

        runtime.update({"status": "APPLIED", "execution_id": execution_id, "applied_at": applied_at, "updated_at": _now(), "source_mutations_performed": True})
        state["architecture_adr_bundle"] = runtime
        return self._pass(command, "GSDLC13C02_ADR_BUNDLE_APPLIED_PASS", "Standalone ADR bundle materialized atomically from the approved frozen Architecture.", {"architecture_adr_bundle": self._runtime_public(runtime), "execution": receipt, "source_mutations_performed": True})

    def _receipt_path(self, workspace_id: str) -> Path:
        safe=re.sub(r"[^A-Za-z0-9_.-]", "_", str(workspace_id or ""))
        return self.root / "outputs" / "pre_code_wizard" / "gsdlc_13_c_02" / safe / "architecture_adr_bundle_execution.json"

    def _load_receipt(self, workspace_id: str) -> dict[str, Any]:
        path=self._receipt_path(workspace_id)
        if not path.is_file():return {}
        try:
            payload=json.loads(path.read_text(encoding="utf-8"))
            return payload if isinstance(payload,dict) else {}
        except Exception:return {}

    def _receipt_valid(self, *, workspace_id: str, expected: dict[str, Any]) -> bool:
        receipt = self._load_receipt(workspace_id)
        if receipt.get("schema_id") != "devpilot.gsdlc13c02.architecture_adr_bundle_execution.v1":
            return False
        if str(receipt.get("workspace_id") or "") != str(workspace_id or ""):
            return False
        if str(receipt.get("architecture_sha256") or "") != str(expected.get("architecture_sha256") or ""):
            return False
        approval_id = str(receipt.get("approval_id") or "")
        plan_id = str(receipt.get("plan_id") or "")
        plan_hash = str(receipt.get("plan_hash") or "")
        if not approval_id or not plan_id or not plan_hash or not str(receipt.get("execution_id") or ""):
            return False
        got = {str(x.get("relative_path") or ""): str(x.get("sha256") or "") for x in receipt.get("paths") or [] if isinstance(x, dict)}
        want = {str(x["relative_path"]): str(x["proposed_sha256"]) for x in expected.get("adrs") or []}
        if got != want or not bool(receipt.get("atomic_all_or_nothing")):
            return False

        # The receipt is evidence, not authority by itself. Re-bind it to the persisted
        # approval record so a copied/forged receipt cannot unlock downstream stages.
        shown = self.approvals.show(approval_id)
        if not shown.ok or not isinstance(shown.data, dict):
            return False
        record = shown.data.get("approval")
        if not isinstance(record, dict) or str(record.get("status") or "").lower() != "approved":
            return False
        if str(record.get("tool_id") or "") != ADR_APPLY_TOOL or str(record.get("action") or "") != ADR_APPLY_ACTION:
            return False
        if str(record.get("subject") or "") != plan_id:
            return False
        scope = record.get("scope") if isinstance(record.get("scope"), dict) else {}
        if str(scope.get("subject_hash") or "") != plan_hash:
            return False
        if str(scope.get("workspace_id") or "") != str(workspace_id or ""):
            return False
        if sorted(str(x) for x in scope.get("exact_path_allowlist") or []) != sorted(want):
            return False
        metadata = record.get("metadata") if isinstance(record.get("metadata"), dict) else {}
        if metadata.get("plan_hash") not in {None, "", plan_hash}:
            return False
        # Do not reclassify a historical successful apply as invalid merely because the
        # already-approved record's TTL elapsed after execution. PolicyEngine enforced
        # validity at apply time; recovery verifies persisted decision + exact binding.
        return True

    def _expected_from_frozen(self, *, workspace_root: Path, workspace_id: str, arch: dict[str, Any]) -> dict[str, Any] | CommandResult:
        command = "guided pre-code architecture ADR bundle"
        path = workspace_root / ARCH_PATH
        if not path.is_file():
            return self._block(command, "GSDLC13C02_ADR_ARCHITECTURE_SOURCE_MISSING_BLOCK", "Frozen Architecture source file is missing.", metadata={"relative_path": ARCH_PATH.as_posix()})
        raw = path.read_bytes(); content = raw.decode("utf-8-sig"); actual_sha = _sha_bytes(raw)
        approved_sha = str(arch.get("approved_sha256") or "")
        if approved_sha and approved_sha != actual_sha:
            return self._block(command, "GSDLC13C02_ADR_ARCHITECTURE_SHA_DRIFT_BLOCK", "Architecture source SHA no longer matches the frozen approved SHA.", metadata={"expected": approved_sha, "actual": actual_sha})
        parsed = parse_frontmatter_text(content, path=ARCH_PATH)
        updated = str(parsed.frontmatter.get("updated") or "1970-01-01")
        owner = str(parsed.frontmatter.get("owner") or "local-owner")
        approval_id = str(arch.get("approval_id") or "")
        extracted = self._extract_adrs(parsed.body)
        if isinstance(extracted, CommandResult):
            return extracted
        adr_root=(workspace_root / ADR_ROOT).resolve()
        try: adr_root.relative_to(workspace_root.resolve())
        except ValueError:
            return self._block(command, "GSDLC13C02_ADR_ROOT_SCOPE_BLOCK", "Governed ADR root escaped the active workspace.")
        if not adr_root.is_dir() or adr_root.is_symlink():
            return self._block(command, "GSDLC13C02_ADR_ROOT_REQUIRED_BLOCK", "The governed docs/02_architecture/adrs directory must already exist as part of the neutral Project Shell.")
        adrs = []
        for item in extracted:
            adr_id = item["adr_id"]; title = item["title"]; body = item["body"]
            rel = (ADR_ROOT / f"{adr_id}-{_safe_slug(title)}.md").as_posix()
            standalone = self._render_standalone(adr_id=adr_id, title=title, body=body, owner=owner, updated=updated, architecture_sha256=actual_sha, architecture_approval_id=approval_id, architecture_path=ARCH_PATH.as_posix())
            adrs.append({"adr_id": adr_id, "title": title, "relative_path": rel, "content": standalone, "proposed_sha256": _sha_bytes(standalone.encode("utf-8"))})
        return {"workspace_id": workspace_id, "architecture_sha256": actual_sha, "architecture_approval_id": approval_id, "adrs": adrs}

    def _extract_adrs(self, body: str) -> list[dict[str, str]] | CommandResult:
        command = "guided pre-code architecture ADR bundle"
        marker = re.search(r"^##\s+ADRs\s*$", body, re.M | re.I)
        if not marker:
            return self._block(command, "GSDLC13C02_ADR_SECTION_MISSING_BLOCK", "Frozen Architecture does not contain an ADR section.")
        tail = body[marker.end():]
        next_section = re.search(r"^##\s+", tail, re.M)
        section = tail[:next_section.start()] if next_section else tail
        matches = list(_ADR_HEADING.finditer(section))
        if not matches:
            return self._block(command, "GSDLC13C02_ADR_RECORDS_MISSING_BLOCK", "Frozen Architecture ADR section contains no material ADR records.")
        result: list[dict[str, str]] = []
        seen: set[str] = set()
        for index, match in enumerate(matches):
            adr_id = match.group(1).upper(); title = match.group(2).strip()
            if adr_id in seen:
                return self._block(command, "GSDLC13C02_ADR_DUPLICATE_ID_BLOCK", "Frozen Architecture contains duplicate ADR ids.", metadata={"adr_id": adr_id})
            seen.add(adr_id)
            start = match.end(); end = matches[index + 1].start() if index + 1 < len(matches) else len(section)
            body_text = section[start:end].strip()
            # ADR-001/002/004 use canonical Contexto/Decisión/Alternativas/Consecuencias.
            # ADR-003 in the already-approved C02_BR generator expresses the Owner technology
            # decision as Perfil propuesto/Decisión bloqueante + alternatives + consequences.
            canonical = all(re.search(rf"\*\*{re.escape(label)}(?:\*\*|:)", body_text, re.I) for label in ("Contexto", "Decisión", "Alternativas", "Consecuencias"))
            technology_profile = adr_id == "ADR-003" and bool(re.search(r"\*\*(?:Perfil propuesto para decisión Owner|Decisión bloqueante):\*\*", body_text, re.I)) and "Alternativas" in body_text and bool(re.search(r"\*\*Consecuencias:\*\*", body_text, re.I))
            if not canonical and not technology_profile:
                return self._block(command, "GSDLC13C02_ADR_STRUCTURE_BLOCK", "Embedded ADR lacks the approved decision structure required for deterministic standalone projection.", metadata={"adr_id": adr_id})
            result.append({"adr_id": adr_id, "title": title, "body": body_text})
        return result

    def _render_standalone(self, *, adr_id: str, title: str, body: str, owner: str, updated: str, architecture_sha256: str, architecture_approval_id: str, architecture_path: str) -> str:
        approval = f"inherited-from-architecture:{architecture_approval_id or 'unknown'}"
        return (
            "---\n"
            f'doc_id: "{adr_id}"\n'
            f'title: "{adr_id} — {title}"\n'
            'status: "frozen"\n'
            'version: "1.0.0"\n'
            f'owner: "{owner}"\n'
            f'updated: "{updated}"\n'
            f'approval: "{approval}"\n'
            f'source_architecture_sha256: "{architecture_sha256}"\n'
            f'source_architecture_path: "{architecture_path}"\n'
            "---\n\n"
            f"# {adr_id} — {title}\n\n"
            f"{body.strip()}\n\n"
            "## Provenance\n\n"
            f"- Derivado sin reinterpretación desde `{architecture_path}` FROZEN.\n"
            f"- Architecture SHA-256: `{architecture_sha256}`.\n"
            f"- Architecture approval: `{architecture_approval_id or 'N/D'}`.\n"
            "- La materialización standalone requiere un approval Owner separado ligado al plan multiarchivo; el receipt runtime conserva ese binding.\n\n"
            "## Riesgos\n\n"
            "- Si Architecture cambia, este ADR deja de ser válido y la revalidación debe bloquear por drift de SHA.\n"
            "- Este documento no amplía la decisión aprobada; solo proyecta la decisión ya contenida en Architecture.\n\n"
            "## Criterios PASS/BLOCK\n\n"
            "- PASS: contenido y SHA coinciden con la proyección determinística del Architecture FROZEN y el bundle fue aplicado con approval válido.\n"
            "- BLOCK: Architecture/preimage cambia, el ADR contiene drift o el approval no está exactamente ligado al plan.\n\n"
            "## Verificación\n\n"
            "- Verificar por el companion gate `Architecture ADRs` de Pre-code; no editar manualmente este archivo.\n"
        )

    def _recheck(self, *, workspace_root: Path, state: dict[str, Any], runtime: dict[str, Any]) -> CommandResult:
        command = "guided pre-code architecture ADR bundle recheck"
        plan = dict(runtime.get("plan") or {})
        if not plan or _canonical_sha({k: v for k, v in plan.items() if k != "plan_hash"}) != str(plan.get("plan_hash") or ""):
            return self._block(command, "GSDLC13C02_ADR_PLAN_TAMPER_BLOCK", "Stored ADR bundle plan hash no longer matches its immutable content.")
        arch = dict((state.get("stages") or {}).get("architecture") or {})
        expected = self._expected_from_frozen(workspace_root=workspace_root, workspace_id=str(plan.get("workspace_id") or ""), arch=arch)
        if isinstance(expected, CommandResult):
            return expected
        if str(expected["architecture_sha256"]) != str(plan.get("architecture_sha256") or ""):
            return self._block(command, "GSDLC13C02_ADR_ARCHITECTURE_RECHECK_BLOCK", "Frozen Architecture changed after ADR plan creation.")
        expected_by_path = {x["relative_path"]: x for x in expected["adrs"]}
        if sorted(expected_by_path) != sorted(plan.get("exact_path_allowlist") or []):
            return self._block(command, "GSDLC13C02_ADR_PATH_SET_DRIFT_BLOCK", "ADR path set changed after plan creation.")
        for change in plan.get("changes") or []:
            rel = str(change.get("relative_path") or ""); target = workspace_root / rel
            current = _sha_bytes(target.read_bytes()) if target.is_file() else ZERO_SHA256
            if current not in {str(change.get("preimage_sha256") or ""), str(change.get("postimage_sha256") or "")}:
                return self._block(command, "GSDLC13C02_ADR_PREIMAGE_DRIFT_BLOCK", "ADR target changed outside the immutable plan.", metadata={"relative_path": rel, "expected_preimage": change.get("preimage_sha256"), "current": current})
            exp = expected_by_path.get(rel)
            if not exp or str(exp["proposed_sha256"]) != str(change.get("postimage_sha256") or ""):
                return self._block(command, "GSDLC13C02_ADR_DERIVATION_DRIFT_BLOCK", "ADR deterministic projection changed after plan creation.", metadata={"relative_path": rel})
        return self._pass(command, "GSDLC13C02_ADR_RECHECK_PASS", "Architecture and all ADR plan preimages remain exact.", {"source_mutations_performed": False})

    def _source_parity(self, workspace_root: Path, adrs: list[dict[str, Any]]) -> dict[str, Any]:
        states: dict[str, str] = {}; preimages: dict[str, str] = {}; before_text: dict[str, str] = {}
        all_exact = True
        for item in adrs:
            rel = str(item["relative_path"]); target = workspace_root / rel; proposed = str(item["proposed_sha256"])
            if not target.exists():
                state = "MISSING"; sha = ZERO_SHA256; text = ""
            elif not target.is_file() or target.is_symlink():
                state = "DRIFT"; sha = "invalid"; text = ""; all_exact = False
            else:
                raw = target.read_bytes(); sha = _sha_bytes(raw); text = raw.decode("utf-8-sig")
                state = "EXACT" if sha == proposed else "DRIFT"
                if state != "EXACT": all_exact = False
            states[rel] = state; preimages[rel] = sha; before_text[rel] = text
            if state != "EXACT": all_exact = False
        return {"states": states, "preimages": preimages, "before_text": before_text, "all_exact": all_exact}

    @staticmethod
    def _runtime_public(runtime: dict[str, Any]) -> dict[str, Any]:
        return {k: deepcopy(v) for k, v in runtime.items() if k not in {"plan", "adrs"}}

    @staticmethod
    def _plan_public(plan: dict[str, Any]) -> dict[str, Any]:
        return {
            "schema_id": plan.get("schema_id"), "plan_id": plan.get("plan_id"), "plan_hash": plan.get("plan_hash"),
            "architecture_sha256": plan.get("architecture_sha256"), "architecture_approval_id": plan.get("architecture_approval_id"),
            "exact_path_allowlist": list(plan.get("exact_path_allowlist") or []),
            "changes": [{k: c.get(k) for k in ("adr_id", "title", "relative_path", "preimage_sha256", "postimage_sha256", "diff")} for c in plan.get("changes") or []],
            "source_mutations_performed": False,
        }

    @staticmethod
    def _atomic_json(path: Path, value: Any) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, raw_tmp = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent))
        tmp = Path(raw_tmp)
        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
                json.dump(value, handle, ensure_ascii=False, sort_keys=True, indent=2); handle.write("\n"); handle.flush(); os.fsync(handle.fileno())
            os.replace(tmp, path)
        finally:
            tmp.unlink(missing_ok=True)

    @staticmethod
    def _pass(command: str, finding_id: str, message: str, data: dict[str, Any]) -> CommandResult:
        return CommandResult(command, True, ExitCode.PASS, message, data=data, findings=[Finding(finding_id, message, Severity.INFO)])

    @staticmethod
    def _block(command: str, finding_id: str, message: str, *, metadata: dict[str, Any] | None = None) -> CommandResult:
        return CommandResult(command, False, ExitCode.BLOCK, message, data={"source_mutations_performed": False}, findings=[Finding(finding_id, message, Severity.BLOCK, metadata=metadata or {})])
