---
doc_id: "PROMPT-DEVPL-UX-P0-E"
title: "DEVPL-UX-P0-E — Pre-pilot browser, usability and regression closure"
status: "approved"
version: "1.0.1"
owner: "Ordóñez"
updated: "2026-09-17"
approval: "approved_by_owner"
precondition: "UX-P0-D CLOSED/PASS/WINDOWS-VALIDATED on repo_DevPilot_Local_435_DEVPL_UX_P0_D_CROSS_SURFACE_OPERATIONAL_PATTERNS_WINDOWS_VALIDATED_CANDIDATE.zip"
execution_source_policy: "immediate successor of UX-P0-D"
execution_source_repo: "repo_DevPilot_Local_435_DEVPL_UX_P0_D_CROSS_SURFACE_OPERATIONAL_PATTERNS_WINDOWS_VALIDATED_CANDIDATE.zip"
execution_source_commit: "f1e4c5b8dc1882f7dc724ba87755cdd894f274c8"
execution_source_sha256: "3b07e305c1acf2980f9299d09a1f78c90f6420a070b9b57c3ad24d083fa32805"
full_regression_budget: "exactly one logical Full for DEVPL-UX-P0"
successor_expected: "repo436"
---

# Baseline rebound

UX-P0-D cerró con evidencia Windows/browser PASS sobre repo435. El `successor_expected: repo435` del artefacto histórico E queda superseded por este rebound porque repo435 fue consumido por D; E parte exclusivamente de repo435 y produce repo436. Repo430 permanece cierre histórico inmutable.

# Objetivo

Cerrar UX-P0 con evidencia real-browser/usability/a11y/performance y una única Full, produciendo el RC pre-pilot que autorice el greenfield E2E.

## Orden irreversible

1. A-D CLOSED/PASS/WINDOWS-VALIDATED.
2. UX-S0/S1=0.
3. Source delta/Test Impact sin unmatched.
4. HCA + Contract Reconciliation PASS.
5. Project State/Source Registry/README/current frontend metadata coherentes.
6. Browser matrix PASS.
7. No-tech usability gate PASS.
8. Accessibility critical path PASS.
9. Performance budget PASS o owner-justified sin critical regression.
10. FRX current profile/preflight PASS.
11. Full budget 0/1.
12. Ejecutar exactamente una logical Full.

## Browser matrix mínima

- initialized-first-run state + login/home;
- create/open/import;
- project context + status + next action;
- pre-code/documents/planning;
- story/code + diff/approval;
- jobs/quality;
- release;
- recovery/reconciliation;
- AI/provenance;
- Guided/Expert parity;
- owner + negative authorization guard;
- keyboard/focus;
- desktop + bounded tablet/mobile viewport checks.

## Usability gate

Un usuario beginner-medio debe completar el scripted journey sin terminal externo y poder contestar las siete preguntas UX-P0. Registrar time-to-next-valid-action, confused/block moments, first-attempt success y confidence.

## Full policy

- una sola logical Full;
- infra interruption: resume misma sesión solo sobre UNEXECUTED;
- functional FAIL/ERROR: `PRESERVE/NO-RERUN/COMPOSITE-RECOVERY`;
- recovery posterior: exact failed/error + bounded impacted + Historical Regression Guard + post-gates; nunca una segunda Full;
- segunda Full = 0.

## Packaging

Generar repo436 desde closure commit exacto, tracked-only, sin `.git`, `.venv`, outputs, caches, node_modules, runtime DBs ni secretos. Clean-install/smoke final obligatorio.

## PASS

UX-S0/S1=0; terminal escapes normal journey=0; browser/usability/a11y/perf PASS; Full o composite 100% accounted/PASS; second Full=0; RC exact-commit limpio.

## BLOCK

Normal journey depende de terminal externo, critical a11y blocker, policy/authority drift, second Full, stale evidence/hash mismatch, Full con functional FAIL pendiente de recovery, o RC contaminado.

## Reglas transversales obligatorias

- Python preferido para operador Windows; una sola guía `.md`, pasos consecutivos y PowerShell de una línea.
- dry-run por defecto para mutaciones sensibles; no reset-hard, git clean, force push, rebase destructivo, publish ni deploy remoto.
- LF/CRLF no es autoridad; usar Git-semantic/EOL-normalized comparisons.
- No dependencia frontend/runtime nueva.
- Route IDs, APIs, RBAC, approvals y server authority permanecen invariantes.
- Guided/Expert difieren en densidad, nunca en permisos.
- Full se consume exactamente una vez y solo después de los gates baratos.
