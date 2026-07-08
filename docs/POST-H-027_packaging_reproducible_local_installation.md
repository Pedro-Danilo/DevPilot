---
doc_id: "POST-H-027-IMPLEMENTATION"
id: "POST-H-027"
title: "POST-H-027 — Packaging reproducible e instalacion local"
status: "approved"
version: "0.3.0"
owner: "Ordonez"
created: "2026-07-07"
updated: "2026-07-08"
phase: "POST-FASE-H"
priority: "P0"
roadmap_wave: "Ola 2"
roadmap_source: "devpilot_post_h_025_roadmap_detallado_v3_agentes_validadores.md"
onboarding_report_source: "devpilot_onboarding_report_final_compilado.md"
source_repo: "repo_DevPilot_Local_262_POST_H_025_E.zip"
depends_on:
  - "POST-H-026"
local_first: true
dry_run_default: true
read_only_by_default: true
no_remote_execution_enabled: true
no_external_apis_required: true
no_connector_write_enabled: true
no_plugin_execution_enabled: true
claims_allowed:
  - "production-ready-local"
claims_forbidden:
  - "enterprise-ready"
  - "remote-ready"
  - "SaaS-ready"
  - "compliance-certified"
implementation_status: "active/python-artifact-install-verification-implemented-initial"
current_micro_sprint: "POST-H-027-B"
next_micro_sprint: "POST-H-027-C"
---

# POST-H-027 — Packaging reproducible e instalacion local

## 1. Dictamen ejecutivo

POST-H-027 debe convertir la base local `production-ready-local` y el release candidate local de POST-H-026 en una ruta de distribucion local reproducible, verificable por operador y sin publicacion externa obligatoria.

La Ola 2 del roadmap v3 establece:

```text
Ola 2 - POST-H-027: Packaging reproducible e instalacion local

Objetivo:
Hacer que DevPilot sea instalable y verificable por un operador desde artefactos reproducibles.

Micro-sprints:
- POST-H-027-A - Source ZIP release policy hardening
- POST-H-027-B - Wheel/sdist install verification
- POST-H-027-C - Artifact manifest and checksums
- POST-H-027-D - Windows install guide and smoke
- POST-H-027-E - Upgrade/rollback dry-run
```

Este backlog adopta esos cinco micro-sprints sin agregar uno adicional. El alcance ya es suficiente si se ejecuta con rigor: primero se endurece el ZIP fuente, despues se verifica instalacion desde wheel/sdist, luego se unifican manifests/checksums, despues se cierra la experiencia Windows del operador y finalmente se ensaya upgrade/rollback en dry-run.

## 2. Fuentes consultadas

Fuentes obligatorias verificadas en el entorno:

```text
/workspace/.cache/01-devpilot_post_h_025_roadmap_detallado_v3_agentes_validadores.md
/workspace/.cache/02-repo_DevPilot_Local_262_POST_H_025_E.zip
/workspace/.cache/03-devpilot_onboarding_report_final_compilado.md
```

Repo descomprimido para analisis:

```text
/workspace/repo_DevPilot_Local_262_POST_H_025_E
```

Archivos consultados de forma focal:

```text
README.md
pyproject.toml
docs/05_operations/install_guide.md
docs/05_operations/backup_restore_upgrade.md
docs/05_operations/release_artifacts_matrix.md
docs/05_operations/release_manifest.md
docs/05_operations/release_policy.md
docs/05_operations/release_reproducibility_runbook.md
docs/05_operations/release_verification.md
docs/release/CHANGELOG.md
docs/release/release_manifest_v0.1.0.json
.devpilot/release/reproducibility_policy.json
.devpilot/testing/test_contract_registry.json
.devpilot/testing/test_contract_registry_v2.json
.devpilot/docs_governance/source_registry.json
src/devpilot_core/release/package_builder.py
src/devpilot_core/release/installation.py
src/devpilot_core/release/backup.py
src/devpilot_core/release/upgrade.py
src/devpilot_core/release/verification.py
src/devpilot_core/release/reproducibility_pack.py
src/devpilot_core/release/archive_manifest.py
src/devpilot_core/release/sbom.py
tests/test_package_builder.py
tests/test_installation_plan.py
tests/test_backup_upgrade.py
tests/test_release_verification.py
tests/test_release_manifest.py
tests/test_release_sbom.py
tests/test_post_h_017_release_reproducibility_pack.py
```

## 3. Estado base que hereda POST-H-027

El repo 262 ya contiene una linea de release local importante:

