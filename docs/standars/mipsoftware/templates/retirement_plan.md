---
title: Retirement Plan
doc_id: MIPS-TPL-RETIREMENT_PLAN
doc_type: template
version: 0.1.0
status: draft
owner: AI_agents / MIPSoftware
scope: software-engineering-model
created: '2026-05-31'
updated: '2026-06-01'
---

    ---
    title: "Retirement Plan"
    version: "0.1.0"
    status: "draft"
    model: "MIPSoftware"
    template_id: "retirement_plan"
    doc_type: "template"
    owner: "AI_agents / MIPSoftware"
    updated: "2026-05-31"
    required_fields:
  - "system"
  - "reason"
  - "affected_users"
  - "data_handling"
  - "communication_plan"
  - "archive_plan"
  - "shutdown_steps"
    optional_fields:
  - "migration_options"
  - "legal_retention"
  - "post_shutdown_support"
    ---

    # Retirement Plan

    ## 1. Propósito

    Planificar retiro seguro protegiendo usuarios, datos, cumplimiento y continuidad.

    ## 2. Cuándo usarla

    Antes de descontinuar sistema o módulo.

    ## 3. Campos obligatorios

    | Campo | Descripción | Criterio mínimo |
    |---|---|---|
    | `system` | Debe documentarse de forma clara, verificable y trazable. | No puede quedar vacío ni ambiguo. |\n    | `reason` | Debe documentarse de forma clara, verificable y trazable. | No puede quedar vacío ni ambiguo. |\n    | `affected_users` | Debe documentarse de forma clara, verificable y trazable. | No puede quedar vacío ni ambiguo. |\n    | `data_handling` | Debe documentarse de forma clara, verificable y trazable. | No puede quedar vacío ni ambiguo. |\n    | `communication_plan` | Debe documentarse de forma clara, verificable y trazable. | No puede quedar vacío ni ambiguo. |\n    | `archive_plan` | Debe documentarse de forma clara, verificable y trazable. | No puede quedar vacío ni ambiguo. |\n    | `shutdown_steps` | Debe documentarse de forma clara, verificable y trazable. | No puede quedar vacío ni ambiguo. |\n

    ## 4. Campos opcionales

    | Campo | Uso recomendado |
    |---|---|
    | `migration_options` | Usar cuando aporte contexto, riesgo, trazabilidad o decisión. |\n    | `legal_retention` | Usar cuando aporte contexto, riesgo, trazabilidad o decisión. |\n    | `post_shutdown_support` | Usar cuando aporte contexto, riesgo, trazabilidad o decisión. |\n

    ## 5. Ejemplo completo

    ```json
    {
  "system": "Old Validator",
  "reason": "replaced by DevPilot",
  "affected_users": [
    "internal owner"
  ],
  "data_handling": "archive configs",
  "communication_plan": "notify in changelog",
  "archive_plan": "tag final release",
  "shutdown_steps": [
    "disable command",
    "remove docs after deprecation window"
  ]
}
    ```

    ## 6. Criterios de revisión

    - El artefacto tiene owner y fecha de actualización.
    - Todos los campos obligatorios están completos.
    - Las afirmaciones relevantes son verificables.
    - Existe trazabilidad con requerimientos, riesgos, pruebas o gates cuando aplique.
    - Las decisiones críticas incluyen justificación y consecuencias.
    - Si el sistema usa IA, agentes, LLMs, RAG, memoria, tool calling o automatización inteligente, se activa MIASI.

    ## 7. Criterios de rechazo

    - Campos obligatorios vacíos o genéricos.
    - Falta de criterio verificable.
    - Riesgos críticos sin responsable.
    - Evidencia insuficiente para pasar el quality gate relacionado.
    - Omisión de MIASI cuando el artefacto describe capacidad inteligente/agéntica.

    ## 8. Relación con ciclo de vida

    Esta plantilla se integra con MIPS-DOC-003 — Ciclo de vida profesional de software. Debe usarse como evidencia para pasar gates de producto, requerimientos, arquitectura, calidad, seguridad, release u operación según corresponda.

    ## 9. Relación con quality gates

    Resultado esperado:

    | Estado | Significado |
    |---|---|
    | PASS | El artefacto es completo, verificable y trazable. |
    | FAIL | El artefacto requiere corrección. |
    | BLOCK | El artefacto omite información crítica para avanzar. |
