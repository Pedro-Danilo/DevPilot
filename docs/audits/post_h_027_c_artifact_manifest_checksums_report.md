---
doc_id: "POST-H-027-C-ARTIFACT-MANIFEST-CHECKSUMS-AUDIT"
title: "POST-H-027-C — Artifact manifest and checksums"
status: "approved"
version: "1.0.0"
owner: "POST-H-027-C"
updated: "2026-07-08"
source_of_truth: true
approval: "approved_by_owner"
machine_readable_pair: "docs/post_h_027_c_manifest.json"
---

# POST-H-027-C — Artifact manifest and checksums

## Resultado

POST-H-027-C queda implementado como `implemented-initial / artifact-manifest-checksums`.

La nueva capacidad consolida artefactos locales de release en `ReleaseArtifactManifest` y genera `outputs/release/checksums.sha256` con SHA-256 para source ZIP, wheel, sdist y artefactos opcionales existentes. El comando operativo es:

```powershell
python -m devpilot_core release artifact-manifest --version 0.1.0 --verify-checksums --json --write-report
```

## Ajuste correctivo heredado

Antes de cerrar POST-H-027-B se corrigió la verificación de `sdist`: `PythonArtifactInstallVerifier` ahora expone dependencias locales de build backend mediante un `PYTHONPATH` controlado, además del `.pth` de bridge, sin añadir `src/devpilot_core` al entorno temporal. Esto permite resolver `setuptools` en Python 3.12+ con `pip --no-index --no-deps --no-build-isolation` y sin internet obligatorio.

## Checks cubiertos

- Source ZIP, wheel y sdist se declaran como artefactos obligatorios.
- Cada artefacto existente recibe `sha256`, tamaño, clasificación y estado de verificación.
- `checksums.sha256` contiene todos los artefactos existentes y no se versiona como fuente.
- La verificación detecta corrupción o alteración de checksum.
- El manifest distingue `distributable`, `generated-runtime-evidence` y `source-documentation`.
- No hay publicación, deploy, firma, red, APIs externas ni mutaciones de fuente.

## Riesgos y limitaciones

Esta primera versión no firma artefactos, no genera attestation SLSA, no publica, no instala en Windows y no ejecuta upgrade/rollback. Es una base local-first para que POST-H-027-D/E puedan consumir artefactos y checksums de forma gobernada.

## Verificación focal

```powershell
$env:PYTHONPATH="src"
python -m pytest -p no:ddtrace --assert=plain `
  tests/test_post_h_027_artifact_manifest_checksums.py `
  tests/test_post_h_027_python_artifact_install_verification.py `
  tests/test_post_h_027_source_zip_policy.py `
  tests/test_package_builder.py `
  tests/test_schema_registry.py `
  tests/test_project_global_state.py `
  -q

python -m devpilot_core package build --kind all --version 0.1.0 --execute --json --write-report
python -m devpilot_core release artifact-manifest --version 0.1.0 --verify-checksums --json --write-report
python -m devpilot_core schema validate --schema-id ReleaseArtifactManifest --instance outputs/release/release_artifact_manifest.json --json
```
