---
title: "Agent Registry — DevPilot Local"
doc_id: "DEVPL-MIASI-AGENT-REGISTRY"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
standard: "MIASI"
phase: "SPRINT-PRECODE-07"
updated: "2026-06-05"
approval: "approved_by_owner_direction"
baseline_role: "precode_approved_baseline"
---

# Agent Registry — DevPilot Local

| Agent ID | Nombre | Fase | Autonomía máxima | Estado | Artefactos requeridos |
|---|---|---|---:|---|---|
| `precode.documentation` | PreCodeDocumentationAgent | MVP | A2 | Planned | Agent, Tool, Policy, Eval, Obs |
| `precode.audit` | DocumentationAuditAgent | MVP | A2 | Planned | Agent, Tool, Policy, Eval, Obs |
| `requirements.agent` | RequirementsAgent | MVP+ | A3 | Implemented-initial | Agent, Tool, Policy, Eval, Obs |
| `architecture.agent` | ArchitectureAgent | MVP+ | A3 | Implemented-initial | Agent, Tool, Policy, Eval, Obs |
| `security.agent` | SecurityAgent | MVP+ | A3 | Implemented-initial | Agent, Tool, Policy, Eval, Obs |
| `testplanner.agent` | TestPlannerAgent | MVP+ | A3 | Implemented-initial | Agent, Tool, Policy, Eval, Obs |
| `repo.analysis` | RepoAnalysisAgent | MVP+ | A3 | Implemented-initial | Agent, Tool, Policy, Eval, Obs |
| `code.review` | CodeReviewAgent | MVP+ | A3 | Implemented-initial | Agent, Tool, Policy, Eval, Obs |
| `patch.review` | PatchReviewAgent | MVP+ | A3 | Implemented-initial | Agent, Tool, Policy, Eval, Obs |
| `safe.refactor` | SafeRefactorAgent | MVP+ | A3 | Implemented-initial | Agent, Tool, Policy, Eval, Obs |
| `release.agent` | ReleaseAgent | Post-MVP | A5 | Future | Full MIASI |
| `operations.agent` | OperationsAgent | Post-MVP | A5 | Future | Full MIASI |
| `multiagent.coordinator` | MultiAgentCoordinator | Post-MVP | A3 | Implemented-initial | Full MIASI + governance |

## Política

Este registro no habilita automáticamente agentes. Cada agente pasa a `enabled` solo cuando exista implementación, pruebas, evals, policy, observabilidad y aprobación explícita.


## Actualización FUNC-SPRINT-55

La Fase D cierra con agentes SDLC `requirements.agent`, `architecture.agent` y `security.agent` en estado `implemented-initial`. Todos operan monoagente, read-only, con evals y prompts gobernados.

## Actualización FUNC-SPRINT-90 — MultiAgentCoordinator MVP

`multiagent.coordinator` pasa a `implemented-initial` solo para el MVP secuencial `repo-review`, en modo `--dry-run` obligatorio. Su autonomía efectiva queda acotada a A3: coordina agentes implementados, emite handoffs explícitos y consolida evidencia, pero no planifica libremente, no modifica archivos, no ejecuta herramientas críticas, no usa shell, no usa red externa y no habilita APIs externas.


## Actualización FUNC-SPRINT-91 — Workflows SDLC

`multiagent.coordinator` incorpora `multiagent.workflow.run` como herramienta permitida y referencia los artefactos `docs/audits/func_sprint_91_multiagent_workflows_audit.md` y `.devpilot/workflows/sdlc_review.json`. El alcance sigue siendo `implemented-initial`: workflows predefinidos, secuenciales, dry-run y report-only.


## Actualización FUNC-SPRINT-92 — Agent Registry

El Agent Registry declara que `security.agent`, `testplanner.agent` y `multiagent.coordinator` pueden consumir `eval.safety.run` para evidencia local de safety scoring. La capacidad conserva `implemented-initial`, requiere observabilidad/evals y no habilita autonomía superior a A3.
