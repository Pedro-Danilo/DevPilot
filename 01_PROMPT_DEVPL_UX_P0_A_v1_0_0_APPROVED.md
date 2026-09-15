---
doc_id: "PROMPT-DEVPL-UX-P0-A"
title: "DEVPL-UX-P0-A — Authority rebind, frontend identity and design-system foundation"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-09-15"
approval: "approved_by_owner"
source_repo: "repo_DevPilot_Local_430_DEVPL_GSDLC_12_E_LOCAL_RC_WINDOWS_VALIDATED_CANDIDATE.zip"
source_git_commit: "a415504bbf021566243ef4000b1a27d4c8846fee"
source_repo_sha256: "969f7d6b8cbdd8eb3bc32491718e94ee41295647e82234779aee180cea2a388a"
precondition: "DEVPL-POST-GSDLC-GIT-REMOTE-SYNC/CLOSED-PASS-WINDOWS-VALIDATED"
full_regression: "PROHIBITED"
---

# Owner approval — 2026-09-15

El owner aprueba este artefacto como autoridad operativa para DEVPL-UX-P0. Repo430 permanece inmutable; toda mutación inicia en su successor.

# Objetivo

Crear el primer successor de repo430 para activar UX-P0, absorber el drift current-active S3 ya identificado y establecer una base de design system/IA antes de modificar el App Shell.

## Implementación requerida

1. Verificar repo430/commit/SHA y evidencia de Git remote sync PASS.
2. Crear worktree/branch UX-P0-A desde el closure commit sin modificar repo430.
3. Incorporar en `docs/00_product` los documentos owner-approved `DEVPL_POST_GSDLC_TRANSITION_DECISION_v1_0_0_APPROVED.md` y `DEVPL_UI_UX_PRODUCTIZATION_STRATEGY_v1_0_0_APPROVED.md`.
4. Reconciliar Project State, Source Registry, README/roadmap/CURRENT y frontmatter current-active que aún describan GSDLC-12 como programa en curso. Preservar snapshots históricos.
5. Reconciliar `ui/web/package.json` current-active metadata para que describa el frontend post-GSDLC/UX-P0 sin reescribir hechos históricos.
6. Materializar `DEVPL_UX_P0_FRONTEND_NAVIGATION_AUDIT_v1_0_0.md` y baseline JSON como fuentes del backlog.
7. Crear semantic design tokens: color roles, typography scale, spacing, radius, elevation, focus y states PASS/WARN/BLOCK/ERROR/PENDING/RECOVERY.
8. Reducir hardcoded styling solo donde sea necesario para adoptar tokens base; no ejecutar todavía rediseño masivo de vistas.
9. Documentar target IA y shell contract. Crear ADR únicamente si la extracción shell/navigation cambia arquitectura; no crear ADR por detalles cosméticos.
10. Actualizar route/current registries solo si el contrato current-active lo requiere; nunca editar snapshots `*_at_close`.

## Tests mínimos

- UI build/smoke;
- route enforcement;
- UOC/GSDLC accessibility smoke;
- browser state matrix contract;
- Project State/docs governance/TCR;
- Test Impact con unmatched=0;
- visual baseline targeted para demostrar que tokens no rompieron rutas.

## Evidencia

- authority rebind report;
- frontend metadata reconciliation report;
- design token inventory;
- route/IA baseline;
- Test Impact;
- historical/current contract classification;
- minimal browser screenshots si cambió render visible.

## PASS

Autoridad successor coherente, docs approved materializados, drift S3 corregido, tokens/IA contract disponibles, guards y rutas sin regresión, Full=0.

## BLOCK

Mutar/reempaquetar repo430, cambiar route authority por estética, unmatched path, policy drift, dependencia externa injustificada o Full ejecutada.

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
