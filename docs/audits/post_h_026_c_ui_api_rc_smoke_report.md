---
doc_id: "DEVPL-AUDIT-POST-H-026-C-UI-API-RC-SMOKE"
title: "POST-H-026-C — UI/API local RC smoke report"
status: "implemented-initial"
version: "1.0.0"
owner: "Ordonez"
updated: "2026-07-08"
approval: "pending-owner-review"
---

# POST-H-026-C — UI/API local RC smoke report

## Implementado

- Schema `UiApiRcSmokeReport` para evidencia local de smoke UI/API RC.
- Módulo `src/devpilot_core/release_candidate/ui_api_smoke.py`.
- CLI `python -m devpilot_core release-candidate ui-api-smoke --base-url http://127.0.0.1:8787 --json`.
- Pruebas `tests/test_post_h_026_ui_api_rc_smoke.py` y `tests/test_post_h_026_ui_api_rc_smoke_contract.py`.
- Registro en schema catalog, TCR v1/v2, source registry, README, runbook, backlog y project state.

## Estado

`implemented-initial / in-process-api-and-static-ui-contract-smoke`.

La versión actual valida la superficie de operador mediante `FastAPI TestClient` y revisión estática de `ui/web/src`. No abre sockets, no ejecuta navegador real por defecto, no usa red ni APIs externas y no escribe reportes salvo con `--write-report`.

## PASS

- Base URL `localhost/loopback`.
- Bind no-local `0.0.0.0` bloqueado por el guard existente.
- Rutas protegidas requieren token.
- CORS no admite wildcard ni origen remoto.
- `security posture` no expone token raw.
- `operator dashboard` responde protegido.
- Contratos API/UI mantienen no-go flags deshabilitados.
- UI declara estados `loading`, `empty`, `error` y `BLOCK`.
- PolicyEngine bloquea una acción no-go simulada desde UI/API.

## BLOCK

- Base URL no-local.
- CORS wildcard o remoto permitido.
- Ruta protegida sin token.
- Token raw o secreto visible en respuesta/UI.
- UI lee `.devpilot` u `outputs/` directamente.
- Acción no-go no bloqueada.

## Riesgos y límites

- No sustituye pruebas visuales reales con navegador; esa evolución puede añadirse en hardening posterior.
- No verifica instalación local ni empaquetado limpio; eso pertenece a POST-H-026-D.
- No declara release candidate final; el cierre PASS/BLOCK queda reservado para POST-H-026-E.

## Verificación focal

```powershell
python -m pytest -p no:ddtrace --assert=plain tests/test_post_h_026_ui_api_rc_smoke.py tests/test_post_h_026_ui_api_rc_smoke_contract.py tests/test_post_h_014_api_route_contracts.py tests/test_post_h_014_security_hardening.py -q
python -m devpilot_core release-candidate ui-api-smoke --json
python -m devpilot_core release-candidate ui-api-smoke --json --write-report
python -m devpilot_core schema validate --schema-id UiApiRcSmokeReport --instance outputs/reports/ui_api_rc_smoke_report.json --json
npm --prefix ui/web test
```
