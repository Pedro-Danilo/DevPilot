---
title: Template — Test Plan
doc_id: MIPS-TPL-TEST_PLAN
doc_type: template
version: 0.1.0
status: draft
owner: AI_agents / MIPSoftware
scope: quality-testing-verification
created: '2026-05-31'
updated: '2026-05-31'
related_standard: MIPS-DOC-009 — Calidad, testing y verificación
template_id: test_plan
---

# Template — Test Plan

## 1. Propósito

Definir el plan concreto de ejecución de pruebas para una iteración, módulo, release o hito.

## 2. Cuándo usarla

Usar antes de ejecutar una campaña de pruebas o al preparar un release candidato.

## 3. Campos obligatorios

- `test_plan_id`
- `release_or_iteration`
- `scope`
- `items_under_test`
- `test_types`
- `entry_criteria`
- `exit_criteria`
- `environment`
- `test_data`
- `schedule`
- `responsibles`
- `risks`
- `reporting_format`

## 4. Campos opcionales

- dependencies
- known limitations
- manual exploratory charters
- MIASI eval suite
- performance window

## 5. Ejemplo completo

```yaml
test_plan_id: TP-2026-001
release_or_iteration: v0.2.0
scope: checkout y registro de venta
items_under_test:
  - sales_api
  - inventory_service
  - web_checkout
test_types:
  - unit
  - integration
  - contract
  - e2e
entry_criteria:
  code_freeze: true
  requirements_approved: true
exit_criteria:
  critical_defects: 0
  high_defects_without_waiver: 0
```

## 6. Criterios de revisión

- Tiene alcance concreto.
- Define entrada y salida.
- Incluye ambientes y datos.
- Relaciona pruebas con riesgos.
- Incluye reporte esperado.

## 7. Criterios de rechazo

- No tiene criterios de salida.
- Prueba contra producción sin autorización.
- Omite riesgos críticos.
- No define responsables.

## 8. Relación con el ciclo de vida

Fases 13, 16, 17 y 18: plan de pruebas, verificación, validación y release.

## 9. Relación con quality gates

Permite verificar si una campaña de pruebas puede iniciar y cerrarse formalmente.
