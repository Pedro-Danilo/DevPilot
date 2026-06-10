---
title: "Product Roadmap — DevPilot Local"
doc_id: "DEVPL-PROD-005"
status: "approved"
version: "1.1.0"
owner: "Ordóñez"
standard: "MIPSoftware"
extension: "MIASI"
phase: "FUNC-SPRINT-20"
updated: "2026-06-10"
approval: "approved_by_owner"
refinement: "DEVPL-PRE-0107 — MVP+ y visión completa de plataforma"
approved_by: "Ordóñez"
approved_at: "2026-06-02"
approval_scope: "SPRINT-PRECODE-01 product baseline"
change_policy: "controlled_changes_allowed_via_docs_as_code"
change_reason: "Marked as historical directional roadmap and linked to post-18 reconciliation."
---
# Product Roadmap — DevPilot Local

## 1. Propósito

Este roadmap define la evolución incremental y obligatoria de DevPilot Local desde el bootstrap actual hasta una plataforma agent-assisted SDLC local-first con CLI, escritorio y web. Su objetivo es ordenar el crecimiento sin saltar prematuramente a automatizaciones inseguras, pero manteniendo claro que la evolución hacia desktop/web y agentes especializados es un compromiso de producto.



## 1.1 Estado post-18: roadmap histórico + reconciliado

Desde `FUNC-SPRINT-20`, este documento debe leerse como **roadmap histórico y direccional**. Conserva intención de producto, pero los comandos reales vigentes y estados implementados/parciales/planeados se consultan en:

- `docs/audits/roadmap_reconciliation_after_sprint_18.md`;
- `docs/audits/capability_status_matrix_after_sprint_18.md`;
- `README.md`;
- `docs/05_operations/runbook.md`.

Regla operativa: si una tabla histórica usa nombres como `policy-check`, `repo-scan`, `review-code --dry-run`, `git-diff-report`, `validate-schema` o `approval request/list/approve`, esos nombres no deben asumirse como comandos implementados. La reconciliación vigente mapea cada nombre histórico a su comando real, estado `planned` o estado `future`.

## 2. Principios del roadmap

1. Validar documentos antes de automatizar.
2. Validar CLI/core antes de UI.
3. Validar reglas determinísticas antes de LLMs.
4. Validar dry-run antes de execute.
5. Validar Git read-only antes de Git write.
6. Validar patches antes de aplicarlos.
7. Validar MIASI antes de agentes.
8. Validar proyectos propios antes de clientes.
9. Mantener costo externo cero en MVP.
10. Mantener CLI como núcleo operativo aunque existan desktop/web.

## 3. Roadmap macro

```text
Bootstrap
  ↓
Pre-code baseline
  ↓
MVP CLI + validators
  ↓
MVP+ Git/repo/patch/code-review/refactor
  ↓
Agentes controlados
  ↓
Desktop app
  ↓
Web app
  ↓
Plataforma personal SDLC madura
```

## 4. Roadmap por fases

| Fase | Nombre | Objetivo | Resultado esperado |
|---|---|---|---|
| F0 | Bootstrap | Crear repo, entorno, CLI mínimo y docs iniciales. | Sprint 0 PASS. |
| F1 | Pre-code baseline | Completar y aprobar documentos `docs/`. | Baseline documental aprobada. |
| F2 | MVP Validators Core | Validar frontmatter, estructura, campos y checklists. | `validate-artifact`, `readiness-check --strict`. |
| F3 | Traceability Engine | Conectar producto → requerimientos → pruebas → arquitectura. | Matriz consultable y reportes. |
| F4 | Schema Engine | Validar documentos con JSON Schema. | Schemas + reportes detallados. |
| F5 | MIASI Engine | Detectar y aplicar extensión agentic. | Gates MIASI automáticos. |
| F6 | MVP+ Git Adapter | Leer status, ramas, tags y diffs. | `git-status`, `git-diff-report`. |
| F7 | MVP+ Repo Analysis | Analizar estructura, calidad, docs y riesgos. | Reporte de repo. |
| F8 | MVP+ Patch Review | Validar patches en dry-run. | PASS/FAIL + recomendaciones. |
| F9 | MVP+ Safe Refactor | Proponer refactor seguro y reversible. | Plan de refactor. |
| F10 | Agent-assisted Review | Agentes en dry-run para docs/código. | Recomendaciones trazables. |
| F11 | CI/CD Local | Quality gates locales integrables con CI. | Comandos reproducibles. |
| F12 | Desktop App | Interfaz visual para workspaces y gates. | App desktop inicial. |
| F13 | Web App | Dashboard web y colaboración futura. | UI web controlada. |
| F14 | Operational DevPilot | Workflows SDLC completos con agentes, políticas y trazas. | Plataforma personal madura. |

## 5. Roadmap por sprints pre-code

