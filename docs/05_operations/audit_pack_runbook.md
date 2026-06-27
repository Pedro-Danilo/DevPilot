---
title: "DevPilot Local — Audit Pack Runbook"
doc_id: "DEVPL-OPS-AUDIT-PACK-RUNBOOK-001"
status: "approved"
version: "1.1.0"
owner: "Ordóñez"
updated: "2026-06-27"
approval: "approved"
---

# DevPilot Local — Audit Pack Runbook

## Estado

`FUNC-SPRINT-96` mantiene el builder v1. `POST-H-013-B` agrega el builder v2 `implemented-initial` con manifest v2, checksums por archivo y redaction report obligatorio.

## Propósito

Permitir que DevPilot comparta evidencia documental y técnica para revisión offline sin depender de plataforma cloud ni exportar secretos o estado runtime sensible.

## Comandos

```powershell
python -m devpilot_core audit-pack build --json
python -m devpilot_core audit-pack verify --path outputs/auditpacks/<pack>.zip --json
python -m devpilot_core audit-pack build-v2 --dry-run --json
python -m devpilot_core audit-pack build-v2 --execute --json
python -m devpilot_core eval run --suite audit-pack-integrity --json
```

## Contenido del pack

El pack incluye evidencias controladas:

- `README.md`;
- changelog local;
- manifests funcionales;
- auditorías de sprint;
- schema catalog;
- registries MIASI, identity, workspace, plugin y connector;
- fixtures de evaluación;
- reportes locales seguros cuando existen.

## Exclusiones obligatorias

El pack no debe incluir:

- `.env`;
- `.devpilot/providers.yaml`;
- `.devpilot/devpilot.db`;
- `.devpilot/agent_sessions/`;
- `.git/`;
- `.venv/`;
- `node_modules/`;
- `dist/`;
- caches;
- archivos de llaves o secretos.

## Verificación

`audit-pack verify` valida:

- ZIP válido;
- manifest embebido;
- checksums SHA-256;
- ausencia de rutas prohibidas;
- ausencia de patrones secret-like en contenido textual.

## Criterios PASS

- Build retorna `ok=true`.
- Verify retorna `ok=true`.
- `audit-pack-manifest.json` existe.
- `checksum_mismatches=0`.
- `forbidden_paths_total=0`.
- `secret_findings_total=0`.

## Criterios BLOCK

- Falta manifest.
- Hay checksum mismatch.
- Aparecen `.env`, providers locales, DB runtime o sesiones.
- SecretGuard detecta material sensible.
- Se intenta exportar DB runtime.

## Riesgos

Esta versión no implementa cifrado, firma digital, publicación remota, RBAC multiusuario ni verificación de identidad criptográfica del receptor. Es adecuada para colaboración local/offline controlada, no para distribución pública.

## Evolución pendiente

Sprints posteriores deben evaluar cifrado, firma, políticas de retención, perfiles de cumplimiento y trazabilidad de recepción/revisión.


## Builder v2 — POST-H-013-B

`audit-pack build-v2` usa la política `.devpilot/auditpack/audit_pack_policy.json` y el schema `AuditPackManifestV2`.

Modo dry-run por defecto:

```powershell
python -m devpilot_core audit-pack build-v2 --dry-run --json
```

Este modo no escribe ZIP, manifest sidecar ni redaction report sidecar. Solo calcula el plan de selección, exclusiones, hashes y redaction report en memoria.

Modo execute explícito:

```powershell
python -m devpilot_core audit-pack build-v2 --execute --json
```

Este modo escribe exclusivamente bajo `outputs/auditpacks`:

- `<pack_id>.zip`;
- `<pack_id>_manifest_v2.json`;
- `<pack_id>_redaction_report.json`.

El ZIP embebe:

- `audit-pack-manifest-v2.json`;
- `redaction_report.json`;
- archivos fuente/gobernanza permitidos por policy.

Si `SecretGuard` detecta secreto material, el resultado es BLOCK y no se escribe pack. Los ejemplos documentales explícitos con placeholders se tratan como documentación, no como secreto real.

Límites: `build-v2` no verifica packs recibidos, no firma y no cifra. Esas capacidades quedan para POST-H-013-C/D.
