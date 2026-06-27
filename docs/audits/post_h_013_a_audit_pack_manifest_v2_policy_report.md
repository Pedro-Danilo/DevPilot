---
doc_id: "POST-H-013-A-AUDIT"
title: "POST-H-013-A — Audit pack manifest v2 y policy"
status: "implemented-initial"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-06-27"
approval: "approved_by_owner"
---

# POST-H-013-A — Audit pack manifest v2 y policy

## 1. Propósito

Este reporte documenta la implementación inicial de `POST-H-013-A`, orientada a definir el contrato machine-readable de audit packs v2 y la política local que gobernará los micro-sprints posteriores del backlog.

## 2. Estado

`implemented-initial`. El micro-sprint define schemas, política y pruebas contractuales. No implementa todavía builder v2, verifier v2, redaction runtime, firma ni cifrado.

## 3. Implementado

- `AuditPackManifestV2` con flags obligatorios `local_first=true`, `remote_export_used=false`, `network_used=false`, `external_api_used=false` y `compliance_certification_claimed=false`.
- `AuditPackIntegrityReport` para futuros reportes de verificación local.
- Política `.devpilot/auditpack/audit_pack_policy.json` con exclusiones para `outputs/**`, `.devpilot/devpilot.db`, `.devpilot/agent_sessions/**`, `.env`, llaves locales y carpetas de secretos.
- Registro de schemas en `docs/schemas/schema_catalog.json`.
- Test focal `tests/test_audit_pack_manifest_v2_schema.py`.

## 4. Criterios PASS

- Manifest v2 valida contra schema.
- La política excluye outputs, DB local, sesiones agentic crudas y secretos.
- No hay claim de compliance certificada.
- No se requiere red ni API externa.

## 5. Criterios BLOCK

- Cualquier manifest con `compliance_certification_claimed=true`.
- Cualquier manifest con `remote_export_used=true`.
- Cualquier política que omita `.env`, `.devpilot/devpilot.db`, `.devpilot/agent_sessions/**` u `outputs/**`.

## 6. Validación

```powershell
python -m pytest -p no:ddtrace tests/test_audit_pack_manifest_v2_schema.py -q
python -m devpilot_core schema validate --schema-id AuditPackManifestV2 --instance tests/fixtures/audit_pack_manifest_v2_sample.json --json
python -m devpilot_core schema list --json
```

## 7. Riesgos y límites

Esta versión es preliminar. La protección criptográfica y la verificación de ZIP reales quedan para POST-H-013-C/D. La generación de packs reales queda para POST-H-013-B. No se debe declarar compliance certificada ni subir packs a terceros por defecto.
