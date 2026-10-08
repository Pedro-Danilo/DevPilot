from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ArtifactProfile:
    """Versioned artifact-quality profile with backward-compatible Markdown rules.

    Historical DevPilot validators consume ``path_contains``, ``filename`` and
    heading lists. MP-0C extends that same contract with provider-neutral
    quality metadata instead of creating a parallel profile registry. Existing
    JSON profiles remain valid because every new field has a conservative
    deterministic default. Domain-complete professional profiles are later-wave
    scope; this class only establishes the shared foundation.
    """

    id: str
    description: str
    path_contains: tuple[str, ...] = ()
    filename: str | None = None
    required_headings: tuple[str, ...] = ()
    recommended_headings: tuple[str, ...] = ()
    profile_version: str = "1.0.0"
    purpose: str = ""
    payload_schema_ref: str | None = None
    semantic_rules: tuple[str, ...] = ()
    completeness_rules: tuple[str, ...] = ()
    upstream_trace_required: bool = False
    assumptions_policy: str = "explicit"
    open_questions_policy: str = "explicit"
    prohibited_unsupported_claims: tuple[str, ...] = ()
    quality_gates: tuple[str, ...] = ()
    render_template_ref: str | None = None
    human_review_checklist: tuple[str, ...] = ()
    downstream_semantics: tuple[str, ...] = ()
    migration_policy: str = "compatible-additive"

    def __post_init__(self) -> None:
        import re

        if not str(self.id or "").strip():
            raise ValueError("artifact profile id must be non-empty")
        if not str(self.description or "").strip():
            raise ValueError("artifact profile description must be non-empty")
        if not re.fullmatch(r"\d+\.\d+\.\d+", str(self.profile_version or "")):
            raise ValueError("profile_version must use semantic version form MAJOR.MINOR.PATCH")
        if not self.purpose:
            object.__setattr__(self, "purpose", self.description)
        if self.assumptions_policy not in {"explicit", "forbidden", "allowed-with-rationale"}:
            raise ValueError("unsupported assumptions_policy")
        if self.open_questions_policy not in {"explicit", "forbidden", "allowed"}:
            raise ValueError("unsupported open_questions_policy")

    @property
    def required_sections(self) -> tuple[str, ...]:
        return self.required_headings

    @property
    def optional_sections(self) -> tuple[str, ...]:
        return self.recommended_headings

    def foundation_contract(self) -> dict[str, object]:
        """Return MP-v2 foundation metadata without changing legacy selection."""

        return {
            "artifact_type": self.id,
            "profile_version": self.profile_version,
            "purpose": self.purpose,
            "required_sections": list(self.required_sections),
            "optional_sections": list(self.optional_sections),
            "payload_schema_ref": self.payload_schema_ref,
            "semantic_rules": list(self.semantic_rules),
            "completeness_rules": list(self.completeness_rules),
            "upstream_trace_required": self.upstream_trace_required,
            "assumptions_policy": self.assumptions_policy,
            "open_questions_policy": self.open_questions_policy,
            "prohibited_unsupported_claims": list(self.prohibited_unsupported_claims),
            "quality_gates": list(self.quality_gates),
            "render_template_ref": self.render_template_ref,
            "human_review_checklist": list(self.human_review_checklist),
            "downstream_semantics": list(self.downstream_semantics),
            "migration_policy": self.migration_policy,
        }


GENERIC_MARKDOWN_PROFILE = ArtifactProfile(
    id="generic-markdown",
    description="Generic Markdown engineering artifact.",
    required_headings=(),
    recommended_headings=("propósito", "estado"),
)


