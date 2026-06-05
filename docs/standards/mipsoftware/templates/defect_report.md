---
title: Template — Defect Report
doc_id: MIPS-TPL-DEFECT_REPORT
doc_type: template
version: 0.1.0
status: draft
owner: AI_agents / MIPSoftware
scope: quality-testing-verification
created: '2026-05-31'
updated: '2026-05-31'
related_standard: MIPS-DOC-009 — Calidad, testing y verificación
template_id: defect_report
---

# Template — Defect Report

## 1. Propósito

Documentar defectos de forma reproducible, priorizable, auditable y conectada con pruebas de regresión.

## 2. Cuándo usarla

Usar cada vez que se detecte un defecto en desarrollo, QA, staging, producción o evaluación agentic.

## 3. Campos obligatorios

- `defect_id`
- `title`
- `severity`
- `priority`
- `environment`
- `steps_to_reproduce`
- `expected_result`
- `actual_result`
- `evidence`
- `affected_component`
- `linked_requirement`
- `owner`
- `status`

## 4. Campos opcionales

- root_cause
- workaround
- regression_test
- security_impact
- data_impact
- miasi_trace_id

## 5. Ejemplo completo

```yaml
defect_id: BUG-2026-017
title: Error al descontar inventario con venta concurrente
severity: high
priority: P1
environment: staging
affected_component: inventory_service
steps_to_reproduce:
  - crear producto con stock 1
  - registrar dos ventas simultáneas
expected_result: solo una venta debe confirmarse
actual_result: ambas ventas quedan confirmadas
regression_test: TC-INV-REG-003
```

## 6. Criterios de revisión

- Es reproducible.
- Tiene severidad justificada.
- Incluye evidencia.
- Relaciona componente/requerimiento.
- Define prueba de regresión si aplica.

## 7. Criterios de rechazo

- No se puede reproducir ni investigar.
- No tiene ambiente.
- No tiene evidencia.
- Cierra bug crítico sin regresión.

## 8. Relación con el ciclo de vida

Fases 16, 17, 22 y 23: verificación, validación, incidentes y mantenimiento evolutivo.

## 9. Relación con quality gates

Defectos críticos o altos pueden bloquear quality gates y release readiness.
