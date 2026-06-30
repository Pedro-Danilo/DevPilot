---
title: "Runbook — Release reproducibility pack"
doc_id: "DEVPL-OPS-RELEASE-REPRODUCIBILITY"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-06-30"
approval: "approved_by_owner"
phase: "POST-H-017-C"
local_first: true
dry_run: true
---

# Runbook — Release reproducibility pack

## Propósito

Este runbook documenta la operación local de `POST-H-017 — Release reproducibility pack` hasta POST-H-017-C. La capacidad está en estado `implemented-initial`: produce evidencia local de policy, ambiente redactado, inventario de archivo fuente y checksums críticos, pero todavía no declara un release completamente verificable. El verifier local y el quality gate final quedan para POST-H-017-D/E.

## Comandos principales

```powershell
$env:PYTHONPATH="src"
python -m devpilot_core release environment-snapshot --json --write-report
python -m devpilot_core release source-archive-manifest --json --write-report
```

Validación de schemas:

```powershell
python -m devpilot_core schema validate `
  --schema-id ReleaseEnvironmentSnapshot `
  --instance outputs/release/environment_snapshot.json `
  --json

python -m devpilot_core schema validate `
  --schema-id ReleaseSourceArchiveManifest `
  --instance outputs/release/source_archive_manifest.json `
  --json
```

## Artefactos generados

```text
outputs/release/environment_snapshot.json
outputs/release/environment_snapshot.md
outputs/release/source_archive_manifest.json
outputs/release/source_archive_manifest.md
outputs/release/source_archive_checksums.sha256
```

Estos artefactos son evidencia runtime regenerable. No deben versionarse ni incluirse en ZIPs limpios de fuente.

## Criterios PASS

```text
PASS si ReleaseEnvironmentSnapshot valida contra schema.
PASS si ReleaseSourceArchiveManifest valida contra schema.
PASS si secrets_included=false, env_files_read=false y secret_values_read=false.
PASS si forbidden_entries_total=0 para el source archive manifest.
PASS si outputs/, .devpilot/devpilot.db, .venv/ y node_modules/ están declarados como exclusiones o entradas prohibidas.
PASS si los checksums SHA-256 de artefactos críticos se generan para los archivos presentes.
```

## Criterios BLOCK

```text
BLOCK si se lee contenido de .env o valores de secretos.
BLOCK si se detectan outputs/, .devpilot/devpilot.db, .devpilot/agent_sessions/, .venv/ o node_modules/ dentro del archivo fuente.
BLOCK si el manifest generado no valida contra ReleaseSourceArchiveManifest.
BLOCK si se usa red, API externa, remote execution, connector write o plugin execution.
BLOCK si el operador interpreta POST-H-017-C como release reproducible final; esa declaración exige POST-H-017-D/E.
```

## Riesgos y límites

```text
- En un checkout Git real, DevPilot inspecciona git archive HEAD en memoria y filtra entradas runtime/build/cache contra la policy antes de evaluar `forbidden_entries_total`.
- En ZIPs limpios sin .git, DevPilot usa un deterministic-source-archive-plan para auditoría local.
- Los checksums no reemplazan firma criptográfica ni certificación supply-chain.
- La validación de checksum alterado corresponde al verifier POST-H-017-D.
- La integración con quality-gate release-reproducibility corresponde a POST-H-017-E.
```

## Verificación focal recomendada

```powershell
$env:PYTHONPATH="src"
python -m pytest -p no:ddtrace `
  tests/test_post_h_017_source_archive_manifest.py `
  tests/test_post_h_017_environment_snapshot.py `
  tests/test_post_h_017_release_reproducibility_schema.py `
  tests/test_schema_registry.py `
  tests/test_documentation_governance_validator.py `
  tests/test_project_global_state.py `
  -q
```
