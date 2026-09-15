---
doc_id: "DEVPL-UX-P0-FRONTEND-NAVIGATION-AUDIT"
title: "DevPilot — Frontend and navigation audit before UX-P0"
status: "audited"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-09-15"
approval: "accepted_as_execution_input_by_DEVPL-UX-P0-A"
source_repo: "repo_DevPilot_Local_430_DEVPL_GSDLC_12_E_LOCAL_RC_WINDOWS_VALIDATED_CANDIDATE.zip"
source_git_commit: "a415504bbf021566243ef4000b1a27d4c8846fee"
source_repo_sha256: "969f7d6b8cbdd8eb3bc32491718e94ee41295647e82234779aee180cea2a388a"
strategy_binding: "DEVPL_UI_UX_PRODUCTIZATION_STRATEGY_v1_0_0_APPROVED"
audit_scope: "actual repo430 frontend / route registries / navigation / shell / styles / browser evidence"
---

# DevPilot — auditoría real de frontend y navegación previa a UX-P0

## 1. Objetivo

Establecer una línea base técnica y de producto para la fase UX-P0. Esta auditoría no parte de una propuesta visual abstracta: parte del frontend real contenido en repo430 y de los contratos UI que ya fueron cerrados en GSDLC-12.

La finalidad es identificar qué debe conservarse, qué debe refactorizarse antes del piloto greenfield y qué debe aplazarse para UX-P1/P2.

## 2. Fuentes examinadas literalmente

Se verificó primero el ZIP repo430 contra SHA-256 `969f7d6b...388a`. Sobre ese contenido se examinaron, entre otros:

- `ui/web/src/main.ts`;
- `ui/web/src/styles.css` y `planning.css`;
- `ui/web/package.json` / `package-lock.json`;
- todas las páginas de `ui/web/src/pages/*.ts`;
- componentes principales de `ui/web/src/components/*.ts`;
- `SessionBanner`, `ExperienceModeControl`, `WorkspaceContextPanel`;
- `.devpilot/interfaces/ui_route_contract_registry.json`;
- `.devpilot/interfaces/ui_capability_registry.json`;
- `.devpilot/identity/auth_ui_route_contract_registry.json`;
- smoke/acceptance scripts UI;
- evidencia browser final de GSDLC-12-E.

La línea base machine-readable complementaria es `DEVPL_UX_P0_FRONTEND_BASELINE_v1_0_0.json`.

## 3. Arquitectura frontend actual

### 3.1 Stack

El frontend es deliberadamente liviano:

```text
TypeScript
+ DOM API directa
+ Vite
+ CSS propio
+ cero runtime framework dependencies
```

Esto es una fortaleza para local-first, footprint y auditabilidad, pero implica que DevPilot debe construir y mantener explícitamente sus propios patrones de layout, navegación, estados y componentes de interacción.

### 3.2 Router y superficies

`main.ts` declara **23 rutas** dentro de `UI_ROUTES`. El registry auth añade `/login` y `/first-run`; `/account` aparece como ruta global y como contrato auth. El total es **25 route IDs UI únicos** contando auth.

| Dominio actual | Rutas relevantes |
|---|---|
| Home / entry | `/`, `/project/entry` |
| Engineering | `/project/status`, `/pre-code`, `/workspace/documents`, `/planning/roadmap` |
| Build / quality | `/story/code`, `/jobs`, `/quality`, `/approvals` |
| Release | `/release/readiness`, `/release/package`, `/release/lifecycle`, `/release/metadata`, `/release/closure` |
| Recovery | `/recovery`, `/reconciliation` |
| AI | `/ai` |
| Diagnostics | `/reports`, `/traces` |
| Global | `/settings`, `/account`, `/help` |
| Auth | `/login`, `/first-run` |

La registry operacional contiene 22 rutas y la registry auth 3. No se detectó una ruta runtime principal sin contrato correspondiente; `ui.account-role` pertenece intencionadamente al registry auth.

## 4. Cómo funciona actualmente el shell

La composición efectiva es:

```text
AppShell
├── SkipLink
├── SessionBanner
├── ExperienceModeControl
├── PrimaryNavigation
└── RoutePage
```

El `Project Context` no constituye una región persistente garantizada del shell. Existe `WorkspaceContextPanel`, pero su uso es route-owned. Esto impide que proyecto/workspace/etapa/estado/next-action funcionen como contexto visual permanente.

La navegación actual divide las rutas entre:

1. `guidedCorePaths` — 12 paths visibles directamente;
2. `Más herramientas` — el resto de superficies.

Es una mejora respecto de una navegación totalmente plana, pero sigue siendo una clasificación binaria y no una arquitectura de información orientada al ciclo de vida.

## 5. Hallazgos principales

### UXP0-F01 — HIGH — navegación route-flat, no workflow/domain-driven

