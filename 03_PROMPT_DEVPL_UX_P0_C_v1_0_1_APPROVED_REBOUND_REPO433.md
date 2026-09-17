---
doc_id: "PROMPT-DEVPL-UX-P0-C"
title: "DEVPL-UX-P0-C — Greenfield critical-path surface productization"
status: "approved"
version: "1.0.1"
owner: "Ordóñez"
updated: "2026-09-15"
approval: "approved_by_owner"
precondition: "UX-P0-B CLOSED/PASS/WINDOWS-VALIDATED"
execution_source_policy: "immediate Windows-validated successor of UX-P0-B"
source_repo: "repo_DevPilot_Local_433_DEVPL_UX_P0_B_PROJECT_CONTEXT_AUTH_SCOPE_CORRECTIVE_WINDOWS_VALIDATED_CANDIDATE.zip"
source_git_commit: "dc63672f2d617968998f3c68374a03581b348578"
source_repo_sha256: "f4415775bd3bf5a01b6368197d0754374de93b659fa5f6bbff8b7a2b8ead4246"
successor_expected: "repo_DevPilot_Local_434_DEVPL_UX_P0_C_GREENFIELD_CRITICAL_PATH_WINDOWS_VALIDATED_CANDIDATE.zip"
source_backlog: "DEVPL_UX_P0_PRE_PILOT_PRODUCTIZATION_BACKLOG_v1_0_1_APPROVED_REBOUND_REPO433.md"
full_regression: "PROHIBITED"
---

# Owner approval / rebound — 2026-09-15

Este prompt queda rebindeado a repo433. La numeración successor original `repo433` para C queda superseded porque repo433 fue consumido por el correctivo final de UX-P0-B; UX-P0-C debe producir repo434.

# Objetivo

Productizar el tramo que usará primero el greenfield pilot: Home → Create/Open/Import → Project Status → Pre-code/Documents → Planning.

## Implementación requerida

1. Project Home: una primaria clara; separar create/open/import; mostrar resume/recovery sin densidad diagnóstica inicial.
2. Project Entry: plan/dry-run/approval/execute representados como secuencia comprensible; explicar efectos antes de aprobación.
3. Project Status: convertirlo en centro operacional con stage/progress, blocker explanation, next action y señales de control progresivas.
4. Pre-code: stage stepper coherente, criterios ready/block y clear next action; no mostrar raw authority como copy principal.
5. Documents entry/overview: mejorar orientación y estados sin refactor profundo de todos los editores.
6. Planning: jerarquía roadmap→backlog→sprint, primary action única por estado y review claro antes de mutar.
7. Aplicar copy contract Guided: lenguaje simple primero; término técnico y reason code en disclosure/Expert.
8. Aplicar common page header/stage navigation definidos en B.
9. Mantener `plan → dry-run → approval → execute → verify → evidence`.
10. No introducir shortcuts que permitan saltar gates obligatorios.

## Script de aceptación parcial

Un usuario no experto debe poder iniciar en Home y llegar al planning preparado, respondiendo visualmente: proyecto, etapa, pendiente, blocker, next action, efecto de aprobación y recovery.

## Tests mínimos

- targeted browser Home/Entry/Status/Pre-code/Documents/Planning;
- owner + role-negative;
- keyboard path;
- route/API parity;
- relevant smoke tests existentes;
- Test Impact/docs/TCR.

## PASS

Critical path inicial completo sin terminal externo; siete preguntas respondibles; no policy drift; Full=0.

## BLOCK

Usuario necesita JSON/documentación externa para entender la siguiente acción, route/API mismatch, approvals ambiguos, mandatory gate bypass o Full ejecutada.

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