ARTIFACT_PROFILES: tuple[ArtifactProfile, ...] = (
    ArtifactProfile(
        id="product-vision",
        description="Product vision baseline artifact.",
        path_contains=("docs/00_product",),
        filename="product_vision.md",
        required_headings=("resumen ejecutivo", "problema", "visión", "mvp", "indicadores"),
        recommended_headings=("workspaces", "local-first", "post-mvp"),
        profile_version="1.1.0",
        purpose="Define a traceable Product Vision grounded in Project Context, business need and Owner constraints without invented facts.",
        payload_schema_ref="docs/schemas/product_vision_payload.schema.json",
        semantic_rules=("problem-and-vision-must-trace-to-authoritative-inputs", "mvp-outcomes-must-not-introduce-unsupported-capabilities", "claims-require-source-refs-or-must-be-recorded-as-assumptions", "open-decisions-remain-explicit-and-non-authoritative"),
        completeness_rules=("problem-present", "vision-present", "mvp-outcomes-present", "indicators-present", "assumptions-and-open-questions-explicit"),
        upstream_trace_required=True, assumptions_policy="allowed-with-rationale", open_questions_policy="explicit",
        prohibited_unsupported_claims=("factual-claim-without-authoritative-source", "invented-business-rule", "invented-owner-decision"),
        quality_gates=("payload-schema-valid", "grounded-claims-only", "explicit-uncertainty", "human-review-ready"),
        render_template_ref="docs/00_product/product_vision.md",
        human_review_checklist=("problem matches business need", "vision reflects Owner constraints", "MVP does not exceed supported scope", "indicators are measurable or explicitly provisional"),
        downstream_semantics=("authoritative-input-for-mvp-scope-only-when-FROZEN", "upstream-hash-change-invalidates-dependent-scope"),
    ),
    ArtifactProfile(
        id="business-case",
        description="Business case baseline artifact.",
        path_contains=("docs/00_product",),
        filename="business_case.md",
        required_headings=("propósito", "problema", "justificación", "beneficios", "riesgos"),
        recommended_headings=("costos", "criterios", "veredicto"),
    ),
    ArtifactProfile(
        id="mvp-scope",
        description="MVP scope baseline artifact.",
        path_contains=("docs/00_product",),
        filename="mvp_scope.md",
        required_headings=("mvp", "mvp+", "out of scope", "criterios"),
        recommended_headings=("restricciones", "local-first", "workspaces"),
        profile_version="1.1.0",
        purpose="Define MVP scope from FROZEN Product Vision, Project Context and Owner decisions with explicit in/out boundaries.",
        payload_schema_ref="docs/schemas/mvp_scope_payload.schema.json",
        semantic_rules=("scope-must-bind-frozen-product-vision", "in-scope-items-require-upstream-source-refs", "out-of-scope-is-explicit", "owner-decisions-must-be-lineage-bound-not-invented"),
        completeness_rules=("in-scope-present", "out-of-scope-present", "constraints-explicit", "acceptance-boundaries-present", "upstream-vision-binding-present"),
        upstream_trace_required=True, assumptions_policy="allowed-with-rationale", open_questions_policy="explicit",
        prohibited_unsupported_claims=("scope-item-without-authoritative-source", "invented-owner-decision", "silent-scope-expansion"),
        quality_gates=("payload-schema-valid", "frozen-vision-binding", "grounded-claims-only", "explicit-scope-boundaries", "human-review-ready"),
        render_template_ref="docs/00_product/mvp_scope.md",
        human_review_checklist=("Vision binding is current and FROZEN", "every in-scope capability has upstream support", "out-of-scope is explicit", "Owner decisions are lineage-bound"),
        downstream_semantics=("authoritative-input-for-requirements-only-when-FROZEN", "scope-hash-change-invalidates-dependent-requirements"),
    ),
    ArtifactProfile(
        id="requirements-specification",
        description="Requirements specification artifact aligned with MIPSoftware.",
        path_contains=("docs/01_requirements",),
        filename="requirements_specification.md",
        required_headings=(
            "propósito",
            "alcance",
            "requerimientos funcionales del mvp",
            "requerimientos no funcionales",
            "criterios de bloqueo",
        ),
        recommended_headings=("mvp+", "post-mvp", "miasi"),
        profile_version="1.1.0",
        purpose="Define traceable functional and non-functional requirements from FROZEN Vision/Scope plus decisions and constraints.",
        payload_schema_ref="docs/schemas/requirements_payload.schema.json",
        semantic_rules=("requirements-must-bind-frozen-vision-and-scope", "each-requirement-requires-source-refs", "acceptance-criteria-required-for-functional-requirements", "decision-and-constraint-lineage-must-be-explicit"),
        completeness_rules=("functional-requirements-present", "non-functional-requirements-present", "acceptance-criteria-present", "constraints-explicit", "open-decisions-explicit"),
        upstream_trace_required=True, assumptions_policy="allowed-with-rationale", open_questions_policy="explicit",
        prohibited_unsupported_claims=("requirement-without-authoritative-source", "invented-constraint", "invented-acceptance-criterion-as-owner-fact"),
        quality_gates=("payload-schema-valid", "frozen-vision-scope-binding", "grounded-requirements-only", "acceptance-criteria-complete", "human-review-ready"),
        render_template_ref="docs/01_requirements/requirements_specification.md",
        human_review_checklist=("Vision and Scope bindings are current/FROZEN", "RF and RNF IDs are stable", "every requirement has source refs", "acceptance criteria are testable", "unresolved decisions remain explicit"),
        downstream_semantics=("authoritative-input-for-architecture-and-test-when-FROZEN", "requirements-hash-change-invalidates-downstream-engineering-baseline"),
    ),
    ArtifactProfile(
        id="use-cases",
        description="Use cases baseline artifact.",
        path_contains=("docs/01_requirements",),
        filename="use_cases.md",
        required_headings=("propósito", "casos de uso", "mvp"),
        recommended_headings=("mvp+", "post-mvp", "criterios"),
    ),
    ArtifactProfile(
        id="traceability-matrix",
        description="Traceability matrix artifact.",
        path_contains=("docs/01_requirements",),
        filename="traceability_matrix.md",
        required_headings=("propósito", "matriz"),
        recommended_headings=("producto", "requerimiento", "prueba"),
    ),
    ArtifactProfile(
        id="architecture-document",
        description="Architecture document artifact aligned with C4/arc42 discipline.",
        path_contains=("docs/02_architecture",),
        filename="architecture_document.md",
        required_headings=("propósito", "alcance", "drivers", "componentes", "riesgos"),
        recommended_headings=("persistencia", "seguridad", "tecnología", "agentes"),
    ),
    ArtifactProfile(
        id="c4-context",
        description="C4 context view artifact.",
        path_contains=("docs/02_architecture",),
        filename="c4_context.md",
        required_headings=("propósito", "contexto"),
        recommended_headings=("mermaid", "actores", "sistemas"),
    ),
    ArtifactProfile(
        id="c4-container",
        description="C4 container view artifact.",
        path_contains=("docs/02_architecture",),
        filename="c4_container.md",
        required_headings=("propósito", "contenedores"),
        recommended_headings=("mermaid", "responsabilidades", "tecnología"),
    ),
    ArtifactProfile(
        id="adr",
        description="Architecture Decision Record artifact.",
        path_contains=("docs/02_architecture/adrs",),
        required_headings=("contexto", "decisión", "consecuencias"),
        recommended_headings=("alternativas", "estado"),
    ),
    ArtifactProfile(
        id="security-threat-model",
        description="Security threat model artifact.",
        path_contains=("docs/03_security",),
        filename="security_threat_model.md",
        required_headings=("propósito", "alcance", "amenazas", "controles", "criterios de bloqueo"),
        recommended_headings=("activos", "límites de confianza", "miasi"),
    ),
    ArtifactProfile(
        id="privacy-assessment",
        description="Privacy assessment artifact.",
        path_contains=("docs/03_security",),
        filename="privacy_assessment.md",
        required_headings=("propósito", "alcance", "datos", "retención", "riesgos"),
        recommended_headings=("redacción", "privacidad", "apis externas"),
    ),
    ArtifactProfile(
        id="test-strategy",
        description="Quality and testing strategy artifact.",
        path_contains=("docs/04_quality",),
        filename="test_strategy.md",
        required_headings=("propósito", "alcance", "tipos de pruebas", "quality gates", "criterios"),
        recommended_headings=("trazabilidad", "coverage", "agentic tests"),
    ),
    ArtifactProfile(
        id="observability-plan",
        description="Observability plan artifact.",
        path_contains=("docs/05_operations",),
        filename="observability_plan.md",
        required_headings=("propósito", "señales", "trazas", "métricas"),
        recommended_headings=("eventos", "retención", "opentelemetry"),
    ),
    ArtifactProfile(
        id="runbook",
        description="Local operations runbook artifact.",
        path_contains=("docs/05_operations",),
        filename="runbook.md",
        required_headings=("propósito", "instalación", "validación", "fallos", "recuperación"),
        recommended_headings=("pytest", "git", "agentes"),
    ),
    ArtifactProfile(
        id="miasi-agent-card",
        description="MIASI Agent Card artifact.",
        path_contains=("docs/06_miasi",),
        filename="agent_card.md",
        required_headings=("propósito", "alcance", "taxonomía", "contrato", "criterios pass", "criterios block"),
        recommended_headings=("autonomía", "herramientas", "mipsoftware"),
    ),
    ArtifactProfile(
        id="miasi-tool-card",
        description="MIASI Tool Card artifact.",
        path_contains=("docs/06_miasi",),
        filename="tool_card.md",
        required_headings=("propósito", "herramientas", "tool contract", "criterios pass", "criterios block"),
        recommended_headings=("riesgo", "restricciones", "aprobación"),
    ),
    ArtifactProfile(
        id="miasi-policy-card",
        description="MIASI Policy Card artifact.",
        path_contains=("docs/06_miasi",),
        filename="policy_card.md",
        required_headings=("propósito", "política", "modos de ejecución", "criterios block"),
        recommended_headings=("costguard", "secretguard", "matriz"),
    ),
    ArtifactProfile(
        id="miasi-eval-card",
        description="MIASI Eval Card artifact.",
        path_contains=("docs/06_miasi",),
        filename="eval_card.md",
        required_headings=("propósito", "evaluación", "métricas", "criterios pass", "criterios block"),
        recommended_headings=("datasets", "quality gates", "reportes"),
    ),
    ArtifactProfile(
        id="miasi-human-approval-card",
        description="MIASI Human Approval Card artifact.",
        path_contains=("docs/06_miasi",),
        filename="human_approval_card.md",
        required_headings=("propósito", "aprobación", "acciones", "criterios pass", "criterios block"),
        recommended_headings=("matriz", "registro", "revisión humana"),
    ),
    ArtifactProfile(
        id="miasi-observability-card",
        description="MIASI Observability Card artifact.",
        path_contains=("docs/06_miasi",),
        filename="observability_card.md",
        required_headings=("propósito", "señales", "eventos", "criterios"),
        recommended_headings=("agentops", "opentelemetry", "métricas"),
    ),
)


