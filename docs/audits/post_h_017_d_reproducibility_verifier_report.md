---
doc_id: "POST-H-017-D-REPRODUCIBILITY-VERIFIER-REPORT"
title: "POST-H-017-D — Verifier local de reproducibilidad"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-06-30"
approval: "approved_by_owner"
---

# POST-H-017-D — Verifier local de reproducibilidad

## Resultado

Estado: `implemented-initial`.

POST-H-017-D agrega un verifier local para paquetes de evidencia `ReleaseReproducibilityPack`. El comando focal es:

```powershell
python -m devpilot_core release reproducibility-verify --pack outputs/release/reproducibility_pack.json --json --write-report
```

Cuando se usa `--write-report`, genera:

```text
outputs/release/reproducibility_verification.json
outputs/release/reproducibility_verification.md
```

Estos outputs son runtime evidence y no deben versionarse.

## Controles de seguridad

```text
local_first=true
dry_run=true
read_only=true
network_used=false
external_api_used=false
remote_execution_used=false
connector_write_used=false
plugin_execution_used=false
mutations_performed=false
source_mutations_performed=false
secrets_included=false
```

## Alcance técnico

```text
- Valida ReleaseReproducibilityPack contra schema.
- Valida la policy local de reproducibilidad.
- Bloquea git.dirty=true en el pack.
- Bloquea safety.secrets_included=true y flags de publicación/deploy/red/API.
- Verifica que el environment snapshot exista, valide contra schema y declare secrets_included=false.
- Verifica que el source archive manifest exista, valide contra schema y tenga forbidden_entries_total=0.
- Recalcula SHA-256 de artefactos críticos presentes y bloquea mismatch.
- Escribe reporte local opcional bajo outputs/release.
```

## Criterios PASS

```text
PASS si el pack valida contra ReleaseReproducibilityPack.
PASS si dirty=false y safety flags son local-first/dry-run/secret-free.
PASS si environment snapshot y source archive manifest validan contra schema.
PASS si forbidden_entries_total=0.
PASS si los checksums críticos coinciden con los archivos locales.
```

## Criterios BLOCK

```text
BLOCK si el pack falta, es inválido o no valida contra schema.
BLOCK si dirty=true o falta commit.
BLOCK si secrets_included=true.
BLOCK si falta environment snapshot o source archive manifest.
BLOCK si un checksum crítico no coincide.
BLOCK si el operador interpreta POST-H-017-D como quality gate final; esa integración corresponde a POST-H-017-E.
```

## Riesgos y limitaciones

```text
- POST-H-017-D no genera todavía outputs/release/reproducibility_pack.json.
- Los artifacts opcionales de release legacy se reportan como warnings hasta integrar el pack/gate final.
- No reemplaza firma criptográfica ni certificación supply-chain.
- No publica, no despliega, no firma remoto y no usa servicios externos.
```
