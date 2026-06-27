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

## Verifier v2 — POST-H-013-C

Objetivo: verificar localmente un audit pack v2 recibido o generado antes de usarlo como evidencia.

```powershell
python -m devpilot_core audit-pack verify-v2 --pack outputs/auditpacks/<pack>.zip --json
```

El comando valida schema, self-hash del manifest, existencia de miembros declarados, SHA-256 por archivo y ausencia de miembros extra. Genera un integrity report bajo `outputs/auditpacks/<pack_id>_integrity_report.json`.

Criterios de aceptación:

```text
manifest_schema_valid=true
manifest_hash_valid=true
files_total=files_verified
missing_files_total=0
hash_mismatches_total=0
extra_files_total=0
compliance_certification_claimed=false
network_used=false
external_api_used=false
```

Este reporte es evidencia runtime local, no fuente de verdad versionada. No se debe incluir en ZIPs limpios de entrega; debe regenerarse en el entorno del operador.


## Crypto local opcional — POST-H-013-D

`audit-pack build-v2` soporta firma y cifrado local opcional únicamente mediante banderas explícitas. El flujo base sin crypto debe seguir funcionando.

Dry-run con intención crypto sin escribir artefactos:

```powershell
python -m devpilot_core audit-pack build-v2 --dry-run --sign optional --encrypt optional --json
```

Ejecución con keyfile externo al repositorio:

```powershell
python -m devpilot_core audit-pack build-v2 `
  --execute `
  --sign optional `
  --encrypt optional `
  --crypto-keyfile C:\ruta\externa\auditpack.key `
  --json
```

Verificación de sidecars crypto:

```powershell
python -m devpilot_core audit-pack verify-v2 `
  --pack outputs/auditpacks/<pack>.zip `
  --signature outputs/auditpacks/<pack>.sig.json `
  --encrypted-pack outputs/auditpacks/<pack>.zip.fernet `
  --crypto-keyfile C:\ruta\externa\auditpack.key `
  --json
```

Controles de seguridad:

```text
- No se permite keyfile dentro del repo.
- No se usa red ni API externa.
- No se usa KMS remoto.
- La firma/cifrado se ejecuta después de redaction y policy checks.
- El cifrado no puede ocultar errores de secretos o integridad.
```

Limitación explícita: esta es una primera versión local opcional, no una PKI enterprise ni una certificación de compliance. POST-H-013-E debe cerrar el subgate y los disclaimers operativos finales.
