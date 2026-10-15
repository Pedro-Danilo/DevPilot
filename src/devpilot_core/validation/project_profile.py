"""PESP v2 first vertical: project-scoped, evidence-bound applicability.

Structural Artifact Profiles remain owned by ArtifactProfileRegistry. This
module never evaluates semantic document quality or grants execution rights.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import hashlib
import json
from typing import Literal

from devpilot_core.validation.artifact_profile_registry import ArtifactProfileRegistry

Applicability = Literal["REQUIRED", "CONDITIONAL", "RECOMMENDED", "NOT_APPLICABLE", "REVIEW_REQUIRED"]
_AI_SCOPES = frozenset({"agent", "tool", "tool_write", "memory", "rag", "model_runtime", "autonomy"})
_FORBIDDEN_WAIVER_TOKENS = ("mipsoftware", "miasi", "security", "privacy", "legal", "auth", "permission", "human-approval", "policy", "threat", "compliance")


@dataclass(frozen=True)
class ProjectFacts:
    project_id: str
    revision: int
    product_has_ai: bool | None
    confirmed_scopes: tuple[str, ...] = ()
    evidence_refs: tuple[str, ...] = ()
    devtool_uses_llm: bool = False
    state: Literal["DRAFT", "FROZEN"] = "DRAFT"
    supersedes_revision: int | None = None
    previous_frozen_sha256: str | None = None

    def __post_init__(self) -> None:
        if not self.project_id.strip() or self.revision < 1:
            raise ValueError("PESP_PROJECT_ID_OR_REVISION_INVALID")
        if self.state not in {"DRAFT", "FROZEN"}:
            raise ValueError("PESP_STATE_INVALID")
        if type(self.product_has_ai) not in (bool, type(None)):
            raise ValueError("PESP_AI_FACT_INVALID")
        if not set(self.confirmed_scopes).issubset(_AI_SCOPES):
            raise ValueError("PESP_UNKNOWN_COMPONENT_SCOPE")
        if self.product_has_ai is False and self.confirmed_scopes:
            raise ValueError("PESP_CONTRADICTORY_FACTS")
        if self.product_has_ai is True and (not self.confirmed_scopes or not self.evidence_refs):
            raise ValueError("PESP_AI_FACT_EVIDENCE_REQUIRED")
        if self.product_has_ai is None and self.confirmed_scopes:
            raise ValueError("PESP_UNCONFIRMED_SCOPE")
        if self.product_has_ai is False and not self.evidence_refs:
            raise ValueError("PESP_NON_AI_EVIDENCE_REQUIRED")
        if self.supersedes_revision is not None and (self.supersedes_revision >= self.revision or not self.previous_frozen_sha256):
            raise ValueError("PESP_SUCCESSOR_BINDING_REQUIRED")


@dataclass(frozen=True)
class Waiver:
    control_ref: str
    reason: str
    risk: str
    compensating_controls: tuple[str, ...]
    owner: str
    expires: str
    review_trigger: str
    evidence_ref: str


def assess_waiver(waiver: Waiver, *, today: date | None = None) -> dict[str, str]:
    """Waivers never disable obligatory standards or safety/legal controls."""
    if any(term in waiver.control_ref.lower() for term in _FORBIDDEN_WAIVER_TOKENS):
        raise ValueError("PESP_NON_WAIVABLE_CONTROL")
    if not all((waiver.control_ref, waiver.reason, waiver.risk, waiver.owner, waiver.review_trigger, waiver.evidence_ref)) or not waiver.compensating_controls:
        raise ValueError("PESP_WAIVER_INCOMPLETE")
    try:
        expiry = date.fromisoformat(waiver.expires)
    except ValueError as exc:
        raise ValueError("PESP_WAIVER_DATE_INVALID") from exc
    if expiry <= (today or date.today()):
        raise ValueError("PESP_WAIVER_EXPIRED")
    return {"control_ref": waiver.control_ref, "decision": "REVIEW_REQUIRED", "reason": waiver.reason, "evidence_ref": waiver.evidence_ref}


def project_hash(facts: ProjectFacts) -> str:
    """Canonical fingerprint for immutable, FROZEN project facts."""
    from dataclasses import asdict
    payload=json.dumps(asdict(facts),sort_keys=True,ensure_ascii=False,separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def successor_of(previous: ProjectFacts, updated: ProjectFacts) -> ProjectFacts:
    if previous.state != "FROZEN" or previous.project_id != updated.project_id or updated.state != "DRAFT":
        raise ValueError("PESP_FROZEN_SUCCESSOR_STATE_INVALID")
    if updated.revision <= previous.revision:
        raise ValueError("PESP_FROZEN_REVISION_REUSED")
    if updated.supersedes_revision != previous.revision or updated.previous_frozen_sha256 != project_hash(previous):
        raise ValueError("PESP_FROZEN_LINEAGE_INVALID")
    return updated


class ProjectApplicability:
    """First vertical PESP, backed by the existing artifact-profile registry."""
    def __init__(self, registry: ArtifactProfileRegistry):
        self.registry = registry

    def evaluate(self, facts: ProjectFacts, waivers: tuple[Waiver, ...] = ()) -> dict:
        profiles, _, used_fallback = self.registry.load_profiles(allow_fallback=False)
        by_id = {p.id: p for p in profiles}
        required = {"miasi-agent-card", "miasi-policy-card", "miasi-eval-card", "miasi-tool-card", "miasi-human-approval-card", "miasi-observability-card"}
        if not required.issubset(by_id):
            raise ValueError("PESP_EXISTING_ARTIFACT_PROFILES_MISSING")
        if facts.product_has_ai is None:
            miasi = "REVIEW_REQUIRED"
            why = "Project AI scope not confirmed; human review and evidence required"
        elif facts.product_has_ai:
            miasi = "REQUIRED"
            why = "Confirmed AI components in the delivered product"
        else:
            miasi = "NOT_APPLICABLE"
            why = "Evidence confirms conventional product; devtool LLM use does not imply product AI"
        tool = bool({"tool", "tool_write"} & set(facts.confirmed_scopes))
        write = "tool_write" in facts.confirmed_scopes
        artifacts = []
        for name in sorted(required):
            if miasi == "NOT_APPLICABLE":
                decision = "NOT_APPLICABLE"
            elif miasi == "REVIEW_REQUIRED":
                decision = "REVIEW_REQUIRED"
            elif name in {"miasi-tool-card", "miasi-human-approval-card"}:
                decision = "REQUIRED" if (tool if name == "miasi-tool-card" else write) else "NOT_APPLICABLE"
            elif name == "miasi-observability-card":
                decision = "RECOMMENDED"
            else:
                decision = "REQUIRED"
            reason = why if miasi != "REQUIRED" else (
                "Tool-write component requires human approval" if name == "miasi-human-approval-card" and write
                else "No confirmed tool-write component" if name == "miasi-human-approval-card"
                else "Confirmed tool component" if name == "miasi-tool-card" and tool
                else "No confirmed tool component" if name == "miasi-tool-card"
                else "Confirmed AI scope; document-specific requirement"
            )
            artifacts.append({"artifact_type":name,"profile_version":by_id[name].profile_version,
                              "applicability":decision,"rationale":reason,"evidence_refs":list(facts.evidence_refs)})
        waiver_assessments=[assess_waiver(w) for w in waivers]
        return {"contract":"PESP-V2-FIRST-VERTICAL","project_id":facts.project_id,"revision":facts.revision,
                "state":facts.state,"fingerprint":project_hash(facts),"source_catalog":"docs/validation/artifact_profiles.json",
                "catalog_fallback_used":used_fallback,
                "standards":[{"id":"MIPSoftware","applicability":"REQUIRED","rationale":"All software projects"},
                             {"id":"MIASI","applicability":miasi,"rationale":why,"evidence_refs":list(facts.evidence_refs)}],
                "artifacts":artifacts,"waiver_reviews":waiver_assessments,
                "evaluation_only":True,"owner_approval_granted":False,"external_egress":"DENIED"}
