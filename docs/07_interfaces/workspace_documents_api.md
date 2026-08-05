---
doc_id: "DEVPL-UOC-001-WORKSPACE-DOCUMENTS-API"
title: "UOC-001 — Workspace Documents API and UI contract"
status: "implemented-initial"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-08-04"
created_by: "UOC-001"
preliminary: true
---

# UOC-001 — Workspace Documents API and UI contract

## Routes

```text
GET /api/v1/workspace/documents
GET /api/v1/workspace/documents/{document_id}
GET /api/v1/workspace/documents/{document_id}/metadata
UI  /workspace/documents
```

Todas las rutas son locales, autenticadas, policy-bound y read-only. Un
`document_id` es un identificador opaco emitido por el servidor; no codifica una
ruta utilizable como autoridad. El servicio vuelve a descubrir el workspace y
solo resuelve IDs presentes en el índice gobernado.

## Error contract

- 400: identificador desconocido/malformado o parámetro inválido;
- 401: token ausente o inválido;
- 403: workspace no configurado, policy/path block;
- 413/403 semántico: archivo excede budget;
- 422/403 semántico: binario o encoding no permitido;
- 500: error controlado sin rutas absolutas ni secretos.

## Invariantes

```text
read_only=true
mutations_performed=false
absolute_paths_accepted_from_browser=false
symlink_following=false
external_api_used=false
```

## Evolución

UOC-002 añadirá metadata Git, historial, diff y búsqueda full-text mediante
adapters tipados. UOC-001 no ejecuta Git ni crea índices persistentes.
