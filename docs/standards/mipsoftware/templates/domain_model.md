---
title: Domain Model
doc_id: MIPS-TPL-DOMAIN_MODEL
doc_type: template
version: 0.1.0
status: draft
owner: AI_agents / MIPSoftware
scope: software-engineering-model
created: '2026-05-31'
updated: '2026-06-01'
---

    ---
    title: "Domain Model"
    version: "0.1.0"
    status: "draft"
    model: "MIPSoftware"
    template_id: "domain_model"
    doc_type: "template"
    owner: "AI_agents / MIPSoftware"
    updated: "2026-05-31"
    required_fields:
  - "bounded_context"
  - "entities"
  - "aggregates"
  - "business_rules"
  - "invariants"
  - "use_cases"
    optional_fields:
  - "domain_events"
  - "ubiquitous_language"
  - "external_dependencies"
    ---

    # Domain Model

    ## 1. Propósito

    Documentar entidades, agregados, casos de uso, reglas e invariantes del dominio.

    ## 2. Cuándo usarla

    Antes de implementar módulos transaccionales.

    ## 3. Campos obligatorios

    | Campo | Descripción | Criterio mínimo |
    |---|---|---|
    | `bounded_context` | Debe documentarse de forma clara, verificable y trazable. | No puede quedar vacío ni ambiguo. |\n    | `entities` | Debe documentarse de forma clara, verificable y trazable. | No puede quedar vacío ni ambiguo. |\n    | `aggregates` | Debe documentarse de forma clara, verificable y trazable. | No puede quedar vacío ni ambiguo. |\n    | `business_rules` | Debe documentarse de forma clara, verificable y trazable. | No puede quedar vacío ni ambiguo. |\n    | `invariants` | Debe documentarse de forma clara, verificable y trazable. | No puede quedar vacío ni ambiguo. |\n    | `use_cases` | Debe documentarse de forma clara, verificable y trazable. | No puede quedar vacío ni ambiguo. |\n

    ## 4. Campos opcionales

    | Campo | Uso recomendado |
    |---|---|
    | `domain_events` | Usar cuando aporte contexto, riesgo, trazabilidad o decisión. |\n    | `ubiquitous_language` | Usar cuando aporte contexto, riesgo, trazabilidad o decisión. |\n    | `external_dependencies` | Usar cuando aporte contexto, riesgo, trazabilidad o decisión. |\n

    ## 5. Ejemplo completo

    ```json
    {
  "bounded_context": "Project Governance",
  "entities": [
    "Project",
    "Artifact",
    "Gate"
  ],
  "aggregates": [
    "Project"
  ],
  "business_rules": [
    "Un gate bloqueado impide release."
  ],
  "invariants": [
    "Todo artefacto tiene owner."
  ],
  "use_cases": [
    "Validate readiness"
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
