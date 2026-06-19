---
title: "Auditoría FUNC-SPRINT-93 — Plugin y connector ecosystem controlado"
doc_id: "DEVPL-AUDIT-FUNC-SPRINT-93"
version: "1.0.0"
updated: "2026-06-19"
approval: "internal"
status: "approved"
owner: "Ordóñez"
sprint: "FUNC-SPRINT-93"
---

# Auditoría FUNC-SPRINT-93 — Plugin y connector ecosystem controlado

## Estado

`implemented-initial`. Plugin loading ejecutable queda deshabilitado; solo se valida metadata y loader dry-run.

## Propósito

Crear una base de extensibilidad local para plugins y conectores internos sin permitir carga dinámica arbitraria.

## Alcance implementado

- Plugin Registry en `.devpilot/plugins/plugin_registry.json`.
- Schema `docs/schemas/plugin_manifest.schema.json`.
- CLI `plugin validate`, `plugin list` y `plugin dry-run`.
- Validación de policy ids, permisos, conectores, observabilidad y eval.
- Evaluación `plugin-ecosystem`.
- Eventos `plugin.dry_run.evaluated`.

## Funcionamiento

`plugin validate --json` valida schema y semántica. `plugin list --json` expone metadata pública. `plugin dry-run --plugin local.docs.plugin --operation metadata --dry-run --json` simula carga metadata-only y emite traza local sin importar ni ejecutar código.

## Integración

Integra `SchemaValidator`, `ConnectorRegistry`, `PolicyEngine`, `PathGuard`, `SecretGuard`, `EventLogger`, MIASI y `quality-gate run --profile ci`.

## Criterios PASS

- Registry valida.
- Policy ids existen en MIASI.
- Conectores referenciados existen.
- Permisos son safe read/report/simulation.
- `plugin_code_loaded=false`.
- `arbitrary_code_execution_performed=false`.

## Criterios BLOCK

- `execution_enabled=true`.
- EntryPoints importables o shell/network.
- Permisos sin policy.
- Conectores inexistentes.
- Red, API externa, shell, ejecución remota o secretos reales.

## Riesgos

La capacidad es preliminar: no hay sandbox de ejecución real, instalación de paquetes, firma de plugins, marketplace, version resolution, compatibilidad ABI ni permisos dinámicos.

## Comandos de verificación

```powershell
python -m devpilot_core plugin validate --json
python -m devpilot_core plugin list --json
python -m devpilot_core plugin dry-run --plugin local.docs.plugin --operation metadata --dry-run --json
python -m devpilot_core eval run --suite plugin-ecosystem --json
python -m devpilot_core quality-gate run --profile ci --json
```

## Veredicto

Sprint 93 queda implementado como base controlada de ecosistema plugin/conector. Es apto para validación local y trazabilidad, no para ejecución real de plugins.
