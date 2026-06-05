---
title: Security Threat Model
doc_id: MIPS-TPL-SECURITY_THREAT_MODEL
doc_type: template
version: 0.1.0
status: draft
owner: AI_agents / MIPSoftware
scope: software-engineering-model
created: '2026-05-31'
updated: '2026-06-01'
---

    ---
    title: "Security Threat Model"
    version: "0.1.0"
    status: "draft"
    model: "MIPSoftware"
    template_id: "security_threat_model"
    doc_type: "template"
    owner: "AI_agents / MIPSoftware"
    updated: "2026-05-31"
    required_fields:
  - "assets"
  - "trust_boundaries"
  - "threats"
  - "controls"
  - "risk_rating"
  - "residual_risk"
  - "owner"
    optional_fields:
  - "attack_trees"
  - "abuse_cases"
  - "miasi_risks"
    ---

    # Security Threat Model

    ## 1. Propósito

    Identificar activos, amenazas, controles, riesgos residuales y decisiones de seguridad.

    ## 2. Cuándo usarla

    Antes de release y cuando existan datos sensibles o exposición externa.

    ## 3. Campos obligatorios

    | Campo | Descripción | Criterio mínimo |
    |---|---|---|
    | `assets` | Debe documentarse de forma clara, verificable y trazable. | No puede quedar vacío ni ambiguo. |\n    | `trust_boundaries` | Debe documentarse de forma clara, verificable y trazable. | No puede quedar vacío ni ambiguo. |\n    | `threats` | Debe documentarse de forma clara, verificable y trazable. | No puede quedar vacío ni ambiguo. |\n    | `controls` | Debe documentarse de forma clara, verificable y trazable. | No puede quedar vacío ni ambiguo. |\n    | `risk_rating` | Debe documentarse de forma clara, verificable y trazable. | No puede quedar vacío ni ambiguo. |\n    | `residual_risk` | Debe documentarse de forma clara, verificable y trazable. | No puede quedar vacío ni ambiguo. |\n    | `owner` | Debe documentarse de forma clara, verificable y trazable. | No puede quedar vacío ni ambiguo. |\n

    ## 4. Campos opcionales

    | Campo | Uso recomendado |
    |---|---|
    | `attack_trees` | Usar cuando aporte contexto, riesgo, trazabilidad o decisión. |\n    | `abuse_cases` | Usar cuando aporte contexto, riesgo, trazabilidad o decisión. |\n    | `miasi_risks` | Usar cuando aporte contexto, riesgo, trazabilidad o decisión. |\n

    ## 5. Ejemplo completo

    ```json
    {
  "assets": [
    "project docs",
    "tokens"
  ],
  "trust_boundaries": [
    "local filesystem",
    "CI"
  ],
  "threats": [
    "secret leakage"
  ],
  "controls": [
    "secret scan",
    "redaction"
  ],
  "risk_rating": "medium",
  "residual_risk": "accepted with control",
  "owner": "SecurityAgent"
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
