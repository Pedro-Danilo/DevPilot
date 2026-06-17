---
title: "Matriz de artefactos de release — DevPilot Local"
doc_id: "DEVPL-OPS-RELEASE-ARTIFACTS-MATRIX-001"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
standard: "MIPSoftware"
extension: "MIASI"
phase: "FUNC-SPRINT-74"
updated: "2026-06-17"
source_repo: "repo_DevPilot_Local_95.zip"
source_adr: "docs/02_architecture/adrs/ADR-0014-release-versioning-packaging.md"
source_policy: "docs/05_operations/release_policy.md"
change_policy: "controlled_changes_allowed_via_docs_as_code"
approval: "approved_by_func_sprint_74"
---

# Matriz de artefactos de release — DevPilot Local

## 0. Estado

`approved` como primera matriz de artefactos liberables de Fase G.

Esta matriz es **preliminar**: define artefactos esperados, reglas de inclusión/exclusión y criterios de madurez. La generación automática de estos artefactos se implementará de forma progresiva en sprints posteriores.

## 1. Propósito

Definir qué artefactos componen un release de DevPilot local-first, cuáles son obligatorios, cuáles son opcionales y cuáles están prohibidos dentro de un paquete liberable.

## 2. Familias de artefactos

| Familia | Propósito | Estado Sprint 74 |
|---|---|---|
| Source package limpio | Distribuir fuente verificable sin runtime state. | Definido, no automatizado. |
| Python package | Instalar CLI/core con tooling Python. | Definido, no automatizado. |
| Release metadata | Trazar versión, commit, comandos, pruebas y artefactos. | Definido, no automatizado. |
| Evidencia humana | Explicar cambios, riesgos y verificación. | Definido, parcialmente manual. |
| Supply chain | Inventario, SBOM, checksums y hashes. | SBOM baseline automatizado en Sprint 80; checksums pendientes Sprint 81. |
| Install/upgrade | Permitir instalación y migración local. | Definido, no automatizado. |

## 3. Matriz de artefactos liberables

| Artefacto | Obligatorio Fase G | Generado en | Incluye | Excluye | Criterio PASS |
|---|---:|---|---|---|---|
| Repo ZIP limpio | Sí | Sprint 79 | Código fuente, docs, tests, `pyproject.toml`, `ui/web` source, ejemplos seguros. | `outputs/`, caches, `.venv`, `.git`, `node_modules`, `.devpilot/devpilot.db`, secretos. | ZIP reconstruible y verificable. |
| Wheel Python | Sí, si build local disponible | Sprint 79 | Paquete `devpilot_core`, metadata Python. | Tests, outputs, state local, secrets. | Instalable localmente. |
| sdist Python | Sí, si build local disponible | Sprint 79 | Fuente Python empaquetada. | Runtime state y caches. | Build reproducible local. |
| Release manifest | Sí | Sprint 77 | Versión, fecha, fuente, artefactos, checks, hashes, referencias. | Secretos y datos runtime. | JSON parseable y validable. |
| Changelog | Sí | Sprint 78 | Cambios notables por versión. | Cambios inventados sin fuente. | Humano, trazable y revisable. |
| SBOM baseline | Sí | Sprint 80 | Runtime/dev/build dependencies, UI deps, CycloneDX-compatible baseline. | Vulnerability scan remoto obligatorio. | No requiere red y genera evidencia local. |
| Checksums SHA256 | Sí | Sprint 81 | Hashes de artefactos. | Datos sensibles. | Hash calculado sobre artefacto real. |
| Release verification report | Sí | Sprint 81 | Resultado de package + checksum + smoke test. | Logs crudos con secretos. | PASS/BLOCK accionable. |
| Install guide | Sí | Sprint 82 | Instalación local Windows/dev. | Auto-update o privilegios innecesarios. | Procedimiento reproducible. |
| Backup/upgrade report | Sí al cierre de G | Sprint 83 | Plan/resultado backup y upgrade check. | Backup de `.venv`/`.git` por defecto. | Dry-run seguro. |
| ReleaseAgent report | Sí al cierre de G | Sprint 84 | Recomendaciones basadas en evidencia. | Publicación/deploy/tag real. | Dry-run auditable. |

