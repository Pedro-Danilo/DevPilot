---
doc_id: "PROMPT-DEVPL-UX-P0-B"
title: "DEVPL-UX-P0-B — Product App Shell, grouped navigation and persistent project context"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-09-15"
approval: "approved_by_owner"
precondition: "UX-P0-A CLOSED/PASS/WINDOWS-VALIDATED"
source_repo: "repo_DevPilot_Local_431_DEVPL_UX_P0_A_AUTHORITY_DESIGN_SYSTEM_FOUNDATION_WINDOWS_VALIDATED_CANDIDATE.zip"
source_git_commit: "013cc84f0df9eff1fb750b542644bfd0c7dc8717"
source_repo_sha256: "be80b6490cbbbfc7b5827fa896cbe5528a2b2d3676fb6c2ceef672820ee2f097"
execution_source_policy: "immediate successor of UX-P0-A"
full_regression: "PROHIBITED"
---

# Owner approval — 2026-09-15

El owner autoriza la implementación de DEVPL-UX-P0-B sobre el successor Windows-validado de UX-P0-A.

# Objetivo

Reestructurar el chrome transversal de DevPilot para que navegación, project context, etapa y next action sean comprensibles sin debilitar guards ni autoridad server-side.

## Implementación requerida

1. Extraer de `main.ts` únicamente catálogos/helpers de presentation necesarios para reducir acoplamiento; no sustituir el router probado por una librería nueva.
2. Implementar navegación agrupada por dominios: Start, Understand & Plan, Build & Validate, Release, Recover, AI, Diagnostics y Global.
3. Mantener los mismos paths/route IDs y progressive-disclosure guards.
4. Implementar breadcrumbs/location context derivados del catálogo de rutas.
5. Convertir Project Context en región persistente del shell para rutas project-scoped: project/workspace, stage, state, blocker/revalidation y recovery indicator.
6. Proyectar authoritative Next Action desde server state cuando exista; fail-closed/fallback explícito cuando no exista.
7. Integrar Session y Guided/Expert dentro del shell sin que dominen el viewport.
8. Mover route ID/raw path/TTL/diagnósticos a Expert o Evidence/Diagnostics; Guided conserva solo información accionable.
9. Resolver responsive navigation para desktop/tablet/mobile; targets >=44px en controles críticos.
10. Preservar approval handoff y recovery redirects exactos.

## Tests mínimos

- auth first-run/login/logout;
- route guards home/entry/project;
- project-entry approval handoff;
- session-bound recovery;
- keyboard/focus navigation;
- responsive targeted browser;
- route registry enforcement;
- Test Impact, docs/TCR.

## PASS

En cualquier ruta project-scoped el usuario identifica proyecto, etapa, estado y next action; ninguna ruta/authority cambia; Full=0.

## BLOCK

Route guard bypass, browser-only authority, duplicate project context contradictory, mobile navigation unusable, a11y critical blocker o Full ejecutada.

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
