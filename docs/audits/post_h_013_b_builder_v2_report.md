---
doc_id: "POST-H-013-B-BUILDER-V2-REPORT"
title: "POST-H-013-B — Builder v2 con checksums y redaction report"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-06-27"
approval: "approved_by_owner"
phase: "POST-FASE-H"
local_first: true
dry_run_default: true
no_external_apis_used: true
no_remote_execution_enabled: true
no_connector_write_enabled: true
no_plugin_execution_enabled: true
compliance_certification_claimed: false
---

# POST-H-013-B — Builder v2 con checksums y redaction report

## Propósito

Documentar la implementación inicial del builder v2 de audit packs locales. La capacidad transforma la política y los schemas de POST-H-013-A en un flujo ejecutable controlado para planear o construir un audit pack v2 con evidencia de integridad y redacción.

## Resultado

Estado: `implemented-initial`.

Se implementó `AuditPackV2Builder` con dos modos:

- `dry-run`: modo por defecto; calcula selección, exclusiones, checksums, manifest en memoria y redaction report en memoria sin escribir pack artifacts.
- `execute`: modo explícito; escribe ZIP, manifest v2 sidecar y redaction report sidecar bajo `outputs/auditpacks`.

## Controles de seguridad

- Local-first.
- Sin red.
- Sin APIs externas.
- Sin KMS remoto.
- Sin connector write.
- Sin plugin execution.
- Sin remote execution.
- Sin claim de certificación compliance.
- Exclusión de `.env`, `.devpilot/devpilot.db`, `.devpilot/agent_sessions/**`, outputs crudos, llaves y carpetas de secretos.
- BLOCK si `SecretGuard` detecta secreto material.

## Evidencia esperada

```powershell
python -m devpilot_core audit-pack build-v2 --dry-run --json
python -m devpilot_core audit-pack build-v2 --execute --json
python -m pytest -p no:ddtrace tests/test_post_h_013_audit_pack_integrity.py tests/test_audit_pack_manifest_v2_schema.py -q
```

## Limitaciones

POST-H-013-B no implementa `verify-v2`, firma ni cifrado. Tampoco integra todavía el subgate final `audit-pack-integrity` al quality gate. Esos controles quedan para POST-H-013-C/D/E.
