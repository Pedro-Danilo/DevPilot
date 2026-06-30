---
doc_id: "POST-H-017-E-QUALITY-GATE-RUNBOOK-REPORT"
title: "POST-H-017-E — Quality gate y runbook release"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-06-30"
approval: "approved_by_owner"
---

# POST-H-017-E — Quality gate y runbook release

## Resultado

Estado: `implemented-initial / hito cerrado`.

POST-H-017-E agrega el generador local de `ReleaseReproducibilityPack`, el comando:

```powershell
python -m devpilot_core release reproducibility-pack --json --write-report --verify
```

y el subgate `release-reproducibility` en:

```powershell
python -m devpilot_core quality-gate run --profile hardening --json
python -m devpilot_core quality-gate run --profile industrial --json
```

## Implementado

- `ReleaseReproducibilityPackBuilder` genera el pack local bajo `outputs/release/`.
- El builder invoca `environment-snapshot` y `source-archive-manifest` como evidencia previa.
- `--verify` ejecuta el verifier local y produce `reproducibility_verification`.
- El subgate `release-reproducibility` integra el flujo en `quality-gate`.
- README, runbook general, runbook específico, backlog, project state, source registry y TCR quedan sincronizados.

## Criterios PASS

```text
PASS si el pack valida contra ReleaseReproducibilityPack.
PASS si el verifier confirma dirty=false, secrets_included=false y checksums críticos sin mismatch.
PASS si forbidden_entries_total=0.
PASS si quality-gate hardening incluye release-reproducibility.
PASS si no hay red, APIs externas, publicación, despliegue, remote execution, connector write ni plugin execution.
```

## Criterios BLOCK

```text
BLOCK si el checkout Git está dirty y se usa `--require-clean-git` para declarar un release candidate limpio.
BLOCK si faltan environment_snapshot, source_archive_manifest, pack o verification report.
BLOCK si hay secretos, entradas runtime prohibidas o checksum alterado.
BLOCK si se presenta esta capacidad implemented-initial como release publicado, firma remota, attestation SLSA o certificación supply-chain.
```

## Riesgos

```text
- Riesgo: confundir evidencia local dry-run con release publicado. Mitigación: disclaimers en README/runbook/backlog.
- Riesgo: ejecutar gate en workspace dirty. Mitigación: builder bloquea dirty Git state.
- Riesgo: drift documental. Mitigación: TCR, docs-governance y project-state sincronizados.
```

## Comandos de verificación

```powershell
$env:PYTHONPATH="src"
python -m devpilot_core release reproducibility-pack --json --write-report --verify
python -m devpilot_core release reproducibility-verify --pack outputs/release/reproducibility_pack.json --json --write-report
python -m devpilot_core schema validate --schema-id ReleaseReproducibilityPack --instance outputs/release/reproducibility_pack.json --json
python -m devpilot_core schema validate --schema-id ReleaseReproducibilityVerification --instance outputs/release/reproducibility_verification.json --json
python -m devpilot_core quality-gate run --profile hardening --json
python -m pytest -p no:ddtrace tests/test_post_h_017_release_reproducibility_pack.py tests/test_post_h_017_reproducibility_verify.py tests/test_post_h_017_source_archive_manifest.py tests/test_post_h_017_environment_snapshot.py tests/test_post_h_017_release_reproducibility_schema.py tests/test_quality_gate.py tests/test_project_global_state.py -q
```
