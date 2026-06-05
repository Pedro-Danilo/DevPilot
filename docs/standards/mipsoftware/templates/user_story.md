---
title: User Story
doc_id: MIPS-TPL-USER_STORY
doc_type: template
version: 0.1.0
status: draft
owner: AI_agents / MIPSoftware
scope: software-engineering-model
created: '2026-05-31'
updated: '2026-06-01'
---

    ---
    title: "User Story"
    version: "0.1.0"
    status: "draft"
    model: "MIPSoftware"
    template_id: "user_story"
    doc_type: "template"
    owner: "AI_agents / MIPSoftware"
    updated: "2026-05-31"
    required_fields:
  - "story_id"
  - "role"
  - "goal"
  - "benefit"
  - "acceptance_criteria"
  - "priority"
  - "definition_of_done"
    optional_fields:
  - "dependencies"
  - "ux_notes"
  - "test_notes"
  - "miasi_notes"
    ---

    # User Story

    ## 1. Propósito

    Traducir necesidades de usuario en backlog implementable con aceptación verificable.

    ## 2. Cuándo usarla

    Durante refinamiento de backlog.

    ## 3. Campos obligatorios

    | Campo | Descripción | Criterio mínimo |
    |---|---|---|
    | `story_id` | Debe documentarse de forma clara, verificable y trazable. | No puede quedar vacío ni ambiguo. |\n    | `role` | Debe documentarse de forma clara, verificable y trazable. | No puede quedar vacío ni ambiguo. |\n    | `goal` | Debe documentarse de forma clara, verificable y trazable. | No puede quedar vacío ni ambiguo. |\n    | `benefit` | Debe documentarse de forma clara, verificable y trazable. | No puede quedar vacío ni ambiguo. |\n    | `acceptance_criteria` | Debe documentarse de forma clara, verificable y trazable. | No puede quedar vacío ni ambiguo. |\n    | `priority` | Debe documentarse de forma clara, verificable y trazable. | No puede quedar vacío ni ambiguo. |\n    | `definition_of_done` | Debe documentarse de forma clara, verificable y trazable. | No puede quedar vacío ni ambiguo. |\n

    ## 4. Campos opcionales

    | Campo | Uso recomendado |
    |---|---|
    | `dependencies` | Usar cuando aporte contexto, riesgo, trazabilidad o decisión. |\n    | `ux_notes` | Usar cuando aporte contexto, riesgo, trazabilidad o decisión. |\n    | `test_notes` | Usar cuando aporte contexto, riesgo, trazabilidad o decisión. |\n    | `miasi_notes` | Usar cuando aporte contexto, riesgo, trazabilidad o decisión. |\n

    ## 5. Ejemplo completo

    ```json
    {
  "story_id": "US-001",
  "role": "arquitecto",
  "goal": "validar un ADR",
  "benefit": "asegurar trazabilidad de decisiones",
  "acceptance_criteria": [
    "El ADR contiene contexto, decisión y consecuencias."
  ],
  "priority": "medium",
  "definition_of_done": [
    "tests pass",
    "documentación actualizada"
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
