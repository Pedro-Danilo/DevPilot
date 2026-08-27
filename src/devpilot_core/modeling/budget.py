from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.store import LocalStore


@dataclass(frozen=True)
class BudgetLedger:
    """Local model budget ledger backed by LocalStore cost_events.

    Sprint 48 records monetary and compute estimates without storing prompts or
    raw model payloads. Local providers normally produce zero monetary cost;
    external providers remain disabled by default.
    """

    root: Path

    def record_model_result(self, result: CommandResult, *, source: str = "model-cli") -> str | None:
        data = result.data or {}
        summary = dict(data.get("summary") or {})
        provider_payload = dict(data.get("provider") or {})
        result_payload = dict(data.get("result") or {})
        provider = str(summary.get("provider") or provider_payload.get("provider_id") or result_payload.get("provider") or "unknown")
        if not provider or provider == "unknown":
            return None
        task = str(summary.get("task") or result_payload.get("task") or "unknown")
        model = str(summary.get("model") or result_payload.get("model") or provider_payload.get("default_model") or "unknown")
        tokens = int(summary.get("tokens_estimated") or result_payload.get("tokens_estimated") or 0)
        monetary_cost = float(summary.get("cost_estimate_usd") or result_payload.get("cost_estimate_usd") or 0.0)
        prompt_reference = dict(data.get("prompt_reference") or {})
        metadata = {
            "source": source,
            "task": task,
            "model": model,
            "tokens_estimated": tokens,
            "monetary_cost_estimate_usd": monetary_cost,
            "compute_estimate_units": tokens,
            "result_ok": bool(result.ok),
            "exit_code": int(result.exit_code),
            "external_api_used": bool(summary.get("external_api_used") or result_payload.get("external_api_used") or False),
            "payload_redacted": True,
            "prompt_stored": False,
            "content_stored": False,
            "preliminary": True,
        }
        if prompt_reference:
            metadata["prompt_id"] = prompt_reference.get("prompt_id")
            metadata["prompt_version"] = prompt_reference.get("version")
            metadata["prompt_inputs_used"] = prompt_reference.get("inputs_used") or []
            metadata["prompt_payload_redacted"] = True
        return LocalStore(self.root).record_cost_event(
            provider=provider,
            estimated_cost_usd=monetary_cost,
            actual_cost_usd=0.0,
            budget_limit_usd=0.0,
            budget_used_usd=0.0,
            metadata=metadata,
        )

    def status(self, *, limit: int = 20) -> CommandResult:
        store = LocalStore(self.root)
        summary = store.cost_events_summary()
        events = store.list_cost_events(limit=limit)
        unsafe_events = [event for event in events if _metadata_has_prompt_or_secret(event.get("metadata", {}))]
        findings = [Finding(id="MODEL_BUDGET_LEDGER_STATUS_PASS", message="Model budget ledger status computed from local cost_events.", severity=Severity.INFO)]
        if unsafe_events:
            findings.append(
                Finding(
                    id="MODEL_BUDGET_LEDGER_UNSAFE_METADATA_BLOCKED",
                    message="One or more cost_events appear to contain prompt/secret-like metadata.",
                    severity=Severity.BLOCK,
                    metadata={"unsafe_events_total": len(unsafe_events)},
                )
            )
        ok = not unsafe_events
        return CommandResult(
            command="model budget status",
            ok=ok,
            exit_code=ExitCode.PASS if ok else ExitCode.BLOCK,
            message="Model budget ledger status passed." if ok else "Model budget ledger contains unsafe metadata.",
            data={
                "summary": {
                    **summary,
                    "events_returned": len(events),
                    "unsafe_events_total": len(unsafe_events),
                    "external_api_used": False,
                    "preliminary": True,
                },
                "events": events,
                "notes": [
                    "BudgetLedger records local monetary estimates and compute units only.",
                    "Prompts, completions and raw secrets are not stored in cost_events metadata.",
                ],
            },
            findings=findings,
        )


def _metadata_has_prompt_or_secret(metadata: dict[str, Any]) -> bool:
    suspicious_keys = {"prompt", "completion", "content", "raw_prompt", "raw_response", "api_key", "secret", "password", "token"}
    keys = {str(key).lower() for key in metadata.keys()}
    if keys & suspicious_keys:
        return True
    text = str(metadata).lower()
    return any(marker in text for marker in ("sk-", "api_key=", "password=", "secret="))


# GSDLC-06-D successor contracts -------------------------------------------------
from dataclasses import field
from datetime import datetime, timezone
from enum import Enum
import json
import os
import tempfile
from math import ceil
from typing import Mapping


