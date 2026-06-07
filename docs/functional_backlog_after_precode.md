---
title: "DevPilot Local — Backlog ejecutable posterior a pre-code"
doc_id: "DEVPL-FUNC-BACKLOG-001"
status: "approved"
version: "1.3.0"
owner: "Ordóñez"
standard: "MIPSoftware"
extension: "MIASI"
phase: "POST-PRECODE"
updated: "2026-06-07"
approval: "approved_by_owner_direction"
source_baseline: "precode_baseline_approved"
change_policy: "controlled_changes_allowed_via_docs_as_code"
approved_on: "2026-06-06"
approval_scope: "functional_backlog_after_precode"
baseline_execution: "FUNC-SPRINT-00"
next_sprint: "FUNC-SPRINT-06"
---

# DevPilot Local — Backlog ejecutable posterior a pre-code

# Estado de aprobación funcional

Este backlog queda promovido a `approved` el 2026-06-06 como guía ejecutable para iniciar la implementación funcional de DevPilot Local después del cierre de la fase pre-code.

La aprobación no congela el documento: cualquier ajuste futuro debe seguir la política docs-as-code definida en MIPSoftware, dejar trazabilidad, actualizar criterios de aceptación cuando aplique y preservar la relación entre producto, requerimientos, arquitectura, seguridad, calidad, operación y MIASI.

La ejecución de `FUNC-SPRINT-00` confirma que el repositorio queda limpio, reproducible y listo para iniciar `FUNC-SPRINT-01 — Arquitectura interna del CLI y modelo común de resultados`.


## 1. Propósito

Este documento convierte la baseline pre-code aprobada de DevPilot Local en un backlog funcional ejecutable. Su función es guiar el inicio de la codificación de la plataforma de forma progresiva, verificable, local-first, segura y alineada con MIPSoftware y MIASI.

El backlog no reemplaza los documentos de producto, requerimientos, arquitectura, seguridad, calidad, operación y MIASI. Los operacionaliza. Cada sprint debe producir código, pruebas, reportes o documentación técnica verificable.

## 2. Regla central después de pre-code

La fase pre-code está cerrada, pero la carpeta `docs/` sigue siendo el contrato de ingeniería vivo del proyecto. Puede ajustarse durante la implementación, pero solo bajo control:

1. todo cambio debe ser versionado en Git;
2. todo cambio significativo debe explicar motivo, impacto y trazabilidad;
3. los cambios que alteren arquitectura, seguridad, agentes, herramientas, persistencia, costos o APIs deben generar o actualizar ADR;
4. los cambios que afecten requerimientos deben actualizar criterios de aceptación y matriz de trazabilidad;
5. los cambios que afecten comportamiento ejecutable deben acompañarse de tests;
6. los cambios que afecten MIASI deben actualizar Agent/Tool/Policy/Eval/Approval/Observability cards;
7. ningún documento aprobado debe modificarse como atajo para hacer pasar un gate sin justificar el cambio.

## 3. Alcance del primer ciclo funcional

El primer ciclo funcional busca convertir DevPilot de un proyecto documentado en una herramienta local ejecutable capaz de:

- validar artefactos MIPSoftware/MIASI;
- leer y evaluar frontmatter YAML;
- aplicar gates pre-code;
- generar reportes JSON/Markdown;
- emitir trazas JSONL;
- trabajar con workspaces locales;
- aplicar políticas de seguridad sobre rutas, secretos y costos;
- preparar registries ejecutables de agentes y herramientas;
- iniciar agentes documentales controlados;
- integrar Git en modo read-only;
- preparar patch/code review en dry-run;
- mantener pruebas herméticas sin API keys reales.

## 4. Niveles de implementación

| Nivel | Nombre | Objetivo | Estado esperado |
|---|---|---|---|
| L0 | Bootstrap funcional | CLI mínimo y pruebas básicas | Ya iniciado |
| L1 | Gates documentales | MIPSoftware/MIASI ejecutable como validadores | Próximo |
| L2 | Workspace local | Proyecto gestionado por `.devpilot/` | Pendiente |
| L3 | Evidencia y observabilidad | Reportes, JSONL, auditoría local | Pendiente |
| L4 | Seguridad operativa | Policy Engine, SecretGuard, CostGuard | Pendiente |
| L5 | MIASI ejecutable | Agent/Tool/Policy registries verificables | Pendiente |
| L6 | Agentes documentales | Agentes mock/local en dry-run | Pendiente |
| L7 | Repositorios | Git read-only, inventario, análisis | Pendiente |
| L8 | Patches y código | Patch review, code review, refactor plan | Pendiente |
| L9 | Modelos híbridos | ModelAdapter local/API opcional con costos | Pendiente |
| L10 | Interfaces | Desktop/web sobre DevPilot Core | Futuro |

## 5. Definition of Done transversal

Un sprint funcional solo se considera cerrado si cumple:

- código integrado en `src/devpilot_core/`;
- comandos documentados en `README.md` o `docs/05_operations/runbook.md`;
- pruebas `pytest` nuevas o actualizadas;
- reportes o trazas cuando aplique;
- sin API keys reales;
- sin llamadas externas obligatorias;
- dry-run por defecto en cualquier acción con side effects;
- errores con mensajes claros y exit codes consistentes;
- `pytest -q` en PASS;
- `git status` limpio después del commit;
- documentación actualizada si cambió contrato, arquitectura, seguridad o MIASI.

