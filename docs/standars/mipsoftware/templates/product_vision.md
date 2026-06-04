---
title: Product Vision
doc_id: MIPS-TPL-PRODUCT_VISION
doc_type: template
version: 0.1.0
status: draft
owner: AI_agents / MIPSoftware
scope: software-engineering-model
created: '2026-05-31'
updated: '2026-06-01'
---

    ---
    title: "Product Vision"
    version: "0.1.0"
    status: "draft"
    model: "MIPSoftware"
    template_id: "product_vision"
    doc_type: "template"
    owner: "AI_agents / MIPSoftware"
    updated: "2026-05-31"
    required_fields:
  - "product_name"
  - "problem_statement"
  - "target_users"
  - "value_proposition"
  - "success_metrics"
  - "scope_summary"
  - "miasi_applicability"
    optional_fields:
  - "competitors"
  - "constraints"
  - "assumptions"
  - "open_questions"
    ---

    # Product Vision

    ## 1. Propósito

    Formalizar la visión del producto, problema, usuarios, propuesta de valor y métricas iniciales.

    ## 2. Cuándo usarla

    Durante intake, descubrimiento de problema y antes de formular requerimientos.

    ## 3. Campos obligatorios

    | Campo | Descripción | Criterio mínimo |
    |---|---|---|
    | `product_name` | Debe documentarse de forma clara, verificable y trazable. | No puede quedar vacío ni ambiguo. |\n    | `problem_statement` | Debe documentarse de forma clara, verificable y trazable. | No puede quedar vacío ni ambiguo. |\n    | `target_users` | Debe documentarse de forma clara, verificable y trazable. | No puede quedar vacío ni ambiguo. |\n    | `value_proposition` | Debe documentarse de forma clara, verificable y trazable. | No puede quedar vacío ni ambiguo. |\n    | `success_metrics` | Debe documentarse de forma clara, verificable y trazable. | No puede quedar vacío ni ambiguo. |\n    | `scope_summary` | Debe documentarse de forma clara, verificable y trazable. | No puede quedar vacío ni ambiguo. |\n    | `miasi_applicability` | Debe documentarse de forma clara, verificable y trazable. | No puede quedar vacío ni ambiguo. |\n

    ## 4. Campos opcionales

    | Campo | Uso recomendado |
    |---|---|
    | `competitors` | Usar cuando aporte contexto, riesgo, trazabilidad o decisión. |\n    | `constraints` | Usar cuando aporte contexto, riesgo, trazabilidad o decisión. |\n    | `assumptions` | Usar cuando aporte contexto, riesgo, trazabilidad o decisión. |\n    | `open_questions` | Usar cuando aporte contexto, riesgo, trazabilidad o decisión. |\n

    ## 5. Ejemplo completo

    ```json
    {
  "product_name": "DevPilot Local",
  "problem_statement": "Los proyectos de software propios carecen de trazabilidad consistente desde requerimientos hasta release.",
  "target_users": [
    "desarrollador principal",
    "arquitecto",
    "revisor técnico"
  ],
  "value_proposition": "Reducir improvisación y aumentar calidad mediante guías, gates y automatización local-first.",
  "success_metrics": [
    "80% de proyectos con checklist pre-code completo",
    "100% de releases con rollback documentado"
  ],
  "scope_summary": "MVP CLI local para validar artefactos MIPSoftware.",
  "miasi_applicability": "Sí, usa agentes y evaluación MIASI."
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
