---
title: Plantilla — Operational Readiness Review
doc_id: MIPS-TPL-OPERATIONAL-READINESS
doc_type: template
version: 0.1.0
status: draft
owner: AI_agents / MIPSoftware
scope: observability-operations-sre
created: '2026-05-31'
updated: '2026-05-31'
related_standard: MIPS-DOC-012 — Observabilidad, operación, SRE e incidentes
---

# Plantilla — Operational Readiness Review

## 1. Propósito

Evaluar si un sistema está listo para operar en producción o producción controlada.

## 2. Checklist mínimo

| Ítem | PASS/FAIL | Evidencia |
|---|---|---|
| Logs estructurados |  |  |
| Métricas mínimas |  |  |
| Trazas para flujos críticos |  |  |
| Dashboards |  |  |
| Alertas accionables |  |  |
| Runbook |  |  |
| Backup/restore |  |  |
| Incident response |  |  |
| SLO/SLI definidos |  |  |
| Post-release verification |  |  |
| MIASI activado si aplica |  |  |

## 3. Decisión

```yaml
decision: "approved | approved_with_risks | blocked"
blocking_findings: []
accepted_risks: []
next_review_date: "YYYY-MM-DD"
```

## 4. Criterios de bloqueo

- No hay runbook.
- No hay logs o métricas mínimas.
- No existe backup/restore para datos persistentes.
- Sistema con agentes IA sin trazas MIASI y evaluación mínima.
