---
doc_id: "ADR-GSDLC-002"
title: "ADR-GSDLC-002 — Platform, workspace engineering and runtime state separation"
status: "reviewed"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-08-14"
approval: "pending_owner_00_c_adjudication"
program_id: "DEVPL-GSDLC"
micro_sprint: "DEVPL-GSDLC-00-C"
runtime_implemented: false
---
# ADR-GSDLC-002 — Platform, workspace engineering and runtime state separation

## Contexto

`.devpilot/project_state.json` describe la evolución de **DevPilot como producto**. Usarlo también como máquina de estados de cada proyecto gestionado mezclaría dos agregados distintos y haría frágil la reanudación, los tests y la trazabilidad.

## Decisión

Separar tres dominios:

| Dominio | Owner | Persistencia objetivo | Autoridad |
|---|---|---|---|
| `PlatformState` | gobierno de la plataforma | repo DevPilot `.devpilot/project_state.json` | baseline/programa de DevPilot |
| `WorkspaceEngineeringState` | `GuidedSDLCService/WorkflowEngine` | store local por `workspace_id`, reconstruible desde metadata + artifacts + Git | fase/paso/artifacts/gates/next action |
| `RuntimeOperationalState` | servicios runtime | SQLite/JSONL/runtime local | sessions/jobs/approvals/locks/agent runs |

`WorkspaceEngineeringState` no almacena credenciales ni logs efímeros y no sustituye Git ni los documentos canónicos.

## Reconciliación

En `open/resume` se compara el fingerprint anterior con:

- Git HEAD/branch/dirty;
- hashes de artifacts gobernados;
- metadata del workspace;
- gates aprobados.

Si un archivo fue modificado externamente, DevPilot no lo sobreescribe. El artifact afectado pasa a `REVALIDATION_REQUIRED`, se invalidan approvals derivados cuando corresponda y se recalcula `next_action`.

## Restart

El estado de ingeniería debe recuperarse sin depender de memoria de proceso. El estado runtime puede expirar/reconciliarse, pero nunca convertir un job perdido en PASS.

## Invariantes

- source state ≠ engineering state ≠ runtime state;
- ningún estado derivado prevalece silenciosamente sobre un Git/source más reciente;
- approvals son runtime auditables, no texto editable en el source;
- la máquina de estados debe ser reconstruible.

## Estado de implementación

`planned-GSDLC`; la persistencia concreta se implementará en GSDLC-01.
