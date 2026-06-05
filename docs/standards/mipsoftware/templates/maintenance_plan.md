---
title: Maintenance Plan
doc_id: MIPS-TPL-MAINTENANCE_PLAN
doc_type: template
version: 0.1.0
status: draft
owner: AI_agents / MIPSoftware
scope: software-engineering-model
created: '2026-05-31'
updated: '2026-06-01'
---

    ---
    title: "Maintenance Plan"
    version: "0.1.0"
    status: "draft"
    model: "MIPSoftware"
    template_id: "maintenance_plan"
    doc_type: "template"
    owner: "AI_agents / MIPSoftware"
    updated: "2026-05-31"
    required_fields:
  - "system"
  - "maintenance_types"
  - "cadence"
  - "responsibilities"
  - "risk_controls"
  - "backlog_policy"
    optional_fields:
  - "support_window"
  - "dependency_update_policy"
  - "miasi_model_update_policy"
    ---

    # Maintenance Plan

    ## 1. Propósito

    Definir mantenimiento correctivo, preventivo, evolutivo y adaptativo.

    ## 2. Cuándo usarla

    Después del primer release y durante operación continua.

    ## 3. Campos obligatorios

    | Campo | Descripción | Criterio mínimo |
    |---|---|---|
    | `system` | Debe documentarse de forma clara, verificable y trazable. | No puede quedar vacío ni ambiguo. |\n    | `maintenance_types` | Debe documentarse de forma clara, verificable y trazable. | No puede quedar vacío ni ambiguo. |\n    | `cadence` | Debe documentarse de forma clara, verificable y trazable. | No puede quedar vacío ni ambiguo. |\n    | `responsibilities` | Debe documentarse de forma clara, verificable y trazable. | No puede quedar vacío ni ambiguo. |\n    | `risk_controls` | Debe documentarse de forma clara, verificable y trazable. | No puede quedar vacío ni ambiguo. |\n    | `backlog_policy` | Debe documentarse de forma clara, verificable y trazable. | No puede quedar vacío ni ambiguo. |\n

    ## 4. Campos opcionales

    | Campo | Uso recomendado |
    |---|---|
    | `support_window` | Usar cuando aporte contexto, riesgo, trazabilidad o decisión. |\n    | `dependency_update_policy` | Usar cuando aporte contexto, riesgo, trazabilidad o decisión. |\n    | `miasi_model_update_policy` | Usar cuando aporte contexto, riesgo, trazabilidad o decisión. |\n

    ## 5. Ejemplo completo

    ```json
    {
  "system": "DevPilot Local",
  "maintenance_types": [
    "corrective",
    "evolutionary",
    "preventive"
  ],
  "cadence": "weekly review",
  "responsibilities": [
    "owner"
  ],
  "risk_controls": [
    "tests before release"
  ],
  "backlog_policy": "prioritize critical defects"
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
