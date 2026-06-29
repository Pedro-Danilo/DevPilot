---
doc_id: "POST-H-017-B-ENVIRONMENT-SNAPSHOT-REPORT"
title: "POST-H-017-B — Environment snapshot redactado"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-06-29"
approval: "approved_by_owner"
---

# POST-H-017-B — Environment snapshot redactado

## Resultado

Estado: `implemented-initial`.

Se implementó un snapshot local redactado para evidencia de reproducibilidad de release. El comando focal es:

```powershell
python -m devpilot_core release environment-snapshot --json --write-report
```

Cuando se usa `--write-report`, genera:

```text
outputs/release/environment_snapshot.json
outputs/release/environment_snapshot.md
```

Estos outputs son runtime evidence y no deben versionarse.

## Controles de seguridad

```text
local_first=true
dry_run=true
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
- Captura versión Python e implementación.
- Captura plataforma local básica.
- Registra presencia de pyproject.toml, ui/web/package.json y ui/web/package-lock.json.
- Extrae nombres de dependencias declaradas desde manifiestos locales.
- No ejecuta package managers.
- No lee .env ni valores de entorno.
- No llama red ni APIs externas.
```

## Limitaciones

POST-H-017-B no construye todavía el release reproducibility pack completo, no genera source archive manifest, no calcula checksums y no implementa verifier local. Esas capacidades quedan para POST-H-017-C/D/E.

## Criterios PASS

```text
PASS si el snapshot valida contra ReleaseEnvironmentSnapshot.
PASS si secrets_included=false.
PASS si env_files_read=false y secret_values_read=false.
PASS si el caso negativo con .env sintético no filtra valores.
PASS si documentación, project_state y TCR quedan sincronizados.
```
