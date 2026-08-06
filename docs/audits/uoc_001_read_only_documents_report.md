---
doc_id: "DEVPL-UOC-001-READ-ONLY-DOCUMENTS-REPORT"
title: "UOC-001 — Workspace Documents read-only implementation audit"
status: "closed/PASS"
version: "1.1.0"
owner: "Ordóñez"
updated: "2026-08-05"
created_by: "UOC-001"
canonical_base_commit: "a986f83a7c2da99a734c88feb80bf5d66cde2e4a"
preliminary: "true"
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


## Browser acceptance corrective v1.0.4

The initial browser acceptance contract incorrectly treated `traceability_matrix.md`
and authored ADR documents as UOC-001 prerequisites, even though the approved
sequence creates them during POST-H-EVAL-002-02-B. The corrected gate is
sequence-aware and policy-aligned: every materialized pre-code document that
satisfies the authoritative UOC-001 visibility policy must be visible, while
private control-plane files must remain intentionally hidden and future 02-B
deliverables are reported as planned rather than fabricated.

The responsive acceptance now requires a portrait viewport of at least 360×640
at 100% browser zoom, visible keyboard focus, consistent workspace context, and
coherent document/folder counts. A screenshot that merely scales the desktop
layout does not satisfy the UX gate.


## 7. Evidencia autoritativa de cierre

- Accepted source commit: `e9fe717eb8eafaca40830c691a7efb7bb956b035`.
- Browser acceptance SHA-256: `c826fbd0ba1c6bbd901f6bfce575073aa13a6f83bc8a21e6675455b5f47025eb`.
- Windows path-security SHA-256: `dd9a46cc80010eef4949eb1f575b8480d2dcd25b00b7cb80db1fbb3454a7c948`.
- Browser contract: sequence-aware and policy-aligned v3, zero-write, exact parity for UI-eligible documents and negative verification that policy-excluded control-plane files remain hidden.
- Future 02-B artifacts are classified as planned when absent, rather than falsely required from the read-only UOC-001 sprint.
- UX acceptance includes desktop, product vision/frontmatter, truthful YAML raw-safe evidence and genuine portrait reduced viewport captures at 100% browser zoom.
- The renderer remains preliminary; full CommonMark and advanced document inspection remain future work.
- The npm high-severity advisory remains an explicitly tracked residual risk; no dependency upgrade was applied silently during UOC-001.
