---
doc_id: "PROMPT-DEVPL-GSDLC-09-E"
title: "DEVPL-GSDLC-09-E — Story-level browser acceptance, rollback and one-full closure"
status: "approved"
version: "1.0.1"
owner: "Ordóñez"
updated: "2026-09-08"
approval: "approved_by_owner"
precondition: "GSDLC-09-D CLOSED/PASS/WINDOWS-VALIDATED"
full_regression_budget: "exactly 1 logical full for backlog GSDLC-09 unless already consumed by owner-approved hard trigger"
frx_execution_policy: "mandatory current-active FullRegressionExecutionProfile from FRX-v2.4"

source_repo: "repo_DevPilot_Local_411_DEVPL_GSDLC_09_D_CODING_TEST_AGENTS_WINDOWS_VALIDATED_CANDIDATE.zip"
source_git_commit: "bef575da644f7280d6d31a044d3993f0c5d50a74"
source_repo_sha256: "44bf18817faff0832962e800bca7a21b0c2ff65df5075858c7b1f0678c85c2b1"
source_repo_role: "current-approved-GSDLC-09-D-Windows-validated-predecessor"
frx_profile_id: "frx-v2.4-current"
frx_profile_sha256: "2339df5fd79134fa8a675092e71ed71c8c11300b46747f055e86628e72679219"
---

# 05 — GSDLC-09-E

Cierra la ola demostrando una story real hasta `CHANGES_READY` por ruta manual y agent-assisted,
con apply/rollback/conflict y Project Status coherente.


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


## Orden irreversible

Antes de reservar full:

1. A-D CLOSED/PASS/WINDOWS-VALIDATED.
2. Browser/capability acceptance PASS.
3. Story reaches CHANGES_READY.
4. Apply/rollback evidence PASS.
5. S0/S1=0.
6. Historical Contract Authority PASS.
7. Contract Reconciliation Sweep PASS.
8. Project State / Source Registry / README / roadmap CURRENT coherentes.
9. Runtime-ephemeral exclusion PASS.
10. FRX-v2.4 preflight PASS.
11. Full budget 0/1.
12. Profile hash/version current acreditado.
13. Topology compatibility PASS.
14. Isolation/Duration registry schema+coverage PASS.
15. ETA y projected topology registrados.

Solo entonces consumir la única logical full.

## Prohibiciones

- El operador 09-E no puede pasar `max_nodeids`, planner, nodeid transport ni workers directos.
- No segunda full después de FAIL funcional.
- No cambiar plan/collection/profile a mitad de sesión.
- Interrupción de infraestructura: resume misma session, solo UNEXECUTED.

## FAIL recovery

Si la full completa con FAIL/ERROR funcional:
- preservar full original inmutable;
- exact failed/error nodeid retest;
- bounded impacted retest;
- Historical Regression Guard;
- post-recovery gates;
- composite adjudication;
- no full rerun.

## Browser mínimo

- manual story path;
- agent-assisted proposal path;
- approved SourceChangePlan;
- atomic apply;
- rollback;
- external-edit conflict;
- Project Status/Story state;
- negative wrong-role/path/tool authority;
- screenshots únicas y machine-readable verifier.

## PASS backlog 09

- manual+agent proposal;
- governed apply;
- rollback clean;
- source writes bounded/reproducible;
- browser complete;
- full/composite 100% accounted;
- 0 FAIL/ERROR terminal;
- S0/S1=0.

Salida: CLOSED/PASS y autorización de GSDLC-10.

## Execution rebind 2026-09-08

La única autoridad de ejecución es repo411. Full Regression: exactamente una logical session gobernada por el current profile después de browser/gates; no se permiten low-level overrides ni segunda full.
