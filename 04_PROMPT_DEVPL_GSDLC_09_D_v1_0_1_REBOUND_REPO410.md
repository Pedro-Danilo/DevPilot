---
doc_id: "PROMPT-DEVPL-GSDLC-09-D"
title: "DEVPL-GSDLC-09-D — CodingAgent and TestAgent proposal-only integration"
status: "approved"
version: "1.0.1"
owner: "Ordóñez"
updated: "2026-09-08"
approval: "approved_by_owner/rebound_repo410"
source_repo: "repo_DevPilot_Local_410_DEVPL_GSDLC_09_C_SOURCE_CHANGE_APPLY_WINDOWS_VALIDATED_CANDIDATE.zip"
source_git_commit: "311fa063346441d04b805f9e5ea5b004cfcfbb31"
source_repo_sha256: "457b4499b2f5c774ed5a5c99108b0780b1b55e01595ad07591bc02fb87eb0c33"
frx_v2_4_policy: "CLOSED/PASS/WINDOWS-VALIDATED; A-D focal+impact+cumulative; full=0"
precondition: "GSDLC-09-C CLOSED/PASS/WINDOWS-VALIDATED"
full_regression_runs_allowed: 0
browser_required: true
---

# 04 — GSDLC-09-D

Integra CodingAgent y TestAgent como **proposal-only** sobre StoryContextPack/RAG y Model Gateway.


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


## Autoridad

`ModelRouteDecision != ToolExecutionDecision`.

La selección de modelo/provider nunca concede permiso de escribir.
Toda propuesta debe registrar model_id, provider_id, access_route_id, agent_session, trace_id, ToolIntent y provenance.

Agentes:
- no self-apply;
- no self-approve;
- no self-commit;
- no generic shell;
- no `filesystem.delete`;
- bounded tokens/tools/cost;
- mock/local route obligatoria;
- external API opcional, explícita y nunca requisito para PASS.

## Browser

Demostrar manual vs agent-assisted proposal, diff visible, accept/reject humano, cost/provenance y un unsafe proposal bloqueado.

## Regresión

No full. Agent evals + focal + Test Impact + acumulativa A-D + contract reconciliation.

PASS: proposal-only, human-reviewed diff, complete provenance, no authority escalation, S0/S1=0.
