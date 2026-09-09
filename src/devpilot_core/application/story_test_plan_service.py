from __future__ import annotations

import hashlib
import json
import os
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.story_execution import StoryExecutionStatus, StoryExecutionStore
from devpilot_core.testing import TestImpactAnalyzerV2, TestImpactV2Options


SCHEMA_ID = "SCHEMA-DEVPL-GSDLC-10-A-STORY-TEST-PLAN-V1"
SCHEMA_VERSION = "1.0.0"
RUNTIME_SEGMENT = ("outputs", "story_execution", "gsdlc_10_a")
_SENSITIVE_PREFIXES = (
    ".devpilot/",
    "docs/schemas/",
    "src/devpilot_core/policy",
    "src/devpilot_core/security",
    "src/devpilot_core/approval",
    "src/devpilot_core/rbac",
    "src/devpilot_core/quality",
    "src/devpilot_core/testing",
    "src/devpilot_core/cli.py",
    "pyproject.toml",
)
_CRITICALITY_RANK = {"P0": 4, "P1": 3, "P2": 2, "P3": 1}


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _parse_utc(value: str) -> datetime:
    text = str(value).strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    parsed = datetime.fromisoformat(text)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _canonical_sha(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=str(path.parent))
    temp = Path(name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True, ensure_ascii=False)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp, path)
    finally:
        temp.unlink(missing_ok=True)