```text
- package build con repo-zip, python y all.
- clean source ZIP local-first bajo dist/.
- wheel/sdist minimal creados con standard library.
- exclusion de .git, .venv, node_modules, outputs, dist, caches, devpilot.db, backups, agent_sessions, rag index y providers.yaml.
- install plan para editable, wheel, zip, desktop-bridge y all.
- release reproducibility pack.
- source archive manifest.
- release verify.
- release manifest.
- SBOM baseline.
- backup create/list/restore.
- upgrade check.
- runbooks de install, release, release verification y backup/restore/upgrade.
```

El estado actual sigue siendo `implemented-initial` en instalacion/packaging de usuario final. El onboarding report identifica como pendiente:

```text
- smoke install real desde wheel en entorno temporal.
- validacion de wheel/sdist instalados.
- artifact manifest unificado.
- checksums publicados de forma gobernada.
- guia de instalacion local mas operativa para Windows.
- upgrade automatizado controlado no habilitado.
- rollback probado en dry-run.
- no hay publicacion externa.
- no hay instalador desktop real.
- no hay auto-update.
- no hay servicio persistente.
```

POST-H-027 debe cerrar esa brecha sin convertir DevPilot en SaaS, enterprise deployment ni producto remoto.

## 4. Objetivo del backlog

Implementar un proceso de packaging local reproducible que permita a un operador:

```text
1. Generar artefactos locales limpios.
2. Verificar que el ZIP fuente no contiene runtime artifacts ni secretos.
3. Construir wheel/sdist locales.
4. Instalar wheel/sdist en entorno temporal aislado.
5. Validar CLI, schemas, project-state, docs governance y production-ready-local-final tras instalacion.
6. Obtener manifest/checksums unificados.
7. Seguir una guia Windows operacional.
8. Ensayar upgrade y rollback en dry-run antes de cualquier actualizacion real.
```

## 5. Alcance funcional

Incluye:

```text
- Politica schema-backed para source ZIP release.
- Endurecimiento de PackageBuildBuilder o modulo equivalente.
- Verificacion aislada de wheel/sdist.
- Manifest unificado de artefactos de release local.
- Checksums SHA-256 gobernados.
- Validacion de reproducibilidad minima entre builds equivalentes.
- Guia Windows de instalacion local orientada a operador.
- Smoke post-install local.
- Upgrade/rollback dry-run con backup previo y restore plan.
- Quality gate o subgate packaging-local-ready.
- Sincronizacion README, runbook, changelog, source registry, TCR y project_state.
```

No incluye:

```text
- Publicacion en PyPI.
- GitHub Releases como canal obligatorio.
- Instalador MSI/EXE.
- Auto-update.
- Servicios persistentes.
- Firma externa obligatoria.
- KMS remoto.
- Remote execution.
- Connector write.
- Plugin execution.
- APIs externas obligatorias.
- Enterprise deployment.
- SaaS.
- Compliance certification.
```

## 6. Principios de diseno

```text
1. Reproducible local artifacts before distribution.
2. Clean ZIP is a governed artifact, not a convenience archive.
3. Wheel/sdist must be installed and smoke-tested, not only built.
4. Manifest/checksums must accompany every RC or local package.
5. No runtime artifacts in source packages.
6. No secrets in package artifacts.
7. Upgrade must start with backup and dry-run restore.
8. Rollback must be planned before execute exists.
9. Windows operator path must be explicit and copy-pasteable.
10. BLOCK is preferable to a package with ambiguous integrity.
```

## 7. Artefactos globales esperados al cierre de POST-H-027

Nuevos artefactos sugeridos:

```text
docs/backlogs/POST-H-027_packaging_reproducible_local_installation.md
docs/POST-H-027_packaging_reproducible_local_installation.md
docs/schemas/source_zip_release_policy.schema.json
docs/schemas/source_zip_release_report.schema.json
docs/schemas/python_artifact_install_verification.schema.json
docs/schemas/release_artifact_manifest.schema.json
docs/schemas/windows_install_smoke_report.schema.json
docs/schemas/upgrade_rollback_dry_run_report.schema.json
.devpilot/release/source_zip_release_policy.json
.devpilot/release/local_artifact_manifest_policy.json
src/devpilot_core/release/source_zip_policy.py
src/devpilot_core/release/python_artifact_verify.py
src/devpilot_core/release/artifact_manifest.py
src/devpilot_core/release/windows_install_smoke.py
src/devpilot_core/release/upgrade_rollback_dry_run.py
tests/test_post_h_027_source_zip_policy.py
tests/test_post_h_027_python_artifact_install_verification.py
tests/test_post_h_027_artifact_manifest_checksums.py
tests/test_post_h_027_windows_install_smoke.py
tests/test_post_h_027_upgrade_rollback_dry_run.py
docs/audits/post_h_027_a_source_zip_policy_report.md
docs/audits/post_h_027_b_python_artifact_install_report.md
docs/audits/post_h_027_c_artifact_manifest_checksums_report.md
docs/audits/post_h_027_d_windows_install_smoke_report.md
docs/audits/post_h_027_e_upgrade_rollback_closure_report.md
docs/post_h_027_a_manifest.json
docs/post_h_027_b_manifest.json
docs/post_h_027_c_manifest.json
docs/post_h_027_d_manifest.json
docs/post_h_027_e_manifest.json
```

