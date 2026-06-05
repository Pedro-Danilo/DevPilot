---
title: Api Contract
doc_id: MIPS-TPL-API_CONTRACT
doc_type: template
version: 0.1.0
status: draft
owner: AI_agents / MIPSoftware
scope: software-engineering-model
created: '2026-05-31'
updated: '2026-06-01'
---

    ---
    title: "API Contract"
    version: "0.1.0"
    status: "draft"
    model: "MIPSoftware"
    template_id: "api_contract"
    doc_type: "template"
    owner: "AI_agents / MIPSoftware"
    updated: "2026-05-31"
    required_fields:
  - "api_name"
  - "version"
  - "endpoints"
  - "request_schema"
  - "response_schema"
  - "errors"
  - "auth"
  - "rate_limits"
    optional_fields:
  - "openapi_path"
  - "examples"
  - "idempotency"
  - "deprecation_policy"
    ---

    # API Contract

    ## 1. Propósito

    Documentar endpoints, entradas, salidas, errores, seguridad y versionado de API.

    ## 2. Cuándo usarla

    Antes de publicar o consumir una API.

    ## 3. Campos obligatorios

    | Campo | Descripción | Criterio mínimo |
    |---|---|---|
    | `api_name` | Debe documentarse de forma clara, verificable y trazable. | No puede quedar vacío ni ambiguo. |\n    | `version` | Debe documentarse de forma clara, verificable y trazable. | No puede quedar vacío ni ambiguo. |\n    | `endpoints` | Debe documentarse de forma clara, verificable y trazable. | No puede quedar vacío ni ambiguo. |\n    | `request_schema` | Debe documentarse de forma clara, verificable y trazable. | No puede quedar vacío ni ambiguo. |\n    | `response_schema` | Debe documentarse de forma clara, verificable y trazable. | No puede quedar vacío ni ambiguo. |\n    | `errors` | Debe documentarse de forma clara, verificable y trazable. | No puede quedar vacío ni ambiguo. |\n    | `auth` | Debe documentarse de forma clara, verificable y trazable. | No puede quedar vacío ni ambiguo. |\n    | `rate_limits` | Debe documentarse de forma clara, verificable y trazable. | No puede quedar vacío ni ambiguo. |\n

    ## 4. Campos opcionales

    | Campo | Uso recomendado |
    |---|---|
    | `openapi_path` | Usar cuando aporte contexto, riesgo, trazabilidad o decisión. |\n    | `examples` | Usar cuando aporte contexto, riesgo, trazabilidad o decisión. |\n    | `idempotency` | Usar cuando aporte contexto, riesgo, trazabilidad o decisión. |\n    | `deprecation_policy` | Usar cuando aporte contexto, riesgo, trazabilidad o decisión. |\n

    ## 5. Ejemplo completo

    ```json
    {
  "api_name": "DevPilot API",
  "version": "v1",
  "endpoints": [
    "POST /projects"
  ],
  "request_schema": "ProjectCreate",
  "response_schema": "Project",
  "errors": [
    "400",
    "409",
    "500"
  ],
  "auth": "local token",
  "rate_limits": "n/a for local MVP"
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
