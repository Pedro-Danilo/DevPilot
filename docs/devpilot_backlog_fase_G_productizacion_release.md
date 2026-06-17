---
title: "DevPilot Local — Backlog ejecutable Fase G: Productización y release"
doc_id: "DEVPL-FUNC-BACKLOG-FASE-G-001"
status: "approved"
version: "1.6.0"
owner: "Ordóñez"
standard: "MIPSoftware"
extension: "MIASI"
phase: "FASE-G-PRODUCTIZACION-RELEASE"
updated: "2026-06-17"
source_repo: "repo_DevPilot_Local_101.zip"
source_report: "Informe de avance DevPilot - sprint 0 - 18.docx"
source_backlog_model: "docs/functional_backlog_after_precode.md"
baseline_dependency: "Fases A-F cerradas; Fase F validada por FUNC-SPRINT-73"
approved_on: "2026-06-16"
approval: "approved_after_phase_f_visual_mvp_web_first_closure"
first_open_sprint: "FUNC-SPRINT-80"
last_completed_sprint: "FUNC-SPRINT-79"
next_sprint: "FUNC-SPRINT-80"
phase_g_status: "in_progress"
first_sprint: "FUNC-SPRINT-74"
last_planned_sprint: "FUNC-SPRINT-84"
change_policy: "controlled_changes_allowed_via_docs_as_code"
approval_scope: "phase_g_executable_backlog_review"
---

# DevPilot Local — Backlog ejecutable Fase G: Productización y release

## Estado de aprobación funcional

Este documento queda promovido a estado `approved` después de la verificación satisfactoria de `FUNC-SPRINT-73 — Cierre Fase F web-first y decisión de evolución`. Su propósito es convertir la **Fase G — Productización y release** en un backlog de implementación ejecutable, siguiendo el modelo operativo usado en `docs/functional_backlog_after_precode.md`.

La Fase G corresponde a la **Ola 10 — CI/CD, release y distribución**. Parte del estado real de `repo_DevPilot_Local_101.zip`, donde DevPilot ya dispone de core CLI local-first, `CommandResult`, validadores, reportes, trazas, SQLite, MIASI, PolicyEngine, agentes documentales y especializados gobernados, Evaluation Harness, Git/repo tooling, review/refactor en modo seguro, ModelAdapter local/API gobernado, AgentOps local, ApplicationService v2, API local segura y Web UI local MVP. La Fase G no debe introducir ejecución destructiva ni despliegue remoto sin pasar por PolicyEngine, Approval Workflow, quality gates y evidencia reproducible.

Aprobación aplicada: la fuente de verdad queda actualizada de `repo_DevPilot_Local_94.zip` a `repo_DevPilot_Local_101.zip`; la entrada de Fase G queda condicionada al cierre validado de Fases A-F y, en particular, al cierre de `FUNC-SPRINT-73`; la primera unidad de trabajo autorizada fue `FUNC-SPRINT-74 — ADR de release, versionado y productización`; tras el cierre de Sprint 79, la siguiente unidad autorizada es `FUNC-SPRINT-80 — SBOM y supply-chain baseline`.

## 1. Propósito

La Fase G busca transformar DevPilot desde un core funcional probado hacia un producto distribuible, versionable, verificable y mantenible. El objetivo no es crear nuevas capacidades agentic profundas, sino industrializar la entrega del producto: versionado, changelog, empaquetado, SBOM, release manifest, CI/CD, checksums, instalación, smoke tests y actualización.

En lenguaje operativo, esta fase avanza desde:

```text
repo funcional + pytest + comandos manuales + zips ad hoc
```

hacia:

```text
release reproducible + quality gate + paquete limpio + manifiesto + SBOM + pipeline CI/CD + smoke test + estrategia de instalación/upgrade
```

## 2. Regla central de Fase G

Una versión de DevPilot solo puede considerarse liberable si existe evidencia reproducible de:

1. pruebas en PASS;
2. quality gate local en PASS;
3. manifest de release;
4. changelog legible para humanos;
5. paquete limpio sin outputs/caches/runtime DB;
6. checksums;
7. SBOM o inventario de componentes;
8. smoke test de instalación/ejecución;
9. runbook actualizado;
10. rollback/backup cuando aplique.

Ningún pipeline de CI/CD debe ejecutar despliegues remotos por defecto. La Fase G debe mantener la filosofía local-first y dry-run-first.

## 3. Alcance de Fase G

Incluye:

- ADR de release/versionado/productización;
- Quality Gate local unificado;
- CI local y scaffolding GitHub/GitLab opcional;
- version metadata;
- release manifest;
- changelog generator;
- packaging Python `sdist`/wheel y ZIP limpio;
- SBOM baseline;
- supply-chain baseline;
- checksums;
- smoke test de release;
- estrategia de installer/desktop packaging;
- backup/restore/upgrade local;
- ReleaseAgent MVP en modo dry-run;
- cierre formal de Fase G.

No incluye:

- despliegue cloud automático;
- publicación pública en PyPI;
- auto-update silencioso;
- firma criptográfica obligatoria de producción;
- soporte enterprise multiusuario;
- remote runners;
- marketplace de plugins;
- SaaS.

## 4. Niveles de implementación de Fase G

| Nivel | Nombre | Objetivo | Estado esperado al cierre |
|---|---|---|---|
| FG-L0 | Decisión de release | Formalizar versionado/productización | ADR aprobable |
| FG-L1 | Quality gate | Unificar pruebas y validaciones | `quality-gate run` en PASS |
| FG-L2 | CI/CD inicial | Automatizar verificación | Workflows dry-run/local-first |
| FG-L3 | Release metadata | Manifest, version, changelog | Release trazable |
| FG-L4 | Packaging | Wheel/sdist/ZIP limpio | Artefactos reproducibles |
| FG-L5 | Supply chain | SBOM/checksums/SLSA baseline | Riesgo reducido |
| FG-L6 | Instalación/upgrade | Smoke test, backup, restore | Producto instalable |
| FG-L7 | Release assistant | ReleaseAgent dry-run | Asistencia gobernada |

