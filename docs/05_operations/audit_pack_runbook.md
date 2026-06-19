---
title: "DevPilot Local — Audit Pack Runbook"
doc_id: "DEVPL-OPS-AUDIT-PACK-RUNBOOK-001"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-06-19"
approval: "approved"
---

# DevPilot Local — Audit Pack Runbook

## Estado

`FUNC-SPRINT-96 — Colaboración local y audit packs` implementa una primera versión `implemented-initial` de paquetes de auditoría locales.

## Propósito

Permitir que DevPilot comparta evidencia documental y técnica para revisión offline sin depender de plataforma cloud ni exportar secretos o estado runtime sensible.

## Comandos

```powershell
python -m devpilot_core audit-pack build --json
python -m devpilot_core audit-pack verify --path outputs/auditpacks/<pack>.zip --json
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
