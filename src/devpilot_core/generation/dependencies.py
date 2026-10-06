from __future__ import annotations

import fnmatch
import hashlib
import json
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping

from devpilot_core.modeling.budget import estimate_text_tokens
from devpilot_core.rag.context_pack_v2 import ContextPackV2Builder, ContextPackV2Options

from .contracts import canonical_sha256


def _non_empty(value: str, name: str) -> str:
    normalized = str(value or "").strip()
    if not normalized:
        raise ValueError(f"{name} must be non-empty")
    return normalized


def _semver(value: str, name: str) -> str:
    import re

    normalized = _non_empty(value, name)
    if not re.fullmatch(r"\d+\.\d+\.\d+", normalized):
        raise ValueError(f"{name} must use MAJOR.MINOR.PATCH")
    return normalized


def _semantic_text(value: str) -> str:
    return str(value or "").replace("\r\n", "\n").replace("\r", "\n")


def _semantic_sha256(value: str) -> str:
    return hashlib.sha256(_semantic_text(value).encode("utf-8")).hexdigest()


def _parse_datetime(value: str | None) -> datetime | None:
    if value in {None, ""}:
        return None
    text = str(value).strip().replace("Z", "+00:00")
    parsed = datetime.fromisoformat(text)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


@dataclass(frozen=True)
class DependencyRequirement:
    artifact_type: str
    min_authority_rank: int = 0
    required_lifecycle: str = "FROZEN"
    max_age_days: int | None = None
    namespace: str | None = None
    allow_unknown_freshness: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "artifact_type", _non_empty(self.artifact_type, "artifact_type"))
        if self.min_authority_rank < 0:
            raise ValueError("min_authority_rank cannot be negative")
        if self.max_age_days is not None and self.max_age_days < 0:
            raise ValueError("max_age_days cannot be negative")


@dataclass(frozen=True)
class ArtifactDependencyProfile:
    profile_id: str
    artifact_type: str
    profile_version: str = "1.0.0"
    required_upstream: tuple[DependencyRequirement, ...] = ()
    optional_supporting: tuple[DependencyRequirement, ...] = ()
    decision_register_types: tuple[str, ...] = ()
    policy_refs: tuple[str, ...] = ()
    allowed_namespaces: tuple[str, ...] = ()
    excluded_sources: tuple[str, ...] = ()
    max_context_tokens: int = 4096
    grounding_step_id: str | None = None
    grounding_required: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "profile_id", _non_empty(self.profile_id, "profile_id"))
        object.__setattr__(self, "artifact_type", _non_empty(self.artifact_type, "artifact_type"))
        object.__setattr__(self, "profile_version", _semver(self.profile_version, "profile_version"))
        if self.max_context_tokens <= 0:
            raise ValueError("max_context_tokens must be > 0")
        overlap = {x.artifact_type for x in self.required_upstream} & {x.artifact_type for x in self.optional_supporting}
        if overlap:
            raise ValueError(f"dependency type cannot be both required and optional: {sorted(overlap)}")
        if self.grounding_required and not self.grounding_step_id:
            raise ValueError("grounding_required requires grounding_step_id")

    @property
    def contract_sha256(self) -> str:
        return canonical_sha256(self.to_dict())

    def to_dict(self) -> dict[str, Any]:
        def row(item: DependencyRequirement) -> dict[str, Any]:
            return {
                "artifact_type": item.artifact_type,
                "min_authority_rank": item.min_authority_rank,
                "required_lifecycle": item.required_lifecycle,
                "max_age_days": item.max_age_days,
                "namespace": item.namespace,
                "allow_unknown_freshness": item.allow_unknown_freshness,
            }

        return {
            "profile_id": self.profile_id,
            "artifact_type": self.artifact_type,
            "profile_version": self.profile_version,
            "required_upstream": [row(item) for item in self.required_upstream],
            "optional_supporting": [row(item) for item in self.optional_supporting],
            "decision_register_types": list(self.decision_register_types),
            "policy_refs": list(self.policy_refs),
            "allowed_namespaces": list(self.allowed_namespaces),
            "excluded_sources": list(self.excluded_sources),
            "max_context_tokens": self.max_context_tokens,
            "grounding_step_id": self.grounding_step_id,
            "grounding_required": self.grounding_required,
        }