class EstimateState(str, Enum):
    KNOWN = "known"
    ESTIMATED = "estimated"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class TokenCostEstimate:
    """Explainable pre/post-run token and monetary estimate.

    ``UNKNOWN`` monetary cost is represented by ``None`` and can never be
    serialized as a synthetic zero.  Local/mock zero-cost routes are ``KNOWN``.
    """

    input_tokens: int
    output_tokens: int
    cost_state: EstimateState
    cost_usd: float | None
    currency: str = "USD"
    source: str = "unknown"
    freshness: str = "unknown"

    def __post_init__(self) -> None:
        if self.input_tokens < 0 or self.output_tokens < 0:
            raise ValueError("token estimates must be non-negative")
        if self.cost_state is EstimateState.UNKNOWN and self.cost_usd is not None:
            raise ValueError("unknown cost must use cost_usd=None")
        if self.cost_state is not EstimateState.UNKNOWN and (self.cost_usd is None or self.cost_usd < 0):
            raise ValueError("known/estimated cost requires non-negative cost_usd")
        if not self.currency.strip():
            raise ValueError("currency is required")

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens

    def to_dict(self) -> dict[str, Any]:
        return {
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.total_tokens,
            "cost_state": self.cost_state.value,
            "cost_usd": self.cost_usd,
            "currency": self.currency,
            "source": self.source,
            "freshness": self.freshness,
        }


@dataclass(frozen=True)
class BudgetScopeLimit:
    max_tokens: int
    max_cost_usd: float | None = None

    def __post_init__(self) -> None:
        if self.max_tokens <= 0:
            raise ValueError("scope max_tokens must be positive")
        if self.max_cost_usd is not None and self.max_cost_usd < 0:
            raise ValueError("scope max_cost_usd cannot be negative")

    def to_dict(self) -> dict[str, Any]:
        return {"max_tokens": self.max_tokens, "max_cost_usd": self.max_cost_usd}


BUDGET_SCOPES = ("request", "artifact", "story", "session", "day", "workspace")


@dataclass(frozen=True)
class TokenBudgetPolicy:
    """Immutable server-side hard budgets from request through workspace.

    The policy object is frozen deliberately: model/agent output cannot mutate
    or expand budget authority during a run.
    """

    scopes: Mapping[str, BudgetScopeLimit]
    hard_stop: bool = True
    agent_may_expand: bool = False
    currency: str = "USD"
    policy_id: str = "gsdlc-06-d-default"

    def __post_init__(self) -> None:
        missing = [scope for scope in BUDGET_SCOPES if scope not in self.scopes]
        if missing:
            raise ValueError(f"budget policy missing scopes: {','.join(missing)}")
        unknown = sorted(set(self.scopes) - set(BUDGET_SCOPES))
        if unknown:
            raise ValueError(f"budget policy contains unknown scopes: {','.join(unknown)}")
        if not self.hard_stop:
            raise ValueError("06-D TokenBudgetPolicy requires hard_stop=true")
        if self.agent_may_expand:
            raise ValueError("agent_may_expand must remain false")

    @classmethod
    def load(cls, root: Path, *, path: str = ".devpilot/modeling/token_budget_policy.json") -> "TokenBudgetPolicy":
        payload = json.loads((Path(root) / path).read_text(encoding="utf-8"))
        scopes = {
            scope: BudgetScopeLimit(
                max_tokens=int(payload["scopes"][scope]["max_tokens"]),
                max_cost_usd=(None if payload["scopes"][scope].get("max_cost_usd") is None else float(payload["scopes"][scope]["max_cost_usd"])),
            )
            for scope in BUDGET_SCOPES
        }
        return cls(
            scopes=scopes,
            hard_stop=bool(payload.get("hard_stop", True)),
            agent_may_expand=bool(payload.get("agent_may_expand", False)),
            currency=str(payload.get("currency") or "USD"),
            policy_id=str(payload.get("policy_id") or "gsdlc-06-d-default"),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "policy_id": self.policy_id,
            "currency": self.currency,
            "hard_stop": self.hard_stop,
            "agent_may_expand": self.agent_may_expand,
            "scopes": {scope: self.scopes[scope].to_dict() for scope in BUDGET_SCOPES},
        }


@dataclass(frozen=True)
class BudgetScopeUsage:
    used_tokens: int = 0
    used_cost_usd: float = 0.0

    def __post_init__(self) -> None:
        if self.used_tokens < 0 or self.used_cost_usd < 0:
            raise ValueError("budget usage cannot be negative")


@dataclass(frozen=True)
class BudgetDecision:
    allowed: bool
    reason: str
    blocked_scope: str | None
    projected: dict[str, dict[str, float | int | None]]
    estimate: TokenCostEstimate
    agent_budget_expansion_rejected: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "allowed": self.allowed,
            "reason": self.reason,
            "blocked_scope": self.blocked_scope,
            "projected": self.projected,
            "estimate": self.estimate.to_dict(),
            "agent_budget_expansion_rejected": self.agent_budget_expansion_rejected,
        }


