---
doc_id: "POST-H-013-C-VERIFIER-V2-REPORT"
title: "POST-H-013-C — Verifier v2 de integridad local"
status: "approved"
owner: "Ordóñez"
updated: "2026-06-27"
phase: "POST-FASE-H"
source_of_truth: "docs/backlogs/POST-H-013_audit_pack_integrity.md"
---

# POST-H-013-C — Verifier v2 de integridad local

## Resultado

Estado: `implemented-initial`.

Se implementó un verificador local para audit packs v2 capaz de validar el manifest embebido, comprobar hashes SHA-256 por archivo, detectar archivos faltantes, detectar miembros ZIP extra no declarados y generar un integrity report local.

## Alcance implementado

```text
- `src/devpilot_core/auditpack/verify_v2.py`.
- CLI `python -m devpilot_core audit-pack verify-v2 --pack <pack>.zip --json`.
- Validación de manifest contra `AuditPackManifestV2`.
- Verificación del self-hash del manifest.
- Verificación de existencia y SHA-256 por cada archivo declarado.
- Detección de archivos extra no declarados.
- Detección de drift de safety flags y compliance claim.
- Generación de `AuditPackIntegrityReport` bajo `outputs/auditpacks`.
```

## Seguridad y límites

```text
local_first=true
network_used=false
external_api_used=false
remote_export_used=false
source_mutations_performed=false
remote_execution_enabled=false
connector_write_enabled=false
plugin_execution_enabled=false
compliance_certification_claimed=false
```

El verificador escribe evidencia runtime bajo `outputs/auditpacks`, pero no modifica archivos fuente. Firma y cifrado permanecen diferidos para POST-H-013-D. La integración al quality gate final queda para POST-H-013-E.

## Validación esperada

```powershell
python -m pytest -p no:ddtrace tests/test_post_h_013_audit_pack_integrity.py tests/test_audit_pack_manifest_v2_schema.py -q
python -m devpilot_core audit-pack build-v2 --execute --json
python -m devpilot_core audit-pack verify-v2 --pack outputs/auditpacks/<pack>.zip --json
python -m devpilot_core schema validate --schema-id AuditPackIntegrityReport --instance outputs/auditpacks/<pack>_integrity_report.json --json
```