## 5. Definition of Done transversal

Un sprint de Fase G solo puede cerrarse si cumple:

- `pytest -q` pasa;
- los comandos nuevos devuelven `CommandResult`;
- todo artefacto generado puede omitirse del repo fuente si es runtime;
- README y runbook se actualizan;
- no se publican secretos ni `.devpilot/devpilot.db`;
- todo release package excluye `outputs/`, `.pytest_cache`, `__pycache__`, `.venv`, `.git`, `.devpilot/devpilot.db`;
- todo comando de release tiene modo dry-run cuando aplica;
- si se agregan dependencias, hay ADR o justificación documentada;
- todo pipeline CI/CD es seguro por defecto y no despliega sin aprobación.

## 6. Convenciones de IDs

| Tipo | Prefijo | Ejemplo |
|---|---|---|
| Sprint funcional | `FUNC-SPRINT-XX` | `FUNC-SPRINT-74` |
| Historia | `US-FUNC-XX-YYY` | `US-FUNC-74-001` |
| Tarea | `FUNC-XX-YYY` | `FUNC-74-003` |
| Prueba | `TEST-FUNC-XX-YYY` | `TEST-FUNC-74-002` |
| Gate | `GATE-FUNC-XX` | `GATE-FUNC-74` |
| Riesgo | `RISK-FUNC-XX-YYY` | `RISK-FUNC-74-001` |
| Release | `REL-*` | `REL-MANIFEST-V1` |
| Packaging | `PKG-*` | `PKG-WHEEL-BUILD` |

## 7. Roadmap funcional de Fase G

| Ola | Sprints | Resultado esperado |
|---|---|---|
| Ola 10 | FUNC-SPRINT-74 a 84 | Release local reproducible, CI/CD inicial, package limpio, SBOM, checksums, smoke tests, installer strategy y ReleaseAgent dry-run |

## 8. Referencias técnicas externas de apoyo

- Semantic Versioning orienta reglas para asignar e incrementar versiones de software.
- Keep a Changelog propone un formato humano para documentar cambios notables por versión.
- Python Packaging User Guide describe empaquetado de proyectos Python y construcción de distribuciones.
- SLSA define controles incrementales para proteger integridad de artefactos y cadena de suministro.
- CycloneDX proporciona un estándar SBOM para visibilidad de componentes y reducción de riesgo de supply chain.

---

## FUNC-SPRINT-74 — ADR de release, versionado y productización

### Objetivo

Definir la estrategia oficial de versionado, release, empaquetado y distribución de DevPilot antes de construir comandos de release.

### Entradas

- `repo_DevPilot_Local_94.zip` como baseline vigente.
- Backlogs Fase A-F aprobados o explícitamente aceptados como prerequisito lógico.
- `docs/functional_backlog_after_precode.md` como modelo operativo.
- `Informe de avance DevPilot - sprint 0 - 18.docx` como diagnóstico de estado y brechas.

### Historias

| ID | Historia | Criterio de aceptación |
|---|---|---|
| US-FUNC-74-001 | Como owner, quiero una política de versionado para liberar DevPilot sin ambigüedad. | Existe ADR con estrategia de versiones. |
| US-FUNC-74-002 | Como desarrollador, quiero saber qué artefactos componen un release. | La ADR define package, manifest, checksums y evidencia. |
| US-FUNC-74-003 | Como revisor de seguridad, quiero que release no incluya runtime state ni secretos. | Existen reglas de exclusión y riesgos. |

### Tareas

| ID | Tarea | Entregable | PASS |
|---|---|---|---|
| FUNC-74-001 | Crear ADR de release/versionado | `docs/02_architecture/adrs/ADR-XXXX-release-versioning-packaging.md` | Decisión explícita. |
| FUNC-74-002 | Definir política SemVer interna | `docs/05_operations/release_policy.md` | Reglas MAJOR/MINOR/PATCH/0.y.z. |
| FUNC-74-003 | Definir matriz de artefactos liberables | `docs/05_operations/release_artifacts_matrix.md` | Incluye repo zip, wheel/sdist, SBOM, manifest, checksums. |
| FUNC-74-004 | Actualizar runbook | `docs/05_operations/runbook.md` | Sección release strategy. |
| FUNC-74-005 | Crear manifiesto Sprint 74 | `docs/functional_sprint_74_manifest.json` | JSON válido. |

### Archivos previstos

```text
docs/02_architecture/adrs/ADR-XXXX-release-versioning-packaging.md
docs/05_operations/release_policy.md
docs/05_operations/release_artifacts_matrix.md
docs/audits/func_sprint_74_release_versioning_audit.md
docs/functional_sprint_74_manifest.json
```

### Comandos objetivo

```powershell
python -m devpilot_core validate-artifact docs/05_operations/release_policy.md --json
python -m devpilot_core validate-artifact docs/05_operations/release_artifacts_matrix.md --json
python -m pytest -q
```

### Criterios PASS

- ADR compara release interno, PyPI, ZIP limpio, wheel/sdist y desktop installer.
- Define explícitamente que publicación externa queda fuera del sprint.
- Define reglas de exclusión para paquetes.
- Define relación con SemVer, changelog, manifest y SBOM.

### Criterios BLOCK

- No cerrar si permite auto-publicación externa sin aprobación.
- No cerrar si no cubre exclusiones de outputs, caches y runtime DB.
- No cerrar si no actualiza runbook.

### Riesgos y mitigaciones