class TokenBudgetEnforcer:
    def __init__(self, policy: TokenBudgetPolicy) -> None:
        self.policy = policy

    def evaluate(
        self,
        estimate: TokenCostEstimate,
        *,
        usage: Mapping[str, BudgetScopeUsage] | None = None,
        requested_policy_override: TokenBudgetPolicy | None = None,
    ) -> BudgetDecision:
        usage = usage or {}
        projected: dict[str, dict[str, float | int | None]] = {}
        if requested_policy_override is not None and requested_policy_override.to_dict() != self.policy.to_dict():
            return BudgetDecision(False, "agent-budget-expansion-denied", None, projected, estimate, True)
        for scope in BUDGET_SCOPES:
            current = usage.get(scope, BudgetScopeUsage())
            limit = self.policy.scopes[scope]
            tokens = current.used_tokens + estimate.total_tokens
            cost = None if estimate.cost_state is EstimateState.UNKNOWN else current.used_cost_usd + float(estimate.cost_usd or 0.0)
            projected[scope] = {
                "tokens": tokens,
                "token_limit": limit.max_tokens,
                "cost_usd": cost,
                "cost_limit_usd": limit.max_cost_usd,
                "cost_state": estimate.cost_state.value,
            }
            if tokens > limit.max_tokens:
                return BudgetDecision(False, "hard-token-budget-exceeded", scope, projected, estimate)
            if limit.max_cost_usd is not None:
                if estimate.cost_state is EstimateState.UNKNOWN:
                    return BudgetDecision(False, "unknown-cost-cannot-satisfy-hard-budget", scope, projected, estimate)
                if float(cost or 0.0) > limit.max_cost_usd:
                    return BudgetDecision(False, "hard-cost-budget-exceeded", scope, projected, estimate)
        return BudgetDecision(True, "within-hard-budget", None, projected, estimate)


@dataclass(frozen=True)
class ContextBudget:
    hard_ceiling_tokens: int
    output_reserve_tokens: int
    safety_margin_tokens: int
    summary_budget_tokens: int
    retrieval_budget_tokens: int
    input_reserve_tokens: int = 0

    def __post_init__(self) -> None:
        values = (
            self.hard_ceiling_tokens,
            self.output_reserve_tokens,
            self.safety_margin_tokens,
            self.summary_budget_tokens,
            self.retrieval_budget_tokens,
            self.input_reserve_tokens,
        )
        if any(value < 0 for value in values) or self.hard_ceiling_tokens <= 0:
            raise ValueError("context budget values must be non-negative and hard ceiling positive")
        if self.output_reserve_tokens + self.safety_margin_tokens + self.input_reserve_tokens >= self.hard_ceiling_tokens:
            raise ValueError("context reserves consume the hard ceiling")

    @property
    def max_input_tokens(self) -> int:
        return self.hard_ceiling_tokens - self.output_reserve_tokens - self.safety_margin_tokens

    def plan(
        self,
        *,
        requested_input_tokens: int,
        invariant_min_tokens: int,
        diff_first_tokens: int | None = None,
        summary_tokens: int | None = None,
        retrieval_tokens: int | None = None,
    ) -> "ContextBudgetPlan":
        if requested_input_tokens < 0 or invariant_min_tokens < 0:
            raise ValueError("context token counts cannot be negative")
        cap = self.max_input_tokens
        if requested_input_tokens <= cap:
            return ContextBudgetPlan("pass", True, requested_input_tokens, cap, "input-within-hard-ceiling")
        if diff_first_tokens is not None and invariant_min_tokens <= diff_first_tokens <= cap:
            return ContextBudgetPlan("diff-first", True, diff_first_tokens, cap, "diff-first-preserves-workload-invariant")
        if summary_tokens is not None and summary_tokens <= self.summary_budget_tokens and invariant_min_tokens <= summary_tokens <= cap:
            return ContextBudgetPlan("summary", True, summary_tokens, cap, "bounded-summary-preserves-workload-invariant")
        if retrieval_tokens is not None and retrieval_tokens <= self.retrieval_budget_tokens and invariant_min_tokens <= retrieval_tokens <= cap:
            return ContextBudgetPlan("retrieval", True, retrieval_tokens, cap, "bounded-retrieval-preserves-workload-invariant")
        if invariant_min_tokens <= cap:
            return ContextBudgetPlan("hard-trim", True, cap, cap, "hard-trim-at-safe-input-ceiling")
        return ContextBudgetPlan("block", False, 0, cap, "context-invariant-cannot-fit-hard-ceiling")

    def to_dict(self) -> dict[str, Any]:
        return {
            "hard_ceiling_tokens": self.hard_ceiling_tokens,
            "input_reserve_tokens": self.input_reserve_tokens,
            "output_reserve_tokens": self.output_reserve_tokens,
            "safety_margin_tokens": self.safety_margin_tokens,
            "summary_budget_tokens": self.summary_budget_tokens,
            "retrieval_budget_tokens": self.retrieval_budget_tokens,
            "max_input_tokens": self.max_input_tokens,
        }


