---
title: Business Case
doc_id: MIPS-TPL-BUSINESS_CASE
doc_type: template
version: 0.1.0
status: draft
owner: AI_agents / MIPSoftware
scope: software-engineering-model
created: '2026-05-31'
updated: '2026-06-01'
---

    ---
    title: "Business Case"
    version: "0.1.0"
    status: "draft"
    model: "MIPSoftware"
    template_id: "business_case"
    doc_type: "template"
    owner: "AI_agents / MIPSoftware"
    updated: "2026-05-31"
    required_fields:
  - "initiative"
  - "business_goal"
  - "expected_benefits"
  - "estimated_costs"
  - "risks"
  - "decision"
  - "review_date"
    optional_fields:
  - "alternatives"
  - "market_context"
  - "financial_assumptions"
  - "dependencies"
    ---

    # Business Case

    ## 1. Propósito

    Justificar inversión, alcance, costos, beneficios, riesgos y decisión de continuidad.

    ## 2. Cuándo usarla

    Antes de comprometer desarrollo significativo o inversión.

    ## 3. Campos obligatorios

    | Campo | Descripción | Criterio mínimo |
    |---|---|---|
    | `initiative` | Debe documentarse de forma clara, verificable y trazable. | No puede quedar vacío ni ambiguo. |\n    | `business_goal` | Debe documentarse de forma clara, verificable y trazable. | No puede quedar vacío ni ambiguo. |\n    | `expected_benefits` | Debe documentarse de forma clara, verificable y trazable. | No puede quedar vacío ni ambiguo. |\n    | `estimated_costs` | Debe documentarse de forma clara, verificable y trazable. | No puede quedar vacío ni ambiguo. |\n    | `risks` | Debe documentarse de forma clara, verificable y trazable. | No puede quedar vacío ni ambiguo. |\n    | `decision` | Debe documentarse de forma clara, verificable y trazable. | No puede quedar vacío ni ambiguo. |\n    | `review_date` | Debe documentarse de forma clara, verificable y trazable. | No puede quedar vacío ni ambiguo. |\n

    ## 4. Campos opcionales

    | Campo | Uso recomendado |
    |---|---|
    | `alternatives` | Usar cuando aporte contexto, riesgo, trazabilidad o decisión. |\n    | `market_context` | Usar cuando aporte contexto, riesgo, trazabilidad o decisión. |\n    | `financial_assumptions` | Usar cuando aporte contexto, riesgo, trazabilidad o decisión. |\n    | `dependencies` | Usar cuando aporte contexto, riesgo, trazabilidad o decisión. |\n

    ## 5. Ejemplo completo

    ```json
    {
  "initiative": "DevPilot Local MVP",
  "business_goal": "Estandarizar desarrollo interno",
  "expected_benefits": [
    "menos retrabajo",
    "mejor trazabilidad"
  ],
  "estimated_costs": [
    "2 sprints",
    "sin servicios pagos por defecto"
  ],
  "risks": [
    "sobreingeniería",
    "documentación no adoptada"
  ],
  "decision": "Proceed with controlled MVP",
  "review_date": "2026-06-15"
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