| ID | Riesgo | Mitigación |
|---|---|---|
| RISK-FUNC-74-001 | Versionado inconsistente | ADR + release policy. |
| RISK-FUNC-74-002 | Paquetes con datos runtime | Matriz de exclusión. |
| RISK-FUNC-74-003 | Publicación prematura | Publicación externa fuera de alcance. |

### Pruebas mínimas

| ID | Prueba | Evidencia esperada |
|---|---|---|
| TEST-FUNC-74-001 | Validar docs nuevos | `validate-artifact` PASS. |
| TEST-FUNC-74-002 | Suite completa | `pytest -q` PASS. |

### Prompt operativo sugerido

```text
Implementa FUNC-SPRINT-74. Crea ADR de release/versionado/productización, política de release, matriz de artefactos liberables y auditoría. No implementes comandos de release todavía. Mantén local-first, dry-run-first y exclusión de runtime artifacts.
```

---

## Estado de implementación Sprint 74

`FUNC-SPRINT-74 — ADR de release, versionado y productización` queda implementado en estado `implemented` / `PASS focalizado`.

Entregables de cierre:

- `docs/02_architecture/adrs/ADR-0014-release-versioning-packaging.md`.
- `docs/05_operations/release_policy.md`.
- `docs/05_operations/release_artifacts_matrix.md`.
- `docs/audits/func_sprint_74_release_versioning_audit.md`.
- `docs/functional_sprint_74_manifest.json`.
- `tests/test_sprint_74_documentation.py`.

La Fase G queda en progreso. La estrategia de release/versionado ya está definida, pero aún no existen comandos automáticos de quality gate, release manifest, changelog, packaging, SBOM, checksums, smoke test, instalación, backup/upgrade ni ReleaseAgent. El siguiente sprint autorizado es `FUNC-SPRINT-75 — Quality Gate local unificado`.


## FUNC-SPRINT-75 — Quality Gate local unificado

### Objetivo

Crear un comando único de quality gate local que ejecute las verificaciones mínimas para determinar si DevPilot está en estado liberable.

### Historias

| ID | Historia | Criterio de aceptación |
|---|---|---|
| US-FUNC-75-001 | Como release manager, quiero un comando único para verificar el repo antes de empaquetar. | Existe `quality-gate run`. |
| US-FUNC-75-002 | Como CI, quiero salida JSON parseable. | El comando retorna `CommandResult`. |
| US-FUNC-75-003 | Como arquitecto, quiero saber qué subgates pasaron o fallaron. | El resultado lista subgates. |

### Tareas

| ID | Tarea | Entregable | PASS |
|---|---|---|---|
| FUNC-75-001 | Crear módulo quality | `src/devpilot_core/quality/gate.py` | Orquesta subgates. |
| FUNC-75-002 | Agregar CLI | `quality-gate run --json` | Salida estructurada. |
| FUNC-75-003 | Incluir subgates mínimos | readiness, standards, MIASI, eval, app contract, pytest optional | Subgates reportados. |
| FUNC-75-004 | Reportes | `outputs/reports/quality_gate.*` | Con `--write-report`. |
| FUNC-75-005 | Tests | `tests/test_quality_gate.py` | PASS. |

### Archivos previstos

```text
src/devpilot_core/quality/__init__.py
src/devpilot_core/quality/gate.py
tests/test_quality_gate.py
docs/audits/func_sprint_75_quality_gate_audit.md
docs/functional_sprint_75_manifest.json
```

### Comandos objetivo

```powershell
python -m devpilot_core quality-gate run --json
python -m devpilot_core quality-gate run --json --write-report
python -m pytest -q
```

### Criterios PASS

- El quality gate no modifica archivos salvo reportes con `--write-report`.
- Los subgates están listados con `ok`, `exit_code`, duración y hallazgos resumidos.
- Si un subgate crítico falla, el gate falla.

### Criterios BLOCK

- No cerrar si el comando oculta fallos de subgates.
- No cerrar si ejecuta comandos destructivos.
- No cerrar si no produce JSON parseable.

### Riesgos y mitigaciones

| ID | Riesgo | Mitigación |
|---|---|---|
| RISK-FUNC-75-001 | Gate lento | Permitir perfiles `fast/full`. |
| RISK-FUNC-75-002 | Duplicar lógica de CLI | Reusar ApplicationService/core. |
| RISK-FUNC-75-003 | Fallos no accionables | Incluir findings por subgate. |

### Pruebas mínimas

| ID | Prueba | Evidencia esperada |
|---|---|---|
| TEST-FUNC-75-001 | Gate con repo válido | PASS. |
| TEST-FUNC-75-002 | Gate con fixture inválido | FAIL/BLOCK esperado. |
| TEST-FUNC-75-003 | Reporte parseable | JSON/MD generado. |

### Prompt operativo sugerido

```text
Implementa FUNC-SPRINT-75. Crea QualityGate local que orqueste readiness, standards, MIASI, eval y app contract en modo no destructivo. Agrega CLI, reportes, tests, README/runbook y manifest.
```

---

## Estado de implementación Sprint 75

`FUNC-SPRINT-75 — Quality Gate local unificado` queda implementado en estado `implemented-initial` / `PASS focalizado`. La Fase G ya dispone de una primera verificación local unificada mediante `python -m devpilot_core quality-gate run --json`, con perfiles `fast/full`, reportes opcionales en `outputs/reports/quality_gate.*` y `pytest` explícitamente opcional mediante `--include-pytest`.

Alcance cerrado: módulo `src/devpilot_core/quality/`, CLI `quality-gate run`, subgates readiness/standards/MIASI/eval fixture/app contract, perfil `full` con validation gateway y visual smoke, pruebas automatizadas, auditoría y manifest Sprint 75.

Límites: esta es una primera versión operacional del Quality Gate; no reemplaza todavía CI/CD, no empaqueta, no genera release manifest, no publica artefactos, no despliega, no calcula SBOM/checksums y no ejecuta `pytest` por defecto. El siguiente sprint autorizado es `FUNC-SPRINT-76 — CI local y workflow scaffolding`.

