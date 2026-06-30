---
doc_id: "POST-H-017-C-SOURCE-ARCHIVE-MANIFEST-REPORT"
title: "POST-H-017-C — Source archive manifest y checksums"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-06-30"
approval: "approved_by_owner"
---

# POST-H-017-C — Source archive manifest y checksums

## Resultado

Estado: `implemented-initial`.

POST-H-017-C agrega evidencia local para auditar qué entraría al archivo fuente de release y qué artefactos críticos tienen checksum SHA-256. El comando focal es:

```powershell
python -m devpilot_core release source-archive-manifest --json --write-report
```

Cuando se usa `--write-report`, genera:

```text
outputs/release/source_archive_manifest.json
outputs/release/source_archive_manifest.md
outputs/release/source_archive_checksums.sha256
```

Estos outputs son runtime evidence y no deben versionarse.

## Controles de seguridad

```text
local_first=true
dry_run=true
read_only=true
network_used=false
external_api_used=false
env_files_read=false
secret_values_read=false
secrets_included=false
remote_execution_used=false
connector_write_used=false
plugin_execution_used=false
source_mutations_performed=false
```

## Alcance técnico

```text
- Inspecciona git archive HEAD en memoria cuando el repo conserva .git y filtra runtime/build/cache prohibidos antes de evaluar el manifest final.
- Usa deterministic-source-archive-plan en ZIPs limpios sin metadata Git.
- Detecta entradas prohibidas por policy de reproducibilidad.
- Calcula SHA-256 de artefactos críticos de release reproducibility.
- Registra ReleaseSourceArchiveManifest en schema catalog.
- Registra los grupos `release` y `portfolio` en CLI registry declarativo para preservar el no-growth gate acumulativo.
- Limpia de la allowlist temporal los comandos `release.*` y `portfolio.status` que ya no deben contarse como legacy.
- Mantiene el verifier local y quality gate final como alcance POST-H-017-D/E.
```

## Criterios PASS

```text
PASS si ReleaseSourceArchiveManifest valida contra schema.
PASS si forbidden_entries_total=0.
PASS si outputs/, .devpilot/devpilot.db, .venv/ y node_modules/ están declarados como prohibidos.
PASS si los checksums SHA-256 se generan para artefactos críticos presentes.
PASS si documentación, project_state y TCR quedan sincronizados.
```

## Criterios BLOCK

```text
BLOCK si el archivo fuente incluye outputs/, .devpilot/devpilot.db, .devpilot/agent_sessions/, .venv/ o node_modules/.
BLOCK si el manifest generado no valida contra ReleaseSourceArchiveManifest.
BLOCK si se usa red, API externa, remote execution, connector write o plugin execution.
BLOCK si se declara release reproducible final antes de POST-H-017-D/E.
```

## Riesgos y limitaciones

```text
- Los checksums no equivalen a firma criptográfica.
- En ZIPs sin .git, el inventario no puede probar literalmente git archive HEAD; usa fallback determinístico verificable.
- En checkouts Git con artefactos runtime históricamente versionados, POST-H-017-C reporta el source archive limpio planeado, no el tar bruto contaminado.
- La detección de checksum alterado contra pack final queda para POST-H-017-D.
- El subgate release-reproducibility queda para POST-H-017-E.
```
