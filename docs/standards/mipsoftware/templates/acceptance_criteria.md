---
title: Acceptance Criteria
doc_id: MIPS-TPL-ACCEPTANCE_CRITERIA
doc_type: template
version: 0.1.0
status: draft
owner: AI_agents / MIPSoftware
scope: software-engineering-model
created: '2026-05-31'
updated: '2026-06-01'
---

    ---
    title: "Acceptance Criteria"
    version: "0.1.0"
    status: "draft"
    model: "MIPSoftware"
    template_id: "acceptance_criteria"
    doc_type: "template"
    owner: "AI_agents / MIPSoftware"
    updated: "2026-05-31"
    required_fields:
  - "target_id"
  - "criteria"
  - "test_method"
  - "owner"
  - "pass_condition"
    optional_fields:
  - "negative_cases"
  - "edge_cases"
  - "automation_status"
    ---

    # Acceptance Criteria

    ## 1. Propósito

    Definir condiciones verificables para aceptar requerimientos, historias o entregables.

    ## 2. Cuándo usarla

    Antes de implementar o cerrar una historia/requerimiento.

    ## 3. Campos obligatorios

    | Campo | Descripción | Criterio mínimo |
    |---|---|---|
    | `target_id` | Debe documentarse de forma clara, verificable y trazable. | No puede quedar vacío ni ambiguo. |\n    | `criteria` | Debe documentarse de forma clara, verificable y trazable. | No puede quedar vacío ni ambiguo. |\n    | `test_method` | Debe documentarse de forma clara, verificable y trazable. | No puede quedar vacío ni ambiguo. |\n    | `owner` | Debe documentarse de forma clara, verificable y trazable. | No puede quedar vacío ni ambiguo. |\n    | `pass_condition` | Debe documentarse de forma clara, verificable y trazable. | No puede quedar vacío ni ambiguo. |\n

    ## 4. Campos opcionales

    | Campo | Uso recomendado |
    |---|---|
    | `negative_cases` | Usar cuando aporte contexto, riesgo, trazabilidad o decisión. |\n    | `edge_cases` | Usar cuando aporte contexto, riesgo, trazabilidad o decisión. |\n    | `automation_status` | Usar cuando aporte contexto, riesgo, trazabilidad o decisión. |\n

    ## 5. Ejemplo completo

    ```json
    {
  "target_id": "US-001",
  "criteria": [
    "Debe crear README.md",
    "Debe crear carpeta templates/"
  ],
  "test_method": "pytest + file existence",
  "owner": "QA/Developer",
  "pass_condition": "Todos los criterios cumplen."
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
