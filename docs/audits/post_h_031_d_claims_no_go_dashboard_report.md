---
doc_id: POST-H-031-D-CLAIMS-NO-GO-DASHBOARD-REPORT
title: "POST-H-031-D - Claims and no-go dashboard"
status: approved
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-07-10"
approval: approved
---

# POST-H-031-D — Claims and no-go dashboard

## Decisión

PASS implementado como `implemented-initial/local-first/read-only`.

## Alcance implementado

Se agregó una vista operacional para claims y no-go gates que consolida criterios POST-H-025, project state, EvidenceGraph y ProductionReadyClaimsValidator. La vista presenta claims permitidos, condicionados y prohibidos; no-go gates activos; evidencia soporte; razones de bloqueo; relación con `production_ready_local_report`; y estado del escaneo determinístico de overclaims en documentos clave.

## Artefactos

- `docs/schemas/claims_no_go_dashboard.schema.json`
- `.devpilot/operator/claims_no_go_dashboard_config.json`
- `src/devpilot_core/evidence_graph/claims_dashboard.py`
- `tests/test_post_h_031_claims_no_go_dashboard.py`
- `docs/post_h_031_d_manifest.json`

## Seguridad

La implementación no muta claims, no muta no-go gates, no ejecuta comandos recomendados, no usa LLM judge, no lee secretos, no lee `.devpilot/devpilot.db`, no usa red, no usa APIs externas y no habilita remote execution, connector write ni plugin execution.

## Límites

Esta primera versión es una vista operacional, no una declaración nueva de readiness. `audit-friendly` queda condicionado a auditoría técnica interna y no implica certificación. La UI visual queda pendiente salvo consumo vía API local protegida.

## Verificación focal

```powershell
python -m pytest -p no:ddtrace --assert=plain tests/test_post_h_031_claims_no_go_dashboard.py -q
python -m devpilot_core evidence claims-dashboard --json
python -m devpilot_core evidence claims-dashboard --json --write-report
python -m devpilot_core schema validate --schema-id ClaimsNoGoDashboard --instance outputs/reports/claims_no_go_dashboard.json --json
```

## PASS/BLOCK

PASS exige claims prohibidos bloqueados, no-go gates visibles, evidencia soporte concreta, schema válido, ApplicationService/API local protegida y cero mutaciones. BLOCK aplica si un claim prohibido aparece disponible, si un no-go gate violado se oculta, si hay claim permitido sin evidencia, o si la vista intenta modificar claims/gates.
