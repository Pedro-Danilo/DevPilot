---
doc_id: "DEVPL-UI-UX-PRODUCTIZATION-STRATEGY"
title: "DevPilot — UI/UX productization strategy for real-product acceptance"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-09-15"
approval: "approved_by_owner"
target_path: "docs/00_product/DEVPL_UI_UX_PRODUCTIZATION_STRATEGY_v1_0_0_APPROVED.md"
source_repo: "repo_DevPilot_Local_430_DEVPL_GSDLC_12_E_LOCAL_RC_WINDOWS_VALIDATED_CANDIDATE.zip"
source_git_commit: "a415504bbf021566243ef4000b1a27d4c8846fee"
source_repo_sha256: "969f7d6b8cbdd8eb3bc32491718e94ee41295647e82234779aee180cea2a388a"
strategy: "foundation-before / evidence-driven-during / consolidation-after"
local_first: true
ui_complete_normal_journey: true
---

# DevPilot — UI/UX productization strategy

## 1. Decisión

La mejora del frontend no debe ejecutarse completamente **antes** del piloto ni aplazarse completamente **después**.

Se adopta una estrategia de tres tiempos:

```text
ANTES DEL PILOTO
UX foundation mínima pero seria

DURANTE EL PILOTO
productización del critical path basada en evidencia real

DESPUÉS DEL PILOTO
consolidación, secondary surfaces y polish industrial
```

El objetivo no es “hacer bonito DevPilot”; es reducir carga cognitiva, ambigüedad y dependencia del operador externo sin debilitar gobernanza.

## 2. Por qué no rediseñar todo antes

Un rediseño integral previo tendría tres riesgos:

1. invertir en superficies que el piloto demuestre irrelevantes o mal concebidas;
2. separar estética de tareas reales;
3. prolongar la fase de construcción sin comprobar si el producto integrado resuelve el problema.

## 3. Por qué tampoco esperar hasta después

El frontend actual fue construido principalmente para habilitar y validar capacidades. Si el piloto greenfield comienza con demasiada deuda UX, la prueba mediría la tolerancia del usuario frente al prototipo y no la calidad del Guided SDLC Engine.

Por eso existe un **pre-pilot UX gate**.

## 4. Fase UX-P0 — Foundation antes del piloto

### Objetivo

Hacer coherente la experiencia transversal antes de medir el producto real.

### Alcance obligatorio

- design tokens y theme contract;
- tipografía, spacing, density y responsive grid;
- application shell;
- navegación principal y breadcrumbs;
- Project Context visible y persistente;
- Project Status como centro operacional, no documento decorativo;
- action hierarchy consistente;
- estados `loading / empty / success / warning / blocked / error / recovery`;
- componentes comunes para approvals, evidence, diffs, jobs y gates;
- feedback de operaciones largas;
- keyboard/focus/accessibility baseline;
- contextual help pattern;
- Guided/Expert visual parity sin policy drift;
- eliminación de labels técnicos innecesarios en modo Guided;
- representación consistente de `PASS/BLOCK/PENDING/RECOVERY`.

### Fuera de alcance

- rediseñar cada detalle de todas las rutas;
- animaciones ornamentales;
- rebranding exhaustivo;
- dashboards sin caso de uso validado;
- alterar políticas backend para simplificar la UI.

### Gate

PASS si un usuario puede responder visualmente, sin inspeccionar JSON o documentación externa:

1. ¿En qué proyecto estoy?
2. ¿En qué etapa estoy?
3. ¿Qué falta?
4. ¿Qué está bloqueado y por qué?
5. ¿Cuál es la siguiente acción válida?
6. ¿Qué cambiará si la apruebo?
7. ¿Cómo vuelvo o me recupero si cierro la app?

## 5. Fase UX-P1 — Productización durante el piloto

El piloto es un instrumento de discovery y acceptance.

Cada segmento del journey sigue:

```text
observe task
→ measure confusion/friction
→ classify UX defect
→ corrective bounded
→ selective validation
→ continue pilot
```

No se permite rediseño continuo sin control durante una misma acceptance run. Un defecto que invalida la tarea provoca pausa, corrective y retest delimitado.

### Critical path prioritario

1. first-run/login;
2. Home/Create/Open Project;
3. project bootstrap;
4. Project Status;
5. Vision/Scope/Requirements;
6. Architecture/Security/Test Strategy/ADRs;
7. Planning;
8. Story/Coding Workbench;
9. Change Plan/Diff/Approval;
10. Jobs/Quality/Remediation;
11. Git/Commit;
12. Release lifecycle;
13. Recovery/conflict flows;
14. AI Control Center y provenance cuando intervenga IA.

## 6. Fase UX-P2 — Consolidación después del piloto

Solo después de completar una aplicación real se ejecuta el sweep de producto:

- secondary routes;
- cross-surface consistency;
- component deduplication;
- visual polish;
- information density tuning;
- responsive edge cases;
- accessibility AA-oriented closure;
- performance budgets;
- copywriting/glossary final;
- onboarding/help refinado;
- optional motion/micro-interactions;
- eliminación de UI dead paths.

## 7. Métricas UX vinculantes

No usar únicamente screenshots o apreciación estética.

Registrar al menos:

- task completion without external operator;
- time-to-next-valid-action;
- number of blocked/confused moments;
- number of manual terminal escapes;
- clicks/steps por tarea crítica;
- recovery success;
- first-attempt success de approvals/diffs/gates;
- Guided-mode completion por usuario no experto;
- accessibility critical blockers;
- browser/runtime errors;
- user-reported confidence: “sé qué pasó y qué hacer después”.

## 8. Arquitectura UI recomendada

El frontend debe converger hacia:

```text
App Shell
├── Global Navigation
├── Project Context
├── Guided Journey / Next Action
├── Workbench Area
├── Evidence / Diagnostics Drawer
└── Notifications / Recovery
```

Las vistas específicas reutilizan patrones y no reinventan estados, headers, approvals o evidence panels.

## 9. Principios

- workflow-first, not dashboard-first;
- progressive disclosure;
- one primary action per state;
- explainability before density;
- evidence available, not dominant;
- Expert mode exposes diagnostics, not extra authority;
- backend policy remains authority;
- no hidden destructive action;
- no UI-only state as execution authority.

## 10. PASS/BLOCK

**PASS:** foundation completa antes del piloto, correctives pilot-driven controlados y consolidation posterior basada en evidencia.

**BLOCK:** rediseño integral sin piloto, UI cosmética sobre workflows confusos, o simplificación visual que debilite RBAC/approval/evidence contracts.


## 11. Adjudicación owner

**APPROVED — 2026-09-15.** Esta estrategia queda vinculante para la fase UX-P0 pre-pilot y para la productización UX pilot-driven/post-pilot posterior.
