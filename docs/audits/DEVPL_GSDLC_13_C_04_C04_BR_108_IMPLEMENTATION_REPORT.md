---
doc_id: "DEVPL-GSDLC-13-C-04-C04-BR-108-IMPLEMENTATION-REPORT"
title: "C04_BR_108 — Story Code successor actionability convergence corrective"
status: "PRE_UI_VALIDATION"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-09-29"
approval: "pending_windows_post_ui"
---
# C04_BR_108 — Story Code successor actionability convergence

## Objective

Close the final Guided actionability gap exposed by the C04_BR_107 full Project Status evidence. The server-authoritative next action already points to Story Code Workbench, but the Project Status `Continuar` control and Step Action Advisor still fail to operationalize that successor consistently.

## Root cause

1. `ProjectStatusView.ts` duplicated navigation-target resolution in a private map containing only `ui.approvals` and `project-status`; therefore `ui.story-code-workbench` was falsely treated as unavailable even though the shared navigation registry and `/story/code` route already exist.
2. `GuidedSDLCApplicationService.step_actions_primary()` evaluated the historical `all_stages_frozen` Pre-code shortcut before considering the reconciled `current_step=story-context-readiness`. That produced the stale advisor card `Pre-code está READY; la siguiente frontera es Planning`.
3. `StepActionAdvisor.ts` consumed raw navigation targets directly instead of the shared navigation presentation resolver, allowing future route-id/path representation drift.

## Implementation

- Project Status now resolves all server navigation targets with `navigationPathFromServerTarget()`; the private incomplete map is removed.
- Step Action Advisor uses the same shared resolver for route ids and governed direct paths.
- `step_actions_primary()` gives the reconciled `story-context-readiness` boundary precedence over the historical Pre-code shortcut and emits an AVAILABLE `Abrir Story Code Workbench` action targeting `ui.story-code-workbench`.
- The prior Planning shortcut remains unchanged for projects whose current boundary is genuinely still Planning.
- Focal/static tests verify both server action selection and UI route resolution.

## Authority and safety

This corrective does not mutate Planning JSON, Markdown projections, Pre-code artifacts, workspace source, MIPSoftware lifecycle, RBAC or the Story Code Workbench itself. It only makes the already-authorized successor action executable and consistent across Guided surfaces. Full regression remains 0.

## Windows acceptance

PASS requires, from Project Status:

- `current_step=story-context-readiness`;
- global `Próxima acción` = Story Code Workbench and **Continuar enabled**;
- `Qué puedes hacer ahora` no longer says that the next frontier is Planning;
- advisor recommended action = `Abrir Story Code Workbench`, AVAILABLE/executable;
- clicking the navigation control reaches `/story/code` without mutating Planning;
- Planning remains `IMPLEMENTING_READY`, Roadmap/Backlog/Sprint remain FROZEN and all nine existing Planning runtime/projection hashes remain unchanged.

## Regression policy

- focal C04_BR_108 + bounded GSDLC-08/Guided impact only;
- Vite build required on Windows;
- full regression: 0;
- no source Git promotion before Owner/ChatGPT evidence review.