## FUNC-SPRINT-76 — CI local y workflow scaffolding

### Objetivo

Preparar DevPilot para verificación automatizada en CI sin introducir despliegue remoto ni secretos.

### Historias

| ID | Historia | Criterio de aceptación |
|---|---|---|
| US-FUNC-76-001 | Como desarrollador, quiero un comando local equivalente al CI. | Existe perfil `quality-gate run --profile ci`. |
| US-FUNC-76-002 | Como equipo, quiero un workflow GitHub Actions opcional. | Existe workflow dry-run seguro. |
| US-FUNC-76-003 | Como revisor, quiero que CI no use APIs externas. | Proveedores externos bloqueados. |

### Tareas

| ID | Tarea | Entregable | PASS |
|---|---|---|---|
| FUNC-76-001 | Agregar perfil CI al quality gate | `quality-gate run --profile ci` | Reproducible. |
| FUNC-76-002 | Crear workflow GitHub Actions | `.github/workflows/devpilot-ci.yml` | Ejecuta pytest/gates. |
| FUNC-76-003 | Crear documento CI local | `docs/05_operations/ci_cd_local.md` | Procedimiento claro. |
| FUNC-76-004 | Validar que no haya deploy | Workflow sin publish/deploy. | Seguro. |
| FUNC-76-005 | Tests/config validation | Tests o validación estática YAML mínima | PASS. |

### Archivos previstos

```text
.github/workflows/devpilot-ci.yml
docs/05_operations/ci_cd_local.md
docs/audits/func_sprint_76_ci_scaffolding_audit.md
docs/functional_sprint_76_manifest.json
```

### Comandos objetivo

```powershell
python -m devpilot_core quality-gate run --profile ci --json
python -m pytest -q
```

### Criterios PASS

- El workflow solo hace checkout/setup Python/install/test/gates.
- No requiere secretos.
- No publica paquetes.
- No despliega.

### Criterios BLOCK

- No cerrar si el workflow usa secrets o deploy.
- No cerrar si el perfil CI no es reproducible localmente.

### Riesgos y mitigaciones

| ID | Riesgo | Mitigación |
|---|---|---|
| RISK-FUNC-76-001 | Divergencia local vs CI | `quality-gate --profile ci` como fuente común. |
| RISK-FUNC-76-002 | Uso accidental de APIs externas | CostGuard y provider disabled. |
| RISK-FUNC-76-003 | CI rompe local-first | Workflow opcional y documentado. |

### Prompt operativo sugerido

```text
Implementa FUNC-SPRINT-76. Agrega perfil CI al QualityGate y workflow GitHub Actions opcional, sin secrets, sin publicación y sin deploy. Documenta procedimiento local y riesgos.
```

---


## Estado de implementación Sprint 76

`FUNC-SPRINT-76 — CI local y workflow scaffolding` queda implementado en estado `implemented-initial` / `PASS focalizado`. La Fase G ya dispone de un perfil CI reproducible mediante `python -m devpilot_core quality-gate run --profile ci --json` y de un workflow GitHub Actions opcional en `.github/workflows/devpilot-ci.yml`.

Alcance cerrado: perfil `ci` del Quality Gate, subgate `ci-workflow-static`, `pytest -q` como paso explícito, workflow opcional sin secretos, sin publicación y sin despliegue, documento `docs/05_operations/ci_cd_local.md`, auditoría y manifest Sprint 76.

Límites: esta es una primera versión de scaffolding CI; no genera release manifest, no empaqueta, no calcula SBOM/checksums, no firma artefactos y no publica releases. El siguiente sprint autorizado es `FUNC-SPRINT-77 — Release metadata y Release Manifest`.

## FUNC-SPRINT-77 — Release metadata y Release Manifest

### Objetivo

Crear un modelo formal de metadata de versión y manifest de release para cada paquete liberable.

### Historias

| ID | Historia | Criterio de aceptación |
|---|---|---|
| US-FUNC-77-001 | Como release manager, quiero un manifest por release. | Existe `release manifest`. |
| US-FUNC-77-002 | Como auditor, quiero rastrear commit, pruebas y artefactos. | Manifest incluye evidencia. |
| US-FUNC-77-003 | Como usuario, quiero saber qué contiene una versión. | Manifest lista componentes y checks. |

### Tareas

| ID | Tarea | Entregable | PASS |
|---|---|---|---|
| FUNC-77-001 | Crear módulo release | `src/devpilot_core/release/manifest.py` | Modelo manifest. |
| FUNC-77-002 | CLI release manifest | `release manifest --json` | Salida parseable. |
| FUNC-77-003 | Capturar metadata | version, timestamp, git, tests, gates | Completo. |
| FUNC-77-004 | Reportes | `outputs/reports/release_manifest.*` | Con `--write-report`. |
| FUNC-77-005 | Tests | `tests/test_release_manifest.py` | PASS. |

### Archivos previstos

```text
src/devpilot_core/release/__init__.py
src/devpilot_core/release/manifest.py
tests/test_release_manifest.py
docs/audits/func_sprint_77_release_manifest_audit.md
docs/functional_sprint_77_manifest.json
```

### Comandos objetivo

```powershell
python -m devpilot_core release manifest --version 0.1.0 --json
python -m devpilot_core release manifest --version 0.1.0 --json --write-report
python -m pytest -q
```

### Criterios PASS

- Manifest no requiere red.
- Manifest incluye quality gate status o referencia.
- Manifest lista archivos release esperados.
- Manifest no incluye secretos.

### Criterios BLOCK

- No cerrar si el manifest no es JSON válido.
- No cerrar si depende de outputs preexistentes no regenerables.

### Riesgos y mitigaciones

