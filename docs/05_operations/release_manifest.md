---
title: "DevPilot Local — Release Manifest"
doc_id: "DEVPL-OPS-RELEASE-MANIFEST-001"
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

# DevPilot Local — Release Manifest

## 0. Estado

Este documento queda aprobado como primera versión operativa del modelo de Release Manifest de DevPilot Local. Es una versión `implemented-initial`: formaliza metadata, evidencia requerida, componentes y artefactos esperados, pero no construye paquetes, no publica, no firma, no calcula SBOM/checksums, no etiqueta Git y no despliega.

## 1. Propósito

Definir cómo se genera y usa el manifiesto de release local de DevPilot. El manifiesto permite auditar qué versión se pretende liberar, qué componentes entran en el release, qué comandos deben respaldar la evidencia y qué artefactos se esperan en sprints posteriores de Fase G.

## 2. Comando principal

```powershell
python -m devpilot_core release manifest --version 0.1.0 --json
python -m devpilot_core release manifest --version 0.1.0 --json --write-report
```

El comando devuelve un `CommandResult` parseable. Con `--write-report` genera evidencia bajo:

```text
outputs/reports/release_manifest.json
outputs/reports/release_manifest.md
```

## 3. Modelo de metadata

El manifest incluye:

- `release_id` y `release_version`.
- `release_channel` y `release_status`.
- `generated_at_utc`.
- metadata de `pyproject.toml`.
- metadata Git si el repo tiene `.git` disponible.
- componentes principales del producto.
- comandos requeridos de evidencia.
- artefactos esperados de release.
- reglas de exclusión.
- límites de seguridad.

## 4. Evidencias requeridas

Sprint 77 no ejecuta automáticamente pruebas ni gates. El manifest declara los comandos que deben respaldar una liberación:

```powershell
python -m pytest -q
python -m devpilot_core quality-gate run --profile ci --json
npm --prefix ui/web test
```

La ejecución explícita evita efectos colaterales ocultos, mantiene trazabilidad y permite que CI/local generen evidencia separada.

## 5. Artefactos esperados

El release manifest lista artefactos implementados y planificados:

- Release manifest JSON/MD: Sprint 77.
- Changelog humano JSON/MD: Sprint 78.
- Package ZIP limpio, wheel y sdist: Sprint 79.
- SBOM: Sprint 80.
- Checksums: Sprint 81.

## 6. Exclusiones obligatorias

Los paquetes de release no deben incluir:

```text
.git/
.venv/
node_modules/
outputs/
__pycache__/
.pytest_cache/
*.pyc
*.pyo
.devpilot/devpilot.db
```

## 7. Criterios PASS

- El comando produce JSON válido.
- La versión sigue SemVer.
- No requiere red ni APIs externas.
- No publica y no despliega.
- No muta archivos fuente.
- Con `--write-report` escribe únicamente bajo `outputs/reports`.
- El manifest declara pruebas/gates requeridos de forma auditable.

## 8. Criterios BLOCK

- Versiones no SemVer.
- Manifest que depende de outputs preexistentes no regenerables.
- Inclusión de secretos, `.devpilot/devpilot.db`, caches o outputs como parte del release.
- Publicación, despliegue, tagging o firma automática dentro del sprint.

## 9. Riesgos

| ID | Riesgo | Mitigación |
|---|---|---|
| RISK-FUNC-77-001 | Metadata incompleta | Manifest con componentes, Git, evidencia y artefactos esperados. |
| RISK-FUNC-77-002 | Git ausente en ZIP limpio | Soportar `is_git_repo=false` sin bloquear. |
| RISK-FUNC-77-003 | Confundir manifest con release final | Documentar que packaging, SBOM, checksums y smoke release son sprints posteriores. |

## 10. Evolución pendiente

Actualización Sprint 78: el Release Manifest reconoce el changelog humano como artefacto esperado implementado inicialmente por `FUNC-SPRINT-78`. La generación del changelog sigue siendo un comando separado para preservar trazabilidad y evitar efectos colaterales ocultos.


La versión industrial completa debe agregar schema formal de Release Manifest, manifest de package real, SBOM, checksums, smoke test de instalación, firma opcional, rollback/upgrade y ReleaseAgent dry-run. Sprint 77 solo crea la base auditable de metadata.
