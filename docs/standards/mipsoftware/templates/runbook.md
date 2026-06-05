---
title: Runbook
doc_id: MIPS-TPL-RUNBOOK
doc_type: template
version: 0.1.0
status: draft
owner: AI_agents / MIPSoftware
scope: software-engineering-model
created: '2026-05-31'
updated: '2026-06-01'
---

    ---
    title: "Runbook"
    version: "0.1.0"
    status: "draft"
    model: "MIPSoftware"
    template_id: "runbook"
    doc_type: "template"
    owner: "AI_agents / MIPSoftware"
    updated: "2026-05-31"
    required_fields:
  - "service"
  - "normal_operation"
  - "alerts"
  - "diagnostics"
  - "recovery_steps"
  - "contacts"
  - "known_issues"
    optional_fields:
  - "dashboards"
  - "slo"
  - "cost_controls"
  - "miasi_ops"
    ---

    # Runbook

    ## 1. Propósito

    Documentar operación normal, diagnóstico, alertas, incidentes y recuperación.

    ## 2. Cuándo usarla

    Antes de operación real.

    ## 3. Campos obligatorios

    | Campo | Descripción | Criterio mínimo |
    |---|---|---|
    | `service` | Debe documentarse de forma clara, verificable y trazable. | No puede quedar vacío ni ambiguo. |\n    | `normal_operation` | Debe documentarse de forma clara, verificable y trazable. | No puede quedar vacío ni ambiguo. |\n    | `alerts` | Debe documentarse de forma clara, verificable y trazable. | No puede quedar vacío ni ambiguo. |\n    | `diagnostics` | Debe documentarse de forma clara, verificable y trazable. | No puede quedar vacío ni ambiguo. |\n    | `recovery_steps` | Debe documentarse de forma clara, verificable y trazable. | No puede quedar vacío ni ambiguo. |\n    | `contacts` | Debe documentarse de forma clara, verificable y trazable. | No puede quedar vacío ni ambiguo. |\n    | `known_issues` | Debe documentarse de forma clara, verificable y trazable. | No puede quedar vacío ni ambiguo. |\n

    ## 4. Campos opcionales

    | Campo | Uso recomendado |
    |---|---|
    | `dashboards` | Usar cuando aporte contexto, riesgo, trazabilidad o decisión. |\n    | `slo` | Usar cuando aporte contexto, riesgo, trazabilidad o decisión. |\n    | `cost_controls` | Usar cuando aporte contexto, riesgo, trazabilidad o decisión. |\n    | `miasi_ops` | Usar cuando aporte contexto, riesgo, trazabilidad o decisión. |\n

    ## 5. Ejemplo completo

    ```json
    {
  "service": "DevPilot Local",
  "normal_operation": "CLI local",
  "alerts": "n/a initial local",
  "diagnostics": [
    "check logs",
    "run validation"
  ],
  "recovery_steps": [
    "restore backup"
  ],
  "contacts": [
    "owner"
  ],
  "known_issues": [
    "schemas draft"
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