| ID | Riesgo | Mitigación |
|---|---|---|
| RISK-FUNC-77-001 | Metadata incompleta | Schema de manifest futuro/actual. |
| RISK-FUNC-77-002 | Git ausente | Soportar `is_git_repo=false`. |
| RISK-FUNC-77-003 | Datos sensibles | Redacción y exclusiones. |

### Prompt operativo sugerido

```text
Implementa FUNC-SPRINT-77. Crea ReleaseManifest local, CLI `release manifest`, reportes y tests. Debe funcionar sin red y sin publicar artefactos.
```

---


## Estado de implementación Sprint 77

`FUNC-SPRINT-77 — Release metadata y Release Manifest` queda implementado en estado `implemented-initial` / `PASS focalizado`. La Fase G ya dispone del módulo `devpilot_core.release`, del comando `python -m devpilot_core release manifest --version 0.1.0 --json` y de reportes opcionales bajo `outputs/reports/release_manifest.*`.

Alcance cerrado: metadata de versión SemVer, timestamp UTC, metadata de `pyproject.toml`, soporte de metadata Git cuando existe `.git`, componentes principales del producto, evidencias requeridas (`pytest`, `quality-gate ci`, Web UI smoke), artefactos esperados de Fase G y reglas de exclusión.

Límites: esta es una primera versión del manifest; no construye package, no genera changelog, no calcula SBOM/checksums, no firma, no etiqueta Git, no publica y no despliega. El siguiente sprint autorizado es `FUNC-SPRINT-78 — Changelog generator y política de cambios`.

## FUNC-SPRINT-78 — Changelog generator y política de cambios

### Objetivo

Crear un generador inicial de changelog legible para humanos, basado en manifests, sprints y/o commits locales, siguiendo una estructura compatible con Keep a Changelog.

### Historias

| ID | Historia | Criterio de aceptación |
|---|---|---|
| US-FUNC-78-001 | Como usuario, quiero entender qué cambió en una versión. | Existe changelog generado. |
| US-FUNC-78-002 | Como release manager, quiero categorías consistentes. | Usa Added/Changed/Fixed/Security/etc. |
| US-FUNC-78-003 | Como auditor, quiero trazabilidad a sprints/manifests. | Referencias incluidas. |

### Tareas

| ID | Tarea | Entregable | PASS |
|---|---|---|---|
| FUNC-78-001 | Crear generador | `src/devpilot_core/release/changelog.py` | Genera Markdown. |
| FUNC-78-002 | CLI | `release changelog --version` | JSON/MD. |
| FUNC-78-003 | Plantilla | `docs/release/CHANGELOG.md` | Estructura base. |
| FUNC-78-004 | Integrar manifests | Lee `docs/functional_sprint_*_manifest.json` | Referencias. |
| FUNC-78-005 | Tests | `tests/test_release_changelog.py` | PASS. |

### Archivos previstos

```text
src/devpilot_core/release/changelog.py
docs/release/CHANGELOG.md
tests/test_release_changelog.py
docs/audits/func_sprint_78_changelog_audit.md
docs/functional_sprint_78_manifest.json
```

### Comandos objetivo

```powershell
python -m devpilot_core release changelog --version 0.1.0 --json
python -m devpilot_core release changelog --version 0.1.0 --write-report --json
python -m pytest -q
```

### Criterios PASS

- Changelog es legible por humanos.
- No es un dump crudo de git log.
- Categoriza cambios.
- Mantiene trazabilidad a sprints/manifests cuando existan.

### Criterios BLOCK

- No cerrar si el changelog inventa cambios no soportados por manifests/commits/docs.
- No cerrar si sobrescribe manualmente sin dry-run/confirmación.

### Riesgos y mitigaciones

| ID | Riesgo | Mitigación |
|---|---|---|
| RISK-FUNC-78-001 | Changelog falso o inflado | Solo fuentes locales verificables. |
| RISK-FUNC-78-002 | Texto poco útil | Categorías y resumen humano. |
| RISK-FUNC-78-003 | Sobrescritura | Dry-run por defecto. |

### Prompt operativo sugerido

```text
Implementa FUNC-SPRINT-78. Crea generador de changelog local basado en sprints/manifests y estilo Keep a Changelog. Debe operar en dry-run por defecto y generar evidencia.
```

---


### Estado de implementación Sprint 78

`FUNC-SPRINT-78 — Changelog generator y política de cambios` queda implementado en estado `implemented-initial` y con veredicto `PASS` focalizado. El alcance introduce `release changelog --version`, `docs/release/CHANGELOG.md`, `docs/05_operations/change_policy.md`, auditoría, manifest funcional y pruebas. El generador usa manifests locales como fuente primaria, produce categorías compatibles con Keep a Changelog y no sobrescribe el changelog canónico desde CLI.

Límites explícitos: no publica, no despliega, no firma, no etiqueta Git, no construye paquetes, no genera SBOM/checksums y no analiza todavía todos los commits como fuente primaria. La siguiente unidad autorizada es `FUNC-SPRINT-79 — Packaging Python y ZIP limpio reproducible`.

## FUNC-SPRINT-79 — Packaging Python y ZIP limpio reproducible

### Objetivo

Automatizar la creación de paquetes liberables: wheel/sdist si aplica y ZIP limpio del repo, excluyendo artefactos runtime.

### Historias

| ID | Historia | Criterio de aceptación |
|---|---|---|
| US-FUNC-79-001 | Como release manager, quiero construir un paquete limpio. | Existe `package build`. |
| US-FUNC-79-002 | Como usuario, quiero instalar DevPilot localmente. | Wheel/sdist o estrategia equivalente. |
| US-FUNC-79-003 | Como auditor, quiero saber qué fue excluido. | Reporte de exclusiones. |

### Tareas