Runtime outputs esperados, no versionables:

```text
outputs/release/source_zip_release_report.json
outputs/release/source_zip_release_report.md
outputs/release/python_artifact_install_verification.json
outputs/release/python_artifact_install_verification.md
outputs/release/release_artifact_manifest.json
outputs/release/release_artifact_manifest.md
outputs/release/checksums.sha256
outputs/reports/windows_install_smoke_report.json
outputs/reports/windows_install_smoke_report.md
outputs/reports/upgrade_rollback_dry_run_report.json
outputs/reports/upgrade_rollback_dry_run_report.md
```

Artefactos a mantener sincronizados:

```text
README.md
docs/05_operations/runbook.md
docs/05_operations/install_guide.md
docs/05_operations/backup_restore_upgrade.md
docs/05_operations/release_artifacts_matrix.md
docs/05_operations/release_policy.md
docs/05_operations/release_verification.md
docs/release/CHANGELOG.md
docs/schemas/schema_catalog.json
.devpilot/project_state.json
.devpilot/docs_governance/source_registry.json
.devpilot/testing/test_contract_registry.json
.devpilot/testing/test_contract_registry_v2.json
src/devpilot_core/cli.py o command registry equivalente
src/devpilot_core/quality/gate.py si se integra subgate packaging-local-ready
```

## 8. Modelo de decision del backlog

POST-H-027 puede cerrar como `PASS` solo si:

```text
- source_zip_policy_passed = true
- wheel_install_verification_passed = true
- sdist_install_verification_passed = true
- release_artifact_manifest_valid = true
- checksums_valid = true
- windows_install_smoke_passed = true
- upgrade_rollback_dry_run_passed = true
- no_runtime_artifacts_in_packages = true
- no_secrets_in_packages = true
- no_network_required_for_core_verification = true
- no_forbidden_claims = true
```

Debe emitir `BLOCK` si:

```text
- El source ZIP incluye outputs, .git, .venv, node_modules, dist, caches, devpilot.db, backups o providers.yaml.
- Wheel/sdist no se pueden instalar en entorno temporal.
- Post-install CLI smoke falla.
- Faltan manifest o checksums.
- El checksum no coincide con artefacto.
- La guia Windows exige pasos no documentados.
- Upgrade check no exige backup previo.
- Restore dry-run no detecta paths fuera de workspace.
- Se habilita auto-update, servicio persistente o publicacion externa sin ADR.
```

## 9. Micro-sprint POST-H-027-A — Source ZIP release policy hardening

### Objetivo

Endurecer la politica de ZIP fuente limpio para que el paquete local no dependa de convenciones informales ni de exclusiones dispersas en codigo.

### Justificacion

`PackageBuildBuilder` ya excluye marcadores sensibles y runtime artifacts. POST-H-027-A debe elevar esa logica a politica versionada, schema-backed, testeable, auditable e integrable con release verification.

### Alcance

Incluye:

```text
- Crear SourceZipReleasePolicy schema.
- Crear .devpilot/release/source_zip_release_policy.json.
- Unificar forbidden markers, required includes, optional includes y runtime exclusions.
- Validar que package build use la politica versionada o produzca reporte equivalente.
- Detectar archivos prohibidos dentro del ZIP construido.
- Detectar secretos por path y por SecretGuard textual en archivos permitidos.
- Generar SourceZipReleaseReport.
- Mantener package build dry-run por defecto y execute explicito.
```

No incluye:

```text
- Cambiar canal de distribucion.
- Publicar artefactos.
- Firmar artefactos.
- Construir instalador desktop.
```

### Artefactos esperados

```text
docs/schemas/source_zip_release_policy.schema.json
docs/schemas/source_zip_release_report.schema.json
.devpilot/release/source_zip_release_policy.json
src/devpilot_core/release/source_zip_policy.py
tests/test_post_h_027_source_zip_policy.py
docs/audits/post_h_027_a_source_zip_policy_report.md
docs/post_h_027_a_manifest.json
```

### Criterios PASS

