---
title: "Auditoría FUNC-SPRINT-77 — Release metadata y Release Manifest"
doc_id: "DEVPL-AUDIT-FUNC-SPRINT-77"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
standard: "MIPSoftware"
extension: "MIASI"
phase: "FASE-G-PRODUCTIZACION-RELEASE"
sprint: "FUNC-SPRINT-77"
updated: "2026-06-17"
approval: "approved_after_func_sprint_77_validation"
---

# Auditoría FUNC-SPRINT-77 — Release metadata y Release Manifest

## 0. Estado

`FUNC-SPRINT-77` queda implementado como primera versión operativa de Release Manifest local. El sprint queda en estado `implemented-initial` y requiere evolución posterior para package real, SBOM, checksums, firma, smoke release y ReleaseAgent.

## 1. Propósito

Crear el modelo local de metadata de versión y manifest de release para cada paquete liberable de DevPilot, manteniendo la regla local-first y la política de no publicación/no despliegue de Fase G.

## 2. Alcance implementado

- Módulo `src/devpilot_core/release/manifest.py`.
- CLI `python -m devpilot_core release manifest --version 0.1.0 --json`.
- Reportes opcionales `outputs/reports/release_manifest.json` y `.md`.
- Metadata de versión, proyecto, Git, componentes, evidencias y artefactos esperados.
- Tests unitarios/CLI para manifest.
- Sin dependencias nuevas.

## 3. Funcionamiento técnico

`ReleaseManifestBuilder` genera un `CommandResult` con un objeto `release_manifest` que incluye metadata de versión, pyproject, Git si está disponible, componentes locales, evidencia requerida y artefactos previstos de Fase G. El comando no ejecuta pruebas ni gates; declara esos comandos como evidencia requerida para que CI o el operador los ejecuten explícitamente.

## 4. Archivos creados

- `src/devpilot_core/release/__init__.py`.
- `src/devpilot_core/release/manifest.py`.
- `docs/05_operations/release_manifest.md`.
- `docs/audits/func_sprint_77_release_manifest_audit.md`.
- `docs/functional_sprint_77_manifest.json`.
- `tests/test_release_manifest.py`.
- `tests/test_sprint_77_documentation.py`.

## 5. Archivos modificados

- `src/devpilot_core/cli.py`.
- `README.md`.
- `docs/05_operations/runbook.md`.
- `docs/devpilot_backlog_fase_G_productizacion_release.md`.
- `docs/functional_backlog_after_precode.md`.
- Tests documentales históricos sincronizados con el hito actual.

## 6. Criterios PASS

- `release manifest --version 0.1.0 --json` retorna JSON parseable.
- `--write-report` genera reportes bajo `outputs/reports`.
- Versiones no SemVer fallan con `ExitCode.ERROR`.
- El manifest no requiere red ni APIs externas.
- No hay publicación, despliegue, firma ni tagging automático.
- README, runbook, backlog G y manifest quedan sincronizados.

## 7. Criterios BLOCK

- Manifest no parseable.
- Manifest dependiente de outputs no regenerables.
- Metadata sin versión, evidencia o componentes.
- Inclusión de secretos o runtime DB.
- Publicación/despliegue durante generación del manifest.

## 8. Riesgos y limitaciones

- El manifest declara evidencias requeridas, pero no ejecuta pruebas ni gates.
- No construye paquetes ni artefactos distribuibles.
- Git puede no estar disponible cuando se trabaja desde ZIP limpio; esto se reporta como `is_git_repo=false` sin bloquear.
- Falta schema JSON dedicado de Release Manifest, previsto como mejora futura si el manifest comienza a ser consumido por terceros.

## 9. Comandos de verificación

```powershell
python -m devpilot_core release manifest --version 0.1.0 --json
python -m devpilot_core release manifest --version 0.1.0 --json --write-report
python -m pytest -q
python -m devpilot_core quality-gate run --profile ci --json
python -m devpilot_core validate-artifact docs/05_operations/release_manifest.md --json
python -m devpilot_core validate-artifact docs/audits/func_sprint_77_release_manifest_audit.md --json
python -m devpilot_core schema validate-manifest docs/functional_sprint_77_manifest.json --json
python -m pytest tests/test_release_manifest.py tests/test_sprint_77_documentation.py -q
```

## 10. Conclusión

Sprint 77 queda listo para servir como base de los sprints 78–81: changelog, packaging limpio, SBOM y checksums. El comando introduce metadata de release auditable sin adelantar publicación, distribución real ni despliegue; no despliega.
