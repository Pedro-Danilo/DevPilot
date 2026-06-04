---
title: Test Strategy
doc_id: MIPS-TPL-TEST_STRATEGY
doc_type: template
version: 0.1.0
status: draft
owner: AI_agents / MIPSoftware
scope: software-engineering-model
created: '2026-05-31'
updated: '2026-06-01'
---

    ---
    title: "Test Strategy"
    version: "0.1.0"
    status: "draft"
    model: "MIPSoftware"
    template_id: "test_strategy"
    doc_type: "template"
    owner: "AI_agents / MIPSoftware"
    updated: "2026-05-31"
    required_fields:
  - "scope"
  - "test_levels"
  - "quality_gates"
  - "test_data"
  - "environments"
  - "coverage_targets"
    optional_fields:
  - "automation_plan"
  - "performance_targets"
  - "miasi_evals"
    ---

    # Test Strategy

    ## 1. Propósito

    Definir niveles de prueba, alcance, datos, ambientes, herramientas y gates.

    ## 2. Cuándo usarla

    Antes de implementación sostenida y antes de release.

    ## 3. Campos obligatorios

    | Campo | Descripción | Criterio mínimo |
    |---|---|---|
    | `scope` | Debe documentarse de forma clara, verificable y trazable. | No puede quedar vacío ni ambiguo. |\n    | `test_levels` | Debe documentarse de forma clara, verificable y trazable. | No puede quedar vacío ni ambiguo. |\n    | `quality_gates` | Debe documentarse de forma clara, verificable y trazable. | No puede quedar vacío ni ambiguo. |\n    | `test_data` | Debe documentarse de forma clara, verificable y trazable. | No puede quedar vacío ni ambiguo. |\n    | `environments` | Debe documentarse de forma clara, verificable y trazable. | No puede quedar vacío ni ambiguo. |\n    | `coverage_targets` | Debe documentarse de forma clara, verificable y trazable. | No puede quedar vacío ni ambiguo. |\n

    ## 4. Campos opcionales

    | Campo | Uso recomendado |
    |---|---|
    | `automation_plan` | Usar cuando aporte contexto, riesgo, trazabilidad o decisión. |\n    | `performance_targets` | Usar cuando aporte contexto, riesgo, trazabilidad o decisión. |\n    | `miasi_evals` | Usar cuando aporte contexto, riesgo, trazabilidad o decisión. |\n

    ## 5. Ejemplo completo

    ```json
    {
  "scope": "DevPilot CLI MVP",
  "test_levels": [
    "unit",
    "integration",
    "contract"
  ],
  "quality_gates": [
    "pytest pass",
    "security scan pass"
  ],
  "test_data": "fixtures sintéticas",
  "environments": [
    "local",
    "CI"
  ],
  "coverage_targets": "70% mínimo inicial"
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
