from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RequiredStandard:
    """One internal standard that must exist in docs/standards.

    DevPilot keeps MIPSoftware and MIASI inside the repository because the
    project uses docs-as-code and must validate artifacts without network
    access. A standard entry defines the canonical folder, a human label and
    the core files that prove the standard is present.
    """

    id: str
    title: str
    directory: str
    required_files: tuple[str, ...]


@dataclass(frozen=True)
class RequiredProjectArtifact:
    """One DevPilot project artifact required by the approved baseline."""

    id: str
    path: str
    standard: str
    purpose: str


REQUIRED_STANDARDS: tuple[RequiredStandard, ...] = (
    RequiredStandard(
        id="mipsoftware",
        title="MIPSoftware — Modelo de Ingeniería Profesional de Software",
        directory="docs/standards/mipsoftware",
        required_files=(
            "README.md",
            "01_modelo_ingenieria_profesional_software.md",
            "02_ciclo_vida_software.md",
            "13_extension_miasi.md",
        ),
    ),
    RequiredStandard(
        id="miasi",
        title="MIASI — Modelo de Ingeniería de Sistemas Agénticos Inteligentes",
        directory="docs/standards/miasi",
        required_files=(
            "README.md",
            "01_modelo_ingenieria_sistemas_agenticos.md",
            "03_agentic_sdlc.md",
            "04_estandares_tecnicos_transversales.md",
        ),
    ),
)


REQUIRED_PROJECT_ARTIFACTS: tuple[RequiredProjectArtifact, ...] = (
    RequiredProjectArtifact(
        id="product_vision",
        path="docs/00_product/product_vision.md",
        standard="MIPSoftware",
        purpose="Product vision approved in pre-code baseline.",
    ),
    RequiredProjectArtifact(
        id="business_case",
        path="docs/00_product/business_case.md",
        standard="MIPSoftware",
        purpose="Business justification and viability baseline.",
    ),
    RequiredProjectArtifact(
        id="mvp_scope",
        path="docs/00_product/mvp_scope.md",
        standard="MIPSoftware",
        purpose="MVP, MVP+ and post-MVP scope boundary.",
    ),
    RequiredProjectArtifact(
        id="requirements_specification",
        path="docs/01_requirements/requirements_specification.md",
        standard="MIPSoftware",
        purpose="Functional and non-functional requirements baseline.",
    ),
    RequiredProjectArtifact(
        id="architecture_document",
        path="docs/02_architecture/architecture_document.md",
        standard="MIPSoftware",
        purpose="Architecture baseline and main technical decisions.",
    ),
    RequiredProjectArtifact(
        id="security_threat_model",
        path="docs/03_security/security_threat_model.md",
        standard="MIPSoftware",
        purpose="Security threats, controls and blocking criteria.",
    ),
    RequiredProjectArtifact(
        id="test_strategy",
        path="docs/04_quality/test_strategy.md",
        standard="MIPSoftware",
        purpose="Quality, testing and verification baseline.",
    ),
    RequiredProjectArtifact(
        id="observability_plan",
        path="docs/05_operations/observability_plan.md",
        standard="MIPSoftware",
        purpose="Operational observability baseline.",
    ),
    RequiredProjectArtifact(
        id="runbook",
        path="docs/05_operations/runbook.md",
        standard="MIPSoftware",
        purpose="Local operation and recovery guide.",
    ),
    RequiredProjectArtifact(
        id="agent_card",
        path="docs/06_miasi/agent_card.md",
        standard="MIASI",
        purpose="Agent scope, taxonomy and autonomy rules.",
    ),
    RequiredProjectArtifact(
        id="tool_card",
        path="docs/06_miasi/tool_card.md",
        standard="MIASI",
        purpose="Tool permissions, side effects and control rules.",
    ),
    RequiredProjectArtifact(
        id="policy_card",
        path="docs/06_miasi/policy_card.md",
        standard="MIASI",
        purpose="Policy-as-code baseline for agentic execution.",
    ),
    RequiredProjectArtifact(
        id="eval_card",
        path="docs/06_miasi/eval_card.md",
        standard="MIASI",
        purpose="Agentic evaluation baseline.",
    ),
    RequiredProjectArtifact(
        id="human_approval_card",
        path="docs/06_miasi/human_approval_card.md",
        standard="MIASI",
        purpose="Human approval criteria for sensitive actions.",
    ),
    RequiredProjectArtifact(
        id="observability_card",
        path="docs/06_miasi/observability_card.md",
        standard="MIASI",
        purpose="AgentOps observability and event baseline.",
    ),
    RequiredProjectArtifact(
        id="precode_checklist",
        path="docs/checklists/checklist_pre_code.md",
        standard="MIPSoftware",
        purpose="Approved pre-code gate checklist.",
    ),
    RequiredProjectArtifact(
        id="precode_audit_report",
        path="docs/precode_audit_report.md",
        standard="MIPSoftware",
        purpose="Final pre-code audit report.",
    ),
    RequiredProjectArtifact(
        id="precode_baseline_decision",
        path="docs/precode_baseline_decision.md",
        standard="MIPSoftware",
        purpose="Formal decision to close pre-code baseline.",
    ),
)