```text
- Policy JSON valida contra schema.
- ZIP fuente construido cumple la politica.
- Outputs, dist, .git, .venv, node_modules, caches, .devpilot/devpilot.db, .devpilot/backups, .devpilot/agent_sessions, .devpilot/rag y providers.yaml quedan excluidos.
- Archivos criticos requeridos estan presentes: README, pyproject, src, tests relevantes, docs/schemas, docs/backlogs, .devpilot registries versionables permitidos.
- SecretGuard no detecta secretos embebidos.
- Reporte SourceZipReleaseReport valida contra schema.
- TCR v1/v2 registra el contrato.
```

### Criterios BLOCK

```text
- Cualquier runtime artifact prohibido entra al ZIP.
- El ZIP omite pyproject.toml o src/devpilot_core.
- La politica solo existe hardcodeada en Python.
- Package build escribe sin --execute.
- El reporte no diferencia excluded, included, required_missing y forbidden_present.
```

### Pruebas focales

```powershell
$env:PYTHONPATH="src"
python -m pytest -p no:ddtrace --assert=plain `
  tests/test_post_h_027_source_zip_policy.py `
  tests/test_package_builder.py `
  tests/test_post_h_017_source_archive_manifest.py `
  tests/test_post_h_017_release_reproducibility_pack.py `
  tests/test_schema_registry.py `
  -q
```

### Comandos objetivo

```powershell
python -m devpilot_core schema validate --schema-id SourceZipReleasePolicy --instance .devpilot/release/source_zip_release_policy.json --json
python -m devpilot_core package source-zip-policy --json
python -m devpilot_core package build --kind repo-zip --version 0.1.0 --execute --json --write-report
python -m devpilot_core package source-zip-policy --artifact dist\release\devpilot-local-0.1.0-source.zip --json --write-report
python -m devpilot_core schema validate --schema-id SourceZipReleaseReport --instance outputs/release/source_zip_release_report.json --json
```

## 9.1 Implementacion POST-H-027-A

Estado: `implemented-initial / source-zip-release-policy-hardening`.

POST-H-027-A eleva la logica de ZIP fuente limpio a una politica versionada y schema-backed: `SourceZipReleasePolicy` y `SourceZipReleaseReport`. La politica vive en `.devpilot/release/source_zip_release_policy.json`, el validador en `src/devpilot_core/release/source_zip_policy.py` y el comando operativo es `python -m devpilot_core package source-zip-policy --json`.

La primera version valida el arbol fuente y, opcionalmente, un ZIP candidato sin extraerlo. Verifica includes requeridos, exclusiones de runtime/build/secrets, SecretGuard textual, dry-run default y ausencia de publish/deploy/network. No instala wheel/sdist, no firma artefactos, no publica releases y no reemplaza los micro-sprints B-E.

## 10. Micro-sprint POST-H-027-B — Wheel/sdist install verification

### Objetivo

Verificar que los artefactos Python locales `wheel` y `sdist` no solo se construyen, sino que se pueden instalar y ejecutar en un entorno temporal aislado.

### Justificacion

El repo actual incluye wheel/sdist minimal con standard library y documenta instalacion desde wheel. Falta smoke install real y validacion post-install. Sin esto, un paquete puede parecer correcto y fallar al ser usado por un operador.

### Alcance

Incluye:

```text
- Crear PythonArtifactInstallVerification schema.
- Crear verificador local para wheel y sdist.
- Crear venv temporal bajo outputs/tmp o ruta temporal controlada.
- Instalar artefacto local sin publicacion externa.
- Ejecutar python -m devpilot_core --version.
- Ejecutar comandos minimos: schema list, project-state validate, docs-governance validate.
- Verificar import de devpilot_core.
- Verificar que no hay dependencia de ruta fuente accidental.
- Reportar duracion, comandos ejecutados, stdout/stderr acotados y resultado.
```

No incluye:

```text
- Dependencia obligatoria de internet.
- Publicacion en PyPI.
- Validacion exhaustiva multi-OS.
- Instalador desktop.
```

### Artefactos esperados

```text
docs/schemas/python_artifact_install_verification.schema.json
src/devpilot_core/release/python_artifact_verify.py
tests/test_post_h_027_python_artifact_install_verification.py
docs/audits/post_h_027_b_python_artifact_install_report.md
docs/post_h_027_b_manifest.json
```

### Criterios PASS

```text
- Wheel install smoke pasa desde un entorno temporal.
- Sdist install smoke pasa o queda BLOCK con causa clara si falta herramienta local.
- devpilot_core --version funciona post-install.
- schema list produce JSON parseable.
- project-state validate produce PASS.
- docs-governance validate produce PASS o WARNING no bloqueante documentado si el paquete no contiene outputs runtime.
- No se llama red ni API externa.
- El verificador limpia o marca claramente los temporales como runtime no versionable.
```

### Criterios BLOCK

