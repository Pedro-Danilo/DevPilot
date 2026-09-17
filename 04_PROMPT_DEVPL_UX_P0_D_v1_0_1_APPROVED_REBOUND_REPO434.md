---
doc_id: "PROMPT-DEVPL-UX-P0-D"
title: "DEVPL-UX-P0-D — Cross-surface operational patterns and progressive evidence"
status: "approved"
version: "1.0.1"
owner: "Ordóñez"
updated: "2026-09-15"
approval: "approved_by_owner"
precondition: "UX-P0-C CLOSED/PASS/WINDOWS-VALIDATED on repo_DevPilot_Local_434_DEVPL_UX_P0_C_GREENFIELD_CRITICAL_PATH_WINDOWS_VALIDATED_CANDIDATE.zip"
execution_source_policy: "immediate successor of UX-P0-C"
full_regression: "PROHIBITED"
---

# Baseline rebound

Fuente obligatoria: `repo_DevPilot_Local_434_DEVPL_UX_P0_C_GREENFIELD_CRITICAL_PATH_WINDOWS_VALIDATED_CANDIDATE.zip` / `75dbead73c6c6aaf1f792e02f3659ee2b6c0b927` / `e1117ba5e9c3bace2de482940d6b447b0150acb2e26ba1647f9677939f5faf39`. Successor esperado: `repo435`; UX-P0-E se rebindea a `repo436`.

# Objetivo

Normalizar los patrones que se repiten en Workbenches, approvals, jobs, quality, release, recovery y AI para que estados/acciones/evidencia tengan la misma semántica visual.

## Implementación requerida

1. Crear primitives/patterns mínimos y reutilizables para OperationState, PrimaryAction, GateSummary, ApprovalSummary, DiffSummary, LongRunningOperation y progressive Evidence/Diagnostics.
2. Estados mínimos: loading, empty, ready, pending, running, success/PASS, warn, block, error, recovery/stale/revalidation cuando aplique.
3. La jerarquía visual debe distinguir claramente primary action, secondary safe actions y destructive/blocked actions.
4. Evidence permanece accesible y hash/provenance visible cuando importe, pero no domina Guided.
5. Aplicar prioritariamente a Story/Code, Approvals, Jobs, Quality y Release.
6. Integrar Recovery/Reconciliation con mensajes consistentes y acciones seguras.
7. Integrar AI Control Center/AI-RAG sin ocultar provider/policy/provenance importantes.
8. Reports/Traces permanecen diagnostic-heavy y preferentemente Expert; no rediseño exhaustivo.
9. Asegurar responsive density y keyboard/focus.
10. Reducir duplicación CSS solo dentro del delta impactado; no emprender cleanup total no relacionado.

## Tests mínimos

- Story source-change/test/git smoke impacted;
- approval/action flows;
- Jobs/Quality;
- Release readiness/package/lifecycle/closure impacted;
- recovery/reconciliation;
- AI/RAG policy parity;
- a11y targeted;
- browser matrix focal;
- Test Impact/docs/TCR.

## PASS

El mismo estado y tipo de acción se interpreta igual entre superficies; blockers críticos visibles; evidence progresiva; policy parity; Full=0.

## BLOCK

Hidden blocker/destructive action, inconsistent PASS/BLOCK semantics, authority moved to UI, evidence loss, S0/S1 UX o Full ejecutada.

## Reglas transversales obligatorias

- Partir únicamente del successor Windows-validado inmediato; nunca mutar repo430 directamente.
- Python preferido para operadores Windows.
- Una sola guía `.md` por operador; pasos consecutivos; comandos PowerShell físicamente en una sola línea.
- `dry-run` por defecto para mutaciones sensibles.
- No `reset --hard`, `git clean`, force push, rebase destructivo, publish ni deploy remoto.
- LF/CRLF nunca constituye autoridad de cambio.
- No añadir dependencia frontend/runtime salvo necesidad dura owner-approved.
- Preservar route IDs, API contracts, RBAC, approvals y server authority.
- Guided y Expert no pueden divergir en permisos.
- Browser evidence se repite solo cuando la superficie cambiada lo exija.
- A-D usan Test Impact + focal/impacted; Full rutinaria prohibida. E consume exactamente una logical Full para UX-P0.
- Todo FAIL funcional de esa Full se preserva; no rerun; composite selective recovery.
- Cada cierre registra Git pre/post, S0/S1, UX findings, `network_used`, `external_api_used`, `secrets_exposed`, `mutations_performed`.

## Riesgos que el implementador debe vigilar

- scope creep hacia redesign total;
- regresión de auth/project guards;
- divergencia entre Guided/Expert;
- stale UI metadata/current authority;
- duplicación de patrones en vez de primitives;
- exceso de evidencia en el viewport Guided;
- performance regressions por DOM/CSS;
- false blockers por EOL o parsing de stderr.
