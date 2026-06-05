---
title: Checklist Miasi Required
doc_id: MIPS-CHK-CHECKLIST_MIASI_REQUIRED
doc_type: checklist
version: 0.1.0
status: draft
owner: AI_agents / MIPSoftware
scope: software-engineering-model
created: '2026-05-31'
updated: '2026-06-01'
---

    ---
    title: "Checklist MIASI required"
    version: "0.1.0"
    status: "draft"
    model: "MIPSoftware"
    checklist_id: "checklist_miasi_required"
    doc_type: "checklist"
    owner: "AI_agents / MIPSoftware"
    updated: "2026-05-31"
    items:
  - "MR-001"
  - "MR-002"
  - "MR-003"
  - "MR-004"
    ---

    # Checklist MIASI required

    ## Propósito

    Auditar si un proyecto debe activar MIASI como extensión inteligente.

    ## Resultado esperado

    - **PASS**: todos los ítems obligatorios cumplen.
    - **FAIL**: existe al menos un ítem obligatorio incompleto o ambiguo.
    - **BLOCK**: existe riesgo crítico, falta de evidencia esencial o violación de política.

    ## Checklist

    | Ítem | Descripción | Obligatorio/opcional | Evidencia requerida | Responsable | Criterio PASS | Criterio FAIL | Referencia |
    |---|---|---|---|---|---|---|---|
    | MR-001 | El sistema usa LLMs o modelos IA | obligatorio | architecture_document.md | Architect | Si sí, MIASI activado | IA sin MIASI | MIPS-DOC-014 |
| MR-002 | El sistema usa agentes o tool calling | obligatorio | architecture_document.md | Architect | Si sí, Agent/Tool/Policy Cards | Tool calling sin controles | MIPS-DOC-014 |
| MR-003 | El sistema usa RAG o memoria | obligatorio | data_model.md / MIASI RAG Card | Architect | Si sí, grounding/evals/traces | RAG sin evaluación | MIPS-DOC-014 |
| MR-004 | El sistema automatiza acciones con efecto | obligatorio | security_threat_model.md | Security | Si sí, human approval/dry-run | Acción crítica sin aprobación | MIPS-DOC-014 |

    ## Criterios de bloqueo

    - Cualquier ítem obligatorio marcado como crítico sin evidencia suficiente.
    - Omisión de MIASI cuando el sistema usa IA, agentes, LLMs, RAG, memoria o tool calling.
    - Riesgo de seguridad, privacidad, datos o operación sin owner.

    ## Salida sugerida YAML

    ```yaml
    checklist: "checklist_miasi_required"
    result: "PASS|FAIL|BLOCK"
    mandatory_items_total: 0
    mandatory_items_passed: 0
    findings: []
    decision: "continue|fix|required_approval|block"
    ```