```text
- Wheel construido no instala.
- CLI post-install depende del repo fuente original.
- El verificador usa pip remoto sin opt-in.
- El reporte oculta stderr relevante.
- El smoke escribe dentro de src/docs/.devpilot versionable.
```

### Pruebas focales

```powershell
$env:PYTHONPATH="src"
python -m pytest -p no:ddtrace --assert=plain `
  tests/test_post_h_027_python_artifact_install_verification.py `
  tests/test_package_builder.py `
  tests/test_installation_plan.py `
  tests/test_release_verification.py `
  -q
```

### Comandos objetivo

```powershell
python -m devpilot_core package build --kind python --version 0.1.0 --execute --json --write-report
python -m devpilot_core release python-artifact-verify --artifact dist\devpilot_local-0.1.0-py3-none-any.whl --json --write-report
python -m devpilot_core release python-artifact-verify --artifact dist\devpilot-local-0.1.0.tar.gz --json --write-report
python -m devpilot_core schema validate --schema-id PythonArtifactInstallVerification --instance outputs/release/python_artifact_install_verification.json --json
```

## 10.1 Implementacion POST-H-027-B

Estado: `implemented-initial / python-artifact-install-verification`.

POST-H-027-B agrega `PythonArtifactInstallVerifier` y el comando `python -m devpilot_core release python-artifact-verify --artifact <wheel|sdist> --json`. El verificador crea un venv temporal bajo `outputs/tmp/python-artifact-install`, instala el artefacto local con `pip --no-index --no-deps`, ejecuta `devpilot_core --version`, `schema list`, `project-state validate` y `docs-governance validate`, y confirma que el import de `devpilot_core` proviene del entorno instalado, no de `src/devpilot_core`.

La verificacion de `sdist` usa `--no-build-isolation` para aprovechar herramientas locales ya disponibles sin descargar build dependencies. Esta primera version no publica, no firma, no genera manifest/checksums unificados, no implementa instalador Windows ni upgrade/rollback; esos alcances permanecen en POST-H-027-C/D/E.

## 11. Micro-sprint POST-H-027-C — Artifact manifest and checksums

### Objetivo

Crear un manifest unificado de artefactos de release local y checksums SHA-256 gobernados para source ZIP, wheel, sdist, SBOM, release notes y reportes de verificacion.

### Justificacion

El repo ya tiene release manifests, source archive checksums y release verification. POST-H-027-C debe consolidar esos elementos en un contrato unico de paquete local entregable, evitando que cada entrega dependa de una lista manual incompleta.

### Alcance

Incluye:

```text
- Crear ReleaseArtifactManifest schema.
- Crear politica .devpilot/release/local_artifact_manifest_policy.json.
- Calcular SHA-256 de artefactos locales.
- Generar outputs/release/checksums.sha256.
- Verificar que cada checksum coincide con el archivo.
- Asociar artefactos a version, commit/contexto si esta disponible, generated_at, generator, policy id y safety flags.
- Incluir relacion con SBOM y release notes si existen.
- Reportar artefactos faltantes como BLOCK si son obligatorios.
```

No incluye:

```text
- Firma criptografica obligatoria.
- Attestation SLSA.
- Publicacion externa.
```

### Artefactos esperados

```text
docs/schemas/release_artifact_manifest.schema.json
.devpilot/release/local_artifact_manifest_policy.json
src/devpilot_core/release/artifact_manifest.py
tests/test_post_h_027_artifact_manifest_checksums.py
docs/audits/post_h_027_c_artifact_manifest_checksums_report.md
docs/post_h_027_c_manifest.json
```

### Manifest minimo recomendado

```json
{
  "schema_version": "1.0",
  "manifest_id": "DEVPL-LOCAL-ARTIFACT-MANIFEST-0.1.0",
  "release_version": "0.1.0",
  "scope": "local-package",
  "artifacts": [
    {
      "artifact_id": "source-zip",
      "path": "dist/release/devpilot-local-0.1.0-source.zip",
      "sha256": "<sha256>",
      "required": true,
      "artifact_type": "source_zip"
    }
  ],
  "checksums_file": "outputs/release/checksums.sha256",
  "safety": {
    "network_used": false,
    "external_api_used": false,
    "publish_performed": false,
    "secrets_embedded": false
  }
}
```

### Criterios PASS

```text
- Manifest valida contra schema.
- checksums.sha256 contiene todos los artefactos obligatorios.
- Verificador detecta checksum alterado mediante fixture.
- Manifest diferencia required, optional y generated-runtime evidence.
- Manifest no incluye outputs como fuente versionable.
- Release notes y SBOM quedan referenciados si se generan.
```

### Criterios BLOCK

```text
- Faltan checksums de artefactos obligatorios.
- Checksum no coincide.
- Manifest mezcla artefacto fuente limpio con outputs runtime sin clasificacion.
- Se omite version o generator.
- El manifest declara publicacion o deploy.
```

### Pruebas focales

```powershell
$env:PYTHONPATH="src"
python -m pytest -p no:ddtrace --assert=plain `
  tests/test_post_h_027_artifact_manifest_checksums.py `
  tests/test_release_manifest.py `
  tests/test_release_sbom.py `
  tests/test_release_verification.py `
  tests/test_post_h_017_release_reproducibility_pack.py `
  -q
