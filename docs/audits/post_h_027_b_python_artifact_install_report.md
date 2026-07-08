---
doc_id: "POST-H-027-B-PYTHON-ARTIFACT-INSTALL-AUDIT"
title: "POST-H-027-B — Wheel/sdist install verification"
status: "approved"
version: "1.0.0"
owner: "POST-H-027-B"
updated: "2026-07-08"
source_of_truth: true
approval: "approved_by_owner"
machine_readable_pair: "docs/post_h_027_b_manifest.json"
---

# POST-H-027-B — Wheel/sdist install verification

## Resultado

POST-H-027-B queda implementado como `implemented-initial / python-artifact-install-verification`.

La nueva capacidad verifica artefactos Python locales `wheel` y `sdist` mediante un entorno temporal creado bajo `outputs/tmp/python-artifact-install`. El verificador instala el artefacto con `pip --no-index --no-deps`; para `sdist` usa `--no-build-isolation` para aprovechar herramientas locales ya disponibles sin descargar dependencias de build.

## Comando operativo

```powershell
python -m devpilot_core release python-artifact-verify --artifact dist\devpilot_local-0.1.0-py3-none-any.whl --json --write-report
python -m devpilot_core release python-artifact-verify --artifact dist\devpilot-local-0.1.0.tar.gz --json --write-report
```

## Checks cubiertos

- El artefacto existe dentro del workspace y es `.whl` o `.tar.gz`.
- Se crea un venv temporal controlado.
- `pip install` opera en modo local-first, sin índice remoto.
- `devpilot_core` se importa desde `site-packages` del entorno instalado, no desde `src/devpilot_core`.
- `python -m devpilot_core --version` funciona post-install.
- `schema list --json`, `project-state validate --json` y `docs-governance validate --json` producen PASS post-install.
- No hay publicación, deploy, red, APIs externas ni mutaciones de fuente.

## Riesgos y limitaciones

Esta primera versión no implementa wheelhouse gobernado, firma, matriz multi-OS ni checksums unificados. La verificación usa dependencias locales ya presentes en el entorno del operador para evitar internet obligatorio. El manifest/checksums queda para POST-H-027-C, guía Windows para POST-H-027-D y upgrade/rollback para POST-H-027-E.

## Verificación focal

```powershell
$env:PYTHONPATH="src"
python -m pytest -p no:ddtrace --assert=plain `
  tests/test_post_h_027_python_artifact_install_verification.py `
  tests/test_package_builder.py `
  tests/test_installation_plan.py `
  tests/test_release_verification.py `
  tests/test_schema_registry.py `
  -q

python -m devpilot_core package build --kind python --version 0.1.0 --execute --json --write-report
python -m devpilot_core release python-artifact-verify --artifact dist\devpilot_local-0.1.0-py3-none-any.whl --json --write-report
python -m devpilot_core release python-artifact-verify --artifact dist\devpilot-local-0.1.0.tar.gz --json --write-report
python -m devpilot_core schema validate --schema-id PythonArtifactInstallVerification --instance outputs/release/python_artifact_install_verification.json --json
```

## Nota correctiva POST-H-027-C

La validacion de operador detecto que `sdist` podia bloquear en Python 3.12 cuando el venv temporal no tenia `setuptools`. Se corrigio `PythonArtifactInstallVerifier` para añadir un bridge seguro de dependencias locales al `PYTHONPATH` del proceso de pip/build hook, sin incluir `src/devpilot_core` y sin habilitar red.