@dataclass(frozen=True)
class ArtifactAuthorityRecord:
    artifact_type: str
    artifact_id: str
    content: str
    authority_rank: int
    namespace: str
    lifecycle: str = "FROZEN"
    updated_at_utc: str | None = None
    citation_ref: str | None = None
    source_path: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "artifact_type", _non_empty(self.artifact_type, "artifact_type"))
        object.__setattr__(self, "artifact_id", _non_empty(self.artifact_id, "artifact_id"))
        object.__setattr__(self, "namespace", _non_empty(self.namespace, "namespace"))
        if self.authority_rank < 0:
            raise ValueError("authority_rank cannot be negative")
        _parse_datetime(self.updated_at_utc)

    @property
    def content_sha256(self) -> str:
        return _semantic_sha256(self.content)

    @property
    def estimated_tokens(self) -> int:
        return estimate_text_tokens(_semantic_text(self.content))

    def to_context_ref(self) -> dict[str, Any]:
        return {
            "artifact_type": self.artifact_type,
            "artifact_id": self.artifact_id,
            "authority_rank": self.authority_rank,
            "namespace": self.namespace,
            "lifecycle": self.lifecycle,
            "updated_at_utc": self.updated_at_utc,
            "citation_ref": self.citation_ref or self.source_path or self.artifact_id,
            "source_path": self.source_path,
            "content_sha256": self.content_sha256,
            "estimated_tokens": self.estimated_tokens,
            "content": _semantic_text(self.content),
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class ResolvedArtifactContext:
    profile_id: str
    profile_version: str
    artifact_type: str
    selected_sources: tuple[dict[str, Any], ...]
    rejected_sources: tuple[dict[str, Any], ...]
    selected_tokens: int
    max_context_tokens: int
    grounding: Mapping[str, Any]
    context_sha256: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "profile_id": self.profile_id,
            "profile_version": self.profile_version,
            "artifact_type": self.artifact_type,
            "selected_sources": [dict(item) for item in self.selected_sources],
            "rejected_sources": [dict(item) for item in self.rejected_sources],
            "selected_tokens": self.selected_tokens,
            "max_context_tokens": self.max_context_tokens,
            "grounding": dict(self.grounding),
            "context_sha256": self.context_sha256,
            "terminology": {
                "dependency_context": "authoritative upstream artifact assembly",
                "context_pack_v2": "supplementary local grounding",
                "agentic_rag": False,
            },
        }


class ArtifactDependencyResolutionError(ValueError):
    pass


