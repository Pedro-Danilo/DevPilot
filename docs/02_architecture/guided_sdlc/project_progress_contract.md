---
doc_id: "DEVPL-GSDLC-01-C-PROJECT-PROGRESS-CONTRACT"
title: "DEVPL-GSDLC-01-C — ProjectStatus and NextAction projection contract"
status: "implemented-initial"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-08-16"
approval: "pending_windows_owner_adjudication"
program_id: "DEVPL-GSDLC"
backlog_id: "DEVPL-GSDLC-01"
micro_sprint: "DEVPL-GSDLC-01-C"
source_repo: "repo_DevPilot_Local_350_DEVPL_GSDLC_01_B_DETERMINISTIC_WORKFLOW_ENGINE.zip"
source_git_commit: "c6a720d1c8b329566bdd56af79ff23a4f6582c33"
source_repo_sha256: "f293f8e314fed766f410413fa47b094ee00f017436fb668fbccd33467c3cffda"
local_first: true
read_only: true
preliminary: true
---

# DEVPL-GSDLC-01-C — ProjectStatus and NextAction projection contract

## 1. Propósito

Definir una única semántica determinística, read-only y serializable para proyectar el estado durable de un workspace como `ProjectStatus` y su recomendación `NextAction`.

La proyección consume exclusivamente autoridad ya materializada por `WorkspaceEngineeringState` y `WorkflowEngine`. No consulta un LLM, no ejecuta acciones, no modifica estado, no llama Git directamente y no crea todavía una ruta HTTP o UI.

## 2. Boundary

```text
WorkspaceEngineeringState
        +
WorkflowEngine / TransitionCatalog
        ↓
ProjectProgressEngine
        ├── ProjectStatus
        └── NextAction
        ↓
GuidedSDLCService
        ↓
GuidedSDLCApplicationService
        ↓
ApplicationService (read-only capabilities)
```

La UI futura de 01-E debe consumir esta semántica. No se permite duplicarla en TypeScript.

## 3. ProjectStatus v1

Incluye identidad workspace/project, fase, current step, lifecycle, progreso 0..100, resumen MIPSoftware/MIASI, readiness de artifacts, planning, blockers ordenados, approvals pendientes, quality, snapshot Git, revalidation, model budget, freshness, source refs y referencia a NextAction.

## 4. NextAction v1

`NextAction` es una recomendación, nunca una ejecución. Su prioridad determinística es:

1. `INSPECT_STATE` — estado corrupto/desconocido;
2. `REVALIDATE` — `REVALIDATION_REQUIRED`;
3. `RESOLVE_BLOCKER` — blockers/gates;
4. `OBTAIN_APPROVAL` — approvals pendientes;
5. `CONTINUE_STEP` — artifacts/prerequisites/step work;
6. `ADVANCE_TRANSITION` — transición válida en preview;
7. `COMPLETE` — estado terminal.

Cada acción incluye reason code, explicación, target phase/step, transition id cuando aplique, navigation placeholder, prerequisites, approval flag, mutating/dry-run metadata, disponibilidad, disabled reason y evidencia esperada.

## 5. Freshness

La proyección no convierte la edad de un timestamp en verdad de ingeniería. Se usa fingerprint del state cargado/esperado. `STALE` significa mismatch de fingerprint, no una heurística de edad.

La reconciliación real filesystem/Git pertenece a DEVPL-GSDLC-01-D.

## 6. Señales no disponibles todavía

Esta primera versión no fabrica información de capacidades posteriores:

- MIASI: `UNKNOWN` mientras `WorkspaceEngineeringState v1` no materialice applicability/state MIASI;
- model/token/cost budget: `NOT_AVAILABLE / GSDLC_06_NOT_IMPLEMENTED`;
- Git: se proyecta únicamente el snapshot persistido; 01-D será autoridad de drift real;
- navigation target: placeholder/disabled cuando la vista pertenece a una ola futura;
- Project Status HTTP/API/UI: 01-E.

Estas limitaciones son explícitas.

## 7. Seguridad

- outputs sanitizados;
- no session/job/runtime payloads;
- no credentials/tokens;
- no network/external API;
- no source mutation;
- no transition execution;
- ningún model/agent influye en prioridad o autoridad.

## 8. Compatibilidad histórica

01-A y 01-B conservan snapshots pre-owner. La autoridad final se expresa mediante adjudicaciones y campos sucesores. No se reescriben contratos UOC ni snapshots GSDLC-00/R01.

## 9. Evolución posterior requerida

Esta es una **primera versión production-oriented del projection kernel**, no la experiencia industrial completa. Evoluciona con 01-D (reconciliation), 01-E (HTTP/UI/browser), GSDLC-05 (workflow artifact/dependency) y GSDLC-06 (budget real).