## 6. Convenciones de IDs

| Tipo | Prefijo | Ejemplo |
|---|---|---|
| Sprint funcional | `FUNC-SPRINT-XX` | `FUNC-SPRINT-01` |
| Historia | `US-FUNC-XX-YYY` | `US-FUNC-01-001` |
| Tarea | `FUNC-XX-YYY` | `FUNC-01-003` |
| Prueba | `TEST-FUNC-XX-YYY` | `TEST-FUNC-01-002` |
| Gate | `GATE-FUNC-XX` | `GATE-FUNC-01` |
| Riesgo | `RISK-FUNC-XX-YYY` | `RISK-FUNC-04-001` |

## 7. Roadmap funcional por releases

| Release | Sprints | Resultado esperado |
|---|---|---|
| R0 | FUNC-SPRINT-00 | Higiene del repo y baseline lista para codificar |
| R1 | FUNC-SPRINT-01 a 05 | Validadores, reportes y trazas MIPSoftware/MIASI |
| R2 | FUNC-SPRINT-06 a 09 | Workspace, políticas, persistencia local y registries |
| R3 | FUNC-SPRINT-10 a 12 | Agentes documentales, evaluación y observabilidad agentic |
| R4 | FUNC-SPRINT-13 a 15 | Git read-only, repo inventory, patch/code review dry-run |
| R5 | FUNC-SPRINT-16 a 18 | ModelAdapter híbrido, CostGuard, preparación desktop/web |

---

# FUNC-SPRINT-00 — Higiene del repo y sincronización de baseline

## Objetivo

Asegurar que el repo completo esté limpio, reproducible y listo para iniciar implementación funcional fuerte.

## Entradas

- `repo_DevPilot_Local.zip` o repo local actual.
- Baseline pre-code aprobada.
- `pyproject.toml`.
- `.gitignore`.

## Historias

| ID | Historia | Criterio de aceptación |
|---|---|---|
| US-FUNC-00-001 | Como desarrollador, quiero que el repo no contenga caches ni artefactos generados para mantenerlo limpio. | `.pytest_cache`, `__pycache__`, `*.egg-info` y ZIPs locales no quedan versionados. |
| US-FUNC-00-002 | Como desarrollador, quiero poder ejecutar pruebas desde entorno local sin configuración ambigua. | `python -m pytest -q` funciona tras instalación editable o con instrucciones claras. |

## Tareas

| ID | Tarea | Entregable | PASS |
|---|---|---|---|
| FUNC-00-001 | Revisar `.gitignore` | `.gitignore` actualizado | Ignora caches, builds, zips locales y `*.egg-info`. |
| FUNC-00-002 | Eliminar artefactos generados del repo si están trackeados | repo limpio | No hay caches en `git status`. |
| FUNC-00-003 | Confirmar instalación editable | instrucciones en README/runbook | `python -m pip install -e .[dev]` documentado. |
| FUNC-00-004 | Ejecutar pruebas baseline | salida pytest | `pytest -q` PASS. |
| FUNC-00-005 | Registrar baseline funcional inicial | commit/tag | commit limpio. |

## Comandos objetivo

```powershell
python -m pip install -e .[dev]
python -m pytest -q
python -m devpilot_core --version
python -m devpilot_core readiness-check
python -m devpilot_core miasi-required
git status
```

## BLOCK

- No continuar si `pytest` falla.
- No continuar si el repo contiene caches versionadas.
- No continuar si la documentación pre-code no está aplicada.

## Prompt operativo

```text
Estamos en DevPilot Local. Ejecuta FUNC-SPRINT-00: audita higiene del repo, .gitignore, instalación editable, pytest, readiness-check y miasi-required. Si hay artefactos generados versionados, proyecta patch. No modifiques funcionalidad de negocio.
```

---

# FUNC-SPRINT-01 — Arquitectura interna del CLI y modelo común de resultados

## Objetivo

Endurecer la base del CLI para que todos los comandos futuros compartan contrato de entrada/salida, errores, exit codes, reportes y trazas.

## Historias

| ID | Historia | Criterio de aceptación |
|---|---|---|
| US-FUNC-01-001 | Como usuario, quiero comandos CLI consistentes para entender resultados y fallos. | Todo comando devuelve salida humana y opción JSON cuando aplique. |
| US-FUNC-01-002 | Como desarrollador, quiero un contrato común de resultado para evitar lógica duplicada. | Existe `CommandResult` o equivalente. |

## Tareas

| ID | Tarea | Entregable | PASS |
|---|---|---|---|
| FUNC-01-001 | Crear `devpilot_core.cli_models` | modelos de resultado | `CommandResult`, `Finding`, `Severity`, `ExitCode`. |
| FUNC-01-002 | Normalizar exit codes | constantes | `0 PASS`, `1 FAIL`, `2 BLOCK`, `3 ERROR`. |
| FUNC-01-003 | Refactorizar `cli.py` | CLI modular | `--version`, `readiness-check`, `miasi-required` siguen funcionando. |
| FUNC-01-004 | Agregar opción `--json` donde aplique | salida JSON | JSON válido parseable. |
| FUNC-01-005 | Agregar tests de CLI básico | tests | pruebas de versión, readiness y MIASI. |

## Archivos previstos

```text
src/devpilot_core/cli.py
src/devpilot_core/cli_models.py
src/devpilot_core/errors.py
tests/test_cli_core.py
```