| Sprint | Objetivo | Entregables | Gate |
|---|---|---|---|
| SPRINT-PRECODE-00 | Cierre limpio bootstrap | `.gitignore`, commit baseline, validaciones | Git limpio + tests PASS |
| SPRINT-PRECODE-01 | Producto y alcance | 5 docs de producto aprobados | Producto PASS |
| SPRINT-PRECODE-02 | Requerimientos | Requirements, stories, use cases, acceptance, traceability | Reqs PASS |
| SPRINT-PRECODE-03 | Arquitectura | Architecture, C4, ADRs | Architecture PASS |
| SPRINT-PRECODE-04 | Seguridad | Threat model, privacy assessment | Security PASS |
| SPRINT-PRECODE-05 | Calidad/operación | Test strategy, observability, runbook | Quality/Ops PASS |
| SPRINT-PRECODE-06 | MIASI aplicado | Agent/Tool/Policy/Eval/Human/Obs cards | MIASI PASS |
| SPRINT-PRECODE-07 | Auditoría pre-code | Audit report, baseline decision | Baseline approved |

## 6. Roadmap funcional MVP

| Sprint funcional | Nombre | Objetivo | Comandos esperados |
|---|---|---|---|
| FUNC-01 | Artifact Validators | Validar Markdown/frontmatter. | `validate-artifact`, `validate-frontmatter` |
| FUNC-02 | Checklist Engine | Ejecutar checklists. | `checklist-pre-code` |
| FUNC-03 | Strict Readiness | Readiness con reglas estrictas. | `readiness-check --strict` |
| FUNC-04 | Report Engine | Reportes JSON/Markdown/JSONL. | `report generate` |
| FUNC-05 | Schema Validation | Validar JSON schemas. | `validate-schema` |
| FUNC-06 | MIASI Detector 2 | Reglas avanzadas de activación. | `miasi-required --explain` |
| FUNC-07 | Policy Engine | Reglas de permisos/dry-run. | `policy-check` |

## 7. Roadmap funcional MVP+

| Sprint funcional | Nombre | Objetivo | Comandos esperados |
|---|---|---|---|
| MVPPLUS-01 | Git Adapter Read-only | Leer estado del repo. | `git-status`, `git-branches` |
| MVPPLUS-02 | Diff Analyzer | Analizar cambios. | `git-diff-report` |
| MVPPLUS-03 | Repo Scanner | Analizar estructura del proyecto. | `repo-scan` |
| MVPPLUS-04 | Patch Reviewer | Validar patches. | `patch-review --dry-run` |
| MVPPLUS-05 | Code Review Assistant | Revisar código sin modificar. | `review-code --dry-run` |
| MVPPLUS-06 | Safe Refactor Planner | Proponer refactor seguro. | `refactor-plan --dry-run` |
| MVPPLUS-07 | Env Builder/Validator | Validar entorno local. | `env-check`, `env-plan` |
| MVPPLUS-08 | First Agent Runtime | Agentes controlados. | `agent review --dry-run` |
| MVPPLUS-09 | Human Approval | Aprobar acciones sensibles. | `approval request/list/approve` |
| MVPPLUS-10 | Trace Engine | Registrar eventos JSONL. | `trace report` |

## 8. Roadmap de interfaces

### 8.1 CLI

El CLI es el núcleo inicial y permanente.

```text
devpilot init-project
devpilot readiness-check
devpilot validate-artifact
devpilot checklist pre-code
devpilot miasi-required
devpilot git-status
devpilot repo-scan
devpilot patch-review
devpilot review-code
```

### 8.2 Desktop

La app desktop será la primera interfaz visual fuerte.

| Vista | Función |
|---|---|
| Workspaces | Lista y estado de proyectos. |
| Lifecycle | Fase actual del SDLC. |
| Documents | Estado de documentos MIPSoftware/MIASI. |
| Gates | PASS/FAIL por dominio. |
| Git | Cambios, ramas, diffs y commits. |
| Reports | Reportes navegables. |
| Approvals | Aprobaciones humanas. |
| Agents | Recomendaciones asistidas. |

### 8.3 Web

La app web llegará después de desktop.

| Vista | Función |
|---|---|
| Dashboard multi-proyecto | Seguimiento amplio. |
| Reportes históricos | Evidencia de evolución. |
| Backlog | Tareas y readiness. |
| Releases | Versiones, changelog y rollback. |
| Colaboración futura | Revisión distribuida controlada. |

## 9. Roadmap de workspaces

| Fase | Workspace |
|---|---|
| MVP | Workspace implícito del propio DevPilot. |
| MVP+ | `.devpilot/` inicial para repos gestionados. |
| Desktop | Gestión visual de workspaces. |
| Web | Workspaces sincronizables/controlados. |

## 10. Compromisos de producto

| Compromiso | Decisión |
|---|---|
| CLI permanente | Sí. |
| Desktop app | Sí, fase posterior a MVP+. |
| Web app | Sí, posterior a desktop/core maduro. |
| Git integration | Sí, MVP+. |
| Agentes IA | Sí, controlados por MIASI. |
| Local-first | Sí, por defecto. |
| APIs externas | Opcionales, nunca obligatorias en el core. |
| Human approval | Obligatorio para acciones sensibles. |

## 11. Criterios de promoción

| De | Hacia | Requisito |
|---|---|---|
| Pre-code | MVP | Docs approved + checklist PASS. |
| MVP | MVP+ | Validators strict + reports + policy gates. |
| MVP+ | Agentes | Git/patch safety + MIASI gates. |
| Agentes | Desktop | Core estable + tests + trazas. |
| Desktop | Web | Seguridad, auth, operación y modelo de datos. |

## 12. Veredicto

El roadmap queda corregido: la evolución hacia escritorio/web y agentes especializados no es posibilidad; es compromiso condicionado por gates de madurez.
