---
title: Postmortem
doc_id: MIPS-TPL-POSTMORTEM
doc_type: template
version: 0.1.0
status: draft
owner: AI_agents / MIPSoftware
scope: software-engineering-model
created: '2026-05-31'
updated: '2026-06-01'
---

    ---
    title: "Postmortem"
    version: "0.1.0"
    status: "draft"
    model: "MIPSoftware"
    template_id: "postmortem"
    doc_type: "template"
    owner: "AI_agents / MIPSoftware"
    updated: "2026-05-31"
    required_fields:
  - "incident_id"
  - "impact"
  - "root_causes"
  - "contributing_factors"
  - "what_went_well"
  - "what_went_wrong"
  - "action_items"
    optional_fields:
  - "timeline"
  - "detection_gaps"
  - "prevention_plan"
    ---

    # Postmortem

    ## 1. Propósito

    Convertir un incidente en aprendizaje, acciones preventivas y cambios sistémicos.

    ## 2. Cuándo usarla

    Después de incidentes relevantes.

    ## 3. Campos obligatorios

    | Campo | Descripción | Criterio mínimo |
    |---|---|---|
    | `incident_id` | Debe documentarse de forma clara, verificable y trazable. | No puede quedar vacío ni ambiguo. |\n    | `impact` | Debe documentarse de forma clara, verificable y trazable. | No puede quedar vacío ni ambiguo. |\n    | `root_causes` | Debe documentarse de forma clara, verificable y trazable. | No puede quedar vacío ni ambiguo. |\n    | `contributing_factors` | Debe documentarse de forma clara, verificable y trazable. | No puede quedar vacío ni ambiguo. |\n    | `what_went_well` | Debe documentarse de forma clara, verificable y trazable. | No puede quedar vacío ni ambiguo. |\n    | `what_went_wrong` | Debe documentarse de forma clara, verificable y trazable. | No puede quedar vacío ni ambiguo. |\n    | `action_items` | Debe documentarse de forma clara, verificable y trazable. | No puede quedar vacío ni ambiguo. |\n

    ## 4. Campos opcionales

    | Campo | Uso recomendado |
    |---|---|
    | `timeline` | Usar cuando aporte contexto, riesgo, trazabilidad o decisión. |\n    | `detection_gaps` | Usar cuando aporte contexto, riesgo, trazabilidad o decisión. |\n    | `prevention_plan` | Usar cuando aporte contexto, riesgo, trazabilidad o decisión. |\n

    ## 5. Ejemplo completo

    ```json
    {
  "incident_id": "INC-001",
  "impact": "release delayed",
  "root_causes": [
    "schema too strict"
  ],
  "contributing_factors": [
    "missing test fixture"
  ],
  "what_went_well": [
    "rollback worked"
  ],
  "what_went_wrong": [
    "review missed edge case"
  ],
  "action_items": [
    "add regression test"
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
