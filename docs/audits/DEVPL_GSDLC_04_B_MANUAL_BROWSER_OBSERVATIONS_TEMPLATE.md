---
doc_id: "DEVPL-GSDLC-04-B-MANUAL-BROWSER-OBSERVATIONS"
title: "DEVPL-GSDLC-04-B — Plantilla de observaciones browser Windows"
status: "template/ready-for-windows"
version: "1.0.8"
owner: "Ordóñez"
updated: "2026-08-21"
approval: "pending_execution"
---

# DEVPL-GSDLC-04-B — Observaciones browser Windows v1.0.8

> Archivo exclusivo de la ejecución v1.0.8. Las observaciones de guías anteriores se conservan como evidencia histórica y **no se copian ni se interpretan automáticamente**. No registre tokens, passwords, cookies, `.env`, API keys ni otros secretos.

## Identidad de ejecución

- Fecha/hora:
- Operador:
- Repo/commit antes del commit 04-B:
- ZIP de implementación SHA-256:
- Browser/versión:
- Ruta del fixture: `D:\Projects\DevPilot_E2E_Evaluation\worktrees\DEVPL_GSDLC_04_B_BROWSER`

## Matriz de resultados — EDITE SOLO LAS COLUMNAS Resultado y Observación

<!-- BEGIN_BROWSER_MATRIX -->
| Caso | Resultado PASS/BLOCK | Evidencia | Observación |
|---|---|---|---|
| Open Existing / PathGuard fixture | | `00_project_entry_fixture_open.png` | |
| Editor Markdown carga | | `01_editor_markdown_loaded.png` | |
| Autosave | | `02_autosave_saved.png` | |
| Recovery tras restart | | `03_restart_recovery.png` | |
| Version history | | `04_version_history.png` | |
| Discard + recover | | `05_discard_recover.png` | |
| JSON hints | | `06_json_hint.png` | |
| Conflict/stale preimage | | `07_conflict_banner.png` | |
| Project route guard | | `08_project_guard.png` | |
| Source no cambia al guardar draft | | `12_markdown_source_hash_during_draft.json` | |
| Sesión/RBAC | | `09_session_rbac.png` opcional + observación | |
<!-- END_BROWSER_MATRIX -->

## Cómo completar la matriz

- En **Resultado PASS/BLOCK** escriba únicamente `PASS` o `BLOCK`.
- En **Observación** escriba una frase corta describiendo exactamente lo que vio.
- Si una fila es `BLOCK`, detenga los pasos que dependan de ella y conserve evidencia.
- No cambie el texto de la columna **Caso** ni los nombres de **Evidencia**.
- `09_session_rbac.png` es opcional; la fila Sesión/RBAC y su observación sí son obligatorias.
- Antes de guardar una captura, revise toda la imagen y descarte cualquier captura que exponga un secreto.

## Resultado operativo — COMPLETE ESTOS SIETE CAMPOS AL FINAL

<!-- BEGIN_BROWSER_SUMMARY -->
- `browser_acceptance`:
- `S0_open`:
- `S1_open`:
- `secrets_exposed`:
- `network_runtime_used`:
- `external_api_used`:
- `pilot_workspace_accessed`:
<!-- END_BROWSER_SUMMARY -->

Para un cierre PASS-CANDIDATE, los siete campos anteriores deben reflejar: aceptación PASS; cero S0 y S1; ningún secreto expuesto; sin network runtime ni API externa; y sin acceso al workspace piloto. Esta frase es solo una referencia humana y **no es parseada por el harness**.

## Firma/decisión del owner

- Decisión:
- Justificación:
