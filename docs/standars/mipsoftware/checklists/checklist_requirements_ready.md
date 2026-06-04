---
title: Checklist Requirements Ready
doc_id: MIPS-CHK-CHECKLIST_REQUIREMENTS_READY
doc_type: checklist
version: 0.1.0
status: draft
owner: AI_agents / MIPSoftware
scope: software-engineering-model
created: '2026-05-31'
updated: '2026-06-01'
---

    ---
    title: "Checklist requirements ready"
    version: "0.1.0"
    status: "draft"
    model: "MIPSoftware"
    checklist_id: "checklist_requirements_ready"
    doc_type: "checklist"
    owner: "AI_agents / MIPSoftware"
    updated: "2026-05-31"
    items:
  - "RR-001"
  - "RR-002"
  - "RR-003"
  - "RR-004"
    ---

    # Checklist requirements ready

    ## Propósito

    Confirmar que los requerimientos están completos, priorizados, trazables y verificables.

    ## Resultado esperado

    - **PASS**: todos los ítems obligatorios cumplen.
    - **FAIL**: existe al menos un ítem obligatorio incompleto o ambiguo.
    - **BLOCK**: existe riesgo crítico, falta de evidencia esencial o violación de política.

    ## Checklist

    | Ítem | Descripción | Obligatorio/opcional | Evidencia requerida | Responsable | Criterio PASS | Criterio FAIL | Referencia |
    |---|---|---|---|---|---|---|---|
    | RR-001 | Cada requerimiento tiene criterio de aceptación | obligatorio | requirements_specification.md | Analyst | Todos tienen acceptance criteria | Falta criterio de aceptación | MIPS-DOC-005 |
| RR-002 | Los NFR son medibles | obligatorio | requirements_specification.md | Architect/QA | NFR con métrica y umbral | NFR genérico | MIPS-DOC-005 |
| RR-003 | Existe trazabilidad negocio → requerimiento | obligatorio | traceability_matrix.md | Analyst | Cada REQ apunta a necesidad | REQ huérfano | MIPS-DOC-004/005 |
| RR-004 | Cambios tienen responsable | opcional | change log | Project Owner | Cambios relevantes aprobados | Cambios sin control | MIPS-DOC-005 |

    ## Criterios de bloqueo

    - Cualquier ítem obligatorio marcado como crítico sin evidencia suficiente.
    - Omisión de MIASI cuando el sistema usa IA, agentes, LLMs, RAG, memoria o tool calling.
    - Riesgo de seguridad, privacidad, datos o operación sin owner.

    ## Salida sugerida YAML

    ```yaml
    checklist: "checklist_requirements_ready"
    result: "PASS|FAIL|BLOCK"
    mandatory_items_total: 0
    mandatory_items_passed: 0
    findings: []
    decision: "continue|fix|required_approval|block"
    ```