@dataclass(frozen=True)
class ContextBudgetPlan:
    strategy: str
    allowed: bool
    selected_input_tokens: int
    max_input_tokens: int
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "strategy": self.strategy,
            "allowed": self.allowed,
            "selected_input_tokens": self.selected_input_tokens,
            "max_input_tokens": self.max_input_tokens,
            "reason": self.reason,
        }


def estimate_text_tokens(text: str) -> int:
    """Deterministic provider-neutral estimate used before model-specific tokenizers."""
    if not text:
        return 0
    return max(1, int(ceil(len(text.encode("utf-8")) / 4.0)))


def estimate_route_cost(
    *,
    input_tokens: int,
    output_tokens: int,
    input_per_1k_usd: float | None,
    output_per_1k_usd: float | None,
    cost_state: str,
    source: str,
    freshness: str,
) -> TokenCostEstimate:
    normalized = str(cost_state or "unknown").lower()
    if input_per_1k_usd is None or output_per_1k_usd is None or normalized == "unknown":
        return TokenCostEstimate(input_tokens, output_tokens, EstimateState.UNKNOWN, None, source=source, freshness=freshness)
    state = EstimateState.KNOWN if normalized in {"known", "local-hardware/no-api-charge"} else EstimateState.ESTIMATED
    cost = (input_tokens / 1000.0) * float(input_per_1k_usd) + (output_tokens / 1000.0) * float(output_per_1k_usd)
    return TokenCostEstimate(input_tokens, output_tokens, state, round(cost, 10), source=source, freshness=freshness)


@dataclass(frozen=True)
class CostLedgerEntryV2:
    run_id: str
    workload_id: str
    provider_id: str
    model_id: str
    access_route_id: str
    planned: TokenCostEstimate
    actual: TokenCostEstimate | None
    budget_policy_id: str
    adjustment_reason: str | None = None
    provenance: tuple[str, ...] = ()
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"))

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_id": "devpilot.cost-ledger-entry.v2",
            "run_id": self.run_id,
            "workload_id": self.workload_id,
            "provider_id": self.provider_id,
            "model_id": self.model_id,
            "access_route_id": self.access_route_id,
            "planned": self.planned.to_dict(),
            "actual": None if self.actual is None else self.actual.to_dict(),
            "budget_policy_id": self.budget_policy_id,
            "adjustment_reason": self.adjustment_reason,
            "provenance": list(self.provenance),
            "timestamp": self.timestamp,
            "prompt_stored": False,
            "content_stored": False,
            "raw_secret_present": False,
        }


class CostLedgerV2:
    DEFAULT_PATH = Path(".devpilot/runtime/model_budget/cost_ledger_v2.jsonl")

    def __init__(self, root: Path, *, path: Path | None = None) -> None:
        self.root = Path(root).resolve()
        self.path = self.root / (path or self.DEFAULT_PATH)

    def append(self, entry: CostLedgerEntryV2) -> dict[str, Any]:
        payload = entry.to_dict()
        if _metadata_has_prompt_or_secret(payload):
            raise ValueError("cost ledger v2 payload contains prompt/secret-like material")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(payload, sort_keys=True, ensure_ascii=True) + "\n")
        return payload

    def entries(self) -> list[dict[str, Any]]:
        if not self.path.is_file():
            return []
        return [json.loads(line) for line in self.path.read_text(encoding="utf-8").splitlines() if line.strip()]

    def reconcile_actual(
        self,
        entry: CostLedgerEntryV2,
        *,
        actual: TokenCostEstimate,
        enforcer: TokenBudgetEnforcer,
        usage: Mapping[str, BudgetScopeUsage] | None = None,
        reason: str = "provider-usage-reconciliation",
    ) -> tuple[CostLedgerEntryV2, BudgetDecision]:
        decision = enforcer.evaluate(actual, usage=usage)
        reconciled = CostLedgerEntryV2(
            run_id=entry.run_id,
            workload_id=entry.workload_id,
            provider_id=entry.provider_id,
            model_id=entry.model_id,
            access_route_id=entry.access_route_id,
            planned=entry.planned,
            actual=actual,
            budget_policy_id=entry.budget_policy_id,
            adjustment_reason=reason if actual.to_dict() != entry.planned.to_dict() else None,
            provenance=entry.provenance,
        )
        self.append(reconciled)
        return reconciled, decision
