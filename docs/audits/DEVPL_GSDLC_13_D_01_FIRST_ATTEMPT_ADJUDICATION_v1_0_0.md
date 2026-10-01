---
doc_id: "DEVPL-GSDLC-13-D-01-FIRST-ATTEMPT-ADJUDICATION"
title: "DEVPL-GSDLC-13-D-01 — First-attempt adjudication"
status: "BLOCK / ACTIVE-CORRECTIVE-REQUIRED"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-09-30"
checkpoint_id: "13-D-01"
finding_id: "CAP-13D01-STORY-ACTIVATION-002"
execution_source_commit: "fb5f0c906c32bb268aa10c88e5a4e5a99b235e28"
full_regression_runs: 0
---

# 13-D-01 — First-attempt adjudication

## Veredicto

`BLOCK / FUNCTIONAL / ACTIVE-CORRECTIVE-REQUIRED`.

La evidencia first-attempt es válida y suficiente. La captura denominada
`04_story_ready_activation_action-BLOCK-Story sin story.png` **no es una captura defectuosa**:
demuestra el incumplimiento exacto del contrato D01.

## Hechos reproducidos

1. Project Status reconoció el Pilot A y presentó Story Code como siguiente acción.
2. Planning estaba cerrado/FROZEN e `IMPLEMENTING_READY`.
3. La navegación normal llegó a `/story/code`.
4. Story Code respondió y la API devolvió HTTP 200 para status/sources.
5. La superficie mostró `Story sin story · UNKNOWN`.
6. No existía selector ni acción normal para materializar una Story READY.
7. El selector visible `EDIT / CREATE / RENAME` pertenecía al SourceDraftBuffer; no era un selector de Story.
8. El Owner se detuvo sin usar terminal, API manual, JSON seed ni project writes.

## Finding confirmado

`CAP-13D01-STORY-ACTIVATION-002` — el producto disponía de `StoryExecutionApplicationService.prepare()`
y `start()`, pero no existía un bridge productivo Planning FROZEN → StoryExecution en API/UI.

La brecha no está en transporte, autenticación ni en el core de StoryExecution. Está en la integración:

`FROZEN Sprint READY story → DoR → StoryContextPack → StoryExecution PLANNED → Owner start → IN_PROGRESS`.

## Corrective autorizado

Corrective bounded, sin E1/E2/E3 y sin Full Regression:

- proyectar Stories READY desde el Sprint FROZEN;
- exponer status/prepare/start tipados y RBAC-bound;
- reutilizar el StoryExecution core vigente;
- presentar DoR, StoryContextPack y route/provenance en Story Code;
- no escribir source durante activation;
- no mutar Planning FROZEN;
- preparar la exclusión de Stories DONE para el ciclo posterior D05;
- preservar Manual como first-class;
- provider/model no puede conceder tool/source/apply/approval authority.

## Accounting

- `operator_project_writes=0`.
- `normal_user_terminal_escapes=0`.
- `full_regression_runs=0`.
- S0/S1 observados: 0.
- D02 no iniciado.

## Estado del checkpoint

`13-D-01` permanece abierto hasta retest browser sobre el corrective Windows-validado.
