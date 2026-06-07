from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ArtifactProfile:
    """Validation profile for one family of engineering artifacts.

    A profile defines the minimum headings expected for a Markdown artifact.
    FUNC-SPRINT-03 intentionally keeps the rules deterministic and local-first:
    no LLM, no external service and no schema dependency are required.
    """

    id: str
    description: str
    path_contains: tuple[str, ...] = ()
    filename: str | None = None
    required_headings: tuple[str, ...] = ()
    recommended_headings: tuple[str, ...] = ()


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
    """Select the most specific validation profile for a Markdown artifact."""

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
