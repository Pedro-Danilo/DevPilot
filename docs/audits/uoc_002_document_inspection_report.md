---
doc_id: "DEVPL-UOC-002-DOCUMENT-INSPECTION-REPORT"
title: "UOC-002 — Metadata, Git history y búsqueda documental"
status: "implemented-initial"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-08-05"
approval: "pending_windows_acceptance"
base_commit: "9cb67b023c6ac909a2b492370632a3955a454e39"
preliminary: true
---

# UOC-002 — Metadata, Git history y búsqueda documental

## Decisión

La implementación de fuente queda `implemented-initial` sobre el árbol exacto
de `repo_329`. No se declara cerrada: falta aplicación y aceptación autoritativa
en Windows, integración Git y generación del siguiente baseline.

## Capacidades implementadas

- SHA-256, tamaño, mtime y frontmatter parseado;
- badges required/recommended/optional;
- estado Git clean/staged/unstaged/untracked/renamed/deleted;
- último commit, autor, fecha e historial paginado;
- diff read-only contra HEAD o SHA validado;
- truncación explícita cuando el diff supera presupuesto;
- búsqueda full-text local con caché incremental por hash/mtime;
- aislamiento del índice por workspace y sin persistencia externa;
- enlaces entrantes/salientes Markdown dentro del workspace;
- UI responsive con metadata, historial, diff, búsqueda y relaciones.

## Arquitectura y seguridad

La UI consume API tipada. `ApplicationService` delega en
`WorkspaceDocumentInspectionApplicationService`, que reutiliza el índice opaco
de UOC-001 y el `GitAdapter` read-only. No se construyen comandos Git desde
texto libre, no se acepta una ruta absoluta del browser y no se persiste el
contenido documental en una base externa.

## Pruebas focales ejecutadas en el entorno de construcción

```text
24 passed, 0 failed, 0 errors, 0 skipped
TypeScript strict typecheck: PASS
Python compile: PASS
```

Cobertura: repos clean/dirty/detached; staged/unstaged/untracked/renamed/deleted;
historial vacío; diff grande truncado; cache incremental; aislamiento entre
workspaces; contratos API/UI y zero-write.

## Limitaciones y riesgos residuales

- Build Vite no pudo ejecutarse en este entorno porque el registry interno de
  npm devolvió 404 al descargar el tarball de Vite; debe ejecutarse en Windows.
- El índice full-text v1 es lexical y en memoria; no es un motor de búsqueda
  semántica ni persiste entre reinicios.
- El parser de frontmatter es deliberadamente acotado y no sustituye la
  validación determinística de UOC-003.
- Git history/diff se limita a un repositorio local disponible y a budgets
  estrictos; no realiza fetch ni usa red.
- UOC-002 es primera versión y requiere evolución posterior en UOC-011 para
  accesibilidad, rendimiento y hardening final.

## PASS/BLOCK de cierre

PASS requiere tests focales, schemas/registries/TCR/OpenAPI, build Vite,
aceptación browser, seguridad negativa, zero-write, integración canónica,
sincronización origin, baseline exact-tree y S0/S1=0. Cualquier fuga entre
workspaces, lectura fuera del root, 2xx ante traversal, mutación o argumento Git
libre produce BLOCK.
