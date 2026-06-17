---
doc_id: DEVPL-OPS-PACKAGING-FUNC-79
title: DevPilot Local — Packaging Python y ZIP limpio reproducible
status: approved
version: 0.1.0
owner: Ordóñez
updated: 2026-06-17
approval: internal
---

# DevPilot Local — Packaging Python y ZIP limpio reproducible

## 0. Estado

`FUNC-SPRINT-79` implementa una primera versión `implemented-initial` de packaging local para Fase G. El objetivo es producir evidencia y artefactos locales reproducibles sin publicar, desplegar, firmar ni etiquetar Git.

## 1. Propósito

El packaging formal reemplaza los ZIPs ad hoc por un comando gobernado que declara qué se incluye, qué se excluye y qué artefactos locales se producirán. Esta capacidad es necesaria antes de SBOM, checksums, smoke test de instalación y ReleaseAgent.

## 2. Comandos principales

```powershell
python -m devpilot_core package build --kind repo-zip --version 0.1.0 --json
python -m devpilot_core package build --kind python --version 0.1.0 --json
python -m devpilot_core package build --kind all --version 0.1.0 --json
python -m devpilot_core package build --kind all --version 0.1.0 --execute --json --write-report
```

Por defecto, el comando opera en dry-run y no escribe `dist/`. Con `--execute`, escribe artefactos locales bajo `dist/` y reportes opcionales bajo `outputs/reports` si se agrega `--write-report`.

## 3. Artefactos soportados

| ID | Artefacto | Ruta | Estado |
|---|---|---|---|
| `PKG-CLEAN-ZIP` | ZIP limpio de fuente | `dist/release/devpilot-local-<version>-source.zip` | `implemented-initial` |
| `PKG-SDIST` | Python source distribution | `dist/devpilot-local-<version>.tar.gz` | `implemented-initial` |
| `PKG-WHEEL` | Python wheel puro | `dist/devpilot_local-<version>-py3-none-any.whl` | `implemented-initial` |
| `PKG-BUILD-REPORT` | Reporte de packaging | `outputs/reports/package_build.*` | `implemented-initial` |

## 4. Exclusiones obligatorias

Los paquetes limpios deben excluir:

```text
outputs/
.git/
.venv/
node_modules/
dist/
__pycache__/
.pytest_cache/
*.pyc
*.pyo
.devpilot/devpilot.db
.devpilot/providers.yaml
.env y variantes no example
archivos *.pem, *.key, *.p12, *.pfx
```

`providers.yaml.example`, registros MIASI, política local y metadata documental pueden permanecer si no contienen secretos.

## 5. Funcionamiento técnico

`PackageBuildBuilder` clasifica todos los archivos del workspace en incluidos/excluidos, valida SemVer, bloquea rutas con apariencia de secreto, produce una lista auditable y genera artefactos solo cuando se usa `--execute`.

El wheel y el sdist se generan con Python estándar para no introducir dependencias nuevas en este sprint. No publica ni publica externamente; la publicación externa queda fuera de alcance.

## 6. Criterios PASS

- `package build --kind repo-zip --version 0.1.0 --json` retorna `CommandResult` parseable.
- `package build --kind python --version 0.1.0 --json` retorna plan de wheel/sdist.
- `package build --kind all --version 0.1.0 --execute --json` escribe artefactos locales bajo `dist/`.
- El reporte lista archivos incluidos y excluidos.
- Los paquetes excluyen runtime DB, outputs, caches, venv, Git, `node_modules`, `dist` y secretos evidentes.
- No hay red, APIs externas, publicación, despliegue, firma ni tagging Git.

## 7. Criterios BLOCK

- Incluir `.devpilot/devpilot.db`, `.git/`, `.venv/`, `outputs/`, `node_modules/`, caches o secretos.
- Publicar en PyPI, GitHub Releases, Docker o cualquier servicio externo.
- Depender de outputs preexistentes no regenerables.
- Ejecutar tagging Git, firma criptográfica o despliegue.
- Ocultar fallos de escritura de artefactos.

## 8. Riesgos

| ID | Riesgo | Mitigación |
|---|---|---|
| RISK-FUNC-79-001 | Incluir runtime state o secretos | Reglas de exclusión y bloqueo por ruta. |
| RISK-FUNC-79-002 | Confundir package local con release final | Documentar que SBOM/checksums/smoke faltan. |
| RISK-FUNC-79-003 | Wheel/sdist mínimo no cubre todos los metadatos futuros | Evolucionar en Sprint 80/81 con supply chain y smoke install. |
| RISK-FUNC-79-004 | Artefactos `dist/` terminan versionados | `dist/` se trata como output generado y debe omitirse del repo fuente. |

## 9. Evolución pendiente

- Schema dedicado para package build report.
- SBOM CycloneDX baseline.
- Checksums SHA256 gobernados.
- Smoke install del wheel/sdist/ZIP.
- Verificación de integridad contra Release Manifest.
- Publicación externa solo tras ADR, aprobación humana y controles supply-chain.

Nota de seguridad: esta capacidad no publica, no despliega, no firma y no etiqueta Git.
