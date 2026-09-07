---
doc_id: "PROMPT-DEVPL-GSDLC-09-A"
title: "DEVPL-GSDLC-09-A — StoryExecutionState and StoryContextPack"
status: "approved"
version: "1.0.1"
owner: "Ordóñez"
updated: "2026-09-06"
approval: "approved_by_owner/rebound_repo406_frx_v2_4"
precondition: "GSDLC-09 activation/rebind CLOSED/PASS"
base_authority_repo: "repo_DevPilot_Local_406_FRX_V2_4_B_EXECUTION_PROFILE_LOCK_WINDOWS_VALIDATED_CANDIDATE.zip"
base_authority_commit: "6b8a9a5feef65860826904444f651421abad282a"
base_authority_sha256: "59c40713182b84655315773654e49adf95419ceb517ec9496929252fba33b191"
execution_source_policy: "activation-successor-of-repo406"
frx_execution_profile_id: "frx-v2.4-current"
frx_execution_profile_sha256: "2339df5fd79134fa8a675092e71ed71c8c11300b46747f055e86628e72679219"
full_regression_runs_allowed: 0
browser_policy: "only if Project Status integration cannot be proven without browser; otherwise 0"
---

# 01 — GSDLC-09-A

Implementa exclusivamente StoryExecutionState, StoryContextPack, DoR evaluator e integración current story en Project Status.


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


## Contratos

StoryExecutionState:
`PLANNED → IN_PROGRESS → CHANGES_READY → VALIDATING → COMMIT_READY → DONE`.

DoR debe bloquear antes de IN_PROGRESS si faltan requirement, acceptance criteria, test intent, risk/ADR binding requerido
o project context server-validado.

StoryContextPack debe:
- minimizar contexto;
- incluir provenance por fragmento;
- hash determinista;
- excluir secretos/runtime stores;
- distinguir source files candidatos de autoridad para escribir.

## Pruebas

- state transition matrix;
- invalid transition;
- missing DoR;
- context hash determinism;
- requirement/ADR/risk/test trace;
- secret/runtime exclusion;
- project status current story;
- historical/current contract sweep.

## Regresión

No full. Ejecutar focal + Test Impact + acumulativa 08→09-A + deterministic gates.
No configurar FRX knobs.

## Entregables

schema, service, fixture, DoR report, Test Impact, implementation report, Windows bundle y evidence.

PASS: story no inicia sin DoR, context completo/trazable, S0/S1=0.