## Comandos objetivo

```powershell
python -m devpilot_core --version
python -m devpilot_core readiness-check --json
python -m devpilot_core miasi-required --json
python -m pytest -q
```

## BLOCK

- No agregar dependencias externas salvo justificación.
- No cambiar nombres de comandos existentes sin compatibilidad.

## Prompt operativo

```text
Implementa FUNC-SPRINT-01 sobre DevPilot Local. Crea un modelo común de resultados CLI, exit codes, errores y salida JSON. Mantén compatibilidad con --version, readiness-check y miasi-required. Agrega pruebas pytest. No uses APIs externas.
```

---

# FUNC-SPRINT-02 — Validador de frontmatter y metadatos documentales

## Objetivo

Implementar validación estricta del frontmatter YAML-like de documentos Markdown sin introducir dependencias nuevas obligatorias.

## Historias

| ID | Historia | Criterio de aceptación |
|---|---|---|
| US-FUNC-02-001 | Como owner, quiero detectar documentos sin metadatos mínimos. | Documento sin `doc_id`, `status`, `version` u `owner` falla. |
| US-FUNC-02-002 | Como desarrollador, quiero validar un archivo específico desde CLI. | `validate-frontmatter <path>` produce PASS/FAIL y reporte. |

## Tareas

| ID | Tarea | Entregable | PASS |
|---|---|---|---|
| FUNC-02-001 | Crear parser simple de frontmatter | `frontmatter.py` | Lee bloque entre `---`. |
| FUNC-02-002 | Validar campos obligatorios | reglas | Valida `title`, `doc_id`, `status`, `version`, `owner`, `updated`. |
| FUNC-02-003 | Validar estados permitidos | reglas | `draft`, `reviewed`, `approved`, `deprecated`. |
| FUNC-02-004 | Crear comando `validate-frontmatter` | CLI | Reporte por archivo. |
| FUNC-02-005 | Tests válidos e inválidos | fixtures | PASS/FAIL esperado. |

## Archivos previstos

```text
src/devpilot_core/validators/frontmatter.py
src/devpilot_core/validators/__init__.py
tests/test_frontmatter_validator.py
tests/fixtures/docs/valid_frontmatter.md
tests/fixtures/docs/invalid_frontmatter_missing_doc_id.md
```

## Comandos objetivo

```powershell
python -m devpilot_core validate-frontmatter docs/00_product/product_vision.md
python -m devpilot_core validate-frontmatter docs/00_product/product_vision.md --json
python -m pytest -q
```

## BLOCK

- Documento sin frontmatter debe fallar.
- Documento aprobado sin `approval` o `updated` debe advertir o fallar según modo strict.

## Prompt operativo

```text
Implementa FUNC-SPRINT-02: validador de frontmatter Markdown para DevPilot Local. Debe leer campos obligatorios, validar status/version/doc_id/owner/updated, exponer comando validate-frontmatter, generar JSON y tener tests herméticos con fixtures. Sin dependencias externas obligatorias.
```

---

# FUNC-SPRINT-03 — Validador de artefactos MIPSoftware/MIASI

Estado de implementación: `implemented` en FUNC-SPRINT-03.

## Objetivo

Validar que los documentos principales tengan estructura mínima, secciones requeridas y coherencia básica con su tipo documental.

## Historias

| ID | Historia | Criterio de aceptación |
|---|---|---|
| US-FUNC-03-001 | Como owner, quiero saber si un documento cumple su plantilla esperada. | `validate-artifact` lista secciones faltantes. |
| US-FUNC-03-002 | Como desarrollador, quiero reglas por tipo de documento. | Existen perfiles: producto, requerimientos, arquitectura, seguridad, calidad, operación, MIASI. |

## Tareas

| ID | Tarea | Entregable | PASS |
|---|---|---|---|
| FUNC-03-001 | Crear `artifact_profiles.py` | perfiles de secciones | Perfiles por carpeta. |
| FUNC-03-002 | Crear `artifact_validator.py` | validador | Detecta secciones mínimas. |
| FUNC-03-003 | Crear comando `validate-artifact` | CLI | Evalúa archivo individual. |
| FUNC-03-004 | Soportar severidades | findings | `info/warn/fail/block`. |
| FUNC-03-005 | Tests por perfiles | pytest | Casos positivos y negativos. |

## Archivos previstos

```text
src/devpilot_core/validators/artifact.py
src/devpilot_core/validators/artifact_profiles.py
tests/test_artifact_validator.py
```

## Comandos objetivo

```powershell
python -m devpilot_core validate-artifact docs/01_requirements/requirements_specification.md
python -m devpilot_core validate-artifact docs/06_miasi/agent_card.md --json
python -m pytest -q
```

## BLOCK

- No permitir que un documento `approved` falle estructura mínima sin reportar `BLOCK`.

## Prompt operativo

```text
Implementa FUNC-SPRINT-03: validador de artefactos MIPSoftware/MIASI por perfiles. Debe validar secciones mínimas, severidad de findings, comando validate-artifact, salida JSON y tests. No cambies documentos salvo que una prueba demuestre brecha real.
```

---

# FUNC-SPRINT-04 — Standards Registry y carga local de reglas

## Estado de implementación FUNC-SPRINT-04

