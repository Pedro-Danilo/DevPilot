"""R01-04: fail-closed, offline task policy above the existing GenerationRouteResolver.

This is a *planning* boundary. It does not call adapters, route execution, or
change 09-C/source/approval authority. External model egress stays DENIED.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum
import math
from typing import Any, Mapping

from .contracts import GenerationRequest, ProviderClass, canonical_sha256
from .runtime import GenerationRouteResolver, ProviderHealthSnapshot, ProviderSelectionPolicy


class FallbackQuality(str, Enum):
    EQUIVALENT = 'EQUIVALENT'
    REDUCED = 'REDUCED'
    MODEL_REQUIRED = 'MODEL_REQUIRED'


@dataclass(frozen=True)
class TaskRouteRule:
    """Owner-defined task rule, not an inference from provider availability."""

    task_type: str
    artifact_types: tuple[str, ...]
    allowed_classes: tuple[ProviderClass, ...] = (ProviderClass.DETERMINISTIC,)
    fallback_quality: FallbackQuality = FallbackQuality.MODEL_REQUIRED
    equivalence_evidence: str | None = None
    max_input_tokens: int = 2048
    max_output_tokens: int = 1024
    max_cost_usd: float = 0.0
    max_timeout_seconds: float = 30.0

    def __post_init__(self) -> None:
        if not self.task_type.strip() or not self.artifact_types or any(not isinstance(t,str) or not t.strip() for t in self.artifact_types):
            raise ValueError('TASK_RULE_IDENTITY_REQUIRED')
        if not isinstance(self.fallback_quality,FallbackQuality):
            raise ValueError('FALLBACK_MODE_INVALID')
        if not self.allowed_classes or len(set(self.allowed_classes)) != len(self.allowed_classes):
            raise ValueError('TASK_RULE_CLASSES_INVALID')
        if any(not isinstance(c, ProviderClass) for c in self.allowed_classes):
            raise ValueError('TASK_RULE_CLASS_UNKNOWN')
        for name in ('max_input_tokens', 'max_output_tokens'):
            val = getattr(self, name)
            if type(val) is not int or val < 0:
                raise ValueError('TASK_RULE_BUDGET_INVALID')
        for name in ('max_cost_usd','max_timeout_seconds'):
            val = getattr(self,name)
            if isinstance(val,bool) or not isinstance(val,(int,float)) or not math.isfinite(val) or val < 0 or (name=='max_timeout_seconds' and val == 0):
                raise ValueError('TASK_RULE_BUDGET_INVALID')
        if self.fallback_quality is FallbackQuality.EQUIVALENT and not str(self.equivalence_evidence or '').strip():
            raise ValueError('EQUIVALENCE_EVIDENCE_REQUIRED')

    def fingerprint(self) -> str:
        return canonical_sha256({
            'task_type':self.task_type,'artifact_types':self.artifact_types,
            'allowed_classes':tuple(x.value for x in self.allowed_classes),
            'fallback_quality':self.fallback_quality.value,
            'equivalence_evidence':self.equivalence_evidence,
            'max_input_tokens':self.max_input_tokens,'max_output_tokens':self.max_output_tokens,
            'max_cost_usd':self.max_cost_usd,'max_timeout_seconds':self.max_timeout_seconds,
        })


@dataclass(frozen=True)
class WorkloadEstimate:
    input_tokens: int
    output_tokens: int
    cost_usd: float
    timeout_seconds: float

    def __post_init__(self) -> None:
        if any(type(v) is not int or v < 0 for v in (self.input_tokens,self.output_tokens)):
            raise ValueError('INVALID_TOKEN_ESTIMATE')
        if any(isinstance(v,bool) or not isinstance(v,(float,int)) or not math.isfinite(v) or v < 0 for v in (self.cost_usd,self.timeout_seconds)) or self.timeout_seconds == 0:
            raise ValueError('INVALID_TIME_OR_COST_ESTIMATE')


@dataclass(frozen=True)
class GovernedTaskRouteDecision:
    task_type: str
    request_id: str
    status: str
    reason: str
    requested_class: str
    chosen_class: str | None
    fallback_quality: str | None
    fallback_reason: str | None
    rule_sha256: str | None
    request_sha256: str
    trace: tuple[str, ...]
    gateway_route_sha256: str | None = None
    execution_allowed: bool = False
    model_call_performed: bool = False
    network_used: bool = False
    external_api_used: bool = False

    def to_dict(self) -> dict[str, Any]:
        return dict(self.__dict__, trace=list(self.trace))


class GenerationRoutePolicy:
    """One policy owner; delegates existing gateway eligibility, never provider IO.

    Default-deny for unregistered tasks, any E, overruns and non-consented fallback.
    The only executable class exposed here is deterministic. Local can be planned,
    but health/eligibility still requires later independently governed execution.
    """

    def __init__(self, resolver: GenerationRouteResolver, rules: Mapping[str, TaskRouteRule] | None = None):
        self.resolver = resolver
        self.rules = dict(rules or {})
        if any(key != rule.task_type for key,rule in self.rules.items()):
            raise ValueError('RULE_KEY_MISMATCH')

    def plan(self, request: GenerationRequest, *, task_type: str,
             estimate: WorkloadEstimate, selection_policy: ProviderSelectionPolicy,
             health_snapshots: tuple[ProviderHealthSnapshot, ...] = (),
             fallback_consent: bool = False,
             required_capabilities: tuple[str, ...] = ('text_generation','structured_output')) -> GovernedTaskRouteDecision:
        rule = self.rules.get(task_type)
        cls = request.preferred_route
        base = {'task_type':task_type,'request_id':request.request_id,'requested_class':cls,
                'request_sha256':request.canonical_input_sha256,
                'rule_sha256':rule.fingerprint() if rule else None}
        trace: list[str] = ['default-deny', f'task:{task_type}', f'requested:{cls}']
        def block(reason: str) -> GovernedTaskRouteDecision:
            return GovernedTaskRouteDecision(status='DENIED',reason=reason,chosen_class=None,
                fallback_quality=None,fallback_reason=None,trace=tuple(trace+[reason]),**base)
        if not rule:return block('TASK_NOT_REGISTERED')
        if request.artifact_type not in rule.artifact_types:return block('ARTIFACT_NOT_ALLOWED_FOR_TASK')
        if cls == ProviderClass.EXTERNAL_MODEL.value or 'external' in cls:return block('EXTERNAL_EGRESS_DENIED')
        try: requested = ProviderClass(cls)
        except ValueError:return block('UNKNOWN_PROVIDER_CLASS')
        if requested not in rule.allowed_classes or not selection_policy.class_allowed(requested):
            return block('PROVIDER_CLASS_NOT_ALLOWED')
        if rule.fallback_quality is FallbackQuality.MODEL_REQUIRED and requested is ProviderClass.DETERMINISTIC:
            return block('MODEL_REQUIRED_DETERMINISTIC_NOT_EQUIVALENT')
        if estimate.input_tokens > rule.max_input_tokens or estimate.output_tokens > rule.max_output_tokens:
            return block('TOKEN_BUDGET_EXCEEDED')
        if estimate.cost_usd > rule.max_cost_usd:return block('COST_BUDGET_EXCEEDED')
        if estimate.timeout_seconds > rule.max_timeout_seconds:return block('TIMEOUT_BUDGET_EXCEEDED')
        # An explicit request budget may be stricter. Never silently relax it.
        for key, actual in (('max_cost_usd',estimate.cost_usd),('max_input_tokens',estimate.input_tokens),('max_output_tokens',estimate.output_tokens),('max_timeout_seconds',estimate.timeout_seconds)):
            cap=request.budget_snapshot.get(key)
            if cap is not None:
                if isinstance(cap,bool) or not isinstance(cap,(int,float)) or not math.isfinite(cap) or cap < 0:
                    return block('INVALID_REQUEST_BUDGET')
                if actual > cap:return block('REQUEST_BUDGET_EXCEEDED')
        if requested is ProviderClass.LOCAL_MODEL and 'deterministic' in request.allowed_routes and fallback_consent:
            trace.append('fallback-requested-by-owner')
        # Deny local->D fallback inside the old resolver: we adjudicate it explicitly below.
        safe_policy = replace(selection_policy, external_enabled=False, allow_external_fallback=False,
                              allow_local_to_deterministic_fallback=False,
                              execution_enabled_classes=(ProviderClass.DETERMINISTIC,),
                              max_estimated_cost_usd=min(rule.max_cost_usd,
                                  selection_policy.max_estimated_cost_usd if selection_policy.max_estimated_cost_usd is not None else rule.max_cost_usd))
        route=self.resolver.resolve(request, policy=safe_policy,
                 health_snapshots=health_snapshots, required_capabilities=required_capabilities,
                 estimated_input_tokens=estimate.input_tokens,
                 estimated_output_tokens=estimate.output_tokens,
                 estimated_cost_usd=estimate.cost_usd)
        trace.append(f'gateway:{route.status}')
        if route.status=='selected' and route.used_provider_class is requested:
            if requested is ProviderClass.DETERMINISTIC:
                if not route.execution_allowed:return block('DETERMINISTIC_EXECUTION_NOT_ALLOWED')
                return GovernedTaskRouteDecision(status='SELECTED_DETERMINISTIC',reason='GOVERNED_DETERMINISTIC',
                    chosen_class=requested.value,fallback_quality=None,fallback_reason=None,trace=tuple(trace),
                    gateway_route_sha256=route.route_sha256,execution_allowed=True,**base)
            # Local selection is planning-only. Runtime eligibility is not inferred.
            return GovernedTaskRouteDecision(status='PLANNED_LOCAL_NOT_EXECUTABLE',reason='LOCAL_REQUIRES_SEPARATE_EXECUTION_GATE',
                chosen_class=requested.value,fallback_quality=None,fallback_reason=None,trace=tuple(trace),
                gateway_route_sha256=route.route_sha256,**base)
        if requested is not ProviderClass.LOCAL_MODEL:
            return block('GATEWAY_BLOCKED:'+','.join(route.reasons))
        if rule.fallback_quality is FallbackQuality.MODEL_REQUIRED:
            return block('MODEL_REQUIRED_NO_FALLBACK')
        if not fallback_consent:return block('FALLBACK_CONSENT_MISSING')
        if ProviderClass.DETERMINISTIC not in rule.allowed_classes or not selection_policy.class_allowed(ProviderClass.DETERMINISTIC) or 'deterministic' not in request.allowed_routes:
            return block('FALLBACK_CLASS_NOT_ALLOWED')
        fallback_request=replace(request,preferred_route=ProviderClass.DETERMINISTIC.value)
        det=self.resolver.resolve(fallback_request, policy=safe_policy,
                                  required_capabilities=required_capabilities,
                                  estimated_input_tokens=estimate.input_tokens,
                                  estimated_output_tokens=estimate.output_tokens,
                                  estimated_cost_usd=0.0)
        trace.extend([f'local-rejection:{route.route_sha256}',f'fallback-gateway:{det.status}'])
        if det.status!='selected' or not det.execution_allowed or det.used_provider_class is not ProviderClass.DETERMINISTIC:
            return block('DETERMINISTIC_FALLBACK_GATEWAY_BLOCKED')
        return GovernedTaskRouteDecision(status='FALLBACK_'+rule.fallback_quality.value,
            reason='EXPLICIT_FALLBACK_WITH_QUALITY_DECLARATION',chosen_class=ProviderClass.DETERMINISTIC.value,
            fallback_quality=rule.fallback_quality.value,
            fallback_reason=','.join(route.reasons) or route.status,
            trace=tuple(trace),gateway_route_sha256=det.route_sha256,execution_allowed=True,**base)
