---
doc_id: "POST-H-026-A-EVIDENCE-FRESHNESS-REPORT"
title: "POST-H-026-A — Evidence freshness model"
status: "approved"
version: "1.0.1"
owner: "Ordonez"
updated: "2026-07-08"
approval: "approved_by_owner"
created_by: "POST-H-026-A"
phase: "POST-FASE-H"
implementation_status: "implemented-initial"
---

# POST-H-026-A — Evidence freshness model

POST-H-026-A queda implementado como `implemented-initial / evidence-freshness-read-only`.

## Implementado

- `EvidenceFreshnessReport` schema.
- Registry `.devpilot/release/local_release_candidate_criteria.json`.
- `EvidenceFreshnessScanner` en `src/devpilot_core/release_candidate/evidence_freshness.py`.
- CLI `python -m devpilot_core release-candidate evidence-freshness --json`.
- Escritura opcional de reportes JSON/Markdown bajo `outputs/reports`.

## Contrato

El scanner clasifica cada evidencia como:

- `fresh`.
- `stale`.
- `missing`.
- `invalid`.
- `not_applicable`.

El resultado es `BLOCK` si cualquier evidencia critica queda `stale`, `missing` o `invalid`.

## Limites

No ejecuta pytest, no recalcula reportes, no corrige documentos stale, no publica releases y no declara RC final. POST-H-026-B/C/D/E completan el perfil RC, smoke local, UI/API smoke y reporte final PASS/BLOCK.

## Seguridad

No usa red, APIs externas, remote execution, connector write, plugin execution ni secretos. Por defecto no escribe outputs. Con `--write-report`, solo escribe evidencia runtime regenerable en `outputs/reports`.

## Verificacion

```powershell
python -m pytest -p no:ddtrace --assert=plain tests/test_post_h_026_evidence_freshness.py tests/test_post_h_025_production_ready_criteria.py tests/test_post_h_025_production_ready_aggregator.py tests/test_schema_registry.py tests/test_project_global_state.py -q
python -m devpilot_core release-candidate evidence-freshness --json
python -m devpilot_core release-candidate evidence-freshness --json --write-report
python -m devpilot_core schema validate --schema-id EvidenceFreshnessReport --instance outputs/reports/evidence_freshness_report.json --json
```


## Patch correctivo POST-H-026-A-P1 — Autovalidación de schema en workspaces mínimos

### Causa corregida

Durante la validación focal de `POST-H-026-A`, el test `test_evidence_freshness_optional_runtime_absence_is_not_applicable` falló porque el scanner intentaba resolver `EvidenceFreshnessReport` mediante `docs/schemas/schema_catalog.json` aun cuando el fixture usaba un workspace temporal mínimo sin catálogo de schemas. Ese fixture es válido para probar semántica de freshness de evidencia opcional y no debe exigir que exista todo el repo DevPilot.

También se corrigió una inconsistencia diagnóstica: el finding informativo se construía antes de la autovalidación del reporte, por lo que podía conservar metadata `decision=PASS` aunque una validación posterior cambiara el reporte a `BLOCK`.

### Patch aplicado

- `EvidenceFreshnessScanner` ahora valida el reporte contra `docs/schemas/evidence_freshness_report.schema.json` por ruta directa cuando el contrato existe en el repo real.
- En workspaces mínimos sin schema contract, la autovalidación se omite con warning no bloqueante `EVIDENCE_FRESHNESS_SCHEMA_VALIDATION_SKIPPED`.
- La decisión final se calcula antes de construir findings, evitando metadata contradictoria.
- La escritura con `--write-report` ocurre después de calcular la decisión final y escribe el reporte final consistente.

### Verificación del patch

```powershell
python -m pytest -p no:ddtrace --assert=plain tests/test_post_h_026_evidence_freshness.py tests/test_post_h_025_production_ready_criteria.py tests/test_post_h_025_production_ready_aggregator.py tests/test_schema_registry.py tests/test_project_global_state.py tests/test_post_h_006_e_cli_no_growth_gate.py -q
```

Resultado observado en entorno de corrección:

```text
29 passed, 0 failed, 0 errors, 0 skipped
```