## 4. Publicación externa

La matriz no autoriza publicación en PyPI, GitHub Releases, GitLab Releases, Docker Hub ni servicios cloud. Cualquier canal externo requiere ADR posterior, manejo de secretos, supply-chain review y aprobación humana.

## 4. Artefactos prohibidos en packages de release

| Artefacto/patrón | Motivo | Acción requerida |
|---|---|---|
| `outputs/` | Evidencia runtime regenerable. | Excluir siempre. |
| `.devpilot/devpilot.db` | Estado local del workspace. | Excluir siempre. |
| `.devpilot/providers.yaml` con secretos | Configuración local sensible. | Excluir o redactar; preferir `.example`. |
| `.env` | Secretos locales. | Excluir siempre. |
| `.venv/` | Entorno local no portable. | Excluir siempre. |
| `.git/` | Metadata VCS. | Excluir del package. |
| `__pycache__/`, `*.pyc` | Caches Python. | Excluir siempre. |
| `.pytest_cache/` | Cache de pruebas. | Excluir siempre. |
| `node_modules/` | Dependencias generadas. | Excluir siempre. |
| `ui/web/dist/` | Build generado. | Excluir salvo package frontend futuro con ADR. |
| logs locales | Pueden contener rutas o datos sensibles. | Excluir o sanitizar. |

## 5. Artefactos de fuente permitidos

| Ruta | Permitida | Condición |
|---|---:|---|
| `src/` | Sí | Código fuente. |
| `tests/` | Sí | Para release source verificable. |
| `docs/` | Sí | Deben estar sincronizados. |
| `scripts/` | Sí | Solo scripts seguros/documentados. |
| `ui/web/src/` | Sí | Fuente frontend. |
| `ui/web/package.json` | Sí | Metadata frontend. |
| `ui/web/package-lock.json` | Sí | Reproducibilidad npm. |
| `.devpilot/project.yaml` | Sí | Solo si no contiene secretos. |
| `.devpilot/providers.yaml.example` | Sí | Plantilla segura. |
| `.devpilot/policy.yaml` | Sí | Política local sin secretos. |

## 6. Relación con próximos sprints

| Sprint | Responsabilidad |
|---|---|
| 75 | Quality gate local para decidir si el repo puede empaquetarse. |
| 76 | CI local/scaffolding seguro. |
| 77 | Release manifest. |
| 78 | Changelog. |
| 79 | Package builder y ZIP limpio. |
| 80 | SBOM/supply-chain baseline. |
| 81 | Checksums y release verify. |
| 82 | Install guide/installer strategy. |
| 83 | Backup/restore/upgrade. |
| 84 | ReleaseAgent dry-run y cierre Fase G. |

## 7. Criterios PASS

- Cada artefacto tiene propósito, sprint responsable y regla de exclusión.
- Distingue source package, Python package, metadata, evidencia y supply-chain.
- Declara BLOCK para runtime state y secretos.
- No autoriza publicación externa ni auto-update.

## 8. Criterios BLOCK

- Package incluye outputs, caches, `.venv`, `.git`, `node_modules`, `.devpilot/devpilot.db` o secretos.
- Release manifest no referencia artefactos reales.
- Changelog inventa cambios no trazables.
- SBOM requiere red obligatoria.
- Checksums se calculan sobre rutas no existentes o no verificadas.

## 9. Riesgos

| ID | Riesgo | Mitigación |
|---|---|---|
| RISK-ART-001 | Confundir repo zip de intercambio con release limpio. | PackageBuilder y manifest formal en sprints posteriores. |
| RISK-ART-002 | Excluir demasiado y romper instalación. | Smoke test de release en Sprint 81. |
| RISK-ART-003 | Incluir state local. | Lista BLOCK y tests de packaging. |
| RISK-ART-004 | Divergencia Python/frontend. | Manifest y matriz de artefactos por familia. |
