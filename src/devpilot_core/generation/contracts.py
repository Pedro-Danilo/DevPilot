from __future__ import annotations

import hashlib
import inspect
import json
from dataclasses import asdict, dataclass, field, is_dataclass, replace
from enum import Enum
from typing import Any, Generic, Mapping, Protocol, TypeVar, runtime_checkable

TInput = TypeVar("TInput")
TPayload = TypeVar("TPayload")

_HEX64 = set("0123456789abcdef")


def _json_ready(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value):
        return {key: _json_ready(item) for key, item in asdict(value).items()}
    if isinstance(value, Mapping):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    return value


def canonical_json(value: Any) -> str:
    return json.dumps(_json_ready(value), sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def canonical_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _require_non_empty(value: str, field_name: str) -> str:
    normalized = str(value or "").strip()
    if not normalized:
        raise ValueError(f"{field_name} must be non-empty")
    return normalized


def _validate_hash(value: str, field_name: str) -> str:
    normalized = str(value or "").strip().lower()
    if len(normalized) != 64 or any(char not in _HEX64 for char in normalized):
        raise ValueError(f"{field_name} must be a lowercase SHA-256 hex digest")
    return normalized


class ProviderClass(str, Enum):
    DETERMINISTIC = "deterministic"
    LOCAL_MODEL = "local-model"
    EXTERNAL_MODEL = "external-model"


class CandidateOriginKind(str, Enum):
    PROVIDER = "provider"
    HUMAN_AUTHORED = "human-authored"
    AGENT_ENRICHMENT = "agent-enrichment"


class CandidateStatus(str, Enum):
    CREATED = "CREATED"
    GENERATING = "GENERATING"
    GENERATED = "GENERATED"
    PARSE_BLOCKED = "PARSE_BLOCKED"
    SCHEMA_BLOCKED = "SCHEMA_BLOCKED"
    SEMANTIC_BLOCKED = "SEMANTIC_BLOCKED"
    EVAL_BLOCKED = "EVAL_BLOCKED"
    VALIDATED = "VALIDATED"
    UNDER_REVIEW = "UNDER_REVIEW"
    SELECTED = "SELECTED"
    REJECTED = "REJECTED"
    SUPERSEDED = "SUPERSEDED"
    EXPIRED = "EXPIRED"


class LineageReason(str, Enum):
    INITIAL_GENERATION = "initial-generation"
    REGENERATION = "regeneration"
    HUMAN_EDIT = "human-edit"
    PROVIDER_SWITCH = "provider-switch"
    AGENT_ENRICHMENT = "agent-enrichment"


LEGAL_TRANSITIONS: dict[CandidateStatus, frozenset[CandidateStatus]] = {
    CandidateStatus.CREATED: frozenset({CandidateStatus.GENERATING, CandidateStatus.SUPERSEDED, CandidateStatus.EXPIRED}),
    CandidateStatus.GENERATING: frozenset({CandidateStatus.GENERATED, CandidateStatus.PARSE_BLOCKED, CandidateStatus.SUPERSEDED, CandidateStatus.EXPIRED}),
    CandidateStatus.GENERATED: frozenset({
        CandidateStatus.PARSE_BLOCKED,
        CandidateStatus.SCHEMA_BLOCKED,
        CandidateStatus.SEMANTIC_BLOCKED,
        CandidateStatus.EVAL_BLOCKED,
        CandidateStatus.VALIDATED,
        CandidateStatus.SUPERSEDED,
        CandidateStatus.EXPIRED,
    }),
    CandidateStatus.PARSE_BLOCKED: frozenset({CandidateStatus.SUPERSEDED, CandidateStatus.EXPIRED}),
    CandidateStatus.SCHEMA_BLOCKED: frozenset({CandidateStatus.SUPERSEDED, CandidateStatus.EXPIRED}),
    CandidateStatus.SEMANTIC_BLOCKED: frozenset({CandidateStatus.SUPERSEDED, CandidateStatus.EXPIRED}),
    CandidateStatus.EVAL_BLOCKED: frozenset({CandidateStatus.SUPERSEDED, CandidateStatus.EXPIRED}),
    CandidateStatus.VALIDATED: frozenset({CandidateStatus.UNDER_REVIEW, CandidateStatus.SUPERSEDED, CandidateStatus.EXPIRED}),
    CandidateStatus.UNDER_REVIEW: frozenset({
        CandidateStatus.SELECTED,
        CandidateStatus.REJECTED,
        CandidateStatus.SUPERSEDED,
        CandidateStatus.EXPIRED,
    }),
    CandidateStatus.SELECTED: frozenset({CandidateStatus.SUPERSEDED, CandidateStatus.EXPIRED}),
    CandidateStatus.REJECTED: frozenset({CandidateStatus.SUPERSEDED, CandidateStatus.EXPIRED}),
    CandidateStatus.SUPERSEDED: frozenset(),
    CandidateStatus.EXPIRED: frozenset(),
}


@dataclass(frozen=True)
class GenerationRequest:
    request_id: str
    artifact_type: str
    profile_version: str
    dependency_profile_version: str
    upstream_hashes: Mapping[str, str]
    owner_inputs: Mapping[str, Any] = field(default_factory=dict)
    preferred_route: str = "deterministic"
    allowed_routes: tuple[str, ...] = ("deterministic",)
    policy_snapshot: Mapping[str, Any] = field(default_factory=dict)
    budget_snapshot: Mapping[str, Any] = field(default_factory=dict)
    context_reference: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "request_id", _require_non_empty(self.request_id, "request_id"))
        object.__setattr__(self, "artifact_type", _require_non_empty(self.artifact_type, "artifact_type"))
        object.__setattr__(self, "profile_version", _require_non_empty(self.profile_version, "profile_version"))
        object.__setattr__(self, "dependency_profile_version", _require_non_empty(self.dependency_profile_version, "dependency_profile_version"))
        normalized_hashes = {str(key): _validate_hash(value, f"upstream_hashes[{key!r}]") for key, value in self.upstream_hashes.items()}
        object.__setattr__(self, "upstream_hashes", normalized_hashes)
        routes = tuple(dict.fromkeys(_require_non_empty(route, "allowed_routes item") for route in self.allowed_routes))
        if not routes:
            raise ValueError("allowed_routes must contain at least one route")
        preferred = _require_non_empty(self.preferred_route, "preferred_route")
        if preferred not in routes:
            raise ValueError("preferred_route must be included in allowed_routes")
        object.__setattr__(self, "allowed_routes", routes)
        object.__setattr__(self, "preferred_route", preferred)

    @property
    def canonical_input_sha256(self) -> str:
        return canonical_sha256({
            "artifact_type": self.artifact_type,
            "profile_version": self.profile_version,
            "dependency_profile_version": self.dependency_profile_version,
            "upstream_hashes": dict(self.upstream_hashes),
            "owner_inputs": dict(self.owner_inputs),
            "policy_snapshot": dict(self.policy_snapshot),
            "budget_snapshot": dict(self.budget_snapshot),
            "context_reference": self.context_reference,
        })

    def to_dict(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "artifact_type": self.artifact_type,
            "profile_version": self.profile_version,
            "dependency_profile_version": self.dependency_profile_version,
            "upstream_hashes": dict(self.upstream_hashes),
            "owner_inputs": _json_ready(dict(self.owner_inputs)),
            "preferred_route": self.preferred_route,
            "allowed_routes": list(self.allowed_routes),
            "policy_snapshot": _json_ready(dict(self.policy_snapshot)),
            "budget_snapshot": _json_ready(dict(self.budget_snapshot)),
            "context_reference": self.context_reference,
            "canonical_input_sha256": self.canonical_input_sha256,
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "GenerationRequest":
        return cls(
            request_id=str(value.get("request_id") or ""),
            artifact_type=str(value.get("artifact_type") or ""),
            profile_version=str(value.get("profile_version") or ""),
            dependency_profile_version=str(value.get("dependency_profile_version") or ""),
            upstream_hashes=dict(value.get("upstream_hashes") or {}),
            owner_inputs=dict(value.get("owner_inputs") or {}),
            preferred_route=str(value.get("preferred_route") or "deterministic"),
            allowed_routes=tuple(str(item) for item in value.get("allowed_routes") or ("deterministic",)),
            policy_snapshot=dict(value.get("policy_snapshot") or {}),
            budget_snapshot=dict(value.get("budget_snapshot") or {}),
            context_reference=value.get("context_reference"),
        )


@dataclass(frozen=True)
class CandidateOrigin:
    kind: CandidateOriginKind
    provider_class: ProviderClass | None = None
    provider_id: str | None = None
    model_id: str | None = None
    actor_id: str | None = None

    def __post_init__(self) -> None:
        if self.kind == CandidateOriginKind.PROVIDER:
            if self.provider_class is None:
                raise ValueError("provider origin requires provider_class")
            object.__setattr__(self, "provider_id", _require_non_empty(self.provider_id or "", "provider_id"))
        else:
            object.__setattr__(self, "actor_id", _require_non_empty(self.actor_id or "", "actor_id"))
            if self.kind == CandidateOriginKind.HUMAN_AUTHORED and any((self.provider_class, self.provider_id, self.model_id)):
                raise ValueError("human-authored origin is not a provider")

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind.value,
            "provider_class": self.provider_class.value if self.provider_class else None,
            "provider_id": self.provider_id,
            "model_id": self.model_id,
            "actor_id": self.actor_id,
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "CandidateOrigin":
        raw_provider_class = value.get("provider_class")
        return cls(
            kind=CandidateOriginKind(str(value.get("kind"))),
            provider_class=ProviderClass(str(raw_provider_class)) if raw_provider_class else None,
            provider_id=value.get("provider_id"),
            model_id=value.get("model_id"),
            actor_id=value.get("actor_id"),
        )


@dataclass(frozen=True)
class GenerationProvenance:
    prompt_ref: str | None = None
    profile_ref: str | None = None
    context_ref: str | None = None
    network_used: bool = False
    external_api_used: bool = False
    cost_usd: float = 0.0
    latency_ms: int | None = None
    evidence_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.cost_usd < 0:
            raise ValueError("cost_usd cannot be negative")
        if self.latency_ms is not None and self.latency_ms < 0:
            raise ValueError("latency_ms cannot be negative")

    def to_dict(self) -> dict[str, Any]:
        return {
            "prompt_ref": self.prompt_ref,
            "profile_ref": self.profile_ref,
            "context_ref": self.context_ref,
            "network_used": self.network_used,
            "external_api_used": self.external_api_used,
            "cost_usd": self.cost_usd,
            "latency_ms": self.latency_ms,
            "evidence_refs": list(self.evidence_refs),
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "GenerationProvenance":
        return cls(
            prompt_ref=value.get("prompt_ref"),
            profile_ref=value.get("profile_ref"),
            context_ref=value.get("context_ref"),
            network_used=bool(value.get("network_used", False)),
            external_api_used=bool(value.get("external_api_used", False)),
            cost_usd=float(value.get("cost_usd", 0.0)),
            latency_ms=int(value["latency_ms"]) if value.get("latency_ms") is not None else None,
            evidence_refs=tuple(str(item) for item in value.get("evidence_refs") or ()),
        )


@dataclass(frozen=True)
class CandidateLineage:
    root_candidate_id: str
    parent_candidate_id: str | None
    parent_version: int | None
    reason: LineageReason
    actor_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "root_candidate_id": self.root_candidate_id,
            "parent_candidate_id": self.parent_candidate_id,
            "parent_version": self.parent_version,
            "reason": self.reason.value,
            "actor_id": self.actor_id,
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "CandidateLineage":
        parent_version = value.get("parent_version")
        return cls(
            root_candidate_id=str(value.get("root_candidate_id") or ""),
            parent_candidate_id=value.get("parent_candidate_id"),
            parent_version=int(parent_version) if parent_version is not None else None,
            reason=LineageReason(str(value.get("reason"))),
            actor_id=value.get("actor_id"),
        )


@dataclass(frozen=True)
class ArtifactCandidateEnvelope(Generic[TPayload]):
    schema_id: str
    candidate_id: str
    version: int
    artifact_type: str
    payload: TPayload
    origin: CandidateOrigin
    request_id: str
    canonical_input_sha256: str
    content_sha256: str
    provenance: GenerationProvenance
    lineage: CandidateLineage
    status: CandidateStatus = CandidateStatus.GENERATED
    evaluation_summary: Mapping[str, Any] = field(default_factory=dict)
    unsupported_claims: tuple[str, ...] = ()
    questions: tuple[str, ...] = ()

    SCHEMA_ID = "devpilot.mp-v2.artifact-candidate-envelope.v1"

    def __post_init__(self) -> None:
        object.__setattr__(self, "schema_id", _require_non_empty(self.schema_id, "schema_id"))
        object.__setattr__(self, "candidate_id", _require_non_empty(self.candidate_id, "candidate_id"))
        if self.version < 1:
            raise ValueError("candidate version must be >= 1")
        object.__setattr__(self, "artifact_type", _require_non_empty(self.artifact_type, "artifact_type"))
        object.__setattr__(self, "request_id", _require_non_empty(self.request_id, "request_id"))
        object.__setattr__(self, "canonical_input_sha256", _validate_hash(self.canonical_input_sha256, "canonical_input_sha256"))
        object.__setattr__(self, "content_sha256", _validate_hash(self.content_sha256, "content_sha256"))
        if self.lineage.reason == LineageReason.INITIAL_GENERATION:
            if self.lineage.parent_candidate_id is not None or self.lineage.parent_version is not None:
                raise ValueError("initial candidate cannot have a parent")
            if self.lineage.root_candidate_id != self.candidate_id:
                raise ValueError("initial candidate root_candidate_id must equal candidate_id")
        else:
            if not self.lineage.parent_candidate_id or self.lineage.parent_version is None:
                raise ValueError("successor candidate requires parent identity/version")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_id": self.schema_id,
            "candidate_id": self.candidate_id,
            "version": self.version,
            "artifact_type": self.artifact_type,
            "payload": _json_ready(self.payload),
            "origin": self.origin.to_dict(),
            "request_id": self.request_id,
            "canonical_input_sha256": self.canonical_input_sha256,
            "content_sha256": self.content_sha256,
            "provenance": self.provenance.to_dict(),
            "lineage": self.lineage.to_dict(),
            "status": self.status.value,
            "evaluation_summary": _json_ready(dict(self.evaluation_summary)),
            "unsupported_claims": list(self.unsupported_claims),
            "questions": list(self.questions),
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "ArtifactCandidateEnvelope[Any]":
        return cls(
            schema_id=str(value.get("schema_id") or cls.SCHEMA_ID),
            candidate_id=str(value.get("candidate_id") or ""),
            version=int(value.get("version") or 0),
            artifact_type=str(value.get("artifact_type") or ""),
            payload=value.get("payload"),
            origin=CandidateOrigin.from_dict(dict(value.get("origin") or {})),
            request_id=str(value.get("request_id") or ""),
            canonical_input_sha256=str(value.get("canonical_input_sha256") or ""),
            content_sha256=str(value.get("content_sha256") or ""),
            provenance=GenerationProvenance.from_dict(dict(value.get("provenance") or {})),
            lineage=CandidateLineage.from_dict(dict(value.get("lineage") or {})),
            status=CandidateStatus(str(value.get("status") or CandidateStatus.GENERATED.value)),
            evaluation_summary=dict(value.get("evaluation_summary") or {}),
            unsupported_claims=tuple(str(item) for item in value.get("unsupported_claims") or ()),
            questions=tuple(str(item) for item in value.get("questions") or ()),
        )

    def content_integrity_ok(self) -> bool:
        return canonical_sha256(self.payload) == self.content_sha256


@runtime_checkable
class GenerationProvider(Protocol[TInput, TPayload]):
    provider_id: str
    provider_class: ProviderClass
    model_id: str | None

    def generate(self, request: GenerationRequest, authoritative_input: TInput) -> ArtifactCandidateEnvelope[TPayload]:
        ...


_PROVIDER_FORBIDDEN_PUBLIC_METHODS = frozenset({
    "apply",
    "approve",
    "commit",
    "freeze",
    "git_commit",
    "quality_pass",
    "source_write",
    "stage",
    "tool_escalate",
    "write_source",
})


def provider_authority_violations(provider_type: type[Any]) -> tuple[str, ...]:
    public_callables = {
        name
        for name, value in inspect.getmembers(provider_type)
        if not name.startswith("_") and callable(value)
    }
    return tuple(sorted(public_callables & _PROVIDER_FORBIDDEN_PUBLIC_METHODS))


def _candidate_id(*, request_id: str, artifact_type: str, version: int, content_sha256: str, origin: CandidateOrigin, parent_id: str | None) -> str:
    digest = canonical_sha256({
        "request_id": request_id,
        "artifact_type": artifact_type,
        "version": version,
        "content_sha256": content_sha256,
        "origin": origin.to_dict(),
        "parent_id": parent_id,
    })
    return f"cand-{digest[:24]}"


def create_candidate(
    *,
    request: GenerationRequest,
    payload: TPayload,
    origin: CandidateOrigin,
    provenance: GenerationProvenance | None = None,
    status: CandidateStatus = CandidateStatus.GENERATED,
    evaluation_summary: Mapping[str, Any] | None = None,
    unsupported_claims: tuple[str, ...] = (),
    questions: tuple[str, ...] = (),
) -> ArtifactCandidateEnvelope[TPayload]:
    content_sha = canonical_sha256(payload)
    candidate_id = _candidate_id(
        request_id=request.request_id,
        artifact_type=request.artifact_type,
        version=1,
        content_sha256=content_sha,
        origin=origin,
        parent_id=None,
    )
    return ArtifactCandidateEnvelope(
        schema_id=ArtifactCandidateEnvelope.SCHEMA_ID,
        candidate_id=candidate_id,
        version=1,
        artifact_type=request.artifact_type,
        payload=payload,
        origin=origin,
        request_id=request.request_id,
        canonical_input_sha256=request.canonical_input_sha256,
        content_sha256=content_sha,
        provenance=provenance or GenerationProvenance(profile_ref=request.profile_version, context_ref=request.context_reference),
        lineage=CandidateLineage(
            root_candidate_id=candidate_id,
            parent_candidate_id=None,
            parent_version=None,
            reason=LineageReason.INITIAL_GENERATION,
            actor_id=None,
        ),
        status=status,
        evaluation_summary=dict(evaluation_summary or {}),
        unsupported_claims=tuple(unsupported_claims),
        questions=tuple(questions),
    )


def create_successor_candidate(
    *,
    parent: ArtifactCandidateEnvelope[Any],
    payload: TPayload,
    reason: LineageReason,
    origin: CandidateOrigin,
    actor_id: str,
    request: GenerationRequest | None = None,
    provenance: GenerationProvenance | None = None,
) -> ArtifactCandidateEnvelope[TPayload]:
    if reason == LineageReason.INITIAL_GENERATION:
        raise ValueError("successor reason cannot be initial-generation")
    if parent.status in {CandidateStatus.SUPERSEDED, CandidateStatus.EXPIRED}:
        raise ValueError("terminal superseded/expired candidate cannot create a successor")
    normalized_actor = _require_non_empty(actor_id, "actor_id")
    if request is not None and request.artifact_type != parent.artifact_type:
        raise ValueError("successor request artifact_type must match parent")
    request_id = request.request_id if request else parent.request_id
    canonical_input = request.canonical_input_sha256 if request else parent.canonical_input_sha256
    version = parent.version + 1
    content_sha = canonical_sha256(payload)
    candidate_id = _candidate_id(
        request_id=request_id,
        artifact_type=parent.artifact_type,
        version=version,
        content_sha256=content_sha,
        origin=origin,
        parent_id=parent.candidate_id,
    )
    return ArtifactCandidateEnvelope(
        schema_id=ArtifactCandidateEnvelope.SCHEMA_ID,
        candidate_id=candidate_id,
        version=version,
        artifact_type=parent.artifact_type,
        payload=payload,
        origin=origin,
        request_id=request_id,
        canonical_input_sha256=canonical_input,
        content_sha256=content_sha,
        provenance=provenance or parent.provenance,
        lineage=CandidateLineage(
            root_candidate_id=parent.lineage.root_candidate_id,
            parent_candidate_id=parent.candidate_id,
            parent_version=parent.version,
            reason=reason,
            actor_id=normalized_actor,
        ),
        status=CandidateStatus.GENERATED,
    )


def transition_candidate(candidate: ArtifactCandidateEnvelope[TPayload], target: CandidateStatus) -> ArtifactCandidateEnvelope[TPayload]:
    if target == candidate.status:
        return candidate
    allowed = LEGAL_TRANSITIONS[candidate.status]
    if target not in allowed:
        raise ValueError(f"illegal candidate lifecycle transition: {candidate.status.value} -> {target.value}")
    return replace(candidate, status=target)


@dataclass(frozen=True)
class CandidateReference:
    candidate_id: str
    version: int
    artifact_type: str
    canonical_input_sha256: str
    content_sha256: str
    origin: CandidateOrigin

    @classmethod
    def from_candidate(cls, candidate: ArtifactCandidateEnvelope[Any]) -> "CandidateReference":
        return cls(
            candidate_id=candidate.candidate_id,
            version=candidate.version,
            artifact_type=candidate.artifact_type,
            canonical_input_sha256=candidate.canonical_input_sha256,
            content_sha256=candidate.content_sha256,
            origin=candidate.origin,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "version": self.version,
            "artifact_type": self.artifact_type,
            "canonical_input_sha256": self.canonical_input_sha256,
            "content_sha256": self.content_sha256,
            "origin": self.origin.to_dict(),
        }


@dataclass(frozen=True)
class CandidateComparisonGroup:
    group_id: str
    artifact_type: str
    canonical_input_sha256: str
    candidates: tuple[CandidateReference, ...] = ()
    selected_candidate_id: str | None = None
    selected_by_owner_id: str | None = None

    @classmethod
    def create(cls, *, group_id: str, artifact_type: str, canonical_input_sha256: str) -> "CandidateComparisonGroup":
        return cls(
            group_id=_require_non_empty(group_id, "group_id"),
            artifact_type=_require_non_empty(artifact_type, "artifact_type"),
            canonical_input_sha256=_validate_hash(canonical_input_sha256, "canonical_input_sha256"),
        )

    def add(self, candidate: ArtifactCandidateEnvelope[Any]) -> "CandidateComparisonGroup":
        if candidate.artifact_type != self.artifact_type:
            raise ValueError("candidate artifact_type does not match comparison group")
        if candidate.canonical_input_sha256 != self.canonical_input_sha256:
            raise ValueError("candidate canonical inputs do not match comparison group")
        if any(item.candidate_id == candidate.candidate_id for item in self.candidates):
            return self
        return replace(self, candidates=self.candidates + (CandidateReference.from_candidate(candidate),))

    def select(self, *, candidate_id: str, actor_id: str, actor_role: str) -> "CandidateComparisonGroup":
        if str(actor_role).strip().lower() != "owner":
            raise PermissionError("material candidate selection requires Owner authority")
        normalized_id = _require_non_empty(candidate_id, "candidate_id")
        if not any(item.candidate_id == normalized_id for item in self.candidates):
            raise ValueError("selected candidate is not part of this comparison group")
        return replace(
            self,
            selected_candidate_id=normalized_id,
            selected_by_owner_id=_require_non_empty(actor_id, "actor_id"),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "group_id": self.group_id,
            "artifact_type": self.artifact_type,
            "canonical_input_sha256": self.canonical_input_sha256,
            "candidates": [item.to_dict() for item in self.candidates],
            "selected_candidate_id": self.selected_candidate_id,
            "selected_by_owner_id": self.selected_by_owner_id,
        }


@dataclass(frozen=True)
class DownstreamAuthorityBinding:
    content_sha256: str
    canonical_input_sha256: str
    plan_id: str | None = None
    diff_id: str | None = None
    approval_id: str | None = None
    valid: bool = True
    invalidated_reason: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "content_sha256", _validate_hash(self.content_sha256, "content_sha256"))
        object.__setattr__(self, "canonical_input_sha256", _validate_hash(self.canonical_input_sha256, "canonical_input_sha256"))


def invalidate_stale_authority(
    binding: DownstreamAuthorityBinding,
    candidate: ArtifactCandidateEnvelope[Any],
) -> DownstreamAuthorityBinding:
    if (
        binding.content_sha256 == candidate.content_sha256
        and binding.canonical_input_sha256 == candidate.canonical_input_sha256
    ):
        return binding
    reasons: list[str] = []
    if binding.content_sha256 != candidate.content_sha256:
        reasons.append("content-hash-changed")
    if binding.canonical_input_sha256 != candidate.canonical_input_sha256:
        reasons.append("canonical-input-hash-changed")
    return DownstreamAuthorityBinding(
        content_sha256=candidate.content_sha256,
        canonical_input_sha256=candidate.canonical_input_sha256,
        plan_id=None,
        diff_id=None,
        approval_id=None,
        valid=False,
        invalidated_reason="+".join(reasons),
    )