```

### Comandos objetivo

```powershell
python -m devpilot_core release artifact-manifest --version 0.1.0 --json --write-report
python -m devpilot_core release artifact-manifest --version 0.1.0 --verify-checksums --json
python -m devpilot_core schema validate --schema-id ReleaseArtifactManifest --instance outputs/release/release_artifact_manifest.json --json
```

## 12. Micro-sprint POST-H-027-D — Windows install guide and smoke

### Objetivo

Convertir la guia de instalacion Windows en un flujo operacional verificable, con smoke post-install, troubleshooting y comandos PowerShell reproducibles.

### Justificacion

El proyecto y el usuario operan principalmente en Windows. La guia actual documenta instalacion editable, wheel y ZIP, pero POST-H-027-D debe transformarla en una ruta de operador: comandos exactos, precondiciones, errores esperados, smoke checks y evidencia generada.

### Alcance

Incluye:

```text
- Actualizar docs/05_operations/install_guide.md.
- Crear WindowsInstallSmokeReport schema.
- Crear comando/verificador windows-install-smoke o modo Windows en install smoke.
- Validar Python version, venv, pip, instalacion editable/wheel/zip segun modo.
- Validar CLI minima.
- Validar API token y host localhost si se incluye UI/API smoke.
- Validar npm --prefix ui/web test si Node esta disponible; si no, reportar advisory claro.
- Incluir troubleshooting: execution policy, path spaces, venv activation, pip cache, npm missing, port in use.
```

No incluye:

```text
- Requerir admin.
- Instalar Node automaticamente.
- Instalar Python automaticamente.
- Crear servicio Windows.
- Crear instalador MSI.
```

### Artefactos esperados

```text
docs/schemas/windows_install_smoke_report.schema.json
src/devpilot_core/release/windows_install_smoke.py
tests/test_post_h_027_windows_install_smoke.py
docs/audits/post_h_027_d_windows_install_smoke_report.md
docs/post_h_027_d_manifest.json
```

### Criterios PASS

```text
- La guia Windows tiene flujo editable, wheel y ZIP.
- El smoke report valida comandos minimos.
- El smoke distingue failure bloqueante de prerequisito ausente.
- No requiere privilegios elevados.
- No requiere red para checks core despues de tener dependencias locales.
- No expone secretos ni tokens raw.
- Documenta que node_modules, outputs, dist y venv no se versionan.
```

### Criterios BLOCK

```text
- La guia tiene comandos que no corresponden a CLI real.
- El smoke asume rutas absolutas del desarrollador.
- Fallos de npm bloquean core Python sin clasificacion.
- Se recomienda CORS wildcard o host 0.0.0.0.
- Se ocultan prerequisitos.
```

### Pruebas focales

```powershell
$env:PYTHONPATH="src"
python -m pytest -p no:ddtrace --assert=plain `
  tests/test_post_h_027_windows_install_smoke.py `
  tests/test_installation_plan.py `
  tests/test_api_security.py `
  tests/test_post_h_014_security_hardening.py `
  -q
```

### Comandos objetivo

```powershell
python -m devpilot_core install windows-smoke --mode editable --json --write-report
python -m devpilot_core install windows-smoke --mode wheel --artifact dist\devpilot_local-0.1.0-py3-none-any.whl --json --write-report
python -m devpilot_core schema validate --schema-id WindowsInstallSmokeReport --instance outputs/reports/windows_install_smoke_report.json --json
```

## 13. Micro-sprint POST-H-027-E — Upgrade/rollback dry-run

### Objetivo

Formalizar un flujo de upgrade/rollback dry-run que obligue a planificar backup, verificacion de paquete, instalacion y restauracion antes de cualquier ejecucion real.

### Justificacion

El repo ya cuenta con `backup create/list/restore` y `upgrade check`, pero el informe final marca upgrade/rollback e2e como pendiente. POST-H-027-E debe cerrar el circuito en modo no destructivo: no auto-upgrade, no restore silencioso, no migraciones automaticas, pero si evidencia de que el operador tiene un plan seguro.

### Alcance

Incluye:

