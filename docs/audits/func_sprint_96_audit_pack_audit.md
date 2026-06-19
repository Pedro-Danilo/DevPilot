---
title: "Auditoría FUNC-SPRINT-96 — Colaboración local y audit packs"
doc_id: "DEVPL-AUDIT-FUNC-SPRINT-96"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-06-19"
approval: "approved"
---

# Auditoría FUNC-SPRINT-96 — Colaboración local y audit packs

## Estado

`implemented-initial`.

## Propósito

Implementar audit packs locales para colaboración documental y revisión offline con manifest, checksums y verificación de integridad.

## Alcance implementado

- `AuditPackBuilder`.
- CLI `audit-pack build --json`.
- CLI `audit-pack verify --path outputs/auditpacks/<pack>.zip --json`.
- Schema `SCHEMA-DEVPL-AUDIT-PACK-MANIFEST-V1`.
- Suite safety `audit-pack-integrity`.
- MIASI tools/policies para build/verify.
- Runbook dedicado.

## Funcionamiento

El builder recolecta evidencias controladas, excluye rutas sensibles, escanea texto con `SecretGuard`, calcula SHA-256 por entrada y escribe un ZIP bajo `outputs/auditpacks`. El verifier recalcula checksums y bloquea manifest ausente, rutas prohibidas, secretos y contenido alterado.

## Integración

La capacidad se integra con `IdentityRegistry`, `PathGuard`, `SecretGuard`, MIASI, `EvalRunner`, `QualityGate`, `ReportEngine` y `ValidationGateway`.

## Criterios PASS

- `audit-pack build --json` retorna `ok=true`.
- `audit-pack verify` retorna `ok=true` sobre pack generado.
- El pack contiene `audit-pack-manifest.json`.
- Los checksums verifican.
- No se exportan secretos, providers locales ni runtime DB.

## Criterios BLOCK

- Manifest ausente.
- Checksum mismatch.
- `.env`, `.devpilot/providers.yaml` o `.devpilot/devpilot.db` dentro del ZIP.
- SecretGuard detecta contenido sensible.
- Uso de red, API externa o cloud export.

## Riesgos

Esta versión no cifra ni firma packs. No implementa colaboración cloud, multiusuario real ni auditoría de recepción. La exportación de runtime DB está bloqueada hasta una ADR futura.

## Comandos de verificación

```powershell
python -m devpilot_core audit-pack build --json
python -m devpilot_core audit-pack verify --path outputs/auditpacks/<pack>.zip --json
python -m devpilot_core eval run --suite audit-pack-integrity --json
python -m pytest tests\test_audit_pack.py tests\test_sprint_96_documentation.py -q
```

## Veredicto

Sprint implementado como primera versión segura y local-first para colaboración offline basada en evidencias verificables.