`FUNC-SPRINT-04` queda implementado como primer Standards Registry local. El sprint introduce `src/devpilot_core/standards/`, el comando `python -m devpilot_core standards status`, pruebas automatizadas y resumen explícito de pruebas en `pytest -q`.


## Objetivo

Crear un registro local que permita a DevPilot saber qué estándares, documentos, carpetas y perfiles de validación aplican a cada workspace.

## Historias

| ID | Historia | Criterio de aceptación |
|---|---|---|
| US-FUNC-04-001 | Como DevPilot, quiero descubrir MIPSoftware y MIASI dentro de `docs/standards`. | `standards status` detecta ambos estándares. |
| US-FUNC-04-002 | Como owner, quiero saber qué documentos obligatorios aplican. | Reporte lista documentos requeridos y estado. |

## Tareas

| ID | Tarea | Entregable | PASS |
|---|---|---|---|
| FUNC-04-001 | Crear `StandardsRegistry` | módulo | Detecta `docs/standards/mipsoftware` y `docs/standards/miasi`. |
| FUNC-04-002 | Crear catálogo de documentos requeridos | config Python/JSON | Lista 00-06 + checklist + audit. |
| FUNC-04-003 | Crear comando `standards status` | CLI | Reporte de estándares disponibles. |
| FUNC-04-004 | Integrar con validators | engine | Perfiles según estándar. |
| FUNC-04-005 | Tests | pytest | Detecta faltantes y presentes. |

## Archivos previstos

```text
src/devpilot_core/standards/registry.py
src/devpilot_core/standards/catalog.py
tests/test_standards_registry.py
```

## Comandos objetivo

```powershell
python -m devpilot_core standards status
python -m devpilot_core standards status --json
python -m pytest -q
```

## Prompt operativo

```text
Implementa FUNC-SPRINT-04: Standards Registry local para detectar MIPSoftware y MIASI en docs/standards, listar documentos obligatorios y conectar perfiles de validación. Agrega comando standards status y pruebas.
```

---

# FUNC-SPRINT-05 — Checklist pre-code y readiness estricto

## Estado de implementación FUNC-SPRINT-05

`FUNC-SPRINT-05` queda implementado como gate ejecutable de baseline documental pre-code. El sprint introduce `src/devpilot_core/validators/checklist.py`, `src/devpilot_core/validators/readiness.py`, el comando `python -m devpilot_core checklist-pre-code`, el modo `python -m devpilot_core readiness-check --strict`, generación de reportes locales en `outputs/reports/readiness_check.json` y `outputs/reports/readiness_check.md`, pruebas automatizadas y sincronización de README/runbook.

Durante la implementación se realizó un ajuste correctivo controlado sobre `validate-artifact`: el extractor de headings ahora ignora fenced code blocks para no confundir comentarios de ejemplos PowerShell con encabezados Markdown. También se alinearon algunos perfiles determinísticos de artefactos con los encabezados reales de la baseline aprobada. Este ajuste no cambia el alcance de producto ni introduce dependencias; fortalece los validadores previos para que puedan operar como parte del readiness estricto.

## Objetivo

Convertir `checklist_pre_code.md` y `readiness-check` en gates ejecutables de baseline documental.

## Historias

| ID | Historia | Criterio de aceptación | Estado |
|---|---|---|---|
| US-FUNC-05-001 | Como owner, quiero un gate pre-code ejecutable. | `checklist-pre-code` evalúa criterios y devuelve PASS/BLOCK. | Implementado |
| US-FUNC-05-002 | Como desarrollador, quiero `readiness-check --strict`. | Valida existencia, estado, frontmatter, artefactos y MIASI. | Implementado |

## Tareas

| ID | Tarea | Entregable | PASS | Estado |
|---|---|---|---|---|
| FUNC-05-001 | Crear parser de checklist Markdown | `validators/checklist.py` | Lee ítems obligatorios. | Implementado |
| FUNC-05-002 | Crear comando `checklist-pre-code` | CLI | Evalúa checklist. | Implementado |
| FUNC-05-003 | Mejorar `readiness-check --strict` | CLI | Ejecuta frontmatter + artifact + checklist + standards. | Implementado |
| FUNC-05-004 | Generar reporte JSON/Markdown | outputs | `outputs/reports/readiness_check.*`. | Implementado |
| FUNC-05-005 | Tests de PASS/BLOCK | pytest | Falla si falta documento crítico. | Implementado |

## Archivos creados

```text
src/devpilot_core/validators/checklist.py
src/devpilot_core/validators/readiness.py
tests/test_precode_readiness.py
docs/audits/func_sprint_05_precode_readiness_audit.md
docs/functional_sprint_05_manifest.json
```

## Archivos modificados

```text
src/devpilot_core/cli.py
src/devpilot_core/validators/artifact.py
src/devpilot_core/validators/artifact_profiles.py
src/devpilot_core/validators/__init__.py
README.md
docs/05_operations/runbook.md
docs/functional_backlog_after_precode.md
```

## Comandos objetivo

```powershell
python -m devpilot_core checklist-pre-code
python -m devpilot_core checklist-pre-code --json
python -m devpilot_core readiness-check --strict
python -m devpilot_core readiness-check --strict --json
python -m pytest -q
```

## Resultado esperado actual

```text
checklist-pre-code -> PASS
readiness-check --strict -> PASS
pytest -q -> 30 passed
```

## BLOCK

