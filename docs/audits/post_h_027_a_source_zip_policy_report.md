---
doc_id: "POST-H-027-A-SOURCE-ZIP-POLICY-REPORT"
title: "POST-H-027-A — Source ZIP release policy hardening report"
status: "approved"
version: "1.0.0"
owner: "Ordonez"
phase: "POST-FASE-H"
updated: "2026-07-08"
---

# POST-H-027-A — Source ZIP release policy hardening report

Estado: `implemented-initial / source-zip-release-policy-hardening`.

## Alcance implementado

POST-H-027-A agrega una politica versionada, schema-backed y auditable para ZIP fuente limpio. El validador `SourceZipReleasePolicyValidator` inspecciona el arbol fuente y, opcionalmente, un ZIP candidato sin extraerlo.

## Artefactos

- `docs/schemas/source_zip_release_policy.schema.json`
- `docs/schemas/source_zip_release_report.schema.json`
- `.devpilot/release/source_zip_release_policy.json`
- `src/devpilot_core/release/source_zip_policy.py`
- `tests/test_post_h_027_source_zip_policy.py`

## PASS/BLOCK

PASS requiere que los includes criticos existan, que runtime/build artifacts queden excluidos, que SecretGuard no detecte secretos materiales, que el reporte valide contra schema y que no se habilite publicacion, deploy, red, APIs externas, remote execution, connector write ni plugin execution.

BLOCK se produce si el ZIP candidato contiene `outputs/`, `dist/`, `.git/`, `.venv/`, `node_modules/`, `.devpilot/devpilot.db`, backups, agent sessions, RAG runtime, providers.yaml, secretos por path o secretos textuales.

## Limitaciones

Esta es una primera version de hardening de ZIP fuente. Wheel/sdist install verification, artifact manifest/checksums, Windows install smoke y upgrade/rollback dry-run quedan para POST-H-027-B/C/D/E.