| ID | Tarea | Entregable | PASS |
|---|---|---|---|
| FUNC-79-001 | Crear módulo package | `src/devpilot_core/release/package_builder.py` | Build plan. |
| FUNC-79-002 | ZIP limpio | `package build --kind repo-zip` | Excluye runtime. |
| FUNC-79-003 | Python package | `package build --kind python` | sdist/wheel si build disponible. |
| FUNC-79-004 | Reporte de package | `outputs/reports/package_build.*` | Incluye excludes. |
| FUNC-79-005 | Tests | `tests/test_package_builder.py` | PASS. |

### Archivos previstos

```text
src/devpilot_core/release/package_builder.py
tests/test_package_builder.py
docs/audits/func_sprint_79_packaging_audit.md
docs/functional_sprint_79_manifest.json
```

### Comandos objetivo

```powershell
python -m devpilot_core package build --kind repo-zip --version 0.1.0 --json
python -m devpilot_core package build --kind python --version 0.1.0 --json
python -m pytest -q
```

### Criterios PASS

- Excluye `outputs/`, `.pytest_cache`, `__pycache__`, `.venv`, `.git`, `.devpilot/devpilot.db`.
- Puede operar en dry-run.
- Produce lista de archivos incluidos/excluidos.
- No requiere publicar en PyPI.

### Criterios BLOCK

- No cerrar si incluye secretos o runtime DB.
- No cerrar si publica externamente.
- No cerrar si no documenta dependencias de build.

### Riesgos y mitigaciones

| ID | Riesgo | Mitigación |
|---|---|---|
| RISK-FUNC-79-001 | Paquete contaminado | Exclusion manifest. |
| RISK-FUNC-79-002 | Build no reproducible | Manifest y checksums. |
| RISK-FUNC-79-003 | Dependencia de build no documentada | ADR/README/runbook. |

### Prompt operativo sugerido

```text
Implementa FUNC-SPRINT-79. Crea package builder para repo zip limpio y paquete Python local. No publiques externamente. Genera reporte de inclusiones/exclusiones y tests.
```

---

### Estado de implementación Sprint 79

`FUNC-SPRINT-79 — Packaging Python y ZIP limpio reproducible` queda implementado en estado `implemented-initial` y con veredicto `PASS` focalizado. El alcance introduce `package build`, `src/devpilot_core/release/package_builder.py`, ZIP limpio de fuente, wheel/sdist Python preliminares, documentación operativa, auditoría, manifest funcional y pruebas. El comando opera en dry-run por defecto; `--execute` escribe artefactos locales bajo `dist/` y `--write-report` genera evidencia bajo `outputs/reports/package_build.*`.

Límites explícitos: no publica, no despliega, no firma, no etiqueta Git, no calcula SBOM/checksums finales y no ejecuta smoke install. La siguiente unidad autorizada es `FUNC-SPRINT-80 — SBOM y supply-chain baseline`.

## FUNC-SPRINT-80 — SBOM y supply-chain baseline

### Objetivo

Crear una línea base de seguridad de cadena de suministro: SBOM, inventario de dependencias, política SLSA inicial y evidencia local.

### Historias

| ID | Historia | Criterio de aceptación |
|---|---|---|
| US-FUNC-80-001 | Como security reviewer, quiero inventario de componentes. | Existe SBOM/report. |
| US-FUNC-80-002 | Como release manager, quiero controles mínimos de supply chain. | Existe supply-chain checklist. |
| US-FUNC-80-003 | Como auditor, quiero saber si hay dependencias externas. | Reporte declara runtime deps/dev deps. |

### Tareas

| ID | Tarea | Entregable | PASS |
|---|---|---|---|
| FUNC-80-001 | Crear módulo SBOM baseline | `src/devpilot_core/release/sbom.py` | Reporte inicial. |
| FUNC-80-002 | CLI | `release sbom --json` | JSON/MD. |
| FUNC-80-003 | Supply chain policy | `docs/03_security/supply_chain_policy.md` | Baseline. |
| FUNC-80-004 | CycloneDX-compatible plan | Doc o JSON preliminar | Compatible progresivo. |
| FUNC-80-005 | Tests | `tests/test_release_sbom.py` | PASS. |

### Archivos previstos

```text
src/devpilot_core/release/sbom.py
docs/03_security/supply_chain_policy.md
tests/test_release_sbom.py
docs/audits/func_sprint_80_sbom_supply_chain_audit.md
docs/functional_sprint_80_manifest.json
```

### Comandos objetivo

```powershell
python -m devpilot_core release sbom --json
python -m devpilot_core release sbom --json --write-report
python -m pytest -q
```

### Criterios PASS

- Declara dependencias runtime y dev.
- Identifica que runtime actual tiene `dependencies = []` si aplica.
- Genera evidencia local.
- No llama servicios externos de vulnerabilidades.

### Criterios BLOCK

- No cerrar si requiere red.
- No cerrar si omite dev dependencies.
- No cerrar si no documenta limitaciones del SBOM inicial.

### Riesgos y mitigaciones

| ID | Riesgo | Mitigación |
|---|---|---|
| RISK-FUNC-80-001 | Falso sentido de seguridad | Declarar SBOM inicial/no SCA completo. |
| RISK-FUNC-80-002 | Dependencias ocultas | Parsear `pyproject.toml`. |
| RISK-FUNC-80-003 | Formato no estándar | Plan hacia CycloneDX. |

### Prompt operativo sugerido

```text
Implementa FUNC-SPRINT-80. Crea SBOM baseline local, política de supply chain y CLI `release sbom`. No uses red ni herramientas externas obligatorias. Documenta limitaciones.
```

---

## FUNC-SPRINT-81 — Checksums, smoke tests y verificación de release

### Objetivo

Crear mecanismos para verificar artefactos de release: checksums, smoke tests y release verification report.

### Historias

