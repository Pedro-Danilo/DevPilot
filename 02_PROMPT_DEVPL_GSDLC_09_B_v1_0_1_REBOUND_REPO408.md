---
doc_id: "PROMPT-DEVPL-GSDLC-09-B"
title: "DEVPL-GSDLC-09-B — Bounded Code/File Workspace Viewer-Editor"
status: "approved"
version: "1.0.1"
owner: "Ordóñez"
updated: "2026-09-07"
approval: "approved_by_owner/rebound_repo408_frx_v2_4"
precondition: "GSDLC-09-A CLOSED/PASS/WINDOWS-VALIDATED"
base_authority_repo: "repo_DevPilot_Local_408_DEVPL_GSDLC_09_A_STORY_EXECUTION_CONTEXT_WINDOWS_VALIDATED_CANDIDATE.zip"
base_authority_commit: "fede10c963d7af571fc0fd062f76323d647877f7"
base_authority_sha256: "c077fcba424527a179773e9f2b155700c357fecd0e7d9af8e40533374d290e59"
execution_source_policy: "successor-of-GSDLC-09-A/repo408"
frx_execution_profile_id: "frx-v2.4-current"
frx_execution_profile_sha256: "2339df5fd79134fa8a675092e71ed71c8c11300b46747f055e86628e72679219"
full_regression_runs_allowed: 0
browser_required: true
---

# 02 — GSDLC-09-B

> **Execution rebind 2026-09-07.** Ejecutar exclusivamente sobre `repo_DevPilot_Local_408_DEVPL_GSDLC_09_A_STORY_EXECUTION_CONTEXT_WINDOWS_VALIDATED_CANDIDATE.zip` / `fede10c963d7af571fc0fd062f76323d647877f7` / SHA-256 `c077fcba424527a179773e9f2b155700c357fecd0e7d9af8e40533374d290e59`. FRX-v2.4 current profile `frx-v2.4-current` permanece obligatorio; este micro-sprint consume `full=0` y exige browser acceptance real.


Implementa exclusivamente el Code Workbench manual con source tree bounded, text viewer/editor y SourceDraftBuffer.


## Política transversal obligatoria

- Ingeniería acumulativa: nunca retroceder a un repo histórico para simplificar.
- Source authority: usar el successor Windows-validado inmediatamente anterior.
- No `reset --hard`, `git clean`, force push ni eliminación de `.git`.
- Operador Windows reentrante, Python preferido; cada comando PowerShell termina PASS verde o BLOCK rojo.
- API/UI solo si el micro-sprint requiere browser; si se requieren, exactamente tres consolas y ambos procesos foreground.
- Runtime stores (`auth.db*`, `devpilot.db*`, equivalentes) y secretos quedan fuera de fixtures/evidence/packages.
- LF/CRLF no puede producir BLOCK; comparar semánticamente.
- Historical Contract Authority y Contract Reconciliation Sweep son precondiciones de cierre.
- No editar tests históricos solo para hacerlos pasar: clasificar `historical-freeze/current-active/successor-needed/deprecated-after-proof/derived/runtime-ephemeral`.
- FRX low-level knobs no pertenecen al operador GSDLC. El profile current-active es autoridad.


## Invariantes de seguridad

- ningún draft modifica source antes de apply gobernado;
- workspace-root enforcement server-side;
- path traversal, symlink escape, hidden/secret files, binary y oversize bloqueados;
- create/edit/rename solo allowlisted;
- external edit invalida preimage/draft;
- no arbitrary executable upload;
- editor no se convierte en shell/IDE con terminal.

## Browser

Demostrar:
1. abrir story/context;
2. navegar source allowlisted;
3. editar en draft;
4. source real permanece sin cambio;
5. external edit/conflict visible;
6. path escape negativo;
7. role/capability negative pertinente.

Tres consolas foreground si hay runtime browser.

## Regresión

No full. Focal + security/path tests + Test Impact + acumulativa A-B + contract reconciliation.

PASS: manual authoring UI completo, zero uncontrolled write, S0/S1=0.
