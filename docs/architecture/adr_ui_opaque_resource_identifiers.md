---
doc_id: "ADR-UOC-000-OPAQUE-RESOURCE-IDENTIFIERS"
title: "ADR UOC-000 — Opaque resource identifiers"
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
decision: "opaque-identifiers-only"
---

# ADR UOC-000 — Opaque resource identifiers

## Estado

Aprobada.

## Contexto

La consola operará documentos, reports, traces, plans, approvals, jobs y
evidencia. Aceptar rutas absolutas del navegador permitiría traversal,
cross-volume access, junction escape o exposición de secretos.

## Decisión

El navegador enviará identificadores opacos emitidos por el backend. El backend
resolverá el identificador contra un registro bounded al workspace y volverá a
aplicar `PathGuard` antes de cada acceso.

Un identificador:

- no contiene una ruta absoluta;
- no revela el root físico;
- tiene longitud máxima 256;
- está ligado a workspace, tipo de recurso y versión/hash;
- expira o se invalida cuando cambia el registro correspondiente.

## Controles

- bloqueo de `..`, UNC, ADS, symlink y junction escape;
- allowlist de extensiones y tamaños;
- comparación de canonical paths;
- no inclusión de `.git`, `.env`, SQLite, tokens o secretos;
- respuesta uniforme ante ID inexistente, expirado o de otro workspace.