- Un documento obligatorio faltante bloquea.
- Un documento obligatorio no aprobado bloquea en modo strict.
- Un bloque MIASI ausente bloquea porque DevPilot activa MIASI.
- Un checklist sin filas obligatorias bloquea.
- Un documento aprobado que incumple secciones mínimas bloquea.

## Riesgos residuales

- El parser de checklist es una primera versión orientada a las tablas actuales; debe evolucionar si los checklists adoptan una gramática más compleja.
- Los perfiles de artefacto siguen en Python; en sprints posteriores deben migrar gradualmente hacia reglas declarativas del estándar.
- Los warnings por secciones recomendadas no bloquean todavía.

## Prompt operativo

```text
Implementa FUNC-SPRINT-05: checklist-pre-code ejecutable y readiness-check --strict. Debe validar existencia, frontmatter, status approved, artefactos obligatorios, MIASI y generar reportes JSON/Markdown. Tests con escenarios PASS/BLOCK.
```

---

# FUNC-SPRINT-06 — Report Engine y contrato de evidencias

## Objetivo

Centralizar generación de reportes reproducibles en JSON y Markdown para todos los comandos.

## Historias

| ID | Historia | Criterio de aceptación |
|---|---|---|
| US-FUNC-06-001 | Como usuario, quiero reportes legibles y máquinas-legibles. | Cada gate puede generar `.json` y `.md`. |
| US-FUNC-06-002 | Como auditor, quiero evidencia reproducible. | Reportes incluyen timestamp, comando, estado, findings y rutas. |

## Tareas

| ID | Tarea | Entregable | PASS |
|---|---|---|---|
| FUNC-06-001 | Crear `ReportEngine` | módulo | Escribe JSON/Markdown. |
| FUNC-06-002 | Definir contrato de reporte | dataclasses | `report_id`, `status`, `findings`, `summary`. |
| FUNC-06-003 | Integrar con readiness/validators | comandos | `--write-report`. |
| FUNC-06-004 | Snapshot tests | tests | Reportes estables. |
| FUNC-06-005 | Documentar en runbook | docs | Uso reproducible. |

## Archivos previstos

```text
src/devpilot_core/reports/report_engine.py
src/devpilot_core/reports/models.py
tests/test_report_engine.py
outputs/reports/
```

## Prompt operativo

```text
Implementa FUNC-SPRINT-06: Report Engine central para JSON/Markdown. Integra validate-frontmatter, validate-artifact, checklist-pre-code y readiness-check. Agrega snapshot tests y documentación de uso.
```

---

# FUNC-SPRINT-07 — Event Log JSONL y observabilidad local

## Objetivo

Emitir trazas JSONL mínimas para comandos, validaciones, findings, gates y errores.

## Historias

| ID | Historia | Criterio de aceptación |
|---|---|---|
| US-FUNC-07-001 | Como auditor, quiero saber qué ejecutó DevPilot. | Cada comando emite evento JSONL. |
| US-FUNC-07-002 | Como desarrollador, quiero trazas sin secretos. | Eventos redactan tokens y rutas sensibles según política. |

## Tareas

| ID | Tarea | Entregable | PASS |
|---|---|---|---|
| FUNC-07-001 | Crear `EventLogger` | módulo | Escribe `outputs/traces/events.jsonl`. |
| FUNC-07-002 | Definir eventos mínimos | modelos | `command.started`, `command.completed`, `gate.evaluated`. |
| FUNC-07-003 | Redacción básica | util | Redacta patrones de secretos sintéticos. |
| FUNC-07-004 | Integrar CLI | eventos | Todos los comandos emiten trazas. |
| FUNC-07-005 | Tests JSONL | pytest | Cada línea es JSON válido. |

## Prompt operativo

```text
Implementa FUNC-SPRINT-07: EventLogger JSONL local para comandos y gates. Debe generar outputs/traces/events.jsonl, redactar secretos sintéticos, emitir eventos started/completed/finding/error y tener tests.
```

---

# FUNC-SPRINT-08 — Workspace Manager mínimo

## Objetivo

Introducir `.devpilot/` como unidad operativa local de proyecto sin romper repos existentes.

## Historias

| ID | Historia | Criterio de aceptación |
|---|---|---|
| US-FUNC-08-001 | Como usuario, quiero inicializar un workspace. | `workspace init` crea `.devpilot/project.yaml` en dry-run o execute explícito. |
| US-FUNC-08-002 | Como usuario, quiero conocer estado del workspace. | `workspace status` muestra docs, standards, gates y outputs. |

## Tareas

| ID | Tarea | Entregable | PASS |
|---|---|---|---|
| FUNC-08-001 | Crear `WorkspaceManager` | módulo | Detecta raíz del proyecto. |
| FUNC-08-002 | Definir `project.yaml` | contrato | Nombre, tipo, estándares, MIASI, rutas. |
| FUNC-08-003 | Crear comando `workspace init --dry-run` | CLI | No escribe por defecto. |
| FUNC-08-004 | Crear `workspace init --execute` | CLI | Crea `.devpilot/` con confirmación explícita. |
| FUNC-08-005 | Crear `workspace status` | CLI | Reporte de estado. |
| FUNC-08-006 | Tests de rutas | pytest | No permite inicializar fuera del root esperado. |

## Prompt operativo

