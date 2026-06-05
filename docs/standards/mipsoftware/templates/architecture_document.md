---
title: Architecture Document
doc_id: MIPS-TPL-ARCHITECTURE_DOCUMENT
doc_type: template
version: 0.1.0
status: draft
owner: AI_agents / MIPSoftware
scope: software-engineering-model
created: '2026-05-31'
updated: '2026-06-01'
---

    ---
    title: "Architecture Document"
    version: "0.1.0"
    status: "draft"
    model: "MIPSoftware"
    template_id: "architecture_document"
    doc_type: "template"
    owner: "AI_agents / MIPSoftware"
    updated: "2026-05-31"
    required_fields:
  - "context"
  - "drivers"
  - "quality_attributes"
  - "constraints"
  - "c4_views"
  - "decisions"
  - "risks"
    optional_fields:
  - "deployment_view"
  - "data_view"
  - "observability_view"
  - "miasi_view"
    ---

    # Architecture Document

    ## 1. Propósito

    Documentar contexto, decisiones, drivers, vistas, riesgos y atributos de calidad.

    ## 2. Cuándo usarla

    Antes de implementación significativa y en cambios estructurales.

    ## 3. Campos obligatorios

    | Campo | Descripción | Criterio mínimo |
    |---|---|---|
    | `context` | Debe documentarse de forma clara, verificable y trazable. | No puede quedar vacío ni ambiguo. |\n    | `drivers` | Debe documentarse de forma clara, verificable y trazable. | No puede quedar vacío ni ambiguo. |\n    | `quality_attributes` | Debe documentarse de forma clara, verificable y trazable. | No puede quedar vacío ni ambiguo. |\n    | `constraints` | Debe documentarse de forma clara, verificable y trazable. | No puede quedar vacío ni ambiguo. |\n    | `c4_views` | Debe documentarse de forma clara, verificable y trazable. | No puede quedar vacío ni ambiguo. |\n    | `decisions` | Debe documentarse de forma clara, verificable y trazable. | No puede quedar vacío ni ambiguo. |\n    | `risks` | Debe documentarse de forma clara, verificable y trazable. | No puede quedar vacío ni ambiguo. |\n

    ## 4. Campos opcionales

    | Campo | Uso recomendado |
    |---|---|
    | `deployment_view` | Usar cuando aporte contexto, riesgo, trazabilidad o decisión. |\n    | `data_view` | Usar cuando aporte contexto, riesgo, trazabilidad o decisión. |\n    | `observability_view` | Usar cuando aporte contexto, riesgo, trazabilidad o decisión. |\n    | `miasi_view` | Usar cuando aporte contexto, riesgo, trazabilidad o decisión. |\n

    ## 5. Ejemplo completo

    ```json
    {
  "context": "CLI local para validación documental",
  "drivers": [
    "local-first",
    "sin cloud obligatorio"
  ],
  "quality_attributes": [
    "maintainability",
    "security",
    "testability"
  ],
  "constraints": [
    "Python 3.12"
  ],
  "c4_views": [
    "context",
    "container"
  ],
  "decisions": [
    "ADR-0001"
  ],
  "risks": [
    "scope creep"
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