Hay 23 rutas principales, pero el shell las organiza principalmente como `core` versus `Más herramientas`. Release, por ejemplo, mantiene cinco rutas hermanas sin una agrupación de lifecycle visible como dominio.

**Impacto:** carga cognitiva, navegación larga y dificultad para responder “¿dónde estoy dentro del SDLC?”.

**UX-P0:** introducir IA por dominios sin cambiar paths/route IDs/authority.

### UXP0-F02 — HIGH — Project Context no es una primitive transversal

El shell muestra sesión, modo de experiencia y navegación; no garantiza en todas las rutas un bloque compacto con proyecto activo, workspace, etapa, health y autoridad.

**Impacto:** el usuario puede conocer la ruta pero no necesariamente el contexto de ingeniería.

**UX-P0:** Project Context persistente derivado de server-authoritative state; browser storage solo como preferencia UX.

### UXP0-F03 — HIGH — Next Action es parcialmente estático

`guidedNextAction()` tiene copy específico para **11 de 23 rutas**; el resto usa un fallback genérico. Esto es distinto del verdadero `GuidedSdlcNextAction` server-side que ya existe.

**Impacto:** Guided mode puede explicar una intención general, pero no siempre proyecta dinámicamente “qué hacer ahora”.

**UX-P0:** unificar el `Next Action` del shell con la autoridad actual del proyecto cuando esté disponible, conservando fail-closed.

### UXP0-F04 — MEDIUM — exceso de metadatos técnicos en el header normal

Cada ruta no-home renderiza en el header:

```text
routeId · raw path · human-session · roles · local-first · no-remote · TTL
```

Es útil en Expert, pero innecesario como jerarquía primaria en Guided.

**UX-P0:** mover diagnóstico detallado a Expert/Evidence Drawer y dejar en Guided nombre, etapa, estado, blocker y acción.

### UXP0-F05 — HIGH — no existe un design-token system real

`styles.css` tiene aproximadamente:

- **1.359 líneas**;
- **411 ocurrencias de color hexadecimal**;
- **187 valores hex distintos**.

Los estilos usan variables puntuales (`--border`, `--surface`, etc.) pero gran parte del sistema visual está hardcodeado.

**Impacto:** inconsistencias de color, spacing, radius, shadow y estados; alto costo para productización coherente.

**UX-P0:** semantic tokens antes de modificar masivamente superficies.

### UXP0-F06 — MEDIUM/HIGH — archivos de presentación demasiado grandes

Páginas más grandes:

- `ApprovalCenterView.ts`: 481 LOC;
- `WorkspaceDocumentsView.ts`: 478;
- `SettingsView.ts`: 452;
- `ProjectStatusView.ts`: 406.

Componentes más grandes:

- `DocumentValidationPanel.ts`: 573 LOC;
- `WorkspaceGitOperationsPanel.ts`: 461;
- `DocumentEditPlanner.ts`: 398.

**Impacto:** orquestación, estado y render quedan mezclados; cada surface tiende a crear patrones propios.

**UX-P0:** no hacer reescritura framework. Extraer solamente primitives/patterns transversales de alto retorno.

### UXP0-F07 — MEDIUM — identidad frontend stale/multi-era

`package.json` en repo430 declara simultáneamente:

- version `0.37.0-gsdlc-12-c`;
- description referida a GSDLC-12-B;
- `devpilot.sprint = FUNC-SPRINT-73`;
- `devpilot.status = phase-f-closed-visual-mvp`;
- `currentSprint = DEVPL-GSDLC-12-E`.

**Impacto:** la metadata del frontend no representa limpiamente la autoridad de producto actual.

**UX-P0-A:** reconciliar metadata current-active sin reescribir snapshots históricos.

### UXP0-F08 — MEDIUM — lenguaje de producto mezclado

Conviven términos como:

- `Estado del proyecto`;
- `Pre-code guiado`;
- `Story Code Workbench`;
- `Jobs`;
- `Release readiness`;
- `Install / rollback`;
- `Conflict Resolution`;
- `Approval Center`.

El problema no es usar términos ingleses técnicos; es que no existe una regla de copy diferenciada para Guided y Expert.

**UX-P0:** vocabulary/copy contract: lenguaje simple primero, término técnico disponible como secondary label/help.

### UXP0-F09 — MEDIUM — evidencia/diagnóstico compite con la tarea primaria

La browser matrix muestra pantallas muy largas y densas en facts, tables, raw technical fields y evidence. La evidencia es una ventaja de DevPilot, pero en Guided mode no debería dominar el viewport inicial.

**UX-P0:** evidence available, not dominant; panel/drawer progresivo y persistencia de blockers críticos.

### UXP0-F10 — MEDIUM — navegación y dispatch están centralizados en `main.ts`

El router, guards, recovery, render dispatch, navigation y header viven en el mismo módulo.

**Impacto:** cada cambio de IA puede tocar un archivo de alta autoridad funcional.

