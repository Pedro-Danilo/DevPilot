---
doc_id: "POST-H-010-C-AUDIT"
title: "POST-H-010-C — Cleanup plan dry-run"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-06-26"
phase: "POST-FASE-H"
local_first: true
dry_run: true
---

# POST-H-010-C — Cleanup plan dry-run

## Resultado

Estado: `implemented-initial`.

Se implementa un planificador local de cleanup de observabilidad. El plan consume la política `.devpilot/observability/retention_policy.json` y el inventario `POST-H-010-B`, calcula acciones potenciales de rotación, borrado, archivado, redacción y exportación, y produce evidencia JSON/Markdown bajo `outputs/reports/` solo cuando el operador usa `--write-report`.

## Artefactos principales

```text
src/devpilot_core/observability/cleanup.py
docs/schemas/observability_cleanup_plan.schema.json
tests/test_observability_cleanup_plan.py
docs/post_h_010_c_manifest.json
```

## Seguridad

```text
dry_run=true
plan_only=true
mutations_performed=false
destructive_cleanup_performed=false
source_mutations_performed=false
raw_payloads_read=false
network_used=false
external_api_used=false
cleanup_execution_enabled=false
```

Las acciones destructivas candidatas (`rotate`, `delete`, `archive`) incluyen simulación `PolicyEngine`, `requires_policy_engine=true`, `requires_approval=true` y `required_approval_id` determinístico. El comando `observability cleanup-plan --execute` está diseñado como safety probe bloqueante y no ejecuta mutaciones.

## PASS/BLOCK

PASS si el plan se genera en dry-run, no hay mutaciones y el reporte valida contra `ObservabilityCleanupPlan`.

BLOCK si un target resuelve fuera del workspace, si se intenta planificar cleanup sobre `.git/`, `src/`, `docs/` o `tests/`, o si se solicita ejecución desde un comando plan-only.

## Limitaciones

No implementa export redactado ni integración con quality gate. Es una primera versión industrial mínima para planear higiene de observabilidad antes de habilitar workflows de export o gates de retención.
