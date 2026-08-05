---
doc_id: "DEVPL-UOC-001-READ-ONLY-DOCUMENTS-REPORT"
title: "UOC-001 — Workspace Documents read-only implementation audit"
status: "implemented-initial"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-08-04"
created_by: "UOC-001"
canonical_base_commit: "a986f83a7c2da99a734c88feb80bf5d66cde2e4a"
preliminary: true
---

# UOC-001 — Workspace Documents read-only implementation audit

## 1. Decisión de implementación

UOC-001 implementa la primera superficie operacional documental de DevPilot:
`/workspace/documents`. La versión es **preliminar y deliberadamente read-only**.
El cierre definitivo requiere validación Windows, API/UI contracts, pruebas de
seguridad negativas y aceptación browser sobre `inventory-sales-local`.

## 2. Capacidades incorporadas

- árbol paginado y búsqueda por nombre/ruta;
- filtros por extensión y categoría;
- visor Markdown seguro sin `innerHTML`;
- visor JSON estructurado y raw seguro;
- breadcrumbs y deep-link por `document_id` opaco;
- contexto de workspace activo visible;
- enlaces desde Dashboard;
- endpoints list/read/metadata protegidos y tipados;
- límites de 2500 archivos, profundidad 12, 250 items/página y 1 MiB inline;
- cero escritura, red, API externa, shell, connector o plugin.

## 3. Controles de seguridad

El root se deriva del registry/contexto activo del servidor. El navegador no
suministra rutas absolutas. Se excluyen `.git`, `.env`, `.venv`, `node_modules`,
caches, SQLite y outputs sensibles; se bloquean binarios, encoding no UTF-8,
ADS-like names, symlinks y reparse points. Las extensiones iniciales son `.md`,
`.json`, `.yaml`, `.yml` y `.txt`.

## 4. UX

La vista dispone de loading, empty, ready, error y BLOCK; navegación por teclado,
árbol semántico, foco visible, layout de dos paneles, responsive a 900 px y 560
px, paginación y feedback explícito de solo lectura.

## 5. Limitaciones

- no hay full-text search, historial/diff Git ni frontmatter enriquecido: UOC-002;
- no hay validaciones/readiness/findings: UOC-003;
- no hay edición, plan, approval, apply ni rollback: UOC-004/UOC-005;
- el renderer Markdown soporta una sintaxis segura mínima, no CommonMark completo;
- el guard de symlink/reparse tiene prueba unitaria determinística independiente de privilegios; la aceptación Windows debe crear y bloquear al menos un junction real, y registrar si el host permite un symlink real;
- la aceptación visual desktop/reduced viewport se genera manualmente.

## 6. Gate pendiente

La implementación no autoriza UOC-002 hasta que el operador Windows produzca
manifest PASS, capturas, zero-write proof, negative path matrix y baseline limpia.
