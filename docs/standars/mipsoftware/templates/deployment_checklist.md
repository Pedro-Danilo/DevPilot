---
title: Deployment Checklist
doc_id: MIPS-TPL-DEPLOYMENT_CHECKLIST
doc_type: template
version: 0.1.0
status: draft
owner: AI_agents / MIPSoftware
scope: software-engineering-model
created: '2026-05-31'
updated: '2026-06-01'
---

    ---
    title: "Deployment Checklist"
    version: "0.1.0"
    status: "draft"
    model: "MIPSoftware"
    template_id: "deployment_checklist"
    doc_type: "template"
    owner: "AI_agents / MIPSoftware"
    updated: "2026-05-31"
    required_fields:
  - "deployment_id"
  - "environment"
  - "pre_checks"
  - "deployment_steps"
  - "post_checks"
  - "rollback_steps"
  - "owner"
    optional_fields:
  - "maintenance_window"
  - "communication_plan"
  - "monitoring_links"
    ---

    # Deployment Checklist

    ## 1. Propósito

    Verificar pasos, precondiciones, postchecks y rollback de despliegue.

    ## 2. Cuándo usarla

    Antes y durante despliegue.

    ## 3. Campos obligatorios

    | Campo | Descripción | Criterio mínimo |
    |---|---|---|
    | `deployment_id` | Debe documentarse de forma clara, verificable y trazable. | No puede quedar vacío ni ambiguo. |\n    | `environment` | Debe documentarse de forma clara, verificable y trazable. | No puede quedar vacío ni ambiguo. |\n    | `pre_checks` | Debe documentarse de forma clara, verificable y trazable. | No puede quedar vacío ni ambiguo. |\n    | `deployment_steps` | Debe documentarse de forma clara, verificable y trazable. | No puede quedar vacío ni ambiguo. |\n    | `post_checks` | Debe documentarse de forma clara, verificable y trazable. | No puede quedar vacío ni ambiguo. |\n    | `rollback_steps` | Debe documentarse de forma clara, verificable y trazable. | No puede quedar vacío ni ambiguo. |\n    | `owner` | Debe documentarse de forma clara, verificable y trazable. | No puede quedar vacío ni ambiguo. |\n

    ## 4. Campos opcionales

    | Campo | Uso recomendado |
    |---|---|
    | `maintenance_window` | Usar cuando aporte contexto, riesgo, trazabilidad o decisión. |\n    | `communication_plan` | Usar cuando aporte contexto, riesgo, trazabilidad o decisión. |\n    | `monitoring_links` | Usar cuando aporte contexto, riesgo, trazabilidad o decisión. |\n

    ## 5. Ejemplo completo

    ```json
    {
  "deployment_id": "DEP-001",
  "environment": "dev",
  "pre_checks": [
    "tests pass"
  ],
  "deployment_steps": [
    "tag release",
    "publish package"
  ],
  "post_checks": [
    "health ok"
  ],
  "rollback_steps": [
    "revert tag"
  ],
  "owner": "ReleaseAgent"
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