class StoryTestPlanApplicationService:
    """GSDLC-10-A story-bound Test Impact/Test Plan boundary.

    This service deliberately does *not* execute tests.  It consumes an already
    immutable SourceChangePlan, reuses Test Impact v2, derives an explainable
    StoryTestPlan, and persists only runtime planning/review evidence under the
    active project workspace.  Full-regression signals are informational only.
    """

    def __init__(
        self,
        platform_root: Path,
        *,
        context_resolver,
        source_plan_loader: Callable[..., CommandResult],
    ) -> None:
        self.platform_root = Path(platform_root).resolve()
        self.context_resolver = context_resolver
        self.source_plan_loader = source_plan_loader

    def create(self, *, source_plan_id: str, source_plan_hash: str, actor: str, actor_role: str) -> CommandResult:
        command = "story test plan create"
        if actor_role not in {"owner", "developer"}:
            return self._block(command, "GSDLC10A_PLAN_ROLE_BLOCK", "StoryTestPlan creation requires owner or developer human role.")
        context, failure = self._context(command)
        if failure:
            return failure
        assert context is not None

        source, failure = self._source_plan(command, source_plan_id, source_plan_hash)
        if failure:
            return failure
        assert source is not None

        story, failure = self._story(command, context)
        if failure:
            return failure
        assert story is not None
        if story.status is not StoryExecutionStatus.CHANGES_READY:
            return self._block(
                command,
                "GSDLC10A_STORY_NOT_CHANGES_READY_BLOCK",
                f"Story must be CHANGES_READY before validation planning; current={story.status.value}.",
                metadata={"story_execution_id": story.execution_id, "status": story.status.value},
            )
        if str(source.get("story_execution_id") or "") != story.execution_id:
            return self._block(command, "GSDLC10A_STORY_PLAN_BINDING_BLOCK", "SourceChangePlan is not bound to the current StoryExecution identity.")

        changed_paths = sorted({str(path).replace("\\", "/") for path in source.get("exact_path_allowlist", []) if str(path).strip()})
        if not changed_paths:
            return self._block(command, "GSDLC10A_CHANGED_PATHS_EMPTY_BLOCK", "SourceChangePlan does not contain an exact changed-path allowlist.")

        impact_result = TestImpactAnalyzerV2(
            self.platform_root,
            TestImpactV2Options(changed_paths=tuple(changed_paths)),
        ).analyze()
        if not impact_result.ok:
            return CommandResult(
                command=command,
                ok=False,
                exit_code=ExitCode.BLOCK,
                message="Test Impact v2 blocked StoryTestPlan derivation.",
                data={"test_impact": impact_result.to_dict(), "source_mutations_performed": False},
                findings=[Finding("GSDLC10A_TEST_IMPACT_BLOCK", "Test Impact v2 blocked StoryTestPlan derivation.", Severity.BLOCK), *impact_result.findings],
            )

        impact_data = dict(impact_result.data or {})
        deterministic_impact = self._deterministic_impact(impact_data)
        impact_hash = _canonical_sha(deterministic_impact)
        matched_contracts = deterministic_impact["matched_contracts"]
        matched_rules = deterministic_impact["matched_rules"]
        unknown_paths = deterministic_impact["unmatched_paths"]
        sensitive_paths = [path for path in changed_paths if self._sensitive_path(path)]
        required_tests, recommended_tests, test_reasons, test_policy = self._test_sets(
            impact_data=impact_data,
            matched_contracts=matched_contracts,
            matched_rules=matched_rules,
            sensitive_paths=sensitive_paths,
        )
        if sensitive_paths and not required_tests:
            return self._block(
                command,
                "GSDLC10A_SENSITIVE_UNDERTESTING_BLOCK",
                "Sensitive changed paths require at least one deterministic required test; Test Impact produced none.",
                metadata={"sensitive_paths": sensitive_paths},
            )

        recommendation_report = dict(impact_data.get("recommendation_report") or {})
        residual = dict(recommendation_report.get("residual_risk") or {})
        full_required = bool(residual.get("full_regression_required"))
        plan_core: dict[str, Any] = {
            "schema_id": SCHEMA_ID,
            "schema_version": SCHEMA_VERSION,
            "workspace_id": str(context.active_workspace_id),
            "story_execution_id": story.execution_id,
            "story_id": story.story_id,
            "story_version": story.story_version,
            "story_state_sha256": story.to_dict()["state_sha256"],
            "source_change_plan_id": str(source["plan_id"]),
            "source_change_plan_hash": str(source["plan_hash"]),
            "changed_paths": changed_paths,
            "test_impact_report_hash": impact_hash,
            "matched_contracts": matched_contracts,
            "matched_rules": matched_rules,
            "required_tests": required_tests,
            "recommended_tests": recommended_tests,
            "test_reasons": test_reasons,
            "test_policy": test_policy,
            "unknown_impact": {
                "paths": unknown_paths,
                "manual_review_required": bool(unknown_paths),
                "fail_closed": True,
            },
            "sensitive_impact": {
                "paths": sensitive_paths,
                "present": bool(sensitive_paths),
                "required_tests_total": len(required_tests),
                "required_tests_unwaivable": True if sensitive_paths else False,
            },
            "full_regression_signal": {
                "required_before_backlog_or_release_closure": full_required,
                "informational_only": True,
                "execution_authorized": False,
                "logical_full_runs_allowed_in_gsdlc_10_a": 0,
                "profile_authority": "frx-v2.4-current",
            },
            "policy": {
                "free_form_test_command_allowed": False,
                "test_execution_performed": False,
                "waiver_requires_human_owner": True,
                "p0_required_test_waiver_allowed": False,
                "sensitive_required_test_waiver_allowed": False,
                "model_or_agent_can_approve_or_waive": False,
            },
            "provenance": {
                "engine": "TestImpactAnalyzerV2",
                "test_contract_registry": str((impact_data.get("summary") or {}).get("registry_path") or ".devpilot/testing/test_contract_registry_v2.json"),
                "test_impact_rules": str((impact_data.get("summary") or {}).get("rules_path") or ".devpilot/testing/test_impact_rules.json"),
                "source_change_plan_hash": str(source["plan_hash"]),
            },
            "safety": {
                "local_first": True,
                "runtime_only": True,
                "source_mutations_performed": False,
                "tests_executed": False,
                "network_used": False,
                "external_api_used": False,
                "full_regression_started": False,
            },
        }
        plan_hash = _canonical_sha(plan_core)
        plan_id = f"story-test-plan-{_canonical_sha({'story_execution_id': story.execution_id, 'source_change_plan_hash': source['plan_hash'], 'impact_hash': impact_hash})[:24]}"
        plan = {**plan_core, "test_plan_id": plan_id, "test_plan_hash": plan_hash}
        record = {
            "plan": plan,
            "status": "REVIEW_REQUIRED" if unknown_paths else "DRAFT",
            "review": None,
            "waivers": [],
            "created_at_utc": _now(),
            "created_by": actor,
            "created_by_role": actor_role,
            "test_impact_report": deterministic_impact,
        }
        path = self._record_path(context.effective_workspace_root, str(context.active_workspace_id), plan_id)
        if path.is_file():
            existing = self._read(path)
            if existing and str((existing.get("plan") or {}).get("test_plan_hash") or "") == plan_hash:
                projected = self._project(existing)
                return self._pass(command, "StoryTestPlan already exists; deterministic idempotent result returned.", {"story_test_plan": projected, "idempotent": True})
            return self._block(command, "GSDLC10A_IMMUTABLE_PLAN_COLLISION_BLOCK", "Existing StoryTestPlan identifier has different immutable content.")
        _atomic_json(path, record)
        return self._pass(command, "StoryTestPlan derived from immutable SourceChangePlan and Test Impact v2; no tests executed.", {"story_test_plan": self._project(record), "idempotent": False})

    def get(self, *, test_plan_id: str) -> CommandResult:
        command = "story test plan get"
        context, failure = self._context(command)
        if failure:
            return failure
        assert context is not None
        record = self._read(self._record_path(context.effective_workspace_root, str(context.active_workspace_id), test_plan_id))
        if record is None:
            return self._block(command, "GSDLC10A_TEST_PLAN_MISSING_BLOCK", "StoryTestPlan does not exist.")
        integrity = self._record_integrity(command, record)
        if integrity:
            return integrity
        source = dict(record["plan"])
        _, failure = self._source_plan(command, str(source["source_change_plan_id"]), str(source["source_change_plan_hash"]))
        if failure:
            return failure
        return self._pass(command, "StoryTestPlan loaded with source-plan binding intact.", {"story_test_plan": self._project(record)})

    def decide(
        self,
        *,
        test_plan_id: str,
        test_plan_hash: str,
        decision: str,
        actor: str,
        actor_role: str,
        reason: str | None = None,
        waived_test_ids: list[str] | None = None,
        ttl_minutes: int = 60,
        authority_source: str = "human-session",
    ) -> CommandResult:
        command = "story test plan decision"
        context, failure = self._context(command)
        if failure:
            return failure
        assert context is not None
        path = self._record_path(context.effective_workspace_root, str(context.active_workspace_id), test_plan_id)
        record = self._read(path)
        if record is None:
            return self._block(command, "GSDLC10A_TEST_PLAN_MISSING_BLOCK", "StoryTestPlan does not exist.")
        integrity = self._record_integrity(command, record)
        if integrity:
            return integrity
        plan = dict(record["plan"])
        if str(plan.get("test_plan_hash")) != str(test_plan_hash or ""):
            return self._block(command, "GSDLC10A_TEST_PLAN_HASH_MISMATCH_BLOCK", "Provided StoryTestPlan hash is stale or does not match the immutable plan.")
        _, failure = self._source_plan(command, str(plan["source_change_plan_id"]), str(plan["source_change_plan_hash"]))
        if failure:
            return failure

        action = str(decision).strip().upper()
        if authority_source != "human-session":
            return self._block(command, "GSDLC10A_AGENT_AUTHORITY_BLOCK", "Agent/model authority cannot approve, reject or waive StoryTestPlan requirements.")
        if action == "WAIVE":
            result = self._waive(record, actor=actor, actor_role=actor_role, reason=str(reason or ""), waived_test_ids=waived_test_ids or [], ttl_minutes=ttl_minutes)
            if not result.ok:
                return result
            _atomic_json(path, record)
            return self._pass(command, "Owner-bound waiver recorded; required-test policy remains fail-closed.", {"story_test_plan": self._project(record), "waiver": result.data["waiver"]})
        if action not in {"APPROVE", "REJECT"}:
            return self._block(command, "GSDLC10A_DECISION_BLOCK", "Decision must be APPROVE, REJECT or WAIVE.")
        if actor_role not in {"owner", "developer"}:
            return self._block(command, "GSDLC10A_REVIEW_ROLE_BLOCK", "StoryTestPlan review requires owner or developer role.")
        if action == "APPROVE" and actor_role != "owner":
            return self._block(command, "GSDLC10A_APPROVAL_ROLE_BLOCK", "Only owner may approve a StoryTestPlan.")
        if action == "APPROVE" and self._expired_waivers(record):
            return self._block(command, "GSDLC10A_EXPIRED_WAIVER_BLOCK", "StoryTestPlan has expired waivers; remove/renew them before approval.")
        if action == "APPROVE" and (plan.get("unknown_impact") or {}).get("paths") and not str(reason or "").strip():
            return self._block(command, "GSDLC10A_UNKNOWN_REVIEW_REASON_BLOCK", "Unknown impact requires an explicit human review reason before approval.")
        record["status"] = "APPROVED" if action == "APPROVE" else "REJECTED"
        record["review"] = {
            "decision": action,
            "actor": actor,
            "actor_role": actor_role,
            "authority_source": "human-session",
            "reason": str(reason or "").strip() or None,
            "decided_at_utc": _now(),
        }
        _atomic_json(path, record)
        return self._pass(command, f"StoryTestPlan {record['status']} by authenticated human review.", {"story_test_plan": self._project(record)})

    def _waive(self, record: dict[str, Any], *, actor: str, actor_role: str, reason: str, waived_test_ids: list[str], ttl_minutes: int) -> CommandResult:
        command = "story test plan waiver"
        if actor_role != "owner":
            return self._block(command, "GSDLC10A_WAIVER_ROLE_BLOCK", "Only owner may create StoryTestPlan waivers.")
        if not reason.strip():
            return self._block(command, "GSDLC10A_WAIVER_REASON_BLOCK", "Waiver reason is required.")
        if not (1 <= int(ttl_minutes) <= 1440):
            return self._block(command, "GSDLC10A_WAIVER_EXPIRY_BLOCK", "Waiver TTL must be between 1 and 1440 minutes.")
        plan = dict(record["plan"])
        requested = sorted({str(x) for x in waived_test_ids if str(x).strip()})
        required = set(str(x) for x in plan.get("required_tests", []))
        if not requested or any(test not in required for test in requested):
            return self._block(command, "GSDLC10A_WAIVER_TEST_SET_BLOCK", "Waiver must reference one or more tests currently classified as required.")
        if (plan.get("sensitive_impact") or {}).get("present"):
            return self._block(command, "GSDLC10A_SENSITIVE_WAIVER_BLOCK", "Required tests for sensitive impact cannot be waived.")
        policy = dict(plan.get("test_policy") or {})
        blocked = [test for test in requested if not bool((policy.get(test) or {}).get("waivable"))]
        if blocked:
            return self._block(command, "GSDLC10A_CRITICAL_WAIVER_BLOCK", "P0 or otherwise unwaivable required tests cannot be waived.", metadata={"blocked_tests": blocked})
        created = datetime.now(timezone.utc).replace(microsecond=0)
        expires = created + timedelta(minutes=int(ttl_minutes))
        waiver = {
            "waiver_id": f"story-test-waiver-{_canonical_sha({'plan': plan['test_plan_hash'], 'tests': requested, 'actor': actor, 'reason': reason, 'expires': expires.isoformat()})[:24]}",
            "test_plan_id": plan["test_plan_id"],
            "test_plan_hash": plan["test_plan_hash"],
            "waived_test_ids": requested,
            "reason": reason.strip(),
            "actor": actor,
            "actor_role": actor_role,
            "authority_source": "human-session",
            "created_at_utc": created.isoformat().replace("+00:00", "Z"),
            "expires_at_utc": expires.isoformat().replace("+00:00", "Z"),
        }
        record.setdefault("waivers", []).append(waiver)
        return self._pass(command, "Bounded owner waiver recorded.", {"waiver": waiver})

    def _deterministic_impact(self, impact_data: dict[str, Any]) -> dict[str, Any]:
        summary = dict(impact_data.get("summary") or {})
        recommendation = dict(impact_data.get("recommendation_report") or {})
        return {
            "schema_id": "SCHEMA-DEVPL-GSDLC-10-A-TEST-IMPACT-REPORT-V1",
            "schema_version": "1.0.0",
            "changed_paths": sorted(str(x) for x in impact_data.get("changed_paths", [])),
            "matched_contracts": sorted(
                [self._contract_projection(x) for x in impact_data.get("matched_contracts", []) if isinstance(x, dict)],
                key=lambda x: x["contract_id"],
            ),
            "matched_rules": sorted(
                [self._rule_projection(x) for x in recommendation.get("matched_rules", []) if isinstance(x, dict)],
                key=lambda x: x["rule_id"],
            ),
            "unmatched_paths": sorted(str(x) for x in impact_data.get("unmatched_paths", [])),
            "recommended_tests": sorted(set(str(x) for x in impact_data.get("recommended_tests", []))),
            "recommended_profiles": sorted(set(str(x) for x in summary.get("recommended_profiles", []))),
            "summary": {
                "changed_paths_total": int(summary.get("changed_paths_total", 0) or 0),
                "matched_contracts_total": int(summary.get("matched_contracts_total", 0) or 0),
                "recommended_tests_total": int(summary.get("recommended_tests_total", 0) or 0),
                "unmatched_paths_total": int(summary.get("unmatched_paths_total", 0) or 0),
                "p0_selected_total": int(summary.get("p0_selected_total", 0) or 0),
                "p1_selected_total": int(summary.get("p1_selected_total", 0) or 0),
                "tests_executed": False,
                "network_used": False,
                "external_api_used": False,
                "source_mutations_performed": False,
            },
        }

    @staticmethod
    def _contract_projection(item: dict[str, Any]) -> dict[str, Any]:
        return {
            "contract_id": str(item.get("contract_id") or ""),
            "domain": str(item.get("domain") or ""),
            "criticality": str(item.get("criticality") or "P3"),
            "risk_level": str(item.get("risk_level") or "low"),
            "matched_paths": sorted(str(x) for x in item.get("matched_paths", [])),
            "match_reasons": sorted(str(x) for x in item.get("match_reasons", [])),
            "test_files": sorted(set(str(x) for x in item.get("test_files", []))),
        }

    @staticmethod
    def _rule_projection(item: dict[str, Any]) -> dict[str, Any]:
        return {
            "rule_id": str(item.get("rule_id") or ""),
            "label": str(item.get("label") or item.get("rule_id") or ""),
            "profiles": sorted(set(str(x) for x in item.get("profiles", []))),
            "recommended_tests": sorted(set(str(x) for x in item.get("recommended_tests", []))),
            "escalation": dict(item.get("escalation") or {}),
        }

    def _test_sets(
        self,
        *,
        impact_data: dict[str, Any],
        matched_contracts: list[dict[str, Any]],
        matched_rules: list[dict[str, Any]],
        sensitive_paths: list[str],
    ) -> tuple[list[str], list[str], dict[str, list[str]], dict[str, dict[str, Any]]]:
        all_tests = sorted(set(str(x) for x in impact_data.get("recommended_tests", [])))
        required: set[str] = set()
        reasons: dict[str, list[str]] = {test: [] for test in all_tests}
        max_criticality: dict[str, str] = {}
        for contract in matched_contracts:
            criticality = str(contract.get("criticality") or "P3")
            for test in contract.get("test_files", []):
                test = str(test)
                if test not in reasons:
                    reasons[test] = []
                reasons[test].append(f"contract:{contract['contract_id']}:{criticality}")
                previous = max_criticality.get(test, "P3")
                if _CRITICALITY_RANK.get(criticality, 0) > _CRITICALITY_RANK.get(previous, 0):
                    max_criticality[test] = criticality
                else:
                    max_criticality.setdefault(test, previous)
                if criticality in {"P0", "P1"}:
                    required.add(test)
        for rule in matched_rules:
            for test in rule.get("recommended_tests", []):
                test = str(test)
                reasons.setdefault(test, []).append(f"rule:{rule['rule_id']}")
        if sensitive_paths:
            required.update(all_tests)
        required_list = sorted(required)
        recommended = sorted(test for test in all_tests if test not in required)
        policy: dict[str, dict[str, Any]] = {}
        for test in required_list:
            criticality = max_criticality.get(test, "P1" if sensitive_paths else "P2")
            policy[test] = {
                "criticality": criticality,
                "waivable": bool(not sensitive_paths and criticality != "P0"),
                "reason": "sensitive-impact" if sensitive_paths else ("P0-unwaivable" if criticality == "P0" else "owner-waiver-policy"),
            }
        return required_list, recommended, {k: sorted(set(v)) for k, v in reasons.items()}, policy

    def _record_integrity(self, command: str, record: dict[str, Any]) -> CommandResult | None:
        plan = dict(record.get("plan") or {})
        expected = str(plan.get("test_plan_hash") or "")
        core = {k: v for k, v in plan.items() if k not in {"test_plan_id", "test_plan_hash"}}
        if not expected or expected != _canonical_sha(core):
            return self._block(command, "GSDLC10A_TEST_PLAN_TAMPER_BLOCK", "StoryTestPlan immutable hash no longer matches its contents.")
        return None

    def _project(self, record: dict[str, Any]) -> dict[str, Any]:
        plan = dict(record["plan"])
        now = datetime.now(timezone.utc)
        active_waivers = []
        expired_waivers = []
        waived: set[str] = set()
        for waiver in record.get("waivers", []):
            item = dict(waiver)
            try:
                expired = _parse_utc(str(item["expires_at_utc"])) <= now
            except Exception:
                expired = True
            (expired_waivers if expired else active_waivers).append(item)
            if not expired:
                waived.update(str(x) for x in item.get("waived_test_ids", []))
        return {
            **plan,
            "status": str(record.get("status") or "DRAFT"),
            "review": record.get("review"),
            "active_waivers": active_waivers,
            "expired_waivers": expired_waivers,
            "effective_required_tests": [x for x in plan.get("required_tests", []) if x not in waived],
            "created_at_utc": record.get("created_at_utc"),
            "created_by": record.get("created_by"),
            "created_by_role": record.get("created_by_role"),
            "test_impact_report": record.get("test_impact_report"),
        }

    def _expired_waivers(self, record: dict[str, Any]) -> list[dict[str, Any]]:
        return list(self._project(record).get("expired_waivers", []))

    def _context(self, command: str):
        context = self.context_resolver.resolve()
        if not context.configured or not context.valid or not context.active_workspace_id or not context.active_workspace_root:
            return None, self._block(command, "GSDLC10A_PROJECT_CONTEXT_BLOCK", "StoryTestPlan requires an active server-validated project workspace.")
        return context, None

    def _story(self, command: str, context):
        store = StoryExecutionStore(context.effective_workspace_root, workspace_id=str(context.active_workspace_id))
        try:
            state = store.load_state()
        except Exception as exc:
            return None, self._block(command, "GSDLC10A_STORY_STATE_BLOCK", f"StoryExecution state is invalid: {type(exc).__name__}: {exc}")
        if state is None:
            return None, self._block(command, "GSDLC10A_STORY_MISSING_BLOCK", "Active workspace has no StoryExecution state.")
        return state, None

    def _source_plan(self, command: str, plan_id: str, plan_hash: str):
        loaded = self.source_plan_loader(plan_id=plan_id)
        if not loaded.ok:
            return None, CommandResult(command, False, ExitCode.BLOCK, "SourceChangePlan dependency blocked StoryTestPlan.", data={"dependency": loaded.to_dict()}, findings=[Finding("GSDLC10A_SOURCE_PLAN_DEPENDENCY_BLOCK", "SourceChangePlan dependency blocked StoryTestPlan.", Severity.BLOCK), *loaded.findings])
        plan = dict((loaded.data or {}).get("plan") or {})
        if str(plan.get("plan_hash") or "") != str(plan_hash or ""):
            return None, self._block(command, "GSDLC10A_STALE_CHANGE_PLAN_HASH_BLOCK", "Provided SourceChangePlan hash is stale or does not match immutable source plan.")
        return plan, None

    def _record_root(self, workspace_root: Path, workspace_id: str) -> Path:
        safe = "".join(c if c.isalnum() or c in "-_" else "-" for c in str(workspace_id)).strip("-") or "workspace"
        return Path(workspace_root).resolve().joinpath(*RUNTIME_SEGMENT, safe, "test_plans")

    def _record_path(self, workspace_root: Path, workspace_id: str, test_plan_id: str) -> Path:
        if not str(test_plan_id).startswith("story-test-plan-") or len(str(test_plan_id)) != 40:
            return self._record_root(workspace_root, workspace_id) / "__invalid__.json"
        return self._record_root(workspace_root, workspace_id) / f"{test_plan_id}.json"

    @staticmethod
    def _read(path: Path) -> dict[str, Any] | None:
        if not path.is_file():
            return None
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            return payload if isinstance(payload, dict) else None
        except (OSError, json.JSONDecodeError):
            return None

    @staticmethod
    def _sensitive_path(path: str) -> bool:
        normalized = str(path).replace("\\", "/").lower()
        return any(normalized == prefix.rstrip("/") or normalized.startswith(prefix) for prefix in _SENSITIVE_PREFIXES)

    @staticmethod
    def _pass(command: str, message: str, data: dict[str, Any]) -> CommandResult:
        return CommandResult(command, True, ExitCode.PASS, message, data={**data, "source_mutations_performed": False, "tests_executed": False, "network_used": False, "external_api_used": False}, findings=[Finding("GSDLC10A_PASS", message, Severity.INFO)])

    @staticmethod
    def _block(command: str, code: str, message: str, *, metadata: dict[str, Any] | None = None) -> CommandResult:
        return CommandResult(command, False, ExitCode.BLOCK, message, data={"source_mutations_performed": False, "tests_executed": False, **(metadata or {})}, findings=[Finding(code, message, Severity.BLOCK, metadata=metadata or {})])
