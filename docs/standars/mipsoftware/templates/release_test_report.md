---
title: Template — Release Test Report
doc_id: MIPS-TPL-RELEASE_TEST_REPORT
doc_type: template
version: 0.1.0
status: draft
owner: AI_agents / MIPSoftware
scope: quality-testing-verification
created: '2026-05-31'
updated: '2026-05-31'
related_standard: MIPS-DOC-009 — Calidad, testing y verificación
template_id: release_test_report
---

# Template — Release Test Report

## 1. Propósito

Documentar la evidencia final de pruebas y calidad para decidir si un release puede ser desplegado.

## 2. Cuándo usarla

Usar para todo release candidato, MVP público, versión productiva o despliegue relevante.

## 3. Campos obligatorios

- `release_id`
- `version`
- `scope`
- `test_summary`
- `requirements_coverage`
- `defects_summary`
- `security_summary`
- `performance_summary`
- `accessibility_summary`
- `data_migration_summary`
- `risks_residual`
- `decision`
- `approvers`

## 4. Campos opcionales

- miasi_eval_summary
- rollback_evidence
- release_notes_link
- observability_readiness
- customer_impact
- post_release_checks

## 5. Ejemplo completo

```yaml
release_id: REL-2026-002
version: 1.0.0-rc1
scope: primer MVP productivo
test_summary:
  total: 312
  passed: 312
  failed: 0
defects_summary:
  critical_open: 0
  high_open_without_waiver: 0
security_summary: pass
performance_summary: pass
accessibility_summary: pass_with_minor_findings
decision: release_approved
approvers:
  - qa_lead
  - tech_lead
```

## 6. Criterios de revisión

- Resume pruebas y riesgos.
- Tiene decisión explícita.
- Lista defectos abiertos.
- Confirma rollback/observabilidad si aplica.
- Incluye aprobadores.

## 7. Criterios de rechazo

- Aprueba release con defectos críticos.
- No tiene evidencia de CI.
- Omite seguridad o migraciones.
- No declara riesgos residuales.

## 8. Relación con el ciclo de vida

Fases 18 y 19: release y despliegue.

## 9. Relación con quality gates

Es el documento final para aprobar, bloquear o aprobar con excepción formal un release.
