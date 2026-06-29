---
doc_id: "POST-H-017-A-RELEASE-REPRODUCIBILITY-SCHEMA-POLICY-REPORT"
title: "POST-H-017-A — Release reproducibility schema y policy report"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-06-29"
approval: "approved_by_owner"
phase: "POST-FASE-H"
---

# POST-H-017-A — Release reproducibility schema y policy

Estado: `implemented-initial`.

## Resultado

POST-H-017 queda aprobado para implementación y se inicia con contratos de reproducibilidad de release local-first:

```text
- ReleaseReproducibilityPack schema.
- ReleaseEnvironmentSnapshot schema.
- Release reproducibility policy local.
- Validator determinístico de policy.
- Fixtures schema-valid para pack y environment snapshot.
- Tests focales de schema/policy/sincronía documental.
```

## Alcance implementado

La entrega define el contrato que deberán producir y verificar los micro-sprints siguientes. No genera aún `outputs/release/reproducibility_pack.json`; por tanto no declara un release reproducible completo.

## Seguridad

```text
local_first=true
dry_run=true
network_used=false
external_api_used=false
remote_execution_used=false
connector_write_used=false
plugin_execution_used=false
secrets_included=false
source_mutations_performed=false
```

## Criterios PASS

```text
PASS si los schemas están registrados en schema_catalog.
PASS si los fixtures contractuales validan contra sus schemas.
PASS si la policy contiene exclusiones runtime críticas.
PASS si la policy bloquea dirty repo para declaración reproducible.
PASS si la policy exige evidencia secret-free y dry-run-only.
```

## Criterios BLOCK

```text
BLOCK si se permite incluir outputs/, .devpilot/devpilot.db, .venv/ o node_modules/.
BLOCK si se permite secrets_included=true.
BLOCK si se confunde dry-run con publicación o despliegue real.
BLOCK si se intenta declarar reproducibilidad final antes de POST-H-017-D/E.
```

## Evolución pendiente

```text
POST-H-017-B — Environment snapshot redactado.
POST-H-017-C — Source archive manifest y checksums.
POST-H-017-D — Verifier local de reproducibilidad.
POST-H-017-E — Quality gate y runbook release.
```
