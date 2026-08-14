---
doc_id: "DEVPL-GSDLC-LEGACY-PRESERVATION-MATRIX"
title: "DEVPL-GSDLC — Legacy Preservation Matrix"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-08-14"
approval: "approved_by_owner_scope_DEVPL-GSDLC-00-A"
program_id: "DEVPL-GSDLC"
micro_sprint: "DEVPL-GSDLC-00-A"
---
# DEVPL-GSDLC — Legacy Preservation Matrix

## 1. Política

La evolución usa `KEEP / EXTEND / REFACTOR / DEPRECATE`. `DEPRECATE` significa **deprecate → migrate → verify → remove**; no autoriza borrado inmediato.

## 2. Matriz inicial

| Capability / artifact family | Decisión | Razón | Successor / owner |
|---|---|---|---|
| PolicyEngine / MIASI | KEEP | Core determinístico de seguridad | GSDLC-05 |
| Schemas / frontmatter / readiness validators | KEEP+EXTEND | Ya convierten estándares en gates | GSDLC-04/05 |
| Documentation Governance / Source Registry | KEEP+EXTEND | Canonical source control | GSDLC-00/04 |
| TCR v1/v2 / Test Impact | KEEP+EXTEND | Evita regresiones y gobierna costo de pruebas | GSDLC-00/10 |
| Workspace isolation | KEEP | Límite de seguridad probado | GSDLC-03 |
| Approval/RBAC inicial | KEEP+REFACTOR | Necesita identidad/sesión real | GSDLC-02 |
| Git governed operations | KEEP+EXTEND | Base de commit workflow | GSDLC-09/10 |
| Jobs / Quality / Evidence / Traces | KEEP+EXTEND | Infraestructura transversal | GSDLC-10 |
| RAG / agents / tool contracts / handoffs | KEEP+EXTEND | Base agentic ya disponible | GSDLC-06/07 |
| ModelAdapter / CostGuard | KEEP+EXTEND | Base multi-model | GSDLC-R01/06 |
| `.devpilot/project_state.json` como único estado | REFACTOR | Mezcla platform y workflow de proyecto | GSDLC-01 |
| Capability-centric primary navigation | REFACTOR | UX futura debe ser project-centric | GSDLC-01/12 |
| `/ai` como único punto de IA | REFACTOR | IA debe ser contextual por step | GSDLC-07 |
| Large external pilot operators writing project content | DEPRECATE | Sustituyen al producto | GSDLC-13 proof required |
| Required PowerShell in normal journey | DEPRECATE | Contradice UI-complete | milestones M1-M6 |
| CLI bridges with proven UI-native successor | DEPRECATE AFTER PROOF | Evitar duplicidad operativa | per backlog |
| UOC route count = 9 as permanent limit | HISTORICAL-FREEZE | Es hecho de UOC, no límite futuro | GSDLC-12 successor |
| POST-H-034-D multiuser.auth continue-blocked | HISTORICAL-FREEZE + SUCCESSOR | Enterprise boundary se preserva | GSDLC-02 local-auth successor |

## 3. Regla

Ningún test histórico se edita solo para pasar. Cada cambio futuro necesita clasificación `historical-freeze`, `current-active`, `successor-needed` o `deprecated-after-proof`.
