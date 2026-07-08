---
doc_id: "POST-H-026-DOC"
title: "POST-H-026 — Release candidate local y verificacion de operador"
status: "approved"
version: "0.1.0"
owner: "Ordonez"
updated: "2026-07-07"
approval: "approved_by_owner"
phase: "POST-FASE-H"
implementation_status: "active"
current_micro_sprint: "POST-H-026-A"
next_micro_sprint: "POST-H-026-B"
local_first: true
dry_run_default: true
read_only_by_default: true
no_external_apis_required: true
---

# POST-H-026 — Release candidate local y verificacion de operador

Este documento operacional acompana el backlog `docs/backlogs/POST-H-026_local_release_candidate_operator_verification.md`. POST-H-026 convierte la declaracion `production-ready-local` de POST-H-025 en un release candidate local verificable por operador.

## Estado Actual

`POST-H-026-A — Evidence freshness model` queda implementado como `implemented-initial`.

Implementado:

- Schema `EvidenceFreshnessReport`.
- Criteria registry `.devpilot/release/local_release_candidate_criteria.json`.
- Scanner deterministicamente local `EvidenceFreshnessScanner`.
- CLI `release-candidate evidence-freshness`.
- Reportes runtime opcionales bajo `outputs/reports`.

No implementado todavia:

- Perfil de verificacion RC.
- Install smoke local.
- UI/API RC smoke.
- Reporte final RC PASS/BLOCK.

## Comandos

```powershell
python -m devpilot_core release-candidate evidence-freshness --json
python -m devpilot_core release-candidate evidence-freshness --json --write-report
python -m devpilot_core schema validate --schema-id EvidenceFreshnessReport --instance outputs/reports/evidence_freshness_report.json --json
```

## PASS/BLOCK

PASS si toda evidencia critica esta `fresh` y no hay no-go gates habilitados.

BLOCK si cualquier evidencia critica esta `stale`, `missing` o `invalid`.

## Riesgos

- Falsos BLOCK si el criteria registry queda desactualizado frente a una renumeracion legitima del repo.
- Falsa confianza si se interpreta POST-H-026-A como cierre RC completo; el cierre real queda para POST-H-026-E.
- Outputs runtime no deben versionarse ni usarse como unica fuente de verdad.
