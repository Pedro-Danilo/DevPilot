---
title: Checklist Security Ready
doc_id: MIPS-CHK-CHECKLIST_SECURITY_READY
doc_type: checklist
version: 0.1.0
status: draft
owner: AI_agents / MIPSoftware
scope: software-engineering-model
created: '2026-05-31'
updated: '2026-06-01'
---

    ---
    title: "Checklist security ready"
    version: "0.1.0"
    status: "draft"
    model: "MIPSoftware"
    checklist_id: "checklist_security_ready"
    doc_type: "checklist"
    owner: "AI_agents / MIPSoftware"
    updated: "2026-05-31"
    items:
  - "SR-001"
  - "SR-002"
  - "SR-003"
  - "SR-004"
    ---

    # Checklist security ready

    ## Propósito

    Verificar controles mínimos de seguridad antes de release.

    ## Resultado esperado

    - **PASS**: todos los ítems obligatorios cumplen.
    - **FAIL**: existe al menos un ítem obligatorio incompleto o ambiguo.
    - **BLOCK**: existe riesgo crítico, falta de evidencia esencial o violación de política.

    ## Checklist

    | Ítem | Descripción | Obligatorio/opcional | Evidencia requerida | Responsable | Criterio PASS | Criterio FAIL | Referencia |
    |---|---|---|---|---|---|---|---|
    | SR-001 | Threat model mínimo completo | obligatorio | security_threat_model.md | Security | Activos, amenazas y controles definidos | Sin threat model | MIPS-DOC-010 |
| SR-002 | Secretos fuera del código | obligatorio | secret scan report | Developer | Sin secretos en repo/logs | Secreto expuesto | MIPS-DOC-010 |
| SR-003 | Datos personales clasificados | obligatorio si aplica | privacy_assessment.md | Privacy/Security | Datos clasificados y política definida | Datos personales sin política | MIPS-DOC-010 |
| SR-004 | Security tests ejecutados | obligatorio | security_test_plan.md | QA/Security | Gates mínimos PASS | Vulnerabilidades críticas abiertas | MIPS-DOC-010 |

    ## Criterios de bloqueo

    - Cualquier ítem obligatorio marcado como crítico sin evidencia suficiente.
    - Omisión de MIASI cuando el sistema usa IA, agentes, LLMs, RAG, memoria o tool calling.
    - Riesgo de seguridad, privacidad, datos o operación sin owner.

    ## Salida sugerida YAML

    ```yaml
    checklist: "checklist_security_ready"
    result: "PASS|FAIL|BLOCK"
    mandatory_items_total: 0
    mandatory_items_passed: 0
    findings: []
    decision: "continue|fix|required_approval|block"
    ```