```text
Implementa FUNC-SPRINT-08: Workspace Manager mínimo con .devpilot/project.yaml, comandos workspace init --dry-run/--execute y workspace status. Aplica seguridad de rutas, no sobrescribir por defecto, reportes y tests.
```

---

# FUNC-SPRINT-09 — Policy Engine, PathGuard, SecretGuard y CostGuard determinísticos

## Objetivo

Crear controles determinísticos antes de habilitar agentes, Git avanzado, patches o APIs externas.

## Historias

| ID | Historia | Criterio de aceptación |
|---|---|---|
| US-FUNC-09-001 | Como owner, quiero bloquear acciones peligrosas por defecto. | Policy Engine evalúa allow/deny/block. |
| US-FUNC-09-002 | Como usuario, quiero evitar exposición de secretos. | SecretGuard redacta patrones sintéticos en reportes y trazas. |
| US-FUNC-09-003 | Como owner, quiero controlar costos externos. | CostGuard bloquea uso externo sin presupuesto/política. |

## Tareas

| ID | Tarea | Entregable | PASS |
|---|---|---|---|
| FUNC-09-001 | Crear `PolicyDecision` | modelo | allow/warn/deny/block + reason. |
| FUNC-09-002 | Crear `PathGuard` | módulo | allowlist/denylist. |
| FUNC-09-003 | Crear `SecretGuard` | módulo | Redacción sintética. |
| FUNC-09-004 | Crear `CostGuard` | módulo | Presupuesto local config. |
| FUNC-09-005 | Crear comando `policy check` | CLI | Evalúa acción simulada. |
| FUNC-09-006 | Tests de bloqueo | pytest | Path traversal, secret, external API sin permiso. |

## Prompt operativo

```text
Implementa FUNC-SPRINT-09: Policy Engine determinístico con PathGuard, SecretGuard y CostGuard. Debe bloquear acciones inseguras por defecto, operar sin APIs, generar decisiones auditables y tener tests de seguridad.
```

---

# FUNC-SPRINT-10 — Persistencia local SQLite y estado operativo

## Objetivo

Crear persistencia local para ejecuciones, gates, findings, agentes, herramientas, aprobaciones y costos sin depender de servicios externos.

## Historias

| ID | Historia | Criterio de aceptación |
|---|---|---|
| US-FUNC-10-001 | Como usuario, quiero histórico local de validaciones. | SQLite guarda runs y gate results. |
| US-FUNC-10-002 | Como auditor, quiero consultar findings anteriores. | CLI puede listar runs recientes. |

## Tareas

| ID | Tarea | Entregable | PASS |
|---|---|---|---|
| FUNC-10-001 | Diseñar schema SQLite v0 | SQL | Tablas: runs, findings, gates, events, approvals, cost_events. |
| FUNC-10-002 | Crear `LocalStore` | módulo | Inicializa DB en `.devpilot/devpilot.db` o `outputs/state`. |
| FUNC-10-003 | Integrar reportes/gates | persistencia | Guarda resultados de readiness. |
| FUNC-10-004 | Crear comando `history list` | CLI | Muestra ejecuciones recientes. |
| FUNC-10-005 | Tests SQLite tempdir | pytest | DB temporal y migración idempotente. |

## Prompt operativo

```text
Implementa FUNC-SPRINT-10: persistencia local SQLite v0 para runs, findings, gates, events, approvals y cost_events. Debe ser local-first, idempotente, testeable con tempdir y sin servicios externos.
```

---

# FUNC-SPRINT-11 — MIASI ejecutable: Agent Registry, Tool Registry y Policy Matrix

## Objetivo

Convertir los documentos MIASI en configuraciones/contratos ejecutables validados por DevPilot.

## Historias

| ID | Historia | Criterio de aceptación |
|---|---|---|
| US-FUNC-11-001 | Como owner, quiero validar agentes permitidos. | `miasi validate-registry` evalúa Agent Registry. |
| US-FUNC-11-002 | Como owner, quiero validar herramientas permitidas. | `miasi validate-tools` evalúa Tool Registry y riesgos. |

## Tareas

| ID | Tarea | Entregable | PASS |
|---|---|---|---|
| FUNC-11-001 | Crear modelos de AgentSpec | dataclasses | nombre, autonomía, tools, riesgos. |
| FUNC-11-002 | Crear modelos de ToolSpec | dataclasses | side_effects, risk_level, approvals. |
| FUNC-11-003 | Parsear documentos/registries Markdown | parser mínimo | Extrae tablas o usa config generada. |
| FUNC-11-004 | Crear comando `miasi validate` | CLI | Valida agent/tool/policy cards. |
| FUNC-11-005 | Tests de registries | pytest | Agente sin policy falla. |

## Prompt operativo

```text
Implementa FUNC-SPRINT-11: validación ejecutable de MIASI para Agent Registry, Tool Registry y Policy Matrix. Debe verificar autonomía, tools permitidas, side effects, approvals y policy coverage. Agrega comando miasi validate y tests.
```

---

# FUNC-SPRINT-12 — Agent Runtime mock/local para agentes documentales MVP

## Objetivo

Implementar agentes documentales controlados, sin LLM externo obligatorio, en dry-run y con separación estricta entre sugerencia y ejecución.

## Agentes MVP

| Agente | Propósito | Modo inicial |
|---|---|---|
| `PreCodeDocumentationAgent` | Sugerir borradores/ajustes para documentos pre-code desde una idea o brecha. | mock/rule-based |
| `DocumentationAuditAgent` | Auditar documentos contra MIPSoftware/MIASI y producir hallazgos. | mock/rule-based |

