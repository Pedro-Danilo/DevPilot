---
title: Template — Quality Gate Report
doc_id: MIPS-TPL-QUALITY_GATE_REPORT
doc_type: template
version: 0.1.0
status: draft
owner: AI_agents / MIPSoftware
scope: quality-testing-verification
created: '2026-05-31'
updated: '2026-05-31'
related_standard: MIPS-DOC-009 — Calidad, testing y verificación
template_id: quality_gate_report
---

# Template — Quality Gate Report

## 1. Propósito

Consolidar el resultado de los gates de calidad, seguridad, testing, performance, accesibilidad, datos y MIASI.

## 2. Cuándo usarla

Usar en CI/CD, revisión de release o cierre de sprint antes de promover software.

## 3. Campos obligatorios

- `gate_report_id`
- `project`
- `version`
- `commit_or_build`
- `environment`
- `gates`
- `summary`
- `decision`
- `blockers`
- `approver`

## 4. Campos opcionales

- metrics
- trends
- waivers
- links_to_reports
- miasi_eval_summary
- recommendations

## 5. Ejemplo completo

```yaml
gate_report_id: QG-2026-004
project: devpilot-local
version: 0.3.0
commit_or_build: abc123
environment: ci
gates:
  unit_tests: pass
  integration_tests: pass
  security_scan: pass
  accessibility: warn
  miasi_evals: pass
decision: pass_with_observations
blockers: []
```

## 6. Criterios de revisión

- Incluye todos los gates aplicables.
- Tiene decisión clara.
- Lista bloqueadores.
- Incluye evidencia o enlaces.
- Declara waivers si existen.

## 7. Criterios de rechazo

- No lista pruebas omitidas.
- Declara PASS con blockers abiertos.
- No identifica build/commit.
- No incluye MIASI cuando aplica.

## 8. Relación con el ciclo de vida

Fases 16 a 19: verificación, validación, release y despliegue.

## 9. Relación con quality gates

Es evidencia directa para release readiness y aprobación de despliegue.
