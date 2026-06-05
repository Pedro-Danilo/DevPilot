---
title: Checklist Architecture Ready
doc_id: MIPS-CHK-CHECKLIST_ARCHITECTURE_READY
doc_type: checklist
version: 0.1.0
status: draft
owner: AI_agents / MIPSoftware
scope: software-engineering-model
created: '2026-05-31'
updated: '2026-06-01'
---

    ---
    title: "Checklist architecture ready"
    version: "0.1.0"
    status: "draft"
    model: "MIPSoftware"
    checklist_id: "checklist_architecture_ready"
    doc_type: "checklist"
    owner: "AI_agents / MIPSoftware"
    updated: "2026-05-31"
    items:
  - "AR-001"
  - "AR-002"
  - "AR-003"
  - "AR-004"
    ---

    # Checklist architecture ready

    ## Propósito

    Confirmar que la arquitectura mínima permite implementar con control de calidad y riesgo.

    ## Resultado esperado

    - **PASS**: todos los ítems obligatorios cumplen.
    - **FAIL**: existe al menos un ítem obligatorio incompleto o ambiguo.
    - **BLOCK**: existe riesgo crítico, falta de evidencia esencial o violación de política.

    ## Checklist

    | Ítem | Descripción | Obligatorio/opcional | Evidencia requerida | Responsable | Criterio PASS | Criterio FAIL | Referencia |
    |---|---|---|---|---|---|---|---|
    | AR-001 | Drivers arquitectónicos definidos | obligatorio | architecture_document.md | Architect | Drivers trazados a negocio/NFR | Drivers ausentes | MIPS-DOC-006 |
| AR-002 | C4 contexto y contenedores documentados | obligatorio | c4_context.md/c4_container.md | Architect | Diagramas o vistas textuales revisadas | No hay vista de arquitectura | MIPS-DOC-006 |
| AR-003 | ADRs para decisiones relevantes | obligatorio | adr_template.md | Architect | Decisiones críticas con ADR | Decisiones implícitas | MIPS-DOC-006 |
| AR-004 | Riesgos arquitectónicos registrados | obligatorio | architecture_risk_log.md | Architect | Riesgos con mitigación/owner | Riesgos no registrados | MIPS-DOC-006 |

    ## Criterios de bloqueo

    - Cualquier ítem obligatorio marcado como crítico sin evidencia suficiente.
    - Omisión de MIASI cuando el sistema usa IA, agentes, LLMs, RAG, memoria o tool calling.
    - Riesgo de seguridad, privacidad, datos o operación sin owner.

    ## Salida sugerida YAML

    ```yaml
    checklist: "checklist_architecture_ready"
    result: "PASS|FAIL|BLOCK"
    mandatory_items_total: 0
    mandatory_items_passed: 0
    findings: []
    decision: "continue|fix|required_approval|block"
    ```