## Tareas

| ID | Tarea | Entregable | PASS |
|---|---|---|---|
| FUNC-12-001 | Crear `AgentRuntime` mínimo | runtime | Ejecuta agentes registrados en dry-run. |
| FUNC-12-002 | Crear `AgentMessage` y `AgentResult` | modelos | Resultado con findings/sugerencias. |
| FUNC-12-003 | Implementar `DocumentationAuditAgent` | agente | Usa validators, no inventa estado. |
| FUNC-12-004 | Implementar `PreCodeDocumentationAgent` | agente | Genera propuestas en `outputs/drafts`. |
| FUNC-12-005 | Policy check antes de tool call | integración | Tool call no permitido se bloquea. |
| FUNC-12-006 | Tests agentic offline | pytest | No requiere API key. |

## Comandos objetivo

```powershell
python -m devpilot_core agent run documentation-audit --target docs/01_requirements
python -m devpilot_core agent run precode-documentation --idea "..." --dry-run
python -m pytest -q
```

## Prompt operativo

```text
Implementa FUNC-SPRINT-12: AgentRuntime mock/local con PreCodeDocumentationAgent y DocumentationAuditAgent. Deben operar en dry-run, sin API keys, usando validators y Policy Engine. Deben generar sugerencias/reporte, no sobrescribir documentos.
```

---

# FUNC-SPRINT-13 — Evaluation Harness para validadores y agentes

## Objetivo

Crear evaluación automática mínima para comprobar calidad de validadores y agentes documentales.

## Tareas

| ID | Tarea | Entregable | PASS |
|---|---|---|---|
| FUNC-13-001 | Crear `evals/fixtures` | datasets sintéticos | Docs válidos/defectuosos. |
| FUNC-13-002 | Crear `EvalRunner` | módulo | Corre casos y genera métricas. |
| FUNC-13-003 | Métricas iniciales | reporte | pass_rate, false_negative, false_positive. |
| FUNC-13-004 | Evaluar `DocumentationAuditAgent` | eval | Detecta brechas esperadas. |
| FUNC-13-005 | Tests de eval harness | pytest | Eval reproducible. |

## Prompt operativo

```text
Implementa FUNC-SPRINT-13: Evaluation Harness offline para validadores y agentes documentales. Crea fixtures sintéticos, métricas, EvalRunner, reporte JSON/Markdown y tests. Sin LLM externo.
```

---

# FUNC-SPRINT-14 — Git read-only y repo inventory MVP+

## Objetivo

Integrar Git en modo lectura para conocer estado de repos reales sin modificar ramas, commits ni archivos.

## Tareas

| ID | Tarea | Entregable | PASS |
|---|---|---|---|
| FUNC-14-001 | Crear `GitAdapter` read-only | módulo | `status`, `branch`, `diff --stat`. |
| FUNC-14-002 | Crear comando `git-status` | CLI | Reporte JSON/Markdown. |
| FUNC-14-003 | Crear `repo-inventory` | CLI | Lista archivos por tipo/tamaño/riesgo. |
| FUNC-14-004 | Detectar archivos sensibles sintéticos | reporte | Redacción de secretos. |
| FUNC-14-005 | Tests con repo temporal | pytest | No modifica repo. |

## BLOCK

- No `git add`, `commit`, `checkout`, `reset`, `merge`, `push`.
- No lectura fuera del workspace.

## Prompt operativo

```text
Implementa FUNC-SPRINT-14: GitAdapter read-only y repo-inventory. Debe usar comandos seguros, no modificar el repo, producir reportes y trazas, detectar patrones sensibles sintéticos y tener tests con repos temporales.
```

---

# FUNC-SPRINT-15 — Patch review y code review en dry-run

## Objetivo

Permitir análisis de diffs/patches sin aplicarlos ni escribir sobre el repo.

## Tareas

| ID | Tarea | Entregable | PASS |
|---|---|---|---|
| FUNC-15-001 | Crear `PatchReviewEngine` | módulo | Lee patch/diff y detecta riesgos. |
| FUNC-15-002 | Crear comando `patch-review` | CLI | Reporte de hallazgos. |
| FUNC-15-003 | Crear `CodeReviewEngine` básico | módulo | Reglas estáticas iniciales. |
| FUNC-15-004 | Integrar Security/Policy findings | reportes | Riesgos por secreto/path/config. |
| FUNC-15-005 | Tests con patches sintéticos | pytest | No aplica patches. |

## Prompt operativo

```text
Implementa FUNC-SPRINT-15: patch-review y code-review en dry-run. Deben leer diffs/patches, producir hallazgos, no aplicar cambios, no escribir fuera de outputs y respetar Policy Engine. Tests con patches sintéticos.
```

---

# FUNC-SPRINT-16 — Safe Refactor Planner

## Objetivo

Proponer planes de refactor seguros, reversibles y testeables sin modificar código automáticamente.

## Tareas

| ID | Tarea | Entregable | PASS |
|---|---|---|---|
| FUNC-16-001 | Crear `RefactorPlanner` | módulo | Produce plan, no cambios. |
| FUNC-16-002 | Crear comando `refactor-plan` | CLI | Plan Markdown/JSON. |
| FUNC-16-003 | Integrar tests requeridos | criterios | Plan exige pruebas antes/después. |
| FUNC-16-004 | Integrar human approval | policy | Requiere aprobación para ejecutar futuro. |
| FUNC-16-005 | Tests | pytest | Plan reproducible. |