| ID | Historia | Criterio de aceptación |
|---|---|---|
| US-FUNC-81-001 | Como usuario, quiero verificar integridad del ZIP/paquete. | Checksums generados. |
| US-FUNC-81-002 | Como release manager, quiero probar instalación mínima. | Smoke test pasa. |
| US-FUNC-81-003 | Como auditor, quiero reporte de verificación. | `release verify` genera evidencia. |

### Tareas

| ID | Tarea | Entregable | PASS |
|---|---|---|---|
| FUNC-81-001 | Crear checksums | `release checksum` | SHA256. |
| FUNC-81-002 | Smoke test | `release smoke-test` | Ejecuta versión/status/gates mínimos. |
| FUNC-81-003 | Verificación release | `release verify` | Consolida package + checksums + smoke. |
| FUNC-81-004 | Tests | `tests/test_release_verification.py` | PASS. |
| FUNC-81-005 | Runbook | `docs/05_operations/release_verification.md` | Procedimiento. |

### Archivos previstos

```text
src/devpilot_core/release/verification.py
docs/05_operations/release_verification.md
tests/test_release_verification.py
docs/audits/func_sprint_81_release_verification_audit.md
docs/functional_sprint_81_manifest.json
```

### Comandos objetivo

```powershell
python -m devpilot_core release checksum --artifact dist/devpilot.zip --json
python -m devpilot_core release smoke-test --artifact dist/devpilot.zip --json
python -m devpilot_core release verify --artifact dist/devpilot.zip --json --write-report
python -m pytest -q
```

### Criterios PASS

- Checksums SHA256 generados.
- Smoke test no requiere red.
- Reporte indica PASS/BLOCK.
- No ejecuta acciones destructivas.

### Criterios BLOCK

- No cerrar si no verifica artefacto real/local.
- No cerrar si smoke test ignora exit codes.

### Riesgos y mitigaciones

| ID | Riesgo | Mitigación |
|---|---|---|
| RISK-FUNC-81-001 | Verificación superficial | Smoke test mínimo estandarizado. |
| RISK-FUNC-81-002 | Artifact path inseguro | PathGuard. |
| RISK-FUNC-81-003 | Falsa reproducibilidad | Reportar inputs/outputs exactos. |

### Prompt operativo sugerido

```text
Implementa FUNC-SPRINT-81. Agrega checksum, smoke-test y release verify sobre artefactos locales. Genera reportes, tests y documentación. No uses red.
```

---

## FUNC-SPRINT-82 — Estrategia de instalación e installer preliminar

### Objetivo

Definir e implementar una estrategia inicial de instalación local para DevPilot, sin auto-update ni distribución remota obligatoria.

### Historias

| ID | Historia | Criterio de aceptación |
|---|---|---|
| US-FUNC-82-001 | Como usuario, quiero instalar DevPilot localmente de forma repetible. | Procedimiento documentado. |
| US-FUNC-82-002 | Como owner, quiero decidir entre editable install, wheel, zip y desktop package. | Matriz de instalación. |
| US-FUNC-82-003 | Como revisor, quiero evitar instaladores inseguros. | Threat model de instalación. |

### Tareas

| ID | Tarea | Entregable | PASS |
|---|---|---|---|
| FUNC-82-001 | Crear install guide | `docs/05_operations/install_guide.md` | Pasos Windows/local. |
| FUNC-82-002 | Crear install strategy | `docs/02_architecture/adrs/ADR-XXXX-installation-strategy.md` | Decisión. |
| FUNC-82-003 | Instalar desde wheel/zip | Script o comando dry-run | Validado. |
| FUNC-82-004 | Desktop packaging bridge | Documento si Fase F existe | No duplicar. |
| FUNC-82-005 | Tests/docs validation | Validadores PASS | PASS. |

### Archivos previstos

```text
docs/05_operations/install_guide.md
docs/02_architecture/adrs/ADR-XXXX-installation-strategy.md
docs/audits/func_sprint_82_installation_audit.md
docs/functional_sprint_82_manifest.json
```

### Comandos objetivo

```powershell
python -m devpilot_core validate-artifact docs/05_operations/install_guide.md --json
python -m pytest -q
```

### Criterios PASS

- Instalación local documentada.
- No hay auto-update.
- No requiere privilegios elevados por defecto.
- Explica relación con Desktop shell si existe.

### Criterios BLOCK

- No cerrar si instala servicios persistentes sin ADR.
- No cerrar si requiere red sin alternativa local.

### Riesgos y mitigaciones

| ID | Riesgo | Mitigación |
|---|---|---|
| RISK-FUNC-82-001 | Instalación frágil | Smoke test. |
| RISK-FUNC-82-002 | Privilegios innecesarios | User-local install. |
| RISK-FUNC-82-003 | Divergencia desktop/core | ADR explícita. |

### Prompt operativo sugerido

```text
Implementa FUNC-SPRINT-82. Documenta estrategia de instalación local, ADR y guía operativa. No implementes auto-update ni distribución remota.
```

---

## FUNC-SPRINT-83 — Backup, restore y upgrade local

### Objetivo

Crear capacidades básicas de backup/restore/upgrade para configuración y estado local, especialmente `.devpilot/project.yaml`, MIASI registries, providers example/local y SQLite state.

### Historias

| ID | Historia | Criterio de aceptación |
|---|---|---|
| US-FUNC-83-001 | Como usuario, quiero respaldar mi workspace antes de actualizar. | Existe `backup create`. |
| US-FUNC-83-002 | Como operador, quiero restaurar configuración. | Existe `backup restore` controlado. |
| US-FUNC-83-003 | Como desarrollador, quiero migrar versiones. | Existe plan `upgrade check`. |

### Tareas

