---
title: Use Case
doc_id: MIPS-TPL-USE_CASE
doc_type: template
version: 0.1.0
status: draft
owner: AI_agents / MIPSoftware
scope: software-engineering-model
created: '2026-05-31'
updated: '2026-06-01'
---

    ---
    title: "Use Case"
    version: "0.1.0"
    status: "draft"
    model: "MIPSoftware"
    template_id: "use_case"
    doc_type: "template"
    owner: "AI_agents / MIPSoftware"
    updated: "2026-05-31"
    required_fields:
  - "use_case_id"
  - "primary_actor"
  - "goal"
  - "preconditions"
  - "main_flow"
  - "alternative_flows"
  - "postconditions"
    optional_fields:
  - "exceptions"
  - "business_rules"
  - "security_notes"
    ---

    # Use Case

    ## 1. Propósito

    Describir interacción actor-sistema, precondiciones, flujo principal, alternos y postcondiciones.

    ## 2. Cuándo usarla

    Para funcionalidades con interacción compleja o reglas de negocio relevantes.

    ## 3. Campos obligatorios

    | Campo | Descripción | Criterio mínimo |
    |---|---|---|
    | `use_case_id` | Debe documentarse de forma clara, verificable y trazable. | No puede quedar vacío ni ambiguo. |\n    | `primary_actor` | Debe documentarse de forma clara, verificable y trazable. | No puede quedar vacío ni ambiguo. |\n    | `goal` | Debe documentarse de forma clara, verificable y trazable. | No puede quedar vacío ni ambiguo. |\n    | `preconditions` | Debe documentarse de forma clara, verificable y trazable. | No puede quedar vacío ni ambiguo. |\n    | `main_flow` | Debe documentarse de forma clara, verificable y trazable. | No puede quedar vacío ni ambiguo. |\n    | `alternative_flows` | Debe documentarse de forma clara, verificable y trazable. | No puede quedar vacío ni ambiguo. |\n    | `postconditions` | Debe documentarse de forma clara, verificable y trazable. | No puede quedar vacío ni ambiguo. |\n

    ## 4. Campos opcionales

    | Campo | Uso recomendado |
    |---|---|
    | `exceptions` | Usar cuando aporte contexto, riesgo, trazabilidad o decisión. |\n    | `business_rules` | Usar cuando aporte contexto, riesgo, trazabilidad o decisión. |\n    | `security_notes` | Usar cuando aporte contexto, riesgo, trazabilidad o decisión. |\n

    ## 5. Ejemplo completo

    ```json
    {
  "use_case_id": "UC-001",
  "primary_actor": "Developer",
  "goal": "Crear nuevo proyecto MIPSoftware",
  "preconditions": [
    "CLI instalada"
  ],
  "main_flow": [
    "Ejecuta init",
    "Selecciona plantilla",
    "Genera estructura"
  ],
  "alternative_flows": [
    "Proyecto ya existe: solicita confirmación"
  ],
  "postconditions": [
    "Estructura docs creada"
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
