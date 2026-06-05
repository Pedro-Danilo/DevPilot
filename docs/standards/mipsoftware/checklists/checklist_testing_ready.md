---
title: Checklist Testing Ready
doc_id: MIPS-CHK-CHECKLIST_TESTING_READY
doc_type: checklist
version: 0.1.0
status: draft
owner: AI_agents / MIPSoftware
scope: software-engineering-model
created: '2026-05-31'
updated: '2026-06-01'
---

    ---
    title: "Checklist testing ready"
    version: "0.1.0"
    status: "draft"
    model: "MIPSoftware"
    checklist_id: "checklist_testing_ready"
    doc_type: "checklist"
    owner: "AI_agents / MIPSoftware"
    updated: "2026-05-31"
    items:
  - "TR-001"
  - "TR-002"
  - "TR-003"
  - "TR-004"
    ---

    # Checklist testing ready

    ## Propósito

    Confirmar que la calidad y pruebas cubren requerimientos críticos y riesgos.

    ## Resultado esperado

    - **PASS**: todos los ítems obligatorios cumplen.
    - **FAIL**: existe al menos un ítem obligatorio incompleto o ambiguo.
    - **BLOCK**: existe riesgo crítico, falta de evidencia esencial o violación de política.

    ## Checklist

    | Ítem | Descripción | Obligatorio/opcional | Evidencia requerida | Responsable | Criterio PASS | Criterio FAIL | Referencia |
    |---|---|---|---|---|---|---|---|
    | TR-001 | Estrategia de pruebas aprobada | obligatorio | test_strategy.md | QA | Niveles y gates definidos | Sin estrategia | MIPS-DOC-009 |
| TR-002 | Requerimientos críticos tienen pruebas | obligatorio | traceability matrix | QA | Cada crítico mapeado a test | Crítico sin test | MIPS-DOC-009 |
| TR-003 | Bugs críticos tienen regresión | obligatorio si aplica | test_case.md | QA | Regression test creado | Bug crítico sin regresión | MIPS-DOC-009 |
| TR-004 | Evaluación MIASI si aplica | obligatorio si aplica | MIASI Eval Card | EvalAgent | Evals agentic PASS | IA sin evaluación | MIPS-DOC-014 |

    ## Criterios de bloqueo

    - Cualquier ítem obligatorio marcado como crítico sin evidencia suficiente.
    - Omisión de MIASI cuando el sistema usa IA, agentes, LLMs, RAG, memoria o tool calling.
    - Riesgo de seguridad, privacidad, datos o operación sin owner.

    ## Salida sugerida YAML

    ```yaml
    checklist: "checklist_testing_ready"
    result: "PASS|FAIL|BLOCK"
    mandatory_items_total: 0
    mandatory_items_passed: 0
    findings: []
    decision: "continue|fix|required_approval|block"
    ```