class ArtifactDependencyResolver:
    """Resolve authoritative artifact dependencies and compose existing ContextPack v2.

    This resolver does not index or retrieve documents. It selects explicit
    upstream authority records. Optional grounding delegates to the existing
    ContextPackV2Builder, preserving one RAG subsystem.
    """

    def __init__(self, root: Path) -> None:
        self.root = Path(root).resolve()

    def resolve(
        self,
        *,
        profile: ArtifactDependencyProfile,
        records: Iterable[ArtifactAuthorityRecord],
        as_of: datetime | None = None,
        grounding_query: str | None = None,
    ) -> ResolvedArtifactContext:
        current = as_of or datetime.now(timezone.utc)
        if current.tzinfo is None:
            current = current.replace(tzinfo=timezone.utc)
        current = current.astimezone(timezone.utc)
        pool = tuple(records)
        selected: list[ArtifactAuthorityRecord] = []
        rejected: list[dict[str, Any]] = []
        seen_ids: set[str] = set()

        for requirement in profile.required_upstream:
            candidate, reasons = self._best(profile, requirement, pool, current)
            rejected.extend(reasons)
            if candidate is None:
                raise ArtifactDependencyResolutionError(f"required dependency unavailable: {requirement.artifact_type}")
            selected.append(candidate)
            seen_ids.add(candidate.artifact_id)

        required_tokens = sum(row.estimated_tokens for row in selected)
        if required_tokens > profile.max_context_tokens:
            raise ArtifactDependencyResolutionError(
                f"required dependencies exceed context budget: {required_tokens}>{profile.max_context_tokens}"
            )

        used_tokens = required_tokens
        for requirement in profile.optional_supporting:
            candidate, reasons = self._best(profile, requirement, pool, current, required=False)
            rejected.extend(reasons)
            if candidate is None or candidate.artifact_id in seen_ids:
                continue
            tokens = candidate.estimated_tokens
            if used_tokens + tokens > profile.max_context_tokens:
                rejected.append({"artifact_id": candidate.artifact_id, "reason": "context-budget"})
                continue
            selected.append(candidate)
            seen_ids.add(candidate.artifact_id)
            used_tokens += tokens

        source_rows = tuple(row.to_context_ref() for row in selected)
        grounding = self._grounding(profile, current.date(), grounding_query)
        canonical = {
            "profile_id": profile.profile_id,
            "profile_version": profile.profile_version,
            "artifact_type": profile.artifact_type,
            "sources": [
                {
                    key: value
                    for key, value in row.items()
                    if key not in {"content"}
                }
                for row in source_rows
            ],
            "source_content_sha256": [row["content_sha256"] for row in source_rows],
            "grounding_pack_sha256": grounding.get("pack_sha256"),
        }
        digest = canonical_sha256(canonical)
        return ResolvedArtifactContext(
            profile_id=profile.profile_id,
            profile_version=profile.profile_version,
            artifact_type=profile.artifact_type,
            selected_sources=source_rows,
            rejected_sources=tuple(rejected),
            selected_tokens=used_tokens,
            max_context_tokens=profile.max_context_tokens,
            grounding=grounding,
            context_sha256=digest,
        )

    def _best(
        self,
        profile: ArtifactDependencyProfile,
        requirement: DependencyRequirement,
        pool: tuple[ArtifactAuthorityRecord, ...],
        as_of: datetime,
        *,
        required: bool = True,
    ) -> tuple[ArtifactAuthorityRecord | None, list[dict[str, Any]]]:
        accepted: list[ArtifactAuthorityRecord] = []
        rejected: list[dict[str, Any]] = []
        for record in pool:
            if record.artifact_type != requirement.artifact_type:
                continue
            reason = self._ineligible_reason(profile, requirement, record, as_of)
            if reason:
                rejected.append({"artifact_id": record.artifact_id, "reason": reason})
                continue
            accepted.append(record)
        if not accepted:
            return None, rejected
        accepted.sort(
            key=lambda item: (
                -item.authority_rank,
                -int((_parse_datetime(item.updated_at_utc) or datetime.min.replace(tzinfo=timezone.utc)).timestamp()),
                item.artifact_id,
            )
        )
        return accepted[0], rejected

    def _ineligible_reason(
        self,
        profile: ArtifactDependencyProfile,
        requirement: DependencyRequirement,
        record: ArtifactAuthorityRecord,
        as_of: datetime,
    ) -> str | None:
        source_key = record.source_path or record.artifact_id
        if any(fnmatch.fnmatch(source_key, pattern) or fnmatch.fnmatch(record.artifact_id, pattern) for pattern in profile.excluded_sources):
            return "excluded-source"
        if profile.allowed_namespaces and record.namespace not in profile.allowed_namespaces:
            return "namespace-not-allowed"
        if requirement.namespace and record.namespace != requirement.namespace:
            return "namespace-mismatch"
        if record.authority_rank < requirement.min_authority_rank:
            return "authority-rank-too-low"
        if requirement.required_lifecycle and record.lifecycle.upper() != requirement.required_lifecycle.upper():
            return "lifecycle-not-authoritative"
        if requirement.max_age_days is not None:
            updated = _parse_datetime(record.updated_at_utc)
            if updated is None:
                if not requirement.allow_unknown_freshness:
                    return "freshness-unknown"
            else:
                age_days = max(0, (as_of.date() - updated.date()).days)
                if age_days > requirement.max_age_days:
                    return "stale"
        return None

    def _grounding(self, profile: ArtifactDependencyProfile, as_of: date, query: str | None) -> dict[str, Any]:
        if not profile.grounding_step_id or not query:
            return {
                "status": "not-requested",
                "pack_id": None,
                "pack_sha256": None,
                "citations": [],
                "network_used": False,
                "external_api_used": False,
            }
        result = ContextPackV2Builder(
            self.root,
            ContextPackV2Options(step_id=profile.grounding_step_id, query=query, as_of_date=as_of),
        ).build()
        if not result.ok:
            if profile.grounding_required:
                raise ArtifactDependencyResolutionError("required ContextPack v2 grounding failed")
            return {
                "status": "unavailable",
                "pack_id": None,
                "pack_sha256": None,
                "citations": [],
                "network_used": False,
                "external_api_used": False,
            }
        pack = result.data.get("context_pack") or {}
        status = str(pack.get("status") or result.data.get("summary", {}).get("status") or "unknown")
        if profile.grounding_required and status != "grounded":
            raise ArtifactDependencyResolutionError("required ContextPack v2 grounding returned insufficient evidence")
        return {
            "status": status,
            "pack_id": pack.get("pack_id"),
            "pack_sha256": (pack.get("provenance") or {}).get("pack_sha256"),
            "citations": list(pack.get("citations") or []),
            "network_used": bool((pack.get("safety") or {}).get("network_used", False)),
            "external_api_used": bool((pack.get("safety") or {}).get("external_api_used", False)),
        }