def _normalize_path(path: Path, root: Path | None = None) -> str:
    candidate = path
    if root is not None:
        try:
            candidate = path.resolve().relative_to(root.resolve())
        except ValueError:
            candidate = path
    return str(candidate).replace("\\", "/")


def select_artifact_profile(path: Path, root: Path | None = None) -> ArtifactProfile:
    """Select the most specific validation profile for a Markdown artifact.

    FUNC-SPRINT-24 makes JSON artifact profiles the preferred source when a
    project root is available. The original Python constants remain the safe
    fallback so readiness strict and historical validators keep their behavior
    if the data-driven catalog is unavailable or invalid.
    """

    if root is not None:
        try:
            from devpilot_core.validation.artifact_profile_registry import ArtifactProfileRegistry

            return ArtifactProfileRegistry(root).select(path)
        except Exception:
            # Conservative fallback: do not break existing validators during the
            # data-driven migration window. Registry health is reported by
            # validate docs / ArtifactProfileRegistry.status().
            pass

    normalized_path = _normalize_path(path, root)
    path_name = Path(normalized_path).name

    # Exact filename + path match first.
    for profile in ARTIFACT_PROFILES:
        if profile.filename and profile.filename != path_name:
            continue
        if all(fragment in normalized_path for fragment in profile.path_contains):
            return profile

    # Folder/path match for families such as ADRs.
    for profile in ARTIFACT_PROFILES:
        if profile.filename is not None:
            continue
        if all(fragment in normalized_path for fragment in profile.path_contains):
            return profile

    return GENERIC_MARKDOWN_PROFILE
