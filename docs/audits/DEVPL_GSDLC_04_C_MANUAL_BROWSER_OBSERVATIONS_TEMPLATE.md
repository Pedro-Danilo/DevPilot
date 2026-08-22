---
doc_id: "DEVPL-GSDLC-04-C-MANUAL-BROWSER-OBSERVATIONS"
title: "DEVPL-GSDLC-04-C — Plantilla de observaciones browser Windows"
status: "template/ready-for-windows"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-08-21"
approval: "pending_execution"
---

# DEVPL-GSDLC-04-C — Observaciones browser Windows

No registre tokens, passwords, cookies, `.env`, API keys ni secretos. El archivo se crea automáticamente en el directorio de evidencia. Edite únicamente la identidad de ejecución, las columnas **Resultado PASS/BLOCK / Observación**, el resumen delimitado y la decisión final.

## Identidad de ejecución

- Fecha/hora:
- Operador:
- Repo/commit antes del commit 04-C: `D:\Projects\DevPilot_Local @ b095bf5b75259c9c7c4a9a5c1b5d546cfe049d6f`
- ZIP de implementación SHA-256: copiar exactamente el campo `package_sha256` mostrado por el bootstrap 04-C
- Browser/versión:
- Ruta del fixture: `D:\Projects\DevPilot_E2E_Evaluation\worktrees\DEVPL_GSDLC_04_C_BROWSER`

## Matriz de resultados — EDITE SOLO Resultado y Observación

<!-- BEGIN_BROWSER_MATRIX -->
| Caso | Resultado PASS/BLOCK | Evidencia | Observación |
|---|---|---|---|
| Open Existing / project context | | `00_project_entry_fixture_open.png` | |
| PASTE preview | | `01_paste_preview.png` | |
| PASTE DRAFT + provenance | | `02_paste_draft_provenance.png` | |
| UPLOAD Markdown DRAFT | | `03_upload_draft_provenance.png` | |
| IMPORT JSON DRAFT | | `04_import_json_provenance.png` | |
| Original/normalized hashes + provenance | | `04_import_json_provenance.png` | |
| Secret warning/redaction | | `05_secret_warning_redacted.png` | |
| Project route guard | | `06_project_guard.png` | |
| Source/workspace files unchanged | | `13_fixture_source_hashes_after.json` | |
| Sesión/RBAC | | `07_session_rbac.png` opcional + observación | |
<!-- END_BROWSER_MATRIX -->

### Cómo diligenciar la matriz

- Escriba únicamente `PASS` o `BLOCK` en la segunda columna.
- La observación debe describir algo que realmente vio; una frase corta es suficiente.
- `07_session_rbac.png` es opcional, pero la comprobación y su observación son obligatorias.
- No cambie los nombres de los casos ni de las evidencias.
- Ante cualquier `BLOCK`, detenga la secuencia que dependa de ese caso y preserve lo ya generado.
- Antes de guardar una captura, revise visualmente toda la imagen. Si contiene un secreto real, no la conserve: repita la captura sin ese dato.

## Resultado operativo — COMPLETE EXACTAMENTE ESTOS SIETE CAMPOS

<!-- BEGIN_BROWSER_SUMMARY -->
- `browser_acceptance`: PENDING
- `S0_open`: PENDING
- `S1_open`: PENDING
- `secrets_exposed`: PENDING
- `network_runtime_used`: PENDING
- `external_api_used`: PENDING
- `pilot_workspace_accessed`: PENDING
<!-- END_BROWSER_SUMMARY -->

Para `PASS-CANDIDATE`, el resumen debe quedar exactamente en: `PASS`, `0`, `0`, `false`, `false`, `false`, `false` respectivamente. Esta frase está fuera del bloque machine-readable y no es interpretada como evidencia.

## Firma/decisión del owner de ejecución

- Decisión: PENDING
- Justificación:
