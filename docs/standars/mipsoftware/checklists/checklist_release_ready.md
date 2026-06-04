---
title: Checklist Release Ready
doc_id: MIPS-CHK-CHECKLIST_RELEASE_READY
doc_type: checklist
version: 0.1.0
status: draft
owner: AI_agents / MIPSoftware
scope: software-engineering-model
created: '2026-05-31'
updated: '2026-06-01'
---

    ---
    title: "Checklist release ready"
    version: "0.1.0"
    status: "draft"
    model: "MIPSoftware"
    checklist_id: "checklist_release_ready"
    doc_type: "checklist"
    owner: "AI_agents / MIPSoftware"
    updated: "2026-05-31"
    items:
  - "RL-001"
  - "RL-002"
  - "RL-003"
  - "RL-004"
    ---

    # Checklist release ready

    ## Propósito

    Confirmar que el release tiene versión, evidencia, rollback y aprobación.

    ## Resultado esperado

    - **PASS**: todos los ítems obligatorios cumplen.
    - **FAIL**: existe al menos un ítem obligatorio incompleto o ambiguo.
    - **BLOCK**: existe riesgo crítico, falta de evidencia esencial o violación de política.

    ## Checklist

    | Ítem | Descripción | Obligatorio/opcional | Evidencia requerida | Responsable | Criterio PASS | Criterio FAIL | Referencia |
    |---|---|---|---|---|---|---|---|
    | RL-001 | Versión definida | obligatorio | release_plan.md | Release Manager | SemVer o regla definida | Release sin versión | MIPS-DOC-011 |
| RL-002 | Quality gates PASS | obligatorio | quality_gate_report.md | QA | Gates críticos PASS | Gate crítico FAIL | MIPS-DOC-009/011 |
| RL-003 | Rollback definido | obligatorio | rollback_plan.md | Release Manager | Rollback probado o documentado | Sin rollback | MIPS-DOC-011 |
| RL-004 | Notas de release listas | obligatorio | release_plan.md | Release Manager | Cambios y riesgos comunicables | Sin comunicación | MIPS-DOC-011 |

    ## Criterios de bloqueo

    - Cualquier ítem obligatorio marcado como crítico sin evidencia suficiente.
    - Omisión de MIASI cuando el sistema usa IA, agentes, LLMs, RAG, memoria o tool calling.
    - Riesgo de seguridad, privacidad, datos o operación sin owner.

    ## Salida sugerida YAML

    ```yaml
    checklist: "checklist_release_ready"
    result: "PASS|FAIL|BLOCK"
    mandatory_items_total: 0
    mandatory_items_passed: 0
    findings: []
    decision: "continue|fix|required_approval|block"
    ```