| ID | Tarea | Entregable | PASS |
|---|---|---|---|
| FUNC-83-001 | Backup manager | `src/devpilot_core/release/backup.py` | Crea backup local. |
| FUNC-83-002 | CLI backup | `backup create/list/restore --dry-run` | Operativo. |
| FUNC-83-003 | Upgrade check | `upgrade check --json` | Plan. |
| FUNC-83-004 | Path/policy gates | Integrar PathGuard | Seguro. |
| FUNC-83-005 | Tests | `tests/test_backup_upgrade.py` | PASS. |

### Archivos previstos

```text
src/devpilot_core/release/backup.py
src/devpilot_core/release/upgrade.py
tests/test_backup_upgrade.py
docs/05_operations/backup_restore_upgrade.md
docs/audits/func_sprint_83_backup_upgrade_audit.md
docs/functional_sprint_83_manifest.json
```

### Comandos objetivo

```powershell
python -m devpilot_core backup create --dry-run --json
python -m devpilot_core backup list --json
python -m devpilot_core backup restore --backup-id <id> --dry-run --json
python -m devpilot_core upgrade check --json
python -m pytest -q
```

### Criterios PASS

- Restore es dry-run por defecto.
- Restore requiere aprobación o `--execute` explícito según política.
- No respalda secretos sin redacción/advertencia.
- Backup excluye caches/outputs salvo opción explícita.

### Criterios BLOCK

- No cerrar si restore sobrescribe sin confirmación.
- No cerrar si backup incluye `.venv` o `.git` por defecto.

### Riesgos y mitigaciones

| ID | Riesgo | Mitigación |
|---|---|---|
| RISK-FUNC-83-001 | Pérdida de datos | Dry-run + backup manifest. |
| RISK-FUNC-83-002 | Exfiltración de secretos | SecretGuard/redacción. |
| RISK-FUNC-83-003 | Upgrade incompatible | `upgrade check`. |

### Prompt operativo sugerido

```text
Implementa FUNC-SPRINT-83. Crea backup/restore/upgrade local con dry-run por defecto, PathGuard, SecretGuard y reportes. No sobrescribas archivos sin confirmación.
```

---

## FUNC-SPRINT-84 — ReleaseAgent MVP dry-run y cierre Fase G

### Objetivo

Implementar un `ReleaseAgent` MVP en modo dry-run, que orquesta checks y genera recomendaciones de release sin publicar ni desplegar.

### Historias

| ID | Historia | Criterio de aceptación |
|---|---|---|
| US-FUNC-84-001 | Como release manager, quiero asistencia para preparar release. | `agent run release-assistant` funciona en dry-run. |
| US-FUNC-84-002 | Como auditor, quiero recomendaciones basadas en evidence. | El agente cita quality gate, manifest, changelog y package. |
| US-FUNC-84-003 | Como owner, quiero cerrar Fase G con evidencia. | Existe closure report. |

### Tareas

| ID | Tarea | Entregable | PASS |
|---|---|---|---|
| FUNC-84-001 | Registrar ReleaseAgent | MIASI registries | Status `implemented-initial`. |
| FUNC-84-002 | Implementar agente dry-run | `src/devpilot_core/agents/release_agent.py` o runtime extension | No publica. |
| FUNC-84-003 | Integrar tools release | quality-gate, manifest, changelog, package, sbom | Tool calls auditables. |
| FUNC-84-004 | Cierre Fase G | `docs/audits/phase_g_productization_release_closure.md` | Completo. |
| FUNC-84-005 | Tests | `tests/test_release_agent.py` | PASS. |

### Archivos previstos

```text
src/devpilot_core/agents/release_agent.py
tests/test_release_agent.py
docs/audits/phase_g_productization_release_closure.md
docs/audits/func_sprint_84_release_agent_audit.md
docs/functional_sprint_84_manifest.json
```

### Comandos objetivo

```powershell
python -m devpilot_core agent run release-assistant --dry-run --json
python -m devpilot_core quality-gate run --profile release --json
python -m pytest -q
```

### Criterios PASS

- ReleaseAgent no publica, no despliega, no etiqueta repositorios.
- Produce checklist de release y recomendaciones.
- Usa tool calls auditables.
- Cierre Fase G resume sprints 74–84.

### Criterios BLOCK

- No cerrar si el agente ejecuta publicación/deploy/tag real.
- No cerrar si no pasa por MIASI/PolicyEngine.
- No cerrar si no actualiza docs de cierre.

### Riesgos y mitigaciones

| ID | Riesgo | Mitigación |
|---|---|---|
| RISK-FUNC-84-001 | Agente con demasiado poder | Dry-run obligatorio. |
| RISK-FUNC-84-002 | Recomendaciones sin evidencia | Basarse en quality gate/manifest/reports. |
| RISK-FUNC-84-003 | Confusión release/deploy | Deploy fuera de alcance. |

### Prompt operativo sugerido

```text
Implementa FUNC-SPRINT-84. Crea ReleaseAgent MVP en dry-run, registra capacidades MIASI, integra quality gate/manifest/changelog/package/sbom como consultas, no publiques ni despliegues. Cierra Fase G con reporte formal.
```

---

## Cierre esperado de Fase G

Al finalizar FUNC-SPRINT-84, DevPilot debe contar con:

```text
- release/versioning ADR;
- quality gate local;
- CI scaffolding seguro;
- release manifest;
- changelog generator;
- package builder;
- SBOM baseline;
- checksums;
- smoke tests;
- install guide;
- backup/restore/upgrade básico;
- ReleaseAgent dry-run;
- closure report Fase G.
```

### Prompt global de Fase G

```text
Desarrolla la Fase G — Productización y release, iniciando en FUNC-SPRINT-74. Respeta el modelo de backlog ejecutable de DevPilot. Mantén local-first, dry-run-first, PolicyEngine, MIASI, reportes y trazabilidad. No publiques paquetes externamente, no despliegues, no uses secrets y no incluyas runtime artifacts en paquetes.
```
