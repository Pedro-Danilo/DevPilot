---
title: Checklist Production Ready
doc_id: MIPS-CHK-CHECKLIST_PRODUCTION_READY
doc_type: checklist
version: 0.1.0
status: draft
owner: AI_agents / MIPSoftware
scope: software-engineering-model
created: '2026-05-31'
updated: '2026-06-01'
---

    ---
    title: "Checklist production ready"
    version: "0.1.0"
    status: "draft"
    model: "MIPSoftware"
    checklist_id: "checklist_production_ready"
    doc_type: "checklist"
    owner: "AI_agents / MIPSoftware"
    updated: "2026-05-31"
    items:
  - "PR-001"
  - "PR-002"
  - "PR-003"
  - "PR-004"
  - "PR-005"
    ---

    # Checklist production ready

    ## Propósito

    Determinar si el sistema puede operar en producción con riesgos controlados.

    ## Resultado esperado

    - **PASS**: todos los ítems obligatorios cumplen.
    - **FAIL**: existe al menos un ítem obligatorio incompleto o ambiguo.
    - **BLOCK**: existe riesgo crítico, falta de evidencia esencial o violación de política.

    ## Checklist

    | Ítem | Descripción | Obligatorio/opcional | Evidencia requerida | Responsable | Criterio PASS | Criterio FAIL | Referencia |
    |---|---|---|---|---|---|---|---|
    | PR-001 | Runbook operativo listo | obligatorio | runbook.md | Ops | Runbook completo y revisado | Sin runbook | MIPS-DOC-012 |
| PR-002 | Observabilidad mínima | obligatorio | observability_plan.md | Ops | Logs/métricas/trazas según criticidad | Sin observabilidad | MIPS-DOC-012 |
| PR-003 | Backup/restore probado si hay datos | obligatorio si aplica | backup_restore_plan.md | Ops/DBA | Restore probado o justificado | Sin restore | MIPS-DOC-012 |
| PR-004 | Seguridad mínima PASS | obligatorio | security report | Security | Sin vulnerabilidades críticas abiertas | Crítica sin excepción | MIPS-DOC-010 |
| PR-005 | MIASI readiness si aplica | obligatorio si aplica | MIASI readiness report | Eval/Security | Evals, policy y tracing PASS | IA sin readiness | MIPS-DOC-014 |

    ## Criterios de bloqueo

    - Cualquier ítem obligatorio marcado como crítico sin evidencia suficiente.
    - Omisión de MIASI cuando el sistema usa IA, agentes, LLMs, RAG, memoria o tool calling.
    - Riesgo de seguridad, privacidad, datos o operación sin owner.

    ## Salida sugerida YAML

    ```yaml
    checklist: "checklist_production_ready"
    result: "PASS|FAIL|BLOCK"
    mandatory_items_total: 0
    mandatory_items_passed: 0
    findings: []
    decision: "continue|fix|required_approval|block"
    ```
