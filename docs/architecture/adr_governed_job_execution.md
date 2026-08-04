---
doc_id: "ADR-UOC-000-GOVERNED-JOB-EXECUTION"
title: "ADR UOC-000 — Governed job execution"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-08-04"
approval: "approved_by_owner"
created_by: "UOC-000"
canonical_commit: "43254e3e61cdafe65e0ed2d773fe9032b0a81f05"
local_first: true
external_api_required: false
preliminary: false
decision: "typed-governed-jobs"
---

# ADR UOC-000 — Governed job execution

## Estado

Aprobada como contrato base; runtime pendiente de UOC-007/UOC-008.

## Contexto

Las operaciones de calidad, validación, Git, release, RAG y agentes pueden ser
costosas o mutantes. Ejecutarlas sin job model impide timeout, cancelación,
heartbeat, trazabilidad y rollback.

## Decisión

Toda operación UI no trivial se representará como `GovernedJob`:

```text
planned → pending-approval → approved → running
→ pass | pass-with-gaps | block | error | cancelled | rolled-back
```

El job queda vinculado a capability, workspace, actor, policy decision, input
hash, timeout, retry limit y evidence references.

## Invariantes

- timeout por defecto 900 s y máximo 7200 s;
- máximo dos reintentos;
- máximo dos jobs paralelos por instancia local;
- heartbeat cada cinco segundos;
- no loops autónomos ilimitados;
- cancelación no implica rollback automático;
- mutación exige plan y approval cuando el riesgo sea sensible;
- logs sanitizados y paginados;
- postcondición obligatoria antes de PASS.
