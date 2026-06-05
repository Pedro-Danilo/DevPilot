---
title: Checklist Operational Ready
doc_id: MIPS-CHK-CHECKLIST_OPERATIONAL_READY
doc_type: checklist
version: 0.1.0
status: draft
owner: AI_agents / MIPSoftware
scope: software-engineering-model
created: '2026-05-31'
updated: '2026-06-01'
---

    ---
    title: "Checklist operational ready"
    version: "0.1.0"
    status: "draft"
    model: "MIPSoftware"
    checklist_id: "checklist_operational_ready"
    doc_type: "checklist"
    owner: "AI_agents / MIPSoftware"
    updated: "2026-05-31"
    items:
  - "OR-001"
  - "OR-002"
  - "OR-003"
  - "OR-004"
    ---

    # Checklist operational ready

    ## Propósito

    Verificar operación, soporte, incidentes, SLO/SLA y aprendizaje.

    ## Resultado esperado

    - **PASS**: todos los ítems obligatorios cumplen.
    - **FAIL**: existe al menos un ítem obligatorio incompleto o ambiguo.
    - **BLOCK**: existe riesgo crítico, falta de evidencia esencial o violación de política.

    ## Checklist

    | Ítem | Descripción | Obligatorio/opcional | Evidencia requerida | Responsable | Criterio PASS | Criterio FAIL | Referencia |
    |---|---|---|---|---|---|---|---|
    | OR-001 | SLO/SLI definidos si aplica | obligatorio para servicios con usuarios | slo_sla.md | Ops | SLIs y SLOs claros | Sin objetivos operativos | MIPS-DOC-012 |
| OR-002 | Alertas definidas | obligatorio si hay monitoreo | observability_plan.md | Ops | Alertas accionables | Alertas ruidosas o ausentes | MIPS-DOC-012 |
| OR-003 | Proceso de incidentes definido | obligatorio | incident_report.md | Ops | Severidades y flujo claros | Sin proceso | MIPS-DOC-012 |
| OR-004 | Postmortem obligatorio para incidentes relevantes | obligatorio | postmortem.md | Ops | Acciones preventivas registradas | Incidente sin aprendizaje | MIPS-DOC-012 |

    ## Criterios de bloqueo

    - Cualquier ítem obligatorio marcado como crítico sin evidencia suficiente.
    - Omisión de MIASI cuando el sistema usa IA, agentes, LLMs, RAG, memoria o tool calling.
    - Riesgo de seguridad, privacidad, datos o operación sin owner.

    ## Salida sugerida YAML

    ```yaml
    checklist: "checklist_operational_ready"
    result: "PASS|FAIL|BLOCK"
    mandatory_items_total: 0
    mandatory_items_passed: 0
    findings: []
    decision: "continue|fix|required_approval|block"
    ```