```text
- Crear UpgradeRollbackDryRunReport schema.
- Extender upgrade check o crear release upgrade-rollback-dry-run.
- Verificar que existe plan de backup previo.
- Verificar que restore dry-run no escapa del workspace.
- Simular upgrade desde version actual a version target.
- Referenciar artifact manifest/checksums.
- Verificar post-upgrade smoke esperado.
- Generar acciones de rollback.
- Integrar con quality gate packaging-local-ready.
```

No incluye:

```text
- Auto-update.
- Migraciones destructivas.
- Restore real por defecto.
- Modificar DB local sin confirmacion.
- Descargar paquetes remotos.
```

### Artefactos esperados

```text
docs/schemas/upgrade_rollback_dry_run_report.schema.json
src/devpilot_core/release/upgrade_rollback_dry_run.py
tests/test_post_h_027_upgrade_rollback_dry_run.py
docs/audits/post_h_027_e_upgrade_rollback_closure_report.md
docs/post_h_027_e_manifest.json
```

### Criterios PASS

```text
- upgrade rollback dry-run produce PASS con fixtures validos.
- Falla con BLOCK si falta backup plan.
- Falla con BLOCK si artifact manifest/checksum no valida.
- Restore real sigue exigiendo --execute --confirm-restore.
- No escribe cambios de version ni modifica DB.
- Reporte final incluye pasos de rollback y validacion post-rollback.
- README/runbook/changelog/TCR/source registry/project_state quedan sincronizados.
```

### Criterios BLOCK

```text
- Upgrade se ejecuta sin backup.
- Restore se ejecuta sin confirmacion explicita.
- Dry-run modifica archivos.
- No hay referencia a checksums.
- Se promueve auto-update o descarga remota.
```

### Pruebas focales

```powershell
$env:PYTHONPATH="src"
python -m pytest -p no:ddtrace --assert=plain `
  tests/test_post_h_027_upgrade_rollback_dry_run.py `
  tests/test_backup_upgrade.py `
  tests/test_rollback_manager.py `
  tests/test_post_h_027_artifact_manifest_checksums.py `
  tests/test_quality_gate.py `
  tests/test_project_global_state.py `
  -q
```

### Comandos objetivo

```powershell
python -m devpilot_core upgrade check --json --write-report
python -m devpilot_core release upgrade-rollback-dry-run --from-version 0.1.0 --to-version 0.1.1 --json --write-report
python -m devpilot_core schema validate --schema-id UpgradeRollbackDryRunReport --instance outputs/reports/upgrade_rollback_dry_run_report.json --json
```

## 14. Quality gate propuesto

Al cierre de POST-H-027-E debe existir un subgate:

```text
packaging-local-ready
```

Debe agregarse a:

```text
quality-gate run --profile hardening
quality-gate run --profile industrial
```

El subgate debe verificar:

```text
- SourceZipReleasePolicy valida.
- SourceZipReleaseReport PASS.
- PythonArtifactInstallVerification PASS para wheel.
- Sdist verification PASS o BLOCK justificado segun soporte local decidido.
- ReleaseArtifactManifest valida.
- checksums.sha256 verifica.
- WindowsInstallSmokeReport PASS o pending/advisory para frontend prereq no instalado.
- UpgradeRollbackDryRunReport PASS.
- No-go gates siguen deshabilitados.
- No forbidden claims.
```

## 15. Secuencia recomendada de implementacion

Orden obligatorio:

```text
1. POST-H-027-A — Source ZIP release policy hardening.
2. POST-H-027-B — Wheel/sdist install verification.
3. POST-H-027-C — Artifact manifest and checksums.
4. POST-H-027-D — Windows install guide and smoke.
5. POST-H-027-E — Upgrade/rollback dry-run.
```

Razon:

```text
- No se deben verificar instalaciones antes de asegurar que el artefacto fuente es limpio.
- No se deben publicar checksums sin saber que artefactos son obligatorios.
- No se debe cerrar la guia Windows sin smoke y artifact manifest.
- No se debe ensayar upgrade/rollback sin manifest/checksums y backup policy.
```

## 16. Validacion focal recomendada por micro-sprint

Validacion base de contratos/documentacion:

```powershell
$env:PYTHONPATH="src"

