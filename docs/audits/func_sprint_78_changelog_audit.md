---
title: "Auditoría FUNC-SPRINT-78 — Changelog generator y política de cambios"
doc_id: "DEVPL-AUDIT-FUNC-SPRINT-78"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
standard: "MIPSoftware"
extension: "MIASI"
phase: "FASE-G-PRODUCTIZACION-RELEASE"
sprint: "FUNC-SPRINT-78"
updated: "2026-06-17"
approval: "approved_by_owner_direction"
change_policy: "controlled_changes_allowed_via_docs_as_code"
---

# Auditoría FUNC-SPRINT-78 — Changelog generator y política de cambios

## 0. Estado

Veredicto focalizado: `PASS`.

`FUNC-SPRINT-78` implementa la primera versión operacional del generador de changelog local y la política de cambios asociada.

## 1. Propósito

Crear una capacidad de release que permita explicar qué cambió en una versión usando evidencia local, trazabilidad a sprints/manifests y categorías legibles para humanos.

## 2. Alcance implementado

- Módulo `devpilot_core.release.changelog`.
- CLI `python -m devpilot_core release changelog --version 0.1.0 --json`.
- Reportes opcionales bajo `outputs/reports/release_changelog.*`.
- `docs/release/CHANGELOG.md` como changelog base controlado.
- `docs/05_operations/change_policy.md` como política de cambios.
- Tests de builder, CLI, reportes, SemVer inválido y documentación.

## 3. Funcionamiento técnico

El generador lee manifests locales `docs/functional_sprint_*_manifest.json` y construye una salida compatible con categorías Keep a Changelog:

- Added;
- Changed;
- Deprecated;
- Removed;
- Fixed;
- Security.

Cada entrada referencia el sprint, el manifest fuente y, cuando existe, el reporte de auditoría del sprint.

## 4. Archivos creados

- `src/devpilot_core/release/changelog.py`: generador de changelog local.
- `docs/05_operations/change_policy.md`: política operacional de cambios.
- `docs/release/CHANGELOG.md`: changelog base controlado.
- `docs/audits/func_sprint_78_changelog_audit.md`: auditoría del sprint.
- `docs/functional_sprint_78_manifest.json`: manifest funcional del sprint.
- `tests/test_release_changelog.py`: pruebas funcionales del generador.
- `tests/test_sprint_78_documentation.py`: pruebas documentales del sprint.

## 5. Archivos modificados

- `src/devpilot_core/cli.py`: agrega `release changelog`.
- `src/devpilot_core/release/__init__.py`: exporta el generador de changelog.
- `src/devpilot_core/release/manifest.py`: incorpora changelog como artefacto esperado del release.
- `README.md`: sincroniza hito actual y siguiente.
- `docs/05_operations/runbook.md`: agrega operación de changelog.
- `docs/devpilot_backlog_fase_G_productizacion_release.md`: registra cierre Sprint 78.
- `docs/functional_backlog_after_precode.md`: avanza a Sprint 79.
- Tests documentales históricos: actualizan marcadores globales.

## 6. Criterios PASS

- Changelog legible por humanos.
- Categorías consistentes.
- Trazabilidad a sprints/manifests.
- No inventa cambios fuera de evidencias locales.
- No sobrescribe `docs/release/CHANGELOG.md` desde CLI.
- Reportes solo bajo `outputs/reports` con `--write-report`.
- Sin red, APIs externas, publicación, despliegue, firma o tags; el comando no publica artefactos externos y no despliega servicios.

## 7. Criterios BLOCK

- Changelog no parseable o no legible.
- Cambios inventados sin manifest/commit/doc aprobado.
- Sobrescritura de fuente sin confirmación gobernada.
- Uso de red o APIs externas.
- Publicación, despliegue, firma o tagging automático.
- Inclusión de secretos o runtime state.

## 8. Riesgos y limitaciones

- Primera versión basada en manifests, no en análisis completo de commits.
- La calidad del changelog depende de la calidad de los manifests.
- No calcula diferencias entre releases publicados.
- No actualiza automáticamente el archivo canónico `docs/release/CHANGELOG.md`.
- Packaging, SBOM, checksums y smoke release quedan para sprints posteriores.

## 9. Comandos de verificación

```powershell
python -m devpilot_core release changelog --version 0.1.0 --json
python -m devpilot_core release changelog --version 0.1.0 --json --write-report
python -m devpilot_core validate-artifact docs\05_operations\change_policy.md --json
python -m devpilot_core validate-artifact docs\release\CHANGELOG.md --json
python -m devpilot_core validate-artifact docs\audits\func_sprint_78_changelog_audit.md --json
python -m devpilot_core schema validate-manifest docs\functional_sprint_78_manifest.json --json
python -m pytest tests\test_release_changelog.py tests\test_sprint_78_documentation.py -q
```

## 10. Conclusión

`FUNC-SPRINT-78` queda implementado como una primera versión local, auditable e industrializable del changelog de release. No cierra todavía packaging ni release final, pero completa un componente obligatorio de Fase G antes de construir paquetes limpios y verificables.