## Prompt operativo

```text
Implementa FUNC-SPRINT-16: Safe Refactor Planner en modo plan-only. Debe analizar archivos permitidos, proponer pasos, riesgos, pruebas necesarias y rollback. No modifica archivos. Integra Policy Engine y reportes.
```

---

# FUNC-SPRINT-17 — ModelAdapter híbrido, proveedores y CostGuard

## Objetivo

Preparar la capa multi-modelo sin obligar API keys ni costos externos.

## Rutas

| Ruta | Proveedor | Requiere API key | Costo |
|---|---|---:|---:|
| Mock | reglas/local | No | No |
| Local | Ollama/LM Studio futuro | No necesariamente | No externo |
| API | OpenAI/Gemini/Mistral/HF futuro | Sí | Controlado |

## Tareas

| ID | Tarea | Entregable | PASS |
|---|---|---|---|
| FUNC-17-001 | Crear `ModelAdapter` interface | módulo | `generate`, `classify`, `embed` futuro. |
| FUNC-17-002 | Implementar `MockModelAdapter` | módulo | Determinístico. |
| FUNC-17-003 | Crear config de proveedores | `.devpilot/providers.yaml.example` | Sin secretos reales. |
| FUNC-17-004 | Integrar CostGuard | policy | Bloquea API sin presupuesto. |
| FUNC-17-005 | Tests sin API | pytest | No requiere red. |

## Prompt operativo

```text
Implementa FUNC-SPRINT-17: ModelAdapter híbrido con MockModelAdapter inicial, config de proveedores sin secretos, CostGuard obligatorio y tests offline. No llames APIs externas ni requieras keys reales.
```

---

# FUNC-SPRINT-18 — Preparación de Desktop/Web sin implementar UI completa

## Objetivo

Definir contratos de API interna y servicios de aplicación para que CLI, escritorio y web consuman el mismo core.

## Tareas

| ID | Tarea | Entregable | PASS |
|---|---|---|---|
| FUNC-18-001 | Crear `ApplicationService` para validators | módulo | CLI usa service, no lógica directa. |
| FUNC-18-002 | Crear DTOs serializables | modelos | Útiles para UI futura. |
| FUNC-18-003 | Documentar API interna | docs | Contratos para desktop/web. |
| FUNC-18-004 | Tests de services | pytest | Core independiente de CLI. |

## Prompt operativo

```text
Implementa FUNC-SPRINT-18: separación de Application Services y DTOs para que CLI, escritorio y web consuman el mismo DevPilot Core. No implementes UI aún; solo contratos internos testeables.
```

---

# 8. Secuencia obligatoria de dependencias

```text
FUNC-SPRINT-00
  ↓
FUNC-SPRINT-01
  ↓
FUNC-SPRINT-02 + FUNC-SPRINT-03
  ↓
FUNC-SPRINT-04
  ↓
FUNC-SPRINT-05
  ↓
FUNC-SPRINT-06 + FUNC-SPRINT-07
  ↓
FUNC-SPRINT-08
  ↓
FUNC-SPRINT-09
  ↓
FUNC-SPRINT-10
  ↓
FUNC-SPRINT-11
  ↓
FUNC-SPRINT-12
  ↓
FUNC-SPRINT-13
  ↓
FUNC-SPRINT-14
  ↓
FUNC-SPRINT-15
  ↓
FUNC-SPRINT-16
  ↓
FUNC-SPRINT-17
  ↓
FUNC-SPRINT-18
```

## 9. Criterios para no avanzar

No avanzar al siguiente nivel si:

- `pytest -q` no pasa;
- el repo no está limpio;
- un gate documental crítico falla;
- un comando con side effects no tiene dry-run;
- un agente puede escribir sin aprobación;
- una API externa puede llamarse sin CostGuard y SecretGuard;
- se detecta secreto sin redacción;
- un patch puede aplicarse sin revisión humana;
- una decisión arquitectónica relevante no tiene ADR.

## 10. Primer sprint recomendado inmediato

El sprint inmediato debe ser:

```text
FUNC-SPRINT-00 — Higiene del repo y sincronización de baseline
```

Si el repo ya está limpio y reproducible, continuar con:

```text
FUNC-SPRINT-01 — Arquitectura interna del CLI y modelo común de resultados
```

## 11. Prompt maestro para iniciar implementación funcional

```text
Estamos iniciando la fase funcional de DevPilot Local después de cerrar la baseline pre-code. Usa como fuente de verdad el repo completo actualizado, especialmente docs/functional_backlog_after_precode.md, MIPSoftware y MIASI en docs/standards, y los documentos aprobados 00_product a 06_miasi.

Tarea: ejecutar el sprint indicado del backlog funcional. Mantén enfoque local-first híbrido, sin API keys obligatorias, sin servicios externos, sin acciones destructivas, dry-run por defecto, pruebas herméticas con pytest, reportes JSON/Markdown y trazas JSONL cuando aplique.

Antes de codificar: inspecciona repo, identifica estado actual, valida dependencias, confirma archivos a modificar. Después de codificar: ejecuta pytest, documenta comandos, genera ZIP completo y patch, explica cambios, pruebas y próximos pasos.
```
