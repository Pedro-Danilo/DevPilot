---
title: Privacy Assessment
doc_id: MIPS-TPL-PRIVACY_ASSESSMENT
doc_type: template
version: 0.1.0
status: draft
owner: AI_agents / MIPSoftware
scope: software-engineering-model
created: '2026-05-31'
updated: '2026-06-01'
---

    ---
    title: "Privacy Assessment"
    version: "0.1.0"
    status: "draft"
    model: "MIPSoftware"
    template_id: "privacy_assessment"
    doc_type: "template"
    owner: "AI_agents / MIPSoftware"
    updated: "2026-05-31"
    required_fields:
  - "data_subjects"
  - "personal_data"
  - "purpose"
  - "lawful_basis_or_policy"
  - "retention"
  - "access_controls"
  - "deletion_process"
    optional_fields:
  - "cross_border_transfer"
  - "processor_roles"
  - "privacy_risks"
    ---

    # Privacy Assessment

    ## 1. Propósito

    Evaluar datos personales, base de tratamiento, minimización, retención y derechos de usuarios.

    ## 2. Cuándo usarla

    Cuando el sistema procese datos personales o sensibles.

    ## 3. Campos obligatorios

    | Campo | Descripción | Criterio mínimo |
    |---|---|---|
    | `data_subjects` | Debe documentarse de forma clara, verificable y trazable. | No puede quedar vacío ni ambiguo. |\n    | `personal_data` | Debe documentarse de forma clara, verificable y trazable. | No puede quedar vacío ni ambiguo. |\n    | `purpose` | Debe documentarse de forma clara, verificable y trazable. | No puede quedar vacío ni ambiguo. |\n    | `lawful_basis_or_policy` | Debe documentarse de forma clara, verificable y trazable. | No puede quedar vacío ni ambiguo. |\n    | `retention` | Debe documentarse de forma clara, verificable y trazable. | No puede quedar vacío ni ambiguo. |\n    | `access_controls` | Debe documentarse de forma clara, verificable y trazable. | No puede quedar vacío ni ambiguo. |\n    | `deletion_process` | Debe documentarse de forma clara, verificable y trazable. | No puede quedar vacío ni ambiguo. |\n

    ## 4. Campos opcionales

    | Campo | Uso recomendado |
    |---|---|
    | `cross_border_transfer` | Usar cuando aporte contexto, riesgo, trazabilidad o decisión. |\n    | `processor_roles` | Usar cuando aporte contexto, riesgo, trazabilidad o decisión. |\n    | `privacy_risks` | Usar cuando aporte contexto, riesgo, trazabilidad o decisión. |\n

    ## 5. Ejemplo completo

    ```json
    {
  "data_subjects": [
    "freelance leads"
  ],
  "personal_data": [
    "nombre",
    "email"
  ],
  "purpose": "gestión de oportunidades",
  "lawful_basis_or_policy": "consent/contract as applicable",
  "retention": "mientras proyecto activo",
  "access_controls": "owner only",
  "deletion_process": "delete request within policy window"
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
