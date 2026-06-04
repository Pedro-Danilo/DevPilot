---
title: Stakeholder Map
doc_id: MIPS-TPL-STAKEHOLDER_MAP
doc_type: template
version: 0.1.0
status: draft
owner: AI_agents / MIPSoftware
scope: software-engineering-model
created: '2026-05-31'
updated: '2026-06-01'
---

    ---
    title: "Stakeholder Map"
    version: "0.1.0"
    status: "draft"
    model: "MIPSoftware"
    template_id: "stakeholder_map"
    doc_type: "template"
    owner: "AI_agents / MIPSoftware"
    updated: "2026-05-31"
    required_fields:
  - "stakeholders"
  - "roles"
  - "interests"
  - "influence_level"
  - "communication_plan"
    optional_fields:
  - "conflicts"
  - "approval_authority"
  - "escalation_path"
    ---

    # Stakeholder Map

    ## 1. Propósito

    Identificar actores, intereses, influencia, responsabilidades y necesidades de comunicación.

    ## 2. Cuándo usarla

    Antes de requerimientos y durante cambios relevantes de alcance.

    ## 3. Campos obligatorios

    | Campo | Descripción | Criterio mínimo |
    |---|---|---|
    | `stakeholders` | Debe documentarse de forma clara, verificable y trazable. | No puede quedar vacío ni ambiguo. |\n    | `roles` | Debe documentarse de forma clara, verificable y trazable. | No puede quedar vacío ni ambiguo. |\n    | `interests` | Debe documentarse de forma clara, verificable y trazable. | No puede quedar vacío ni ambiguo. |\n    | `influence_level` | Debe documentarse de forma clara, verificable y trazable. | No puede quedar vacío ni ambiguo. |\n    | `communication_plan` | Debe documentarse de forma clara, verificable y trazable. | No puede quedar vacío ni ambiguo. |\n

    ## 4. Campos opcionales

    | Campo | Uso recomendado |
    |---|---|
    | `conflicts` | Usar cuando aporte contexto, riesgo, trazabilidad o decisión. |\n    | `approval_authority` | Usar cuando aporte contexto, riesgo, trazabilidad o decisión. |\n    | `escalation_path` | Usar cuando aporte contexto, riesgo, trazabilidad o decisión. |\n

    ## 5. Ejemplo completo

    ```json
    {
  "stakeholders": [
    {
      "name": "Owner técnico",
      "role": "decision maker",
      "interest": "calidad y velocidad",
      "influence_level": "high"
    }
  ],
  "communication_plan": "Revisión por sprint y gate antes de release."
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
