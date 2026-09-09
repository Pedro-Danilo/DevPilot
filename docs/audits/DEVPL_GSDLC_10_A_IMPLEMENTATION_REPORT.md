---
doc_id: "DEVPL-GSDLC-10-A-IMPLEMENTATION-REPORT"
title: "DEVPL-GSDLC-10-A — Test Impact and StoryTestPlan UI-native implementation report"
status: "closed/pass/windows-validated"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-09-09"
approval: "approved_by_owner/prompts-00-and-01"
---

# DEVPL-GSDLC-10-A — Implementation report

## Estado

`CLOSED / PASS / WINDOWS-VALIDATED`. Activation/rebind está absorbido por el mismo delta de 10-A; no existe repo/commit independiente de activación.

## Capacidades implementadas

- `StoryTestPlanApplicationService` determinista y project-scoped.
- Binding StoryExecution `CHANGES_READY` + immutable SourceChangePlan id/hash + Test Impact report hash.
- Reutilización de Test Impact v2: no existe segundo motor de impacto.
- Required/recommended tests explicables por contracts/rules.
- Unknown impact fail-closed con revisión humana explícita.
- Sensitive impact requiere tests deterministas y bloquea waiver de required tests.
- Waiver owner-only, reasoned, expiring y server-authoritative.
- Model/agent authority no puede approve/reject/waive ni convertir model route en test execution authority.
- Full Regression signal informativo; `execution_authorized=false`; Full runs en 10-A = 0.
- Story Code Workbench integra `Validar story → Test Impact → StoryTestPlan review/approval`; no crea Quality UI paralela ni comando libre de test.

## API/UI

Endpoints current-active: create/get/decision de StoryTestPlan bajo `/api/v1/story/code/...`; todos pasan por human-session/RBAC. La UI visible cambia y por ello Windows debe demostrar una única aceptación browser con tres consolas foreground.

## Validación local

- focal GSDLC-10-A: 10/10 PASS;
- TCR v1/v2: 11/11 PASS;
- GSDLC-09-C bounded predecessor: 14/14 PASS;
- GSDLC-09-D bounded predecessor: 8/8 PASS;
- GSDLC-09-E + API security/contract: 31/31 PASS;
- API drift guard: 8/8 PASS;
- UI static smoke `test:gsdlc10a`: PASS;
- Project State, Documentation Governance y Evidence Freshness: PASS;
- Full Regression: 0.

## Seguridad

No arbitrary shell, no free-form test command, no agent waiver authority, no model-route-to-test-execution escalation, runtime stores/secrets excluidos y source mutation por StoryTestPlan = 0.

## Riesgos y limitaciones

Primera versión UI-native de StoryTestPlan. 10-A planifica/revisa validaciones pero no ejecuta jobs; lifecycle de jobs corresponde a 10-B. Browser Windows es obligatorio una vez porque el journey visible cambió. No se afirma cierre Windows hasta evidence+screenshots/verifier PASS.

## PASS Windows

Focal/bounded/gates PASS, browser acceptance única PASS, S0/S1=0, Full=0, repo limpio y promoción Git gobernada fast-forward.

## BLOCK Windows

StoryTestPlan no hash-bound, required test omitible silenciosamente, agent/model puede waivar, free-form execution surface, browser journey incompleto, gate focal/bounded FAIL o cualquier intento de Full en 10-A.


## Correctives browser Windows incorporados al mismo sprint

Durante la aceptación Windows se detectaron tres defectos de continuidad UX del journey, corregidos dentro de 10-A sin Full Regression ni nuevo browser fixture: (1) rehidratación server-side de SourceChangePlan/approval al volver al Story Workbench, (2) handoff dirigido a Approval Center para pestañas auxiliares sin depender de `sessionStorage` del opener y (3) transición post-apply a `CHANGES_READY` que no actualizaba el gating local de `Validar story` y además no podía rehidratar el plan aplicado después de un reload. El corrective final hace que `CHANGES_READY` sea la autoridad para habilitar Validar, recupera el SourceChangePlan aplicado mediante approval exacto `APPROVED` + `metadata.plan_hash` server-side y deja apply/approval deshabilitados fuera de `IN_PROGRESS`. Todos los correctives mantienen `Full Regression=0` y la autoridad de aprobación/plan del servidor.

## Windows closure

Cierre esperado por el operador Windows 10-A: browser real una sola vez, Full Regression=0, focal/bounded/gates PASS, S0/S1=0 y promoción Git fast-forward. Candidate final: `repo_DevPilot_Local_415_DEVPL_GSDLC_10_A_TEST_IMPACT_STORY_TEST_PLAN_WINDOWS_VALIDATED_CANDIDATE.zip`. GSDLC-10-B queda autorizado solo después del receipt de cierre PASS.
