---
title: "Agent Registry — DevPilot Local"
doc_id: "DEVPL-MIASI-AGENT-REGISTRY"
status: "reviewed"
version: "0.6.0"
owner: "Ordóñez"
standard: "MIASI"
phase: "SPRINT-PRECODE-06"
updated: "2026-06-05"
approval: "ready_for_owner_approval"
---

# Agent Registry — DevPilot Local

| Agent ID | Nombre | Fase | Autonomía máxima | Estado | Artefactos requeridos |
|---|---|---|---:|---|---|
| `precode.documentation` | PreCodeDocumentationAgent | MVP | A2 | Planned | Agent, Tool, Policy, Eval, Obs |
| `precode.audit` | DocumentationAuditAgent | MVP | A2 | Planned | Agent, Tool, Policy, Eval, Obs |
| `requirements.agent` | RequirementsAgent | MVP+ | A4 | Planned | Agent, Tool, Policy, Eval, Approval, Obs |
| `architecture.agent` | ArchitectureAgent | MVP+ | A4 | Planned | Agent, Tool, Policy, Eval, Approval, Obs |
| `security.agent` | SecurityAgent | MVP+ | A4 | Planned | Agent, Tool, Policy, Eval, Approval, Obs |
| `testplanner.agent` | TestPlannerAgent | MVP+ | A3 | Planned | Agent, Tool, Policy, Eval, Obs |
| `repo.analysis` | RepoAnalysisAgent | MVP+ | A3 | Planned | Agent, Tool, Policy, Eval, Obs |
| `code.review` | CodeReviewAgent | MVP+ | A4 | Planned | Agent, Tool, Policy, Eval, Approval, Obs |
| `patch.review` | PatchReviewAgent | MVP+ | A4 | Planned | Agent, Tool, Policy, Eval, Approval, Obs |
| `safe.refactor` | SafeRefactorAgent | MVP+ | A4 | Planned | Agent, Tool, Policy, Eval, Approval, Obs |
| `release.agent` | ReleaseAgent | Post-MVP | A5 | Future | Full MIASI |
| `operations.agent` | OperationsAgent | Post-MVP | A5 | Future | Full MIASI |
| `multiagent.coordinator` | MultiAgentCoordinator | Post-MVP | A5/A6 | Future | Full MIASI + governance |

## Política

Este registro no habilita automáticamente agentes. Cada agente pasa a `enabled` solo cuando exista implementación, pruebas, evals, policy, observabilidad y aprobación explícita.
