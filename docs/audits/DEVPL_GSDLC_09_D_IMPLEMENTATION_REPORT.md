---
doc_id: "DEVPL-GSDLC-09-D-IMPLEMENTATION-REPORT"
title: "DEVPL-GSDLC-09-D — CodingAgent and TestAgent proposal-only implementation report"
status: "closed/pass/windows-validated"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-09-08"
approval: "approved_by_owner/prompt-04"
---

# DEVPL-GSDLC-09-D — Implementation report

## Estado

`CLOSED / PASS / WINDOWS-VALIDATED` sobre `repo_DevPilot_Local_410_DEVPL_GSDLC_09_C_SOURCE_CHANGE_APPLY_WINDOWS_VALIDATED_CANDIDATE.zip`.

## Alcance implementado

- `StoryAgentAssistApplicationService` project-scoped y proposal-only.
- CodingAgent: propuesta `EDIT` sobre source bounded seleccionado.
- TestAgent: propuesta `CREATE` bajo `tests/`.
- StoryContextPack como autoridad de story y RAG local bounded como grounding complementario.
- Model Gateway `mock` / `fake-local`; API externa no requerida.
- Provenance por propuesta: `model_id`, `provider_id`, `access_route_id`, `agent_session`, `trace_id`, `ToolIntent` y `ToolExecutionDecision`.
- Decisión humana `ACCEPT/REJECT`. `ACCEPT` autoriza insertar en editor únicamente; no escribe SourceDraftBuffer ni source.
- UI integrada en `/story/code` con diff, costo/provenance y decisión de tool visibles.

## Invariantes de seguridad

- `ModelRouteDecision != ToolExecutionDecision`.
- agentes no self-apply, self-approve ni self-commit;
- generic shell deshabilitado;
- `filesystem.delete` permanece `BLOCK`;
- source/draft mutations desde el agente = 0;
- max instruction = 2000 caracteres;
- costo externo requerido = USD 0;
- runtime network/external API requerido para PASS = 0.

## Pruebas locales

Focal `tests/test_devpl_gsdlc_09_d_agent_proposals.py`: `8 passed`.

Cobertura: mock/fake-local, CodingAgent/TestAgent, human ACCEPT/REJECT, stale source, unsafe/budget BLOCK, API human session y UI static contract.

La acumulativa A→D, Test Impact, Historical Contract Authority y Contract Reconciliation se ejecutan antes del empaquetado Windows. Full Regression = 0 por autoridad del prompt 04; la única full del backlog sigue reservada para 09-E.

## Riesgos y limitaciones

Esta es una primera versión gobernada. El contenido propuesto es determinístico/rule-backed bajo rutas mock/fake-local para permitir validación reproducible y sin costo. Modelos locales reales o APIs externas pueden evolucionar después sin cambiar la autoridad de escritura. La propuesta no reemplaza revisión humana ni el pipeline SourceChangePlan de 09-C.

## PASS

- proposal-only;
- human-reviewed diff;
- provenance/cost completos;
- no authority escalation;
- `filesystem.delete=BLOCK`;
- S0/S1=0;
- browser Windows demuestra manual vs agent-assisted, accept/reject y unsafe BLOCK.

## BLOCK

- self-apply/self-approve/self-commit;
- tool ejecutado por autoridad heredada del modelo;
- source/draft write al generar/aceptar propuesta;
- provider externo requerido para PASS;
- evidencia sin provenance completa;
- browser no demuestra unsafe proposal BLOCK.


## Cierre Windows 09-D

Aplicado únicamente después de qualification PASS, browser real 7/7 y revisión visual humana PASS.

- successor canónico: `repo_DevPilot_Local_411_DEVPL_GSDLC_09_D_CODING_TEST_AGENTS_WINDOWS_VALIDATED_CANDIDATE.zip`;
- browser Windows live: `1`;
- Full Regression: `0`;
- source/draft mutations realizadas por agentes: `0`;
- mock/fake-local suficiente para PASS; API externa no requerida;
- `ModelRouteDecision != ToolExecutionDecision`;
- `GSDLC-09-E authorized=true`.

La única Full Regression del backlog DEVPL-GSDLC-09 permanece reservada para 09-E.
