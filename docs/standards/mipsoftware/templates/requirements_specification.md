---
title: Requirements Specification
doc_id: MIPS-TPL-REQUIREMENTS_SPECIFICATION
doc_type: template
version: 0.1.0
status: draft
owner: AI_agents / MIPSoftware
scope: software-engineering-model
created: '2026-05-31'
updated: '2026-06-01'
---

    ---
    title: "Requirements Specification"
    version: "0.1.0"
    status: "draft"
    model: "MIPSoftware"
    template_id: "requirements_specification"
    doc_type: "template"
    owner: "AI_agents / MIPSoftware"
    updated: "2026-05-31"
    required_fields:
  - "requirement_id"
  - "type"
  - "statement"
  - "rationale"
  - "acceptance_criteria"
  - "priority"
  - "verification_method"
  - "trace_to_business_need"
    optional_fields:
  - "dependencies"
  - "assumptions"
  - "risk"
  - "miasi_impact"
    ---

    # Requirements Specification

    ## 1. Propósito

    Especificar requerimientos funcionales, no funcionales, restricciones, datos, interfaces, seguridad y operación.

    ## 2. Cuándo usarla

    Después de visión/negocio y antes de backlog implementable.

    ## 3. Campos obligatorios

    | Campo | Descripción | Criterio mínimo |
    |---|---|---|
    | `requirement_id` | Debe documentarse de forma clara, verificable y trazable. | No puede quedar vacío ni ambiguo. |\n    | `type` | Debe documentarse de forma clara, verificable y trazable. | No puede quedar vacío ni ambiguo. |\n    | `statement` | Debe documentarse de forma clara, verificable y trazable. | No puede quedar vacío ni ambiguo. |\n    | `rationale` | Debe documentarse de forma clara, verificable y trazable. | No puede quedar vacío ni ambiguo. |\n    | `acceptance_criteria` | Debe documentarse de forma clara, verificable y trazable. | No puede quedar vacío ni ambiguo. |\n    | `priority` | Debe documentarse de forma clara, verificable y trazable. | No puede quedar vacío ni ambiguo. |\n    | `verification_method` | Debe documentarse de forma clara, verificable y trazable. | No puede quedar vacío ni ambiguo. |\n    | `trace_to_business_need` | Debe documentarse de forma clara, verificable y trazable. | No puede quedar vacío ni ambiguo. |\n

    ## 4. Campos opcionales

    | Campo | Uso recomendado |
    |---|---|
    | `dependencies` | Usar cuando aporte contexto, riesgo, trazabilidad o decisión. |\n    | `assumptions` | Usar cuando aporte contexto, riesgo, trazabilidad o decisión. |\n    | `risk` | Usar cuando aporte contexto, riesgo, trazabilidad o decisión. |\n    | `miasi_impact` | Usar cuando aporte contexto, riesgo, trazabilidad o decisión. |\n

    ## 5. Ejemplo completo

    ```json
    {
  "requirement_id": "REQ-001",
  "type": "functional",
  "statement": "El sistema debe validar una Product Vision contra schema JSON.",
  "acceptance_criteria": [
    "Dado un documento válido, cuando se valida, entonces retorna PASS."
  ],
  "priority": "high",
  "verification_method": "automated test",
  "trace_to_business_need": "MIP-BN-001"
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
