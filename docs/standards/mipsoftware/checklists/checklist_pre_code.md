---
title: Checklist Pre Code
doc_id: MIPS-CHK-CHECKLIST_PRE_CODE
doc_type: checklist
version: 0.1.0
status: draft
owner: AI_agents / MIPSoftware
scope: software-engineering-model
created: '2026-05-31'
updated: '2026-06-01'
---

    ---
    title: "Checklist pre-code"
    version: "0.1.0"
    status: "draft"
    model: "MIPSoftware"
    checklist_id: "checklist_pre_code"
    doc_type: "checklist"
    owner: "AI_agents / MIPSoftware"
    updated: "2026-05-31"
    items:
  - "PC-001"
  - "PC-002"
  - "PC-003"
  - "PC-004"
  - "PC-005"
    ---

    # Checklist pre-code

    ## Propósito

    Evitar iniciar implementación sin evidencia mínima de producto, requerimientos, arquitectura, riesgos, calidad, seguridad y MIASI cuando aplique.

    ## Resultado esperado

    - **PASS**: todos los ítems obligatorios cumplen.
    - **FAIL**: existe al menos un ítem obligatorio incompleto o ambiguo.
    - **BLOCK**: existe riesgo crítico, falta de evidencia esencial o violación de política.

    ## Checklist

    | Ítem | Descripción | Obligatorio/opcional | Evidencia requerida | Responsable | Criterio PASS | Criterio FAIL | Referencia |
    |---|---|---|---|---|---|---|---|
    | PC-001 | Existe visión de producto aprobada | obligatorio | product_vision.md | Product Owner | La visión identifica problema, usuarios, valor y métricas | No existe visión o es ambigua | MIPS-DOC-004 |
| PC-002 | Existen requerimientos iniciales verificables | obligatorio | requirements_specification.md | Business Analyst | Requerimientos con aceptación y prioridad | Requerimientos sin aceptación | MIPS-DOC-005 |
| PC-003 | Existe arquitectura mínima | obligatorio | architecture_document.md | Architect | Drivers, restricciones, C4 y riesgos definidos | No hay arquitectura mínima | MIPS-DOC-006 |
| PC-004 | Existe decisión sobre MIASI | obligatorio | checklist_miasi_required.md | Architect/Security | MIASI activado o descartado con justificación | No se evaluó IA/agentes | MIPS-DOC-014 |
| PC-005 | Existe estrategia inicial de pruebas | obligatorio | test_strategy.md | QA | Niveles de prueba y gates definidos | No hay estrategia de pruebas | MIPS-DOC-009 |

    ## Criterios de bloqueo

    - Cualquier ítem obligatorio marcado como crítico sin evidencia suficiente.
    - Omisión de MIASI cuando el sistema usa IA, agentes, LLMs, RAG, memoria o tool calling.
    - Riesgo de seguridad, privacidad, datos o operación sin owner.

    ## Salida sugerida YAML

    ```yaml
    checklist: "checklist_pre_code"
    result: "PASS|FAIL|BLOCK"
    mandatory_items_total: 0
    mandatory_items_passed: 0
    findings: []
    decision: "continue|fix|required_approval|block"
    ```
