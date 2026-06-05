---
title: Ci Cd Strategy
doc_id: MIPS-TPL-CI_CD_STRATEGY
doc_type: template
version: 0.1.0
status: draft
owner: AI_agents / MIPSoftware
scope: software-engineering-model
created: '2026-05-31'
updated: '2026-06-01'
---

    ---
    title: "CI/CD Strategy"
    version: "0.1.0"
    status: "draft"
    model: "MIPSoftware"
    template_id: "ci_cd_strategy"
    doc_type: "template"
    owner: "AI_agents / MIPSoftware"
    updated: "2026-05-31"
    required_fields:
  - "branching_strategy"
  - "pipeline_stages"
  - "quality_gates"
  - "secrets_strategy"
  - "environments"
  - "rollback_strategy"
    optional_fields:
  - "artifact_repository"
  - "sbom"
  - "provenance"
  - "manual_approvals"
    ---

    # CI/CD Strategy

    ## 1. Propósito

    Definir ramas, pipelines, quality gates, ambientes, secretos y despliegue.

    ## 2. Cuándo usarla

    Antes de integración continua real y releases.

    ## 3. Campos obligatorios

    | Campo | Descripción | Criterio mínimo |
    |---|---|---|
    | `branching_strategy` | Debe documentarse de forma clara, verificable y trazable. | No puede quedar vacío ni ambiguo. |\n    | `pipeline_stages` | Debe documentarse de forma clara, verificable y trazable. | No puede quedar vacío ni ambiguo. |\n    | `quality_gates` | Debe documentarse de forma clara, verificable y trazable. | No puede quedar vacío ni ambiguo. |\n    | `secrets_strategy` | Debe documentarse de forma clara, verificable y trazable. | No puede quedar vacío ni ambiguo. |\n    | `environments` | Debe documentarse de forma clara, verificable y trazable. | No puede quedar vacío ni ambiguo. |\n    | `rollback_strategy` | Debe documentarse de forma clara, verificable y trazable. | No puede quedar vacío ni ambiguo. |\n

    ## 4. Campos opcionales

    | Campo | Uso recomendado |
    |---|---|
    | `artifact_repository` | Usar cuando aporte contexto, riesgo, trazabilidad o decisión. |\n    | `sbom` | Usar cuando aporte contexto, riesgo, trazabilidad o decisión. |\n    | `provenance` | Usar cuando aporte contexto, riesgo, trazabilidad o decisión. |\n    | `manual_approvals` | Usar cuando aporte contexto, riesgo, trazabilidad o decisión. |\n

    ## 5. Ejemplo completo

    ```json
    {
  "branching_strategy": "trunk-based with short branches",
  "pipeline_stages": [
    "lint",
    "test",
    "security",
    "package"
  ],
  "quality_gates": [
    "tests pass",
    "no critical vulnerabilities"
  ],
  "secrets_strategy": "environment secrets, never in repo",
  "environments": [
    "local",
    "dev"
  ],
  "rollback_strategy": "restore previous artifact"
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