**UX-P0:** extraer catálogos/presentation helpers sin sustituir el mecanismo de guard/recovery probado.

## 6. Fortalezas que UX-P0 debe preservar

### UXP0-S01 — route/security contracts existentes

- route registry;
- auth registry;
- progressive disclosure por project context;
- session/RBAC server-side;
- no arbitrary shell;
- local-first/no-remote.

### UXP0-S02 — foundations de accesibilidad

- skip link;
- `role=main`;
- programmatic focus después de navegación;
- `aria-current`;
- Guided/Expert parity;
- focus visible en errores;
- smoke a11y existente.

### UXP0-S03 — recovery/reconciliation ya son producto, no solo backend

Hay superficies explícitas para durable recovery y conflict resolution. UX-P0 debe integrarlas en el journey, no ocultarlas.

### UXP0-S04 — state contracts ricos

Las rutas ya declaran loading/empty/error/block/pending/etc. El problema es de consistencia visual, no de ausencia contractual.

## 7. Arquitectura de información objetivo P0

Sin cambiar paths ni route IDs en esta fase:

```text
START
├── Project Home
└── Create / Open / Import

UNDERSTAND & PLAN
├── Project Status
├── Pre-code
├── Documents
└── Planning

BUILD & VALIDATE
├── Story / Code
├── Approvals
├── Jobs
└── Quality

RELEASE
├── Readiness
├── Package
├── Install / Rollback
├── Version / Tag
└── Closure

RECOVER
├── Resume
└── Reconciliation

AI
└── AI / RAG

DIAGNOSTICS
├── Reports
└── Traces

GLOBAL
├── Settings
├── Account
└── Help
```

## 8. App Shell objetivo P0

```text
App Shell
├── Global Navigation / workflow groups
├── Project Context Strip
│   ├── project/workspace
│   ├── current stage
│   ├── state / blocker
│   └── recovery indicator
├── Guided Journey / authoritative Next Action
├── Workbench Area
├── Evidence / Diagnostics Drawer
└── Notifications / long-operation / recovery feedback
```

`SessionBanner` y `ExperienceModeControl` se integran dentro de esta arquitectura sin cambiar autoridad.

## 9. Qué NO debe hacer UX-P0

- no migrar a React/Vue/Svelte por estética;
- no cambiar backend policies;
- no renombrar route IDs históricos;
- no alterar paths salvo successor explícito y justificado;
- no rediseñar todas las secondary surfaces;
- no ocultar blockers críticos;
- no convertir browser state en autoridad;
- no introducir remote/cloud requirements;
- no crear un dashboard ornamental.

## 10. Recomendación de ejecución

Dividir UX-P0 en cinco micro-sprints:

1. **UX-P0-A:** authority/rebind + design system + IA contract + metadata reconciliation.
2. **UX-P0-B:** App Shell + grouped navigation + breadcrumbs + persistent Project Context + authoritative Next Action.
3. **UX-P0-C:** critical journey surfaces: Home/Entry/Status/Pre-code/Planning.
4. **UX-P0-D:** cross-cutting workbench patterns para operations/evidence/approvals/jobs/quality/release/recovery/AI sin rediseño exhaustivo.
5. **UX-P0-E:** real-browser/usability/a11y/performance closure + única Full del backlog.

## 11. Gate pre-pilot

UX-P0 solo autoriza el piloto greenfield si un usuario puede responder visualmente, sin inspeccionar JSON ni documentación externa:

1. ¿En qué proyecto estoy?
2. ¿En qué etapa estoy?
3. ¿Qué falta?
4. ¿Qué está bloqueado y por qué?
5. ¿Cuál es la siguiente acción válida?
6. ¿Qué cambiará si la apruebo?
7. ¿Cómo recupero el trabajo después de cerrar/reabrir?

Además:

- `manual terminal escapes = 0` para el normal journey demostrado;
- critical accessibility blockers = 0;
- Guided y Expert conservan exactamente la misma autoridad;
- route/API/policy contracts continúan PASS;
- Full del backlog UX-P0 = exactamente 1 en el micro-sprint E, nunca en A-D por rutina.

## Risks and limitations

- The inventory describes repo430/current UX-P0-A baseline; later micro-sprints may reorganize presentation while preserving route/API authority.
- Route count alone does not measure usability; browser/usability evidence belongs to UX-P0-C/E.
- Historical route snapshots remain frozen and are not rewritten by this audit.

## PASS/BLOCK

**PASS:** route inventory, shell composition, navigation groupings and debt observations are traceable to repo430 current files.

**BLOCK:** a route/guard is invented, a historical snapshot is rewritten, or the audit is used as execution authority instead of the current registries.

## Verification commands

```text
cd ui/web && npm run test:route-enforcement
python -m pytest tests/test_post_h_028_ui_route_registry_enforcement.py -q
```

