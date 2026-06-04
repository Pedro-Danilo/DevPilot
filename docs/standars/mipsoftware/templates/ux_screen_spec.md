---
title: Ux Screen Spec
doc_id: MIPS-TPL-UX_SCREEN_SPEC
doc_type: template
version: 0.1.0
status: draft
owner: AI_agents / MIPSoftware
scope: software-engineering-model
created: '2026-05-31'
updated: '2026-06-01'
---

    ---
    title: "UX Screen Specification"
    version: "0.1.0"
    status: "draft"
    model: "MIPSoftware"
    template_id: "ux_screen_spec"
    doc_type: "template"
    owner: "AI_agents / MIPSoftware"
    updated: "2026-05-31"
    required_fields:
  - "screen_id"
  - "user_goal"
  - "layout"
  - "states"
  - "components"
  - "validation"
  - "accessibility"
    optional_fields:
  - "wireframe"
  - "analytics_events"
  - "responsive_behavior"
    ---

    # UX Screen Specification

    ## 1. Propósito

    Especificar pantalla, objetivo, estados, componentes, microcopy y accesibilidad.

    ## 2. Cuándo usarla

    Antes de implementar interfaces visibles.

    ## 3. Campos obligatorios

    | Campo | Descripción | Criterio mínimo |
    |---|---|---|
    | `screen_id` | Debe documentarse de forma clara, verificable y trazable. | No puede quedar vacío ni ambiguo. |\n    | `user_goal` | Debe documentarse de forma clara, verificable y trazable. | No puede quedar vacío ni ambiguo. |\n    | `layout` | Debe documentarse de forma clara, verificable y trazable. | No puede quedar vacío ni ambiguo. |\n    | `states` | Debe documentarse de forma clara, verificable y trazable. | No puede quedar vacío ni ambiguo. |\n    | `components` | Debe documentarse de forma clara, verificable y trazable. | No puede quedar vacío ni ambiguo. |\n    | `validation` | Debe documentarse de forma clara, verificable y trazable. | No puede quedar vacío ni ambiguo. |\n    | `accessibility` | Debe documentarse de forma clara, verificable y trazable. | No puede quedar vacío ni ambiguo. |\n

    ## 4. Campos opcionales

    | Campo | Uso recomendado |
    |---|---|
    | `wireframe` | Usar cuando aporte contexto, riesgo, trazabilidad o decisión. |\n    | `analytics_events` | Usar cuando aporte contexto, riesgo, trazabilidad o decisión. |\n    | `responsive_behavior` | Usar cuando aporte contexto, riesgo, trazabilidad o decisión. |\n

    ## 5. Ejemplo completo

    ```json
    {
  "screen_id": "SCR-001",
  "user_goal": "Ver readiness del proyecto",
  "layout": "Header + status cards + findings table",
  "states": [
    "loading",
    "empty",
    "pass",
    "fail"
  ],
  "components": [
    "GateCard",
    "FindingsTable"
  ],
  "validation": "n/a",
  "accessibility": [
    "keyboard navigation",
    "contrast AA"
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
