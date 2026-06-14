---
title: "Auditoría FUNC-SPRINT-61 — CLI de trazas y métricas"
doc_id: "DEVPL-AUDIT-FUNC-SPRINT-61"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
standard: "MIPSoftware"
extension: "MIASI"
phase: "FASE-E-AGENTOPS-OBSERVABILIDAD"
updated: "2026-06-13"
approval: "approved_by_owner"
---

# Auditoría FUNC-SPRINT-61 — CLI de trazas y métricas

## 1. Propósito

Verificar que `FUNC-SPRINT-61` expone consulta operacional de trazas y métricas locales mediante CLI, sin UI, sin red, sin exporter remoto y sin dependencias externas obligatorias.

## 2. Alcance

Incluye `trace report`, `trace inspect <trace_id>`, `metrics summary`, `TraceQueryService`, reportes opcionales JSON/Markdown y pruebas CLI. No incluye dashboard, OpenTelemetry real, exporter remoto, AgentOps Quality Gate ni retención/compactación.

## 3. Resultado

Veredicto: `PASS`. Estado: `implemented-initial`.

## 4. Evidencia de implementación

- `src/devpilot_core/observability/trace_queries.py` implementa consultas read-only.
- `src/devpilot_core/cli.py` expone comandos `trace` y `metrics`.
- `tests/test_observability_cli.py` valida JSON parseable, DB vacía, `trace_id` inexistente, reportes opcionales y agregación de métricas.
- `README.md`, `docs/05_operations/runbook.md`, `docs/05_operations/observability_plan.md`, `docs/06_miasi/observability_card.md` y backlogs quedan sincronizados.

## 5. Criterios PASS

- Los comandos devuelven `CommandResult`.
- `trace report --write-report` y `metrics summary --write-report` escriben reportes en `outputs/reports`.
- DB vacía no produce excepción.
- `trace inspect` con `trace_id` inexistente produce warning controlado.
- No se requiere UI, red, API externa, collector ni OpenTelemetry SDK.

## 6. Criterios BLOCK

- Exponer prompts, completions, secretos, diffs, patches, stdout o stderr crudos.
- Lanzar excepción por DB vacía o traza inexistente.
- Requerir servicios externos para consultar señales.
- Activar exporter remoto o telemetría externa.

## 7. Riesgos

| Riesgo | Mitigación |
|---|---|
| Reportes grandes | Límites `--limit` con cap interno. |
| CLI creciente | Lógica de consulta aislada en `TraceQueryService`. |
| Datos sensibles | Redacción antes de emitir JSON/reportes. |
| Falta dashboard | Queda fuera del alcance de Sprint 61. |

## 8. Comandos de verificación

```powershell
python -m devpilot_core trace report --json --write-report
python -m devpilot_core trace inspect <trace_id> --json
python -m devpilot_core metrics summary --json --write-report
python -m pytest tests/test_observability_cli.py -q
python -m devpilot_core schema validate-manifest docs/functional_sprint_61_manifest.json --json
python -m devpilot_core validate all --json
```

## 9. Estado de capacidades

| Capacidad | Estado |
|---|---|
| trace report | implemented-initial |
| trace inspect | implemented-initial |
| metrics summary | implemented-initial |
| Markdown reports | implemented-initial vía ReportEngine |
| Dashboard AgentOps | pendiente |
| OpenTelemetry exporter | pendiente Sprint 62 |
| AgentOps Quality Gate | pendiente Sprint 63 |

## 10. Próximo paso

`FUNC-SPRINT-62 — Exporter OpenTelemetry opcional y dry-run`, manteniendo no exfiltración, redacción obligatoria y telemetría remota deshabilitada por defecto.
