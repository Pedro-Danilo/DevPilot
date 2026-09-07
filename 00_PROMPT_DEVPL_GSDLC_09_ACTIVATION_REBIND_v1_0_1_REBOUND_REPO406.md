---
doc_id: "PROMPT-DEVPL-GSDLC-09-ACTIVATION"
title: "DEVPL-GSDLC-09 — Activation and execution rebind after FRX-v2.4"
status: "approved"
version: "1.0.1"
owner: "Ordóñez"
updated: "2026-09-06"
approval: "approved_by_owner/rebound_repo406"
design_rebind_repo: "repo_DevPilot_Local_404_DEVPL_GSDLC_08_E_FINAL_CLOSURE_RECONCILIATION_WINDOWS_VALIDATED_CANDIDATE.zip"
design_rebind_commit: "c0347423b78c67ed93f9eb4a2af39e0411b1d22f"
design_rebind_sha256: "c90fb00a4416bb62c50e161b1eb837efcf88f88d0d3c19d0c0bcbc9fd47cb767"
requires: "DEVPL-FRX-v2.4=CLOSED/PASS/WINDOWS-VALIDATED"
execution_source_repo: "repo_DevPilot_Local_406_FRX_V2_4_B_EXECUTION_PROFILE_LOCK_WINDOWS_VALIDATED_CANDIDATE.zip"
execution_source_commit: "6b8a9a5feef65860826904444f651421abad282a"
execution_source_sha256: "59c40713182b84655315773654e49adf95419ceb517ec9496929252fba33b191"
frx_execution_profile_id: "frx-v2.4-current"
frx_execution_profile_sha256: "2339df5fd79134fa8a675092e71ed71c8c11300b46747f055e86628e72679219"
functional_mutation_allowed: false
full_regression_runs_allowed: 0
browser_runs_allowed: 0
---

# 00 — Activación y rebind de DEVPL-GSDLC-09

Ejecutar **solo después** de cerrar FRX-v2.4.

Objetivo: usar `repo_DevPilot_Local_406_FRX_V2_4_B_EXECUTION_PROFILE_LOCK_WINDOWS_VALIDATED_CANDIDATE.zip` como successor Windows-validado real de FRX-v2.4, demostrar ancestry desde repo404 y rebíndear
Project State, Source Registry, README, roadmap y el backlog 09 APPROVED a esa autoridad.

No implementar StoryExecutionState ni ninguna función de 09-A todavía.


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


## Trabajo requerido

1. Verificar:
   - GSDLC-08=CLOSED/PASS/WINDOWS-VALIDATED;
   - repo404 SHA/commit;
   - FRX-v2.4=CLOSED/PASS/WINDOWS-VALIDATED;
   - successor FRX-v2.4 es descendiente de `c0347423b78c67ed93f9eb4a2af39e0411b1d22f`.
2. Reconciliar current-active:
   - `gsdlc_current_backlog = DEVPL-GSDLC-09`;
   - `gsdlc_current_micro_sprint = DEVPL-GSDLC-09-A`;
   - backlog 09 = APPROVED/ACTIVE;
   - `frx_execution_profile` apunta al profile current activo de v2.4;
   - repo current = successor FRX-v2.4.
3. Ejecutar Project State/TCR/Docs Governance/Evidence Freshness/API drift.
4. Generar activation/rebind report y owner adjudication.
5. Windows validate sin browser/full.
6. Promover local ff-only y remote no-force solo tras PASS.

## PASS

- rebind coherente;
- ancestry PASS;
- FRX profile binding explícito;
- full=0;
- browser=0;
- S0/S1=0.

Salida: autoriza 09-A.