python -m devpilot_core project-state validate --json
python -m devpilot_core docs-governance validate --json
python -m devpilot_core schema list --json
python -m devpilot_core test-contracts validate --json
python -m devpilot_core test-contracts validate-v2 --json
python -m devpilot_core quality-gate run --profile hardening --json
```

Validacion focal acumulativa POST-H-027:

```powershell
python -m pytest -p no:ddtrace --assert=plain `
  tests/test_post_h_027_source_zip_policy.py `
  tests/test_post_h_027_python_artifact_install_verification.py `
  tests/test_post_h_027_artifact_manifest_checksums.py `
  tests/test_post_h_027_windows_install_smoke.py `
  tests/test_post_h_027_upgrade_rollback_dry_run.py `
  tests/test_package_builder.py `
  tests/test_installation_plan.py `
  tests/test_backup_upgrade.py `
  tests/test_release_verification.py `
  tests/test_release_manifest.py `
  tests/test_release_sbom.py `
  tests/test_post_h_017_release_reproducibility_pack.py `
  tests/test_quality_gate.py `
  tests/test_schema_registry.py `
  tests/test_project_global_state.py `
  -q
```

Validacion final opcional de cierre:

```powershell
python -m pytest -q
```

La validacion general completa debe reservarse para cierre de backlog, release candidate o incidente de regresion amplia.

## 17. Cierre industrial del backlog

POST-H-027 solo puede cerrarse si:

```text
- Los cinco micro-sprints estan implementados, probados y documentados.
- packaging-local-ready existe y pasa en hardening/industrial.
- Source ZIP, wheel y sdist tienen verificacion clara.
- Artifact manifest/checksums estan generados y verificables.
- La guia Windows permite ejecutar smoke post-install.
- Upgrade/rollback dry-run produce reporte schema-backed.
- README, runbook, install guide, backup_restore_upgrade, changelog, source registry, TCR y project_state estan sincronizados.
- No se habilita publicacion externa, auto-update, servicio persistente ni instalador desktop sin ADR.
```

## 18. Riesgos y mitigaciones

| Riesgo | Severidad | Mitigacion en POST-H-027 |
|---|---:|---|
| ZIP fuente con runtime artifacts | Alta | SourceZipReleasePolicy bloqueante |
| Wheel/sdist construyen pero no instalan | Alta | PythonArtifactInstallVerification en venv temporal |
| Checksums incompletos o manuales | Alta | ReleaseArtifactManifest + checksums.sha256 gobernado |
| Guia Windows no reproducible | Alta | WindowsInstallSmokeReport y troubleshooting |
| Upgrade sin backup | Alta | UpgradeRollbackDryRunReport bloqueante |
| Restore accidental | Alta | Restore sigue dry-run y requiere confirmacion doble |
| Publicacion externa prematura | Alta | No-go policy y ausencia de upload/publish |
| Falsa sensacion de instalador desktop | Media | Mantener desktop-bridge como documentacion, no implementacion |
| Dependencia de red para core install | Media | Core checks locales; red solo como prerequisito explicito de dependencias si no hay cache |

## 19. Instrucciones de almacenamiento en el repo

Ruta canonica recomendada dentro de `repo_DevPilot_Local_262_POST_H_025_E`:

```text
docs/backlogs/POST-H-027_packaging_reproducible_local_installation.md
```

Ruta Windows equivalente:

```powershell
D:\Projects\DevPilot_Local\docs\backlogs\POST-H-027_packaging_reproducible_local_installation.md
```

Si se mantiene la convencion de documento top-level por hito, crear tambien durante POST-H-027-A:

```text
docs/POST-H-027_packaging_reproducible_local_installation.md
```

Ese documento top-level no debe divergir del backlog canonico. Si se crea, registrarlo en:

```text
.devpilot/docs_governance/source_registry.json
README.md
docs/05_operations/runbook.md
docs/release/CHANGELOG.md
```

## 20. Git sugerido para incorporar este backlog

Cuando se copie este archivo al repo:

```bash
git add docs/backlogs/POST-H-027_packaging_reproducible_local_installation.md
git commit -m "Add POST-H-027 reproducible packaging backlog"
```

Si tambien se agrega documento top-level o source registry:

```bash
git add docs/backlogs/POST-H-027_packaging_reproducible_local_installation.md docs/POST-H-027_packaging_reproducible_local_installation.md .devpilot/docs_governance/source_registry.json README.md docs/05_operations/runbook.md docs/release/CHANGELOG.md
git commit -m "Register POST-H-027 reproducible packaging backlog"
```

## 21. Decision de alcance

POST-H-027 no debe convertirse en un backlog de publicacion externa. Su resultado correcto es un packaging local verificable, no un canal de distribucion publico.

La linea de corte es:

```text
Permitido: construir, verificar, manifestar, calcular checksums, documentar, smoke-test, planificar upgrade/rollback.
No permitido: publicar, auto-actualizar, instalar servicios, requerir admin, habilitar remote, habilitar connector write, habilitar plugin execution, declarar enterprise/SaaS/compliance.
```

La siguiente ola, POST-H-028, deberia usar los paquetes locales verificables de POST-H-027 para endurecer UI/API local con mayor confianza operacional.
