---
doc_id: "DEVPL-UOC-007-GOVERNED-JOB-FRAMEWORK"
title: "UOC-007 — CLI Capability Registry and Governed Job Framework"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-08-10"
approval: "approved_by_owner"
---

# UOC-007 — CLI Capability Registry and Governed Job Framework

## 1. Propósito

UOC-007 introduce la infraestructura común para representar capacidades CLI como trabajos gobernados sin convertir la Web UI en una terminal ni habilitar ejecución arbitraria. El framework es local-first, tipado, no-shell y conserva como autoridad los contratos de política, budgets, dry-run, approval y evidencia.

## 2. Arquitectura

```text
CLI capability inventory
  → governed_job_capability_registry.json
  → request/result contracts
  → GovernedJobFramework.plan()
  → immutable request fingerprint
  → idempotency + correlation
  → approval gate cuando corresponda
  → queued/running solo con typed adapter explícitamente bound
  → heartbeat/cancel/result/rollback lifecycle
  → atomic runtime JSON state under outputs/runtime/governed_jobs
```

No existe descubrimiento dinámico de handlers, no se construyen comandos shell y UOC-007 no añade una ruta UI nueva.

## 3. Capability registry

Fuente versionada:

```text
.devpilot/interfaces/governed_job_capability_registry.json
```

El registry cubre exactamente las 193 capacidades clasificadas en `ui_capability_registry.json`. Cada entrada declara:

- `capability_id` y comando CLI de origen;
- Application Service conocido, si existe;
- risk class y parity status;
- policy binding;
- timeout, retry y heartbeat budgets;
- request/result envelope schemas;
- `CommandResult` como contrato normalizado;
- dry-run, approval, cancel y rollback flags;
- evidence mapping;
- estado de runtime.

En UOC-007 todas las capacidades permanecen `execution_enabled=false` y `adapter_bound=false`. Las no prohibidas pueden crear un plan de job; una ejecución real queda bloqueada hasta que un sprint posterior registre un input schema específico y un typed adapter.

## 4. Job lifecycle

Estados autorizados:

```text
planned
pending-approval
approved
queued
running
pass
pass-with-gaps
block
error
cancel-requested
cancelled
rollback-running
rolled-back
expired
```

El transition graph es explícito; una transición no permitida produce bloqueo técnico y no reescribe silenciosamente el estado.

## 5. Idempotencia y correlación

El caller aporta `idempotency_key`, pero el store persiste únicamente SHA-256. La misma key con el mismo request fingerprint devuelve el job existente. La misma key con una solicitud diferente produce `GovernedJobConflict`.

Cada job usa un `correlation_id` opaco (`corr_*`). El cancel token (`ct_*`) se entrega solo al caller y el store conserva únicamente su hash.

## 6. Persistencia y evidencia

El estado runtime vive bajo:

```text
outputs/runtime/governed_jobs/
```

Por tanto, no entra en el repo ni en source ZIPs. Las escrituras usan archivo temporal + `os.replace` atómico. Los valores crudos de parámetros no se persisten: se guardan fingerprint y nombres de claves. Artifact/evidence refs sí quedan ligados al job.

## 7. Seguridad

Criterios PASS:

- cobertura registry exacta respecto de las capacidades UI/CLI vigentes;
- cero capability `forbidden` con planning/runtime enabled;
- cero ejecución habilitada sin typed input schema + adapter bound;
- sensitive execution exige approval;
- arbitrary shell = false;
- remote execution = false;
- connector write = false;
- plugin execution = false;
- external API required = false;
- raw tokens/idempotency keys/parameter values no se persisten.

Criterios BLOCK:

- capability no registrada;
- exceso de timeout/retry budget;
- idempotency conflict;
- transición inválida;
- cancel token inválido;
- runtime adapter no registrado;
- capability prohibida;
- ejecución sensible sin approval.

## 8. Limitaciones de esta primera versión

UOC-007 es una **primera versión de infraestructura**, no una Job Console productiva. Quedan deliberadamente para UOC-008:

- API/GUI de jobs;
- streaming/polling de logs;
- reconciliación de jobs huérfanos después de reinicio;
- locking multi-proceso;
- subprocess-tree cancellation;
- filtros operacionales y retry desde UI;
- UX completa de progress/timeout/cancelled/stale.

## 9. Verificación

La verificación debe cubrir los tests UOC-007, schemas, Project State, Documentation Governance, TCR v1/v2 y no-go gates. Como UOC-007 no añade ni cambia una superficie visible, browser acceptance no es requisito de este sprint; UOC-008 sí deberá realizarla al incorporar `/jobs`.
