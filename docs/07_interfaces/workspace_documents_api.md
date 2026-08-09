---
doc_id: "DEVPL-UOC-001-WORKSPACE-DOCUMENTS-API"
title: "UOC-001/UOC-002 — Workspace Documents API and UI contract"
status: "implemented-initial"
version: "2.0.0"
owner: "Ordóñez"
updated: "2026-08-05"
approval: "pending_windows_acceptance_uoc_002"
created_by: "UOC-001"
updated_by: "UOC-002"
preliminary: true
---

# UOC-001/UOC-002 — Workspace Documents API and UI contract

## Alcance

UOC-001 establece descubrimiento y lectura documental mediante IDs opacos.
UOC-002 complementa esa superficie con inspección técnica read-only, sin
introducir escritura, shell o persistencia externa de contenido.

## Rutas

```text
GET /api/v1/workspace/documents
GET /api/v1/workspace/documents/search
GET /api/v1/workspace/documents/{document_id}
GET /api/v1/workspace/documents/{document_id}/metadata
GET /api/v1/workspace/documents/{document_id}/history
GET /api/v1/workspace/documents/{document_id}/diff
GET /api/v1/workspace/documents/{document_id}/links
UI  /workspace/documents
```

## Contrato UOC-002

- metadata: SHA-256, tamaño, mtime, frontmatter parseado, badges y estado Git;
- history: commits paginados y limitados al archivo;
- diff: comparación contra `HEAD` o SHA Git validado, con presupuesto y truncación explícita;
- search: índice incremental por hash/mtime, exclusivamente en memoria y aislado por workspace;
- links: enlaces Markdown entrantes y salientes resueltos solo dentro del root activo.

## Error contract

- `400`: ID, query, ref o parámetro inválido;
- `401`: token ausente o inválido;
- `403`: policy/path/workspace block;
- `404`: documento o recurso gobernado inexistente;
- `422`: contenido o encoding no permitido;
- `500`: error controlado sin rutas absolutas, secretos ni comandos raw.

## Controles obligatorios

```text
read_only=true
opaque_document_ids=true
browser_paths_authoritative=false
typed_git_adapter=true
free_form_git_arguments=false
search_index_persistence=memory-only
cross_workspace_search=false
document_content_external_persistence=false
mutations_performed=false
external_api_used=false
```

Archivos secretos y plano de control excluido por UOC-001 continúan invisibles,
incluso cuando estén versionados. Los budgets limitan commits, resultados y
bytes de diff. UOC-003 será responsable de validación y trazabilidad; UOC-002 no
reimplementa validators.


## UOC-003 validation and traceability contracts

UOC-003 adds an immutable `plan → execute → status` flow plus explicit-only traceability. Plans bind workspace fingerprint, artifact hashes, scopes and bounded budgets. Execution writes only runtime report/trace evidence under the active workspace; it never modifies source documents. Findings include opaque document identifiers, line and section navigation where available.

Routes:

- `POST /api/v1/workspace/validations/plan`
- `POST /api/v1/workspace/validations/execute`
- `GET /api/v1/workspace/validations/{job_id}`
- `GET /api/v1/workspace/traceability`

This is an initial synchronous implementation. Cancellation, heartbeat and durable asynchronous job recovery are deferred to UOC-007/UOC-008.


## UOC-004 — governed edit planning routes

- `POST /api/v1/workspace/edit-plans/plan` — creates an immutable plan bound to opaque document id and `document_sha_before`; no source write.
- `GET /api/v1/workspace/edit-plans/{plan_id}` — reads the process-local immutable plan.
- `POST /api/v1/workspace/edit-plans/{plan_id}/recheck` — rechecks optimistic concurrency against the current source SHA.

The browser never submits an absolute path. Markdown/JSON/YAML only. `.txt`, secrets, binaries and out-of-root resources remain non-editable. Exported patches are evidence only and are not executed.
