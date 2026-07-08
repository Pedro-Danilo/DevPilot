---
doc_id: "POST-H-026-DOC"
title: "POST-H-026 — Release candidate local y verificacion de operador"
status: "approved"
version: "0.3.0"
owner: "Ordonez"
updated: "2026-07-08"
approval: "approved_by_owner"
phase: "POST-FASE-H"
implementation_status: "active"
current_micro_sprint: "POST-H-026-C"
next_micro_sprint: "POST-H-026-D"
local_first: true
dry_run_default: true
read_only_by_default: true
no_external_apis_required: true
---

# POST-H-026 — Release candidate local y verificacion de operador

Este documento operacional acompana el backlog `docs/backlogs/POST-H-026_local_release_candidate_operator_verification.md`. POST-H-026 convierte la declaracion `production-ready-local` de POST-H-025 en un release candidate local verificable por operador.

## Estado Actual

`POST-H-026-C — UI/API local smoke under RC` queda implementado como `implemented-initial`.

Implementado:

- POST-H-026-A: schema `EvidenceFreshnessReport`, criteria registry y scanner `EvidenceFreshnessScanner`.
- POST-H-026-B: perfil `release-candidate-local`, schema `ReleaseCandidateVerificationProfile` y binding TCR v2.
- POST-H-026-C: schema `UiApiRcSmokeReport`, módulo `UiApiRcSmokeRunner`, CLI `release-candidate ui-api-smoke` y smoke local API/UI sin red.
- Reportes runtime opcionales bajo `outputs/reports` únicamente con `--write-report`.

No implementado todavía:

- Install smoke local.
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

## Estado implementado POST-H-026-C

`POST-H-026-C — UI/API local smoke under RC` queda implementado como `implemented-initial / in-process-api-and-static-ui-contract-smoke`.

Artefactos incorporados:

```text
src/devpilot_core/release_candidate/ui_api_smoke.py
docs/schemas/ui_api_rc_smoke_report.schema.json
tests/test_post_h_026_ui_api_rc_smoke.py
tests/test_post_h_026_ui_api_rc_smoke_contract.py
docs/audits/post_h_026_c_ui_api_rc_smoke_report.md
docs/post_h_026_c_manifest.json
```

Comando principal:

```powershell
python -m devpilot_core release-candidate ui-api-smoke --base-url http://127.0.0.1:8787 --json
python -m devpilot_core release-candidate ui-api-smoke --base-url http://127.0.0.1:8787 --json --write-report
python -m devpilot_core schema validate --schema-id UiApiRcSmokeReport --instance outputs/reports/ui_api_rc_smoke_report.json --json
```

La primera versión valida condiciones RC sin abrir sockets ni requerir navegador real: `localhost/loopback`, bloqueo de bind no-local, token en rutas protegidas, CORS sin wildcard, security posture redacted, operator dashboard protegido, contratos API/UI, estados UI `loading/empty/error/BLOCK` y bloqueo de acción no-go simulada vía PolicyEngine. No habilita remote execution, connector write, plugin execution, external APIs ni acciones destructivas.

Limitación explícita: Playwright o navegador visual real queda como hardening futuro opcional. POST-H-026-D sigue encargado de install smoke y POST-H-026-E del reporte final PASS/BLOCK.
