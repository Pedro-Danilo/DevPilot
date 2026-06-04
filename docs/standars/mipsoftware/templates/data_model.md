---
title: Data Model
doc_id: MIPS-TPL-DATA_MODEL
doc_type: template
version: 0.1.0
status: draft
owner: AI_agents / MIPSoftware
scope: software-engineering-model
created: '2026-05-31'
updated: '2026-06-01'
---

    ---
    title: "Data Model"
    version: "0.1.0"
    status: "draft"
    model: "MIPSoftware"
    template_id: "data_model"
    doc_type: "template"
    owner: "AI_agents / MIPSoftware"
    updated: "2026-05-31"
    required_fields:
  - "conceptual_model"
  - "logical_model"
  - "physical_model"
  - "data_classification"
  - "retention_policy"
    optional_fields:
  - "migration_strategy"
  - "privacy_notes"
  - "backup_requirements"
    ---

    # Data Model

    ## 1. Propósito

    Definir modelo conceptual, lógico, físico, clasificación y retención de datos.

    ## 2. Cuándo usarla

    Antes de crear persistencia o migraciones.

    ## 3. Campos obligatorios

    | Campo | Descripción | Criterio mínimo |
    |---|---|---|
    | `conceptual_model` | Debe documentarse de forma clara, verificable y trazable. | No puede quedar vacío ni ambiguo. |\n    | `logical_model` | Debe documentarse de forma clara, verificable y trazable. | No puede quedar vacío ni ambiguo. |\n    | `physical_model` | Debe documentarse de forma clara, verificable y trazable. | No puede quedar vacío ni ambiguo. |\n    | `data_classification` | Debe documentarse de forma clara, verificable y trazable. | No puede quedar vacío ni ambiguo. |\n    | `retention_policy` | Debe documentarse de forma clara, verificable y trazable. | No puede quedar vacío ni ambiguo. |\n

    ## 4. Campos opcionales

    | Campo | Uso recomendado |
    |---|---|
    | `migration_strategy` | Usar cuando aporte contexto, riesgo, trazabilidad o decisión. |\n    | `privacy_notes` | Usar cuando aporte contexto, riesgo, trazabilidad o decisión. |\n    | `backup_requirements` | Usar cuando aporte contexto, riesgo, trazabilidad o decisión. |\n

    ## 5. Ejemplo completo

    ```json
    {
  "conceptual_model": [
    "Project",
    "Requirement",
    "ADR"
  ],
  "logical_model": "SQLite tables for MVP",
  "physical_model": "projects(id,name,status)",
  "data_classification": "internal",
  "retention_policy": "Retener proyectos activos y archivar cerrados."
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
