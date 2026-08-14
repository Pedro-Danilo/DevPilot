---
doc_id: "ADR-GSDLC-001"
title: "ADR-GSDLC-001 — Guided SDLC Engine boundary"
status: "reviewed"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-08-14"
approval: "pending_owner_00_c_adjudication"
program_id: "DEVPL-GSDLC"
micro_sprint: "DEVPL-GSDLC-00-C"
runtime_implemented: false
---
# ADR-GSDLC-001 — Guided SDLC Engine boundary

## Contexto

00-B convierte la experiencia idea→release en requisitos `planned`. DevPilot ya dispone de `ApplicationService`, PolicyEngine, validators, workspaces, approvals, jobs, Git gobernado, Quality, RAG/agentes y UI operacional, pero no existe todavía un orquestador de estado de ingeniería que guíe una construcción completa.

## Decisión

Introducir en GSDLC-01 un bounded context de aplicación compuesto por `GuidedSDLCService` y `WorkflowEngine`.

La cadena obligatoria será:

```text
UI / API / CLI expert
→ ApplicationService
→ GuidedSDLCService
→ WorkflowEngine
→ typed domain services
→ Policy / Approval / GovernedJob
→ Evidence / Traces
```

`WorkflowEngine` es determinístico. Calcula transiciones, prerequisites, blockers y `next_action` a partir de contratos versionados MIPSoftware/MIASI y resultados verificables. Un LLM puede proponer contenido o planes, pero **nunca** decide PASS/BLOCK, permisos, approvals ni transiciones.

## Ownership

- `ApplicationService`: frontera de entrada y DTO/policy boundary.
- `GuidedSDLCService`: caso de uso project-centric y coordinación.
- `WorkflowEngine`: estado/transiciones determinísticos.
- domain services: artifacts, planning, code, tests, Git, release.
- Policy/Approval/Jobs: side effects y autoridad.
- Evidence/Trace: evidencia de cada transición.

## Invariantes

1. No UI→filesystem/Git/core.
2. No arbitrary shell.
3. No autonomous unbounded loop.
4. No agent self-approval.
5. Toda mutación usa typed operation y pre/postconditions.
6. El workflow puede funcionar sin LLM.

## Consecuencias

Positivas: una sola semántica para UI/CLI/API y continuidad desde idea hasta release.

Costo: añade una capa de orquestación y requiere reconciliación robusta con Git/ediciones externas.

## Estado de implementación

`planned-GSDLC`. Este ADR no crea clases, endpoints ni rutas.
