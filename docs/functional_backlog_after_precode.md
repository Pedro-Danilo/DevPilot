---
title: "DevPilot Local — Backlog ejecutable posterior a pre-code"
doc_id: "DEVPL-FUNC-BACKLOG-001"
status: "approved"
version: "4.9.0"
owner: "Ordóñez"
standard: "MIPSoftware"
extension: "MIASI"
phase: "POST-PRECODE"
updated: "2026-06-17"
approval: "approved_by_owner_direction"
source_baseline: "precode_baseline_approved"
change_policy: "controlled_changes_allowed_via_docs_as_code"
approved_on: "2026-06-06"
approval_scope: "functional_backlog_after_precode"
baseline_execution: "FUNC-SPRINT-00"
next_sprint: "FUNC-SPRINT-79"
---

# DevPilot Local — Backlog ejecutable posterior a pre-code

## Estado de aprobación funcional

Este backlog queda promovido a `approved` el 2026-06-06 como guía ejecutable para iniciar la implementación funcional de DevPilot Local después del cierre de la fase pre-code.

La aprobación no congela el documento: cualquier ajuste futuro debe seguir la política docs-as-code definida en MIPSoftware, dejar trazabilidad, actualizar criterios de aceptación cuando aplique y preservar la relación entre producto, requerimientos, arquitectura, seguridad, calidad, operación y MIASI.

La ejecución de `FUNC-SPRINT-00` confirma que el repositorio queda limpio, reproducible y listo para iniciar `FUNC-SPRINT-01 — Arquitectura interna del CLI y modelo común de resultados`.


## Transición posterior a FUNC-SPRINT-78

`FUNC-SPRINT-78 — Changelog generator y política de cambios` implementa `python -m devpilot_core release changelog --version 0.1.0 --json`, el changelog controlado `docs/release/CHANGELOG.md` y la política `docs/05_operations/change_policy.md`. La capacidad genera cambios desde manifests locales, mantiene categorías legibles, no inventa cambios y no sobrescribe fuentes desde CLI. La siguiente unidad funcional autorizada es `FUNC-SPRINT-79 — Packaging Python y ZIP limpio reproducible`.


## Transición posterior a FUNC-SPRINT-77

`FUNC-SPRINT-77 — Release metadata y Release Manifest` implementa el primer manifest local de release: `python -m devpilot_core release manifest --version 0.1.0 --json`. El comando formaliza metadata de versión, Git, componentes, evidencias requeridas y artefactos esperados sin empaquetar, publicar, firmar ni desplegar. La siguiente unidad funcional autorizada es `FUNC-SPRINT-78 — Changelog generator y política de cambios`.


## Transición posterior a FUNC-SPRINT-76

`FUNC-SPRINT-76 — CI local y workflow scaffolding` implementa el perfil `quality-gate run --profile ci`, el workflow opcional `.github/workflows/devpilot-ci.yml` y la documentación operativa de CI local sin secretos, publicación ni despliegue. La siguiente unidad funcional autorizada fue `FUNC-SPRINT-77 — Release metadata y Release Manifest`.


## Transición posterior a FUNC-SPRINT-75

`FUNC-SPRINT-75 — Quality Gate local unificado` implementa el primer gate operativo de Fase G: `quality-gate run`. El gate orquesta readiness, standards, MIASI, fixture de evaluación y ApplicationService contract en perfil `fast`, y agrega validation gateway + Visual Product Smoke Gate en perfil `full`. `pytest` queda disponible como subgate explícito con `--include-pytest`, pero la verificación general del sprint sigue recomendando `python -m pytest -q` como comando independiente para descartar regresión.

La siguiente unidad funcional autorizada es `FUNC-SPRINT-76 — CI local y workflow scaffolding`, donde deberá alinearse un perfil CI seguro con el Quality Gate sin publicar, desplegar ni usar secrets.

## Transición posterior a FUNC-SPRINT-74

`FUNC-SPRINT-74 — ADR de release, versionado y productización` inicia Fase G y formaliza la estrategia local-first de release: versionado SemVer interno, package limpio, manifest, changelog, SBOM, checksums, smoke tests, instalación/upgrade y ReleaseAgent dry-run como ruta de productización. El sprint no implementa comandos de release ni publicación externa; esa automatización empieza en `FUNC-SPRINT-75 — Quality Gate local unificado`.


## Transición posterior a FUNC-SPRINT-73

`FUNC-SPRINT-73 — Cierre Fase F web-first y decisión de evolución` cierra Fase F como producto visual MVP web-first. La Web UI local queda como interfaz visual canónica, la Web UI real queda planificada como evolución posterior y Desktop permanece diferido salvo ADR futura. La siguiente unidad de trabajo es `FUNC-SPRINT-74 — ADR de release, versionado y productización`, correspondiente a Fase G.

## Transición posterior a FUNC-SPRINT-72

`FUNC-SPRINT-72 — Settings UI: workspace, providers y políticas locales` queda implementado como Settings UI inicial segura. Workspace, providers y policy se consumen por API local; el editor de providers opera en modo plan-only y no escribe `.devpilot/providers.yaml`. La siguiente unidad de trabajo es `FUNC-SPRINT-73 — Cierre Fase F web-first y decisión de evolución`.

## Transición posterior a FUNC-SPRINT-70

`FUNC-SPRINT-70 — Report Viewer y Trace Viewer` queda implementado como viewer visual inicial de reportes, findings, trazas y métricas. La UI continúa siendo API-only y no lee `outputs/` ni `.devpilot/` directamente. La siguiente unidad de trabajo es `FUNC-SPRINT-71 — Approval Center y acciones dry-run desde UI`.

## Transición posterior a FUNC-SPRINT-69

`FUNC-SPRINT-69 — Web UI MVP: dashboard workspace/readiness/MIASI` queda implementado como primera interfaz visual local de DevPilot. La UI vive en `ui/web`, consume exclusivamente `/api/v1`, envía token local por header y mantiene alcance read-only/API-only.

La siguiente unidad de trabajo es `FUNC-SPRINT-70 — Report Viewer y Trace Viewer`. Ese sprint debe agregar vistas visuales de reportes/trazas/métricas sin permitir que el frontend lea `outputs/` ni filesystem directamente; todo acceso debe pasar por API local segura.


## Transición posterior a FUNC-SPRINT-68

`FUNC-SPRINT-68 — Seguridad API local: token, CORS restringido y policy binding` queda implementado como endurecimiento mínimo de la API local. La API exige token en endpoints protegidos, mantiene CORS restringido sin wildcard, aplica headers de seguridad y vincula rutas protegidas con `PolicyEngine`.

La siguiente unidad de trabajo es `FUNC-SPRINT-69 — Web UI MVP: dashboard workspace/readiness/MIASI`. La UI debe consumir `/api/v1`, enviar token local por header, no importar Python/core y mantener operaciones read-only/dry-run.


## Transición posterior a FUNC-SPRINT-67

`FUNC-SPRINT-67 — API local MVP read-only/dry-run` queda implementado como primer adapter HTTP local de DevPilot. La API usa FastAPI, escucha por defecto en `127.0.0.1:8787`, expone rutas `/api/v1` read-only/dry-run/plan-only y delega en `ApplicationService v2`; no contiene lógica de negocio duplicada ni endpoints críticos de ejecución.

La siguiente unidad de trabajo es `FUNC-SPRINT-68 — Seguridad API local: token, CORS restringido y policy binding`. Antes de que la Web UI consuma la API de forma sostenida, Sprint 68 debe agregar token local, CORS allowlist, headers y vinculación de operaciones sensibles con `PolicyEngine`/Approval Workflow.


## Transición posterior a FUNC-SPRINT-66

`FUNC-SPRINT-66 — Contratos API y OpenAPI preliminar` queda implementado como contrato estático `/api/v1` antes de crear un servidor local. La siguiente unidad de trabajo es `FUNC-SPRINT-67 — API local MVP read-only/dry-run`, que debe implementar el servidor local usando los contratos `docs/07_interfaces/api_contract_v1.md`, `docs/07_interfaces/openapi_v1.json` y `docs/07_interfaces/api_service_mapping.md`.

Regla vigente: ningún endpoint HTTP futuro puede importar módulos internos del core directamente; debe construir `ApplicationRequest`, llamar `ApplicationService`/servicios de dominio y devolver `ApplicationResponse`. Token, CORS y policy binding siguen pendientes para Sprint 68.


## Transición posterior a FUNC-SPRINT-65

`FUNC-SPRINT-65 — ApplicationService v2 por dominios` queda implementado como primera versión de fachada de aplicación por dominios. La siguiente unidad de trabajo es `FUNC-SPRINT-66 — Contratos API y OpenAPI preliminar`, donde las operaciones expuestas por `ApplicationService.application_contract()` deben convertirse en contratos API versionados antes de crear un servidor local real.

Regla vigente: ninguna Web UI local debe importar validadores, PolicyEngine, MIASI, repo analyzers, ReviewEngine, RefactorPlanner, ModelAdapterRouter, LocalStore o AgentOps directamente; toda integración visual debe pasar por ApplicationService/API adapter.


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
| L2 | Workspace local | Proyecto gestionado por `.devpilot/` | Implementado inicial |
| L3 | Evidencia y observabilidad | Reportes, JSONL, auditoría local | Implementado inicial |
| L4 | Seguridad operativa | Policy Engine, SecretGuard, CostGuard | Implementado inicial |
| L4.5 | Estado operativo local | SQLite para runs, gates, findings, eventos, aprobaciones y costos | Implementado inicial |
| L5 | MIASI ejecutable | Agent/Tool/Policy registries verificables | Implementado inicial |
| L6 | Agentes documentales | Agentes mock/local en dry-run | Implementado inicial |
| L7 | Repositorios | Git read-only, inventario, análisis | Implementado inicial |
| L8 | Patches y código | Patch review, code review, refactor plan | Implementado inicial |
| L9 | Modelos híbridos | ModelAdapter local/API opcional con costos | Implementado inicial con mock seguro |
| L10 | Interfaces | Desktop/web sobre DevPilot Core | Implementado inicial: ApplicationService y DTOs; UI pendiente |

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
| R2 | FUNC-SPRINT-06 a 10 | Workspace, políticas, persistencia local y estado operativo |
| R3 | FUNC-SPRINT-11 a 13 | MIASI ejecutable, agentes documentales, evaluación y observabilidad agentic |
| R4 | FUNC-SPRINT-13 a 15 | Git read-only, repo inventory, patch/code review dry-run |
| R5 | FUNC-SPRINT-16 a 18 | ModelAdapter híbrido, CostGuard, preparación desktop/web |

---

## FUNC-SPRINT-00 — Higiene del repo y sincronización de baseline

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

## FUNC-SPRINT-01 — Arquitectura interna del CLI y modelo común de resultados

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

## FUNC-SPRINT-02 — Validador de frontmatter y metadatos documentales

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

## FUNC-SPRINT-03 — Validador de artefactos MIPSoftware/MIASI

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

## FUNC-SPRINT-04 — Standards Registry y carga local de reglas

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

## FUNC-SPRINT-05 — Checklist pre-code y readiness estricto

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

## FUNC-SPRINT-06 — Report Engine y contrato de evidencias

## Estado de implementación FUNC-SPRINT-06

`FUNC-SPRINT-06` queda implementado como motor central de evidencias para gates documentales. El sprint crea `src/devpilot_core/reports/`, define el contrato `EvidenceReport`, centraliza la escritura JSON/Markdown mediante `ReportEngine`, conserva compatibilidad con los reportes históricos de `readiness-check` e incorpora `--write-report` en `validate-frontmatter`, `validate-artifact` y `checklist-pre-code`.

La implementación es una primera versión local-first y determinística. No agrega dependencias externas, no requiere API keys, no llama servicios externos, no cambia arquitectura ni seguridad aprobada, y no requiere nueva ADR. Su evolución natural se conecta con `FUNC-SPRINT-07` para Event Log JSONL, `FUNC-SPRINT-09` para SecretGuard/Policy Engine y `FUNC-SPRINT-10` para persistencia SQLite.

## Objetivo

Centralizar generación de reportes reproducibles en JSON y Markdown para todos los comandos/gates documentales de DevPilot.

## Historias

| ID | Historia | Criterio de aceptación | Estado |
|---|---|---|---|
| US-FUNC-06-001 | Como usuario, quiero reportes legibles y máquinas-legibles. | Cada gate puede generar `.json` y `.md`. | Implementado |
| US-FUNC-06-002 | Como auditor, quiero evidencia reproducible. | Reportes incluyen timestamp, comando, estado, findings y rutas. | Implementado |

## Tareas

| ID | Tarea | Entregable | PASS | Estado |
|---|---|---|---|---|
| FUNC-06-001 | Crear `ReportEngine` | `src/devpilot_core/reports/report_engine.py` | Escribe JSON/Markdown bajo `outputs/reports`. | Implementado |
| FUNC-06-002 | Definir contrato de reporte | `src/devpilot_core/reports/models.py` | `report_id`, `status`, `findings`, `summary`, `generated_at`. | Implementado |
| FUNC-06-003 | Integrar con readiness/validators | CLI | `--write-report` en validadores y checklist; readiness delega a ReportEngine. | Implementado |
| FUNC-06-004 | Snapshot tests | `tests/test_report_engine.py` | Markdown estable y JSON parseable. | Implementado |
| FUNC-06-005 | Documentar en runbook | README + runbook | Uso reproducible y riesgos documentados. | Implementado |

## Archivos creados

```text
src/devpilot_core/reports/__init__.py
src/devpilot_core/reports/models.py
src/devpilot_core/reports/report_engine.py
tests/test_report_engine.py
docs/audits/func_sprint_06_report_engine_audit.md
docs/functional_sprint_06_manifest.json
```

## Archivos modificados

```text
src/devpilot_core/cli.py
src/devpilot_core/validators/readiness.py
README.md
docs/05_operations/runbook.md
docs/functional_backlog_after_precode.md
```

## Contrato de evidencia

```text
report_id      identificador estable del reporte
command        comando evaluado
status         PASS | FAIL | BLOCK | ERROR
ok             booleano del resultado
exit_code      código de salida DevPilot
message        mensaje humano del resultado
generated_at   timestamp UTC ISO-8601
summary        resumen compacto
findings       hallazgos normalizados
data           payload original del CommandResult
subject        ruta o sujeto evaluado, si aplica
metadata       metadatos operativos del sprint/contrato
```

## Comandos objetivo

```powershell
python -m devpilot_core readiness-check --strict --json
python -m devpilot_core validate-frontmatter docs/00_product/product_vision.md --strict --json --write-report
python -m devpilot_core validate-artifact docs/01_requirements/requirements_specification.md --strict --json --write-report
python -m devpilot_core checklist-pre-code --json --write-report
python -m pytest -q
```

## Resultado esperado actual

```text
readiness-check --strict --json -> PASS + outputs/reports/readiness_check.json + .md
validate-frontmatter ... --write-report -> PASS + evidence report
validate-artifact ... --write-report -> PASS + evidence report
checklist-pre-code --write-report -> PASS + evidence report
pytest -q -> 36 passed
```

## BLOCK

- No cerrar si `ReportEngine` puede escribir fuera del project root.
- No cerrar si los reportes JSON no son parseables.
- No cerrar si Markdown no incluye command, status, exit code, timestamp y findings.
- No cerrar si `readiness-check` pierde compatibilidad con `outputs/reports/readiness_check.*`.
- No cerrar si `pytest -q` falla.

## Riesgos residuales

- No hay firma criptográfica ni hash de integridad de reportes.
- No hay EventLog JSONL todavía; se abordará en `FUNC-SPRINT-07`.
- No hay política de retención/rotación de evidencias.
- No hay redacción avanzada de secretos; se abordará con SecretGuard/Policy Engine.
- La evidencia sigue siendo local y regenerable; para operación industrial se requerirá persistencia, retención y trazabilidad más robusta.

## Prompt operativo

```text
Implementa FUNC-SPRINT-06: Report Engine central para JSON/Markdown. Integra validate-frontmatter, validate-artifact, checklist-pre-code y readiness-check. Agrega snapshot tests y documentación de uso.
```

---

## FUNC-SPRINT-07 — Event Log JSONL y observabilidad local

## Estado de implementación FUNC-SPRINT-07

`FUNC-SPRINT-07` queda implementado como primera versión local-first de observabilidad JSONL. El sprint crea `src/devpilot_core/observability/`, define el contrato `EventRecord`, implementa `EventLogger`, emite eventos `command.started`, `gate.evaluated`, `command.completed` y `command.error`, y escribe trazas append-only en `outputs/traces/events.jsonl`.

La implementación no agrega dependencias externas, no requiere API keys, no realiza llamadas de red, no modifica persistencia estructural ni altera decisiones arquitectónicas aprobadas. Es una capacidad prevista en el backlog y complementa a `ReportEngine`: los reportes registran evidencia puntual y el EventLog registra la línea temporal local de ejecución.

## Objetivo

Emitir trazas JSONL mínimas para comandos, validaciones, findings, gates y errores.

## Historias

| ID | Historia | Criterio de aceptación | Estado |
|---|---|---|---|
| US-FUNC-07-001 | Como auditor, quiero saber qué ejecutó DevPilot. | Cada comando emitido por CLI produce eventos JSONL. | Implementado |
| US-FUNC-07-002 | Como desarrollador, quiero trazas sin secretos. | Eventos redactan patrones sintéticos de secretos y claves sensibles. | Implementado inicial |

## Tareas

| ID | Tarea | Entregable | PASS | Estado |
|---|---|---|---|---|
| FUNC-07-001 | Crear `EventLogger` | `src/devpilot_core/observability/events.py` | Escribe `outputs/traces/events.jsonl`. | Implementado |
| FUNC-07-002 | Definir eventos mínimos | `EventRecord` | `command.started`, `command.completed`, `gate.evaluated`, `command.error`. | Implementado |
| FUNC-07-003 | Redacción básica | helpers de redacción | Redacta patrones de secretos sintéticos y claves sensibles. | Implementado inicial |
| FUNC-07-004 | Integrar CLI | `src/devpilot_core/cli.py` | Comandos principales emiten trazas sin alterar stdout. | Implementado |
| FUNC-07-005 | Tests JSONL | `tests/test_event_logger.py` | Cada línea es JSON válido y se prueban eventos/redacción/rutas. | Implementado |

## Archivos creados

```text
src/devpilot_core/observability/__init__.py
src/devpilot_core/observability/events.py
tests/test_event_logger.py
docs/audits/func_sprint_07_event_log_audit.md
docs/functional_sprint_07_manifest.json
```

## Archivos modificados

```text
src/devpilot_core/cli.py
README.md
docs/05_operations/runbook.md
docs/functional_backlog_after_precode.md
```

## Contrato de evento

```text
event_id      identificador único local del evento
event_type    tipo lógico del evento
timestamp     fecha UTC ISO-8601
level         info | warning | error
command       comando DevPilot asociado
status        PASS | FAIL | BLOCK | ERROR, cuando aplica
ok            booleano, cuando aplica
exit_code     código de salida DevPilot, cuando aplica
message       mensaje humano compacto
subject       ruta o sujeto evaluado, cuando aplica
summary       resumen acotado del resultado
findings      hallazgos normalizados, cuando aplica
metadata      metadatos redacted y acotados
```

## Comandos objetivo

```powershell
python -m devpilot_core --version
python -m devpilot_core standards status --json
python -m devpilot_core checklist-pre-code --json
python -m devpilot_core readiness-check --strict --json
python -m devpilot_core validate-frontmatter docs/00_product/product_vision.md --strict --json --write-report
python -m pytest -q
```

## Resultado esperado actual

```text
outputs/traces/events.jsonl -> generado por comandos CLI
events.jsonl -> líneas JSON válidas
command.started + command.completed -> emitidos por comando CLI
gate.evaluated -> emitido por validadores/gates
pytest -q -> 42 passed
```

## BLOCK

- No cerrar si `EventLogger` puede escribir fuera del project root.
- No cerrar si alguna línea JSONL no es parseable.
- No cerrar si se rompe compatibilidad con comandos previos.
- No cerrar si secretos sintéticos obvios (`sk-*`, `ghp_*`, `hf_*`) quedan sin redactar en eventos.
- No cerrar si `pytest -q` falla.

## Riesgos residuales

- La redacción de secretos es básica y basada en patrones; debe evolucionar con SecretGuard/Policy Engine.
- No hay rotación, retención ni compactación de `events.jsonl`.
- No hay correlación formal `event_id` ↔ `report_id` todavía.
- No hay persistencia SQLite ni búsquedas históricas.
- No hay exportación OpenTelemetry ni observabilidad centralizada.

## Prompt operativo

```text
Implementa FUNC-SPRINT-07: EventLogger JSONL local para comandos y gates. Debe generar outputs/traces/events.jsonl, redactar secretos sintéticos, emitir eventos started/completed/finding/error y tener tests.
```

---

## FUNC-SPRINT-08 — Workspace Manager mínimo

## Estado de implementación FUNC-SPRINT-08

`FUNC-SPRINT-08` queda implementado como primera versión local-first de workspace. El sprint introduce `.devpilot/project.yaml` como contrato mínimo de unidad operativa local, crea `WorkspaceManager`, agrega comandos `workspace init` y `workspace status`, integra los resultados con `CommandResult`, `ReportEngine` opcional y `EventLogger`, y conserva `outputs/` como artefacto runtime regenerable.

La implementación no agrega dependencias externas, no requiere API keys, no realiza llamadas de red, no cambia proveedores LLM, no introduce agentes nuevos y no altera la arquitectura aprobada. Es una capacidad prevista en el backlog y prepara la base para `FUNC-SPRINT-09` de Policy Engine/guards y para sprints posteriores de persistencia local.

## Objetivo

Introducir `.devpilot/` como unidad operativa local de proyecto sin romper repos existentes.

## Historias

| ID | Historia | Criterio de aceptación | Estado |
|---|---|---|---|
| US-FUNC-08-001 | Como usuario, quiero inicializar un workspace. | `workspace init` crea `.devpilot/project.yaml` en dry-run o execute explícito. | Implementado |
| US-FUNC-08-002 | Como usuario, quiero conocer estado del workspace. | `workspace status` muestra docs, standards, gates y outputs. | Implementado |

## Tareas

| ID | Tarea | Entregable | PASS | Estado |
|---|---|---|---|---|
| FUNC-08-001 | Crear `WorkspaceManager` | `src/devpilot_core/workspace/manager.py` | Detecta raíz del proyecto. | Implementado |
| FUNC-08-002 | Definir `project.yaml` | `.devpilot/project.yaml` | Nombre, tipo, estándares, MIASI, rutas. | Implementado |
| FUNC-08-003 | Crear comando `workspace init --dry-run` | CLI | No escribe por defecto. | Implementado |
| FUNC-08-004 | Crear `workspace init --execute` | CLI | Crea `.devpilot/` con confirmación explícita. | Implementado |
| FUNC-08-005 | Crear `workspace status` | CLI | Reporte de estado. | Implementado |
| FUNC-08-006 | Tests de rutas/comportamiento | `tests/test_workspace_manager.py` | No sobrescribe, discovery seguro, CLI JSON parseable. | Implementado |

## Archivos creados

```text
.devpilot/project.yaml
src/devpilot_core/workspace/__init__.py
src/devpilot_core/workspace/manager.py
tests/test_workspace_manager.py
docs/audits/func_sprint_08_workspace_manager_audit.md
docs/functional_sprint_08_manifest.json
```

## Archivos modificados

```text
src/devpilot_core/cli.py
README.md
docs/05_operations/runbook.md
docs/functional_backlog_after_precode.md
```

## Contrato mínimo `.devpilot/project.yaml`

```text
schema_version
project.id
project.name
project.type
project.owner
standards: MIPSoftware, MIASI
miasi.required
paths.docs
paths.standards
paths.outputs
paths.reports
paths.traces
runtime.dry_run_default
runtime.created_by
runtime.overwrite_policy
```

## Comandos objetivo

```powershell
python -m devpilot_core workspace init --dry-run
python -m devpilot_core workspace init --execute
python -m devpilot_core workspace status
python -m devpilot_core workspace status --json
python -m devpilot_core workspace status --json --write-report
python -m pytest -q
```

## Resultado esperado actual

```text
workspace init --dry-run -> PASS, no escribe archivos
workspace init --execute -> PASS si .devpilot/project.yaml no existe
workspace init --execute -> BLOCK si .devpilot/project.yaml ya existe
workspace status --json -> PASS si workspace + docs + standards + checklist existen
pytest -q -> 51 passed
```

## BLOCK

- No cerrar si `workspace init` escribe archivos sin `--execute`.
- No cerrar si `workspace init --execute` sobrescribe `.devpilot/project.yaml`.
- No cerrar si `workspace status` no detecta `.devpilot/project.yaml`, `docs/`, `docs/standards/` y `docs/checklists/checklist_pre_code.md`.
- No cerrar si los comandos workspace rompen salida JSON normalizada.
- No cerrar si `pytest -q` falla.

## Riesgos residuales

- Es una primera versión de workspace local; no hay múltiples workspaces ni perfiles por usuario.
- No hay migraciones de versiones de `project.yaml`.
- No hay locking contra inicializaciones concurrentes.
- No hay configuración cifrada ni integración con SecretGuard.
- No hay persistencia SQLite ni registro histórico consultable de workspaces.
- `outputs/` sigue siendo runtime y se regenera al ejecutar comandos; no debe versionarse.

## Prompt operativo

```text
Implementa FUNC-SPRINT-08: Workspace Manager mínimo con .devpilot/project.yaml, comandos workspace init --dry-run/--execute y workspace status. Aplica seguridad de rutas, no sobrescribir por defecto, reportes y tests.
```

---

## FUNC-SPRINT-09 — Policy Engine, PathGuard, SecretGuard y CostGuard determinísticos

## Objetivo

Crear controles determinísticos antes de habilitar agentes, Git avanzado, patches o APIs externas.

## Estado

```text
Implementado inicial — 2026-06-08
```

## Historias

| ID | Historia | Criterio de aceptación | Estado |
|---|---|---|---|
| US-FUNC-09-001 | Como owner, quiero bloquear acciones peligrosas por defecto. | Policy Engine evalúa allow/deny/block. | Implementado |
| US-FUNC-09-002 | Como usuario, quiero evitar exposición de secretos. | SecretGuard redacta patrones sintéticos en reportes y trazas. | Implementado |
| US-FUNC-09-003 | Como owner, quiero controlar costos externos. | CostGuard bloquea uso externo sin presupuesto/política. | Implementado |

## Tareas

| ID | Tarea | Entregable | PASS | Estado |
|---|---|---|---|---|
| FUNC-09-001 | Crear `PolicyDecision` | `src/devpilot_core/policy/decisions.py` | allow/warn/deny/block + reason. | Implementado |
| FUNC-09-002 | Crear `PathGuard` | `src/devpilot_core/policy/path_guard.py` | allowlist/denylist. | Implementado |
| FUNC-09-003 | Crear `SecretGuard` | `src/devpilot_core/policy/secrets.py` | Redacción sintética. | Implementado |
| FUNC-09-004 | Crear `CostGuard` | `src/devpilot_core/policy/cost_guard.py` | Presupuesto local config. | Implementado |
| FUNC-09-005 | Crear comando `policy check` | CLI | Evalúa acción simulada. | Implementado |
| FUNC-09-006 | Tests de bloqueo | `tests/test_policy_engine.py` | Path traversal, secret, external API sin permiso. | Implementado |

## Archivos creados

```text
.devpilot/policy.yaml
src/devpilot_core/policy/__init__.py
src/devpilot_core/policy/decisions.py
src/devpilot_core/policy/path_guard.py
src/devpilot_core/policy/secrets.py
src/devpilot_core/policy/cost_guard.py
src/devpilot_core/policy/engine.py
tests/test_policy_engine.py
docs/audits/func_sprint_09_policy_engine_audit.md
docs/functional_sprint_09_manifest.json
```

## Archivos modificados

```text
.devpilot/project.yaml
src/devpilot_core/cli.py
src/devpilot_core/observability/events.py
src/devpilot_core/reports/report_engine.py
src/devpilot_core/workspace/manager.py
README.md
docs/05_operations/runbook.md
docs/functional_backlog_after_precode.md
```

## Comandos implementados

```powershell
python -m devpilot_core policy check read --path docs/00_product/product_vision.md --json
python -m devpilot_core policy check delete --path docs/00_product/product_vision.md --json
python -m devpilot_core policy check read --path docs/file.md --text "api_key=sk-1234567890abcdef" --json --write-report
python -m devpilot_core policy check external-api --external-api --provider openai --estimated-cost-usd 0.01 --json
python -m pytest -q
```

## Contrato de política local

La política local inicial vive en:

```text
.devpilot/policy.yaml
```

Propiedades clave:

```text
security.dry_run_default = true
security.dangerous_actions_blocked_by_default = true
security.secret_redaction_required = true
cost.external_api_allowed = false
cost.budget_limit_usd = 0.0
cost.budget_used_usd = 0.0
```

## Criterios PASS

```text
Safe read dentro del workspace pasa.
Rutas fuera del workspace bloquean.
Acciones destructivas bloquean por defecto.
Secretos sintéticos bloquean y se redactan en reportes/trazas.
External API sin presupuesto/política bloquea.
ReportEngine y EventLogger usan SecretGuard para redacción.
pytest -q pasa.
```

## Criterios BLOCK

```text
Una acción destructiva pasa por defecto.
Una API externa puede llamarse sin CostGuard.
Un secreto aparece sin redacción en evidencia.
Un path traversal puede salir del workspace.
El comando policy check no genera CommandResult.
```

## Riesgos y límites

- SecretGuard es pattern-based y no reemplaza secret scanners industriales.
- CostGuard no mide consumo real de proveedores.
- PathGuard usa política estática inicial.
- No existe todavía aprobación humana persistente.
- La Policy Matrix MIASI ejecutable queda para sprints posteriores.

## Pruebas

```text
tests/test_policy_engine.py
pytest -q -> 63 passed
```

## Prompt operativo

```text
Implementado FUNC-SPRINT-09: Policy Engine determinístico con PathGuard, SecretGuard y CostGuard. Bloquea acciones inseguras por defecto, opera sin APIs, genera decisiones auditables y tiene tests de seguridad.
```

---

## FUNC-SPRINT-10 — Persistencia local SQLite y estado operativo

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

## Implementación FUNC-SPRINT-10

Estado: `implemented-initial`.

Se implementó persistencia local SQLite v0 sin dependencias externas y sin servicios remotos. La base runtime se genera en `.devpilot/devpilot.db` y se excluye del repo/ZIP mediante `.gitignore`.

## Archivos creados

```text
src/devpilot_core/store/local_store.py
src/devpilot_core/store/__init__.py
tests/test_local_store.py
docs/audits/func_sprint_10_local_store_audit.md
docs/functional_sprint_10_manifest.json
```

## Archivos modificados

```text
.gitignore
.devpilot/project.yaml
src/devpilot_core/cli.py
src/devpilot_core/validators/artifact.py
src/devpilot_core/workspace/manager.py
README.md
docs/05_operations/runbook.md
docs/functional_backlog_after_precode.md
```

## Comandos implementados

```powershell
python -m devpilot_core state init --json
python -m devpilot_core state status --json
python -m devpilot_core state status --json --write-report
python -m devpilot_core history list --json --limit 10
python -m devpilot_core history list --json --limit 10 --write-report
python -m devpilot_core readiness-check --strict --json
python -m pytest -q
```

## Schema SQLite v0

```text
schema_migrations
runs
findings
gates
events
approvals
cost_events
```

## Criterios PASS

```text
state init crea schema idempotente.
state status reporta tablas y conteos.
history list consulta runs recientes.
Los gates/validadores integrados persisten CommandResult de forma best-effort.
La base se mantiene dentro del workspace.
pytest -q pasa.
```

## Criterios BLOCK

```text
DB fuera del workspace.
Migración no idempotente.
Schema incompleto.
Pérdida de historial por init.
Persistencia rompe comandos previos.
DB runtime incluida en ZIP/repo.
```

## Riesgos y límites

```text
No hay cifrado.
No hay retención ni backup/restore formal.
No hay locking multi-proceso explícito.
Approvals y cost_events son tablas estructurales iniciales.
EventLog JSONL aún no se replica automáticamente línea por línea a SQLite.
```

## Pruebas

```text
tests/test_local_store.py
pytest -q -> 71 passed
```

## Prompt operativo

```text
Implementado FUNC-SPRINT-10: persistencia local SQLite v0 para runs, findings, gates, events, approvals y cost_events. La base se genera en .devpilot/devpilot.db, no se versiona, es idempotente, local-first y sin servicios externos.
```

---

## FUNC-SPRINT-11 — MIASI ejecutable: Agent Registry, Tool Registry y Policy Matrix

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

## Implementación FUNC-SPRINT-11

Estado: `implemented-initial`.

Se implementó MIASI ejecutable mediante contratos JSON versionables bajo `.devpilot/miasi/` y un validador determinístico local-first. La implementación no ejecuta agentes ni herramientas; valida declaraciones, cobertura de tools, cobertura de Policy Matrix, autonomía, approvals, observabilidad y drift básico contra los documentos MIASI aprobados.

## Archivos creados

```text
.devpilot/miasi/agent_registry.json
.devpilot/miasi/tool_registry.json
.devpilot/miasi/policy_matrix.json
src/devpilot_core/miasi/registry.py
src/devpilot_core/miasi/__init__.py
tests/test_miasi_registry.py
docs/audits/func_sprint_11_miasi_executable_audit.md
docs/functional_sprint_11_manifest.json
```

## Archivos modificados

```text
.devpilot/project.yaml
src/devpilot_core/cli.py
src/devpilot_core/workspace/manager.py
docs/02_architecture/adrs/ADR-0008-agent-runtime-industrial-bajo-miasi.md
README.md
docs/05_operations/runbook.md
docs/functional_backlog_after_precode.md
```

## Comandos implementados

```powershell
python -m devpilot_core miasi validate --json
python -m devpilot_core miasi validate --json --write-report
python -m devpilot_core miasi validate-registry --json
python -m devpilot_core miasi validate-tools --json
python -m devpilot_core miasi validate-policy-matrix --json
python -m pytest -q
```

## Criterios PASS

```text
Los contratos ejecutables MIASI existen y son JSON válido.
Agent Registry valida IDs, fase, estado, autonomía, tools permitidas, eval y observabilidad.
Tool Registry valida side_effect, risk_level, aprobación y policy coverage.
Policy Matrix valida dominio, gate, default_effect, approval y observability.
Los agentes referencian tools existentes.
Las tools y agentes referencian reglas existentes.
Los agentes MVP no superan A2.
Los agentes A4+ requieren aprobación.
pytest -q pasa.
```

## Criterios BLOCK

```text
Falta un contrato ejecutable.
Un agente referencia una tool inexistente.
Una tool o agente carece de policy coverage.
Una regla deny/block no es observable.
Un agente A4+ no requiere aprobación.
Hay drift donde el documento MIASI declara una entidad ausente en el contrato ejecutable.
```

## Riesgos y límites

```text
No hay Agent Runtime todavía.
No se ejecutan tools.
No hay aprobación humana persistente.
No hay eval harness.
El parser Markdown es mínimo.
Los estados planned/future son contractuales; no equivalen a runtime habilitado.
```

## Pruebas

```text
tests/test_miasi_registry.py
pytest -q -> 79 passed
```

## Prompt operativo

```text
Implementado FUNC-SPRINT-11: MIASI ejecutable con Agent Registry, Tool Registry y Policy Matrix determinísticos. Valida autonomía, tools, side effects, approvals, observabilidad y policy coverage sin ejecutar agentes ni herramientas.
```

---

## FUNC-SPRINT-12 — Agent Runtime mock/local para agentes documentales MVP

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


## Implementación FUNC-SPRINT-12

Estado: `implemented-initial`.

Sprint 12 implementa `AgentRuntime` mock/local y los dos agentes documentales MVP:

- `documentation-audit` (`precode.audit`): usa validators existentes, Policy Engine y checklist pre-code para producir hallazgos y sugerencias sin editar documentos.
- `precode-documentation` (`precode.documentation`): genera borradores revisables desde una idea, con `dry-run` por defecto y escritura opcional solo bajo `outputs/drafts`.

Archivos principales:

```text
src/devpilot_core/agents/models.py
src/devpilot_core/agents/runtime.py
src/devpilot_core/agents/__init__.py
tests/test_agent_runtime.py
docs/audits/func_sprint_12_agent_runtime_audit.md
docs/functional_sprint_12_manifest.json
```

Comandos implementados:

```powershell
python -m devpilot_core agent run documentation-audit --target docs/01_requirements --json
python -m devpilot_core agent run precode-documentation --idea "..." --dry-run --json
python -m devpilot_core agent run precode-documentation --idea "..." --dry-run --json --write-report
```

Criterios PASS alcanzados:

- runtime resuelve agentes desde MIASI;
- solo ejecuta agentes MVP implementados;
- policy check antes de tool calls;
- no requiere API key ni red;
- dry-run por defecto;
- no sobrescribe documentos aprobados;
- pruebas offline en PASS.

Criterios BLOCK implementados:

- agente desconocido;
- agente fuera de fase MVP;
- registros MIASI faltantes/rotos;
- path bloqueado;
- secreto sintético detectado;
- draft existente en modo execute.

Riesgos residuales:

- agentes rule-based;
- sin LLM ni ModelAdapter real;
- sin memoria agentic;
- sin evaluación automática de calidad;
- sin aprobación humana persistente;
- escritura opcional solo en `outputs/drafts`, no en docs aprobados.

Siguiente sprint: `FUNC-SPRINT-13 — Evaluation Harness para validadores y agentes`.

---

## FUNC-SPRINT-13 — Evaluation Harness para validadores y agentes

## Objetivo

Crear evaluación automática mínima para comprobar calidad de validadores y agentes documentales.

## Estado

`implemented-initial` — Sprint 13 implementa un Evaluation Harness offline, determinístico y local-first. No usa LLM externo, no requiere API keys y no accede a red.

## Implementación FUNC-SPRINT-13

| ID | Tarea | Entregable | Estado |
|---|---|---|---|
| FUNC-13-001 | Crear `evals/fixtures` | `evals/fixtures/documentation_eval_cases.json` | PASS |
| FUNC-13-002 | Crear `EvalRunner` | `src/devpilot_core/evals/runner.py` | PASS |
| FUNC-13-003 | Métricas iniciales | `pass_rate`, `false_positives`, `false_negatives`, `missing_expected_findings` | PASS |
| FUNC-13-004 | Evaluar `DocumentationAuditAgent` | casos sintéticos limpios/defectuosos | PASS |
| FUNC-13-005 | Tests de eval harness | `tests/test_eval_runner.py` | PASS |

## Comandos

```powershell
python -m devpilot_core eval run --json
python -m devpilot_core eval run --json --write-report
python -m devpilot_core eval run --case-id frontmatter-missing-doc-id --json
python -m pytest -q
```

## Criterios PASS

```text
Suite sintética en PASS.
pass_rate = 1.0.
false_positives = 0.
false_negatives = 0.
missing_expected_findings = 0.
No hay llamadas externas ni dependencias nuevas.
```

## Criterios BLOCK

```text
Falso negativo en fixture defectuoso.
Falso positivo no justificado en fixture limpio.
Hallazgo esperado ausente.
Salida JSON no parseable.
Workdir fuera del project root.
Uso de LLM/API externa.
```

## Riesgos

Primera versión del Evaluation Harness. Los fixtures son sintéticos y pequeños. Pendiente: golden outputs, red teaming, groundedness, evaluación semántica, ponderación por severidad e histórico de tendencias.

Siguiente sprint: `FUNC-SPRINT-14 — Git read-only y repo inventory MVP+`.

---

## FUNC-SPRINT-14 — Git read-only y repo inventory MVP+

## Estado

`implemented-initial` el 2026-06-08.

## Objetivo

Integrar Git en modo lectura para conocer estado de repos reales sin modificar ramas, commits ni archivos.

## Tareas

| ID | Tarea | Entregable | PASS |
|---|---|---|---|
| FUNC-14-001 | Crear `GitAdapter` read-only | `src/devpilot_core/repo/git_adapter.py` | `status`, `branch`, `diff --stat` mediante allowlist read-only. |
| FUNC-14-002 | Crear comando `git-status` | CLI | Reporte JSON/Markdown opcional. |
| FUNC-14-003 | Crear `repo-inventory` | CLI + `src/devpilot_core/repo/inventory.py` | Lista archivos por tipo/tamaño/riesgo. |
| FUNC-14-004 | Detectar archivos sensibles sintéticos | findings | Secret-like content detectado sin valor crudo. |
| FUNC-14-005 | Tests con repo temporal | `tests/test_repo_tools.py` | No modifica repo. |

## Comandos implementados

```powershell
python -m devpilot_core git-status --json
python -m devpilot_core git-status --json --write-report
python -m devpilot_core repo-inventory --json
python -m devpilot_core repo-inventory --json --write-report
python -m pytest -q
```

## Criterios PASS implementados

```text
GitAdapter ejecuta solo comandos Git read-only allowlisted.
git-status no altera `git status --short` antes/después.
repo-inventory no sale del workspace.
repo-inventory excluye outputs/caches.
secret-like content se detecta sin exponer valor crudo.
Tool Registry marca git.status, git.diff y repo.inventory como implemented.
```

## BLOCK

- No `git add`, `commit`, `checkout`, `reset`, `merge`, `rebase`, `tag`, `push`.
- No `shell=True`.
- No lectura fuera del workspace.
- No fuga de secretos crudos.

## Riesgos

Primera versión. No cubre SCA/SAST industrial, licencias, vulnerabilidades, submódulos, LFS, ramas remotas, secret scanning por entropía ni revisión semántica de código.

## Prompt operativo

```text
Implementa FUNC-SPRINT-14: GitAdapter read-only y repo-inventory. Debe usar comandos seguros, no modificar el repo, producir reportes y trazas, detectar patrones sensibles sintéticos y tener tests con repos temporales.
```

Siguiente sprint: `FUNC-SPRINT-15 — Patch review y code review en dry-run`.

---

## FUNC-SPRINT-15 — Patch review y code review en dry-run

Estado: `implemented-initial`.

## Objetivo

Permitir análisis de diffs/patches y revisión estática inicial de código sin aplicarlos ni escribir sobre el repo.

## Implementado

| ID | Tarea | Entregable | PASS |
|---|---|---|---|
| FUNC-15-001 | Crear `PatchReviewEngine` | `src/devpilot_core/review/patch_review.py` | Lee patch/diff y detecta riesgos sin aplicar cambios. |
| FUNC-15-002 | Crear comando `patch-review` | CLI | Reporte de hallazgos JSON/Markdown opcional. |
| FUNC-15-003 | Crear `CodeReviewEngine` básico | `src/devpilot_core/review/code_review.py` | Reglas estáticas iniciales sin modificar archivos. |
| FUNC-15-004 | Integrar Security/Policy findings | PolicyEngine + SecretGuard + reportes | Riesgos por secreto/path/config sin fuga de contenido crudo. |
| FUNC-15-005 | Tests con patches sintéticos | `tests/test_review_engines.py` | No aplica patches y mantiene dry-run. |

## Comandos

```powershell
python -m devpilot_core patch-review --patch-file safe.patch --json
python -m devpilot_core patch-review --patch-text "<unified-diff>" --json
python -m devpilot_core code-review --target src/devpilot_core/validators --json
python -m devpilot_core patch-review --patch-file safe.patch --json --write-report
python -m devpilot_core code-review --target src/devpilot_core/validators --json --write-report
```

## Criterios PASS implementados

```text
PatchReviewEngine nunca aplica patches.
CodeReviewEngine nunca modifica archivos.
PolicyEngine/PathGuard valida rutas.
SecretGuard bloquea o marca secretos sintéticos sin emitir valores crudos.
Reportes opcionales se escriben solo bajo outputs/reports.
pytest -q pasa completo.
```

## BLOCK

- Patch file o target fuera del workspace.
- Ruta denegada como `.env`, `.git`, `.venv`.
- Secreto sintético en patch/código.
- Intento de aplicar patch o ejecutar acción destructiva.
- Fuga de secretos crudos en evidencia.

## Riesgos

Primera versión. No valida si un patch aplica limpiamente, no reemplaza SAST/SCA, no ejecuta linters externos, no revisa dependencias vulnerables, no hace análisis semántico profundo ni habilita aplicación real de patches.

## Prompt operativo

```text
Implementa FUNC-SPRINT-15: patch-review y code-review en dry-run. Deben leer diffs/patches, producir hallazgos, no aplicar cambios, no escribir fuera de outputs y respetar Policy Engine. Tests con patches sintéticos.
```

Siguiente sprint: `FUNC-SPRINT-16 — Safe Refactor Planner`.

---

## FUNC-SPRINT-16 — Safe Refactor Planner

Estado: `implemented-initial`.

## Objetivo

Proponer planes de refactor seguros, reversibles y testeables sin modificar código automáticamente.

## Implementado

| ID | Tarea | Entregable | PASS |
|---|---|---|---|
| FUNC-16-001 | Crear `RefactorPlanner` | `src/devpilot_core/refactor/planner.py` | Produce plan, no cambios. |
| FUNC-16-002 | Crear comando `refactor-plan` | CLI | Plan JSON/Markdown opcional. |
| FUNC-16-003 | Integrar tests requeridos | plan/verificación | Plan exige pytest, code-review, patch-review, MIASI y eval. |
| FUNC-16-004 | Integrar human approval | policy/data | `approval_required_for_execution=true`. |
| FUNC-16-005 | Tests | `tests/test_refactor_planner.py` | Plan reproducible y no destructivo. |

## Comandos

```powershell
python -m devpilot_core refactor-plan --target src/devpilot_core/review --goal "Extract shared helpers" --json
python -m devpilot_core refactor-plan --target src/devpilot_core/review --goal "Extract shared helpers" --json --write-report
```

## Criterios PASS implementados

```text
dry_run=true.
plan_only=true.
files_modified=0.
patch_generated=false.
tests_required=true.
approval_required_for_execution=true.
Reportes opcionales bajo outputs/reports.
pytest -q pasa completo.
```

## BLOCK

- Target fuera del workspace.
- Ruta denegada por PolicyEngine/PathGuard.
- Goal con secreto sintético.
- Target inexistente.
- Error de sintaxis Python en archivos analizados.
- Cualquier intento de modificar archivos o aplicar patches.

## Riesgos

Primera versión. Es heurística y plan-only. No aplica transformaciones AST, no genera patches, no ejecuta tests, no integra linters externos, no valida tipos y no sustituye revisión humana.

## Prompt operativo

```text
Implementa FUNC-SPRINT-16: Safe Refactor Planner en modo plan-only. Debe analizar archivos permitidos, proponer pasos, riesgos, pruebas necesarias y rollback. No modifica archivos. Integra Policy Engine y reportes.
```

---

## FUNC-SPRINT-17 — ModelAdapter híbrido, proveedores y CostGuard

Estado: `implemented-initial`.

## Objetivo

Preparar la capa multi-modelo sin obligar API keys ni costos externos.

## Rutas

| Ruta | Proveedor | Requiere API key | Costo | Estado Sprint 17 |
|---|---|---:|---:|---|
| Mock | reglas/local | No | No | Implementado |
| Local | Ollama/LM Studio futuro | No necesariamente | No externo | Placeholder planificado |
| API | OpenAI/Gemini/Mistral/HF futuro | Sí | Controlado | Deshabilitado/bloqueado |

## Implementado

| ID | Tarea | Entregable | Estado |
|---|---|---|---|
| FUNC-17-001 | Crear `ModelAdapter` interface | `src/devpilot_core/modeling/contracts.py` | PASS |
| FUNC-17-002 | Implementar `MockModelAdapter` | `src/devpilot_core/modeling/mock_adapter.py` | PASS |
| FUNC-17-003 | Crear config de proveedores | `.devpilot/providers.yaml.example` | PASS |
| FUNC-17-004 | Integrar CostGuard | `ModelAdapterRouter` + `PolicyEngine` | PASS |
| FUNC-17-005 | Tests sin API | `tests/test_model_adapter.py` | PASS |

## Comandos

```powershell
python -m devpilot_core model providers --json
python -m devpilot_core model generate --provider mock --prompt "Diseñar agente documental" --json
python -m devpilot_core model classify --provider mock --text "bug detectado" --labels "bug,feature" --json
python -m devpilot_core model embed --provider mock --text "vector estable" --json
python -m devpilot_core model generate --provider openai --prompt "test" --json
```

## Criterios PASS implementados

```text
ProviderRegistry carga metadata sin secretos crudos.
MockModelAdapter genera, clasifica y embebe de forma determinística.
CostGuard/PolicyEngine evalúan cada ruta de proveedor.
API externa queda bloqueada por defecto.
No hay API keys obligatorias.
No hay red ni costo externo.
pytest -q pasa completo.
```

## BLOCK

```text
Proveedor no registrado.
Prompt/texto con secreto sintético.
API externa sin presupuesto/política explícita.
Configuración con API key cruda.
Proveedor local/API ejecutado realmente en Sprint 17.
```

## Riesgos

Primera versión. No implementa clientes reales para Ollama, LM Studio, OpenAI, Gemini, Mistral ni Hugging Face. No mide tokens reales, latencia, calidad semántica, retries, rate limits ni facturación real. La integración real requerirá sprints posteriores, CostGuard reforzado, SecretGuard sobre prompts, evaluación específica y aprobación humana cuando aplique.

## Prompt operativo

```text
Implementa FUNC-SPRINT-17: ModelAdapter híbrido con MockModelAdapter inicial, config de proveedores sin secretos, CostGuard obligatorio y tests offline. No llames APIs externas ni requieras keys reales.
```

Siguiente sprint: `FUNC-SPRINT-18 — Preparación de Desktop/Web sin implementar UI completa`.

---

## FUNC-SPRINT-18 — Preparación de Desktop/Web sin implementar UI completa

## Objetivo

Definir contratos de API interna y servicios de aplicación para que CLI, escritorio y web consuman el mismo core.

## Estado

`implemented-initial` el 2026-06-08.

## Tareas

| ID | Tarea | Entregable | PASS | Estado |
|---|---|---|---|---|
| FUNC-18-001 | Crear `ApplicationService` para validators | `src/devpilot_core/application/services.py` | CLI usa service, no lógica directa. | Implementado inicial |
| FUNC-18-002 | Crear DTOs serializables | `src/devpilot_core/application/dtos.py` | Útiles para UI futura. | Implementado inicial |
| FUNC-18-003 | Documentar API interna | `docs/07_interfaces/internal_application_contract.md` | Contratos para desktop/web. | Implementado inicial |
| FUNC-18-004 | Tests de services | `tests/test_application_services.py` | Core independiente de CLI. | Implementado inicial |

## Comandos

```powershell
python -m devpilot_core app contract --json
python -m devpilot_core app contract --json --write-report
python -m devpilot_core validate-frontmatter docs/00_product/product_vision.md --json
python -m devpilot_core validate-artifact docs/01_requirements/requirements_specification.md --json
```

## Criterios PASS implementados

```text
ApplicationService existe y centraliza validadores principales.
DTOs ApplicationRequest/ApplicationResponse son serializables.
CLI conserva CommandResult, eventos, reportes y persistencia best-effort.
app contract expone capacidades y rutas lógicas.
No hay UI implementada.
No hay dependencias nuevas.
pytest -q pasa completo.
```

## BLOCK

```text
Framework UI o servidor sin ADR.
Duplicación de reglas de validación en una UI.
DTOs con secretos.
Cambio incompatible de CommandResult.
Acciones con side effects sin dry-run.
```

## Riesgos

Contrato preliminar. No incluye autenticación, sesiones, RBAC, schemas JSON formales, HTTP, IPC, WebSocket, empaquetado desktop ni decisión de stack.

## Prompt operativo

```text
Implementa FUNC-SPRINT-18: separación de Application Services y DTOs para que CLI, escritorio y web consuman el mismo DevPilot Core. No implementes UI aún; solo contratos internos testeables.
```

Siguiente sprint: `FUNC-SPRINT-19 — Cierre formal del ciclo 00–18 y release técnico interno`.

---

## 8. Secuencia obligatoria de dependencias

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
  ↓
FUNC-SPRINT-19
  ↓
FUNC-SPRINT-20
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

## 12. Transición posterior al ciclo 00–18

`FUNC-SPRINT-19` pertenece a la Fase A — Baseline industrial mínima y cierra formalmente el ciclo `FUNC-SPRINT-00` a `FUNC-SPRINT-18` mediante:

- `docs/audits/functional_cycle_00_18_closure_report.md`;
- `docs/release/release_manifest_v0.1.0.json`;
- `docs/release/release_notes_v0.1.0.md`;
- `docs/functional_sprint_19_manifest.json`;
- `scripts/verify_release_v0_1_0.py`;
- `tests/test_release_manifest.py`.

A partir de este cierre, la continuidad operativa se gobierna por `docs/devpilot_backlog_fase_A_baseline_industrial_minima.md`. El siguiente sprint es:

```text
FUNC-SPRINT-20 — Reconciliación documental post-18 y roadmap vivo
```



## 13. Transición posterior a la reconciliación documental

`FUNC-SPRINT-20` pertenece a la Fase A y deja reconciliados README, runbook, roadmap histórico y C4 con el estado real del core local-first. Los artefactos principales son:

- `docs/audits/capability_status_matrix_after_sprint_18.md`;
- `docs/audits/roadmap_reconciliation_after_sprint_18.md`;
- `docs/02_architecture/c4_component.md`;
- `docs/functional_sprint_20_manifest.json`;
- `tests/test_sprint_20_documentation_reconciliation.py`.

A partir de este punto, el siguiente sprint operativo es:

```text
FUNC-SPRINT-21 — Schema Registry y catálogo de contratos DevPilot
```


## 14. Transición posterior al Schema Registry

`FUNC-SPRINT-21` pertenece a la Fase A y crea el Schema Registry inicial para contratos internos de DevPilot. Los artefactos principales son:

- `src/devpilot_core/schemas/`;
- `docs/schemas/schema_catalog.json`;
- `docs/schemas/*.schema.json`;
- `docs/audits/func_sprint_21_schema_registry_audit.md`;
- `docs/functional_sprint_21_manifest.json`;
- `tests/test_schema_registry.py`.

El registry lista schemas y valida integridad del catálogo, pero no valida instancias JSON. Esa evolución queda para:

```text
FUNC-SPRINT-22 — Schema Validator y schemas de contratos transversales
```

## 15. Transición posterior al Schema Validator

`FUNC-SPRINT-22` pertenece a la Fase A y habilita `SchemaValidator` para validar instancias JSON locales contra contratos transversales registrados en `docs/schemas/`. Los artefactos principales son:

- `src/devpilot_core/schemas/validator.py`;
- `src/devpilot_core/schemas/errors.py`;
- `docs/02_architecture/adrs/ADR-0010-schema-validation-dependency.md`;
- `docs/audits/func_sprint_22_schema_validator_audit.md`;
- `docs/functional_sprint_22_manifest.json`;
- `tests/test_schema_validator.py`.

La validación es estructural y no reemplaza reglas de negocio, MIASI, readiness, policy ni trazabilidad. La extensión de schemas para MIASI, workspace, providers y manifests queda para:

```text
FUNC-SPRINT-23 — Schemas MIASI, Workspace, Providers y Sprint Manifests
```


## Transición Fase A posterior a FUNC-SPRINT-23

`FUNC-SPRINT-23` agrega schemas y validadores estructurales para MIASI registries, workspace metadata, provider metadata y manifests funcionales. El backlog funcional histórico se mantiene como referencia del ciclo 00–18; la fuente operativa de continuidad es `docs/devpilot_backlog_fase_A_baseline_industrial_minima.md`.

Siguiente sprint entonces abierto: `FUNC-SPRINT-24 — Artifact Profiles data-driven y ValidationGateway inicial`. Tras su implementación, el sprint abierto vigente pasa a `FUNC-SPRINT-25`.


## Transición Fase A posterior a FUNC-SPRINT-24

`FUNC-SPRINT-24` externaliza los perfiles documentales como datos versionados y agrega `ValidationGateway` inicial. El backlog funcional histórico sigue siendo referencia del ciclo 00–18; la continuidad operativa queda en `docs/devpilot_backlog_fase_A_baseline_industrial_minima.md`, con `FUNC-SPRINT-25` como siguiente sprint abierto.

Artefactos de continuidad:

- `docs/validation/artifact_profiles.json`
- `docs/schemas/artifact_profiles.schema.json`
- `src/devpilot_core/validation/`
- `docs/functional_sprint_24_manifest.json`
- `docs/audits/func_sprint_24_validation_gateway_audit.md`

Límite explícito: `ValidationGateway` no reemplaza validaciones semánticas ni trazabilidad. Solo compone validadores existentes bajo `CommandResult`.


## 17. Transición posterior al Traceability Model

`FUNC-SPRINT-25` agrega una primera capa ejecutable de trazabilidad SDLC mediante `src/devpilot_core/traceability/` y el comando `python -m devpilot_core traceability scan --json`.

Estado real:

- implementado `TraceEntity`, `TraceLink`, `TraceGraph` e `InvalidTraceToken`;
- implementado extractor conservador de IDs `FR-*`, `REQ-*`, `US-*`, `AC-*`, `TEST-*`, `ADR-*`;
- implementada detección de duplicados y tokens mal formados;
- implementado reporte opcional con `--write-report`;
- no implementada todavía cobertura ni validación de gaps de trazabilidad.

Siguiente paso: `FUNC-SPRINT-26 — Traceability Engine: validate, coverage y report`.


## 18. Transición posterior al Traceability Engine

`FUNC-SPRINT-26` agrega `TraceabilityEngine` sobre el modelo de Sprint 25. La implementación habilita:

- `python -m devpilot_core traceability validate --json`;
- `python -m devpilot_core traceability coverage --json`;
- `python -m devpilot_core traceability report --json --write-report`;
- cálculo explícito de cobertura Req→AC, Req→Test/Eval y Req→Doc;
- gaps accionables como warnings no bloqueantes;
- reportes JSON/Markdown reproducibles.

Límite explícito: el motor no infiere relaciones semánticas complejas ni corrige documentos. La continuidad de Fase A queda en `docs/devpilot_backlog_fase_A_baseline_industrial_minima.md`, con `FUNC-SPRINT-27 — Architecture/code drift inicial y cierre de Baseline Industrial Mínima` como siguiente sprint abierto.


## Transición posterior a FUNC-SPRINT-27 — Cierre Fase A

`FUNC-SPRINT-27` cierra la Fase A mediante architecture/code drift inicial, checklist de salida, reporte de cierre y smoke final. La continuidad ya no corresponde a nuevos sprints de Fase A sino a una **Fase B pendiente de planificación ejecutable**.

Capacidades habilitadas:

- `traceability architecture-drift`;
- checklist `docs/checklists/checklist_phase_a_exit.md`;
- reporte `docs/audits/phase_a_baseline_industrial_minima_closure_report.md`;
- Fase A marcada como baseline cerrada, no como producto final.

Pendientes recomendados para Fase B:

- approval workflow;
- `tests.run` controlado;
- sandbox y rollback;
- agentes especializados sobre motores existentes;
- observabilidad v2;
- planificación formal de UI/API solo con ADR.


## Transición posterior a FUNC-SPRINT-28

`FUNC-SPRINT-28` inicia la Fase B de seguridad operacional con el modelo de aprobación humana y persistencia operacional. El backlog Fase A queda `approved` y cerrado; el backlog Fase B queda `approved` e iniciado.

Siguiente sprint operativo: `FUNC-SPRINT-29 — CLI de aprobación: request, list, show, approve, deny y revoke`.

Límite explícito: Sprint 28 no conecta aún `approval_id` con `PolicyEngine`, no expone CLI de approvals y no ejecuta acciones críticas.


## Transición posterior a FUNC-SPRINT-29

`FUNC-SPRINT-29` expone el workflow local de aprobaciones humanas mediante CLI. Esta implementación habilita solicitud, listado, consulta, aprobación, denegación y revocación de approvals persistidas localmente.

Estado real:

- implementado `ApprovalService`;
- implementados comandos `approval request/list/show/approve/deny/revoke`;
- reportes opcionales y eventos locales disponibles;
- salida CLI redactada para secretos sintéticos;
- no implementado aún binding con `PolicyEngine`;
- no implementada ejecución controlada de herramientas.

Siguiente sprint operativo: `FUNC-SPRINT-30 — Binding de aprobaciones con PolicyEngine y MIASI`.


## 21. Transición posterior al Approval Policy Binding

`FUNC-SPRINT-30` conecta approvals con `PolicyEngine` y MIASI como binding **implemented-initial**. A partir de este punto, la continuación correcta de Fase B es `FUNC-SPRINT-31 — SafeSubprocessRunner y allowlist de ejecución controlada`, sin habilitar todavía patch apply, refactor execution, deploy ni Git write.


## Transición posterior a FUNC-SPRINT-31 — SafeSubprocessRunner

`FUNC-SPRINT-31` agrega ejecución local controlada como prerequisito de `tests.run`: allowlist, cwd seguro, timeout, subprocess sin shell y redacción de salidas. No expone aún CLI pública de ejecución ni habilita patch apply/refactor execution. El siguiente sprint operativo es `FUNC-SPRINT-32 — tests.run como herramienta MIASI controlada`.


## Transición posterior a FUNC-SPRINT-33 — Security hardening inicial

`FUNC-SPRINT-33` amplía la seguridad local de Fase B con `SecretGuard` endurecido, `PromptInjectionGuard` y `ToolInjectionGuard`. Los payloads textuales de `PolicyEngine`, agentes documentales y model routing reciben checks determinísticos contra secretos, bypass de política e intentos de forzar herramientas.

Estado real:

- implementación `implemented-initial`, sin LLM judge;
- sin APIs externas ni dependencias nuevas;
- findings accionables y metadata sin payload crudo;
- no habilita patch apply, refactor execution, Git write ni deploy.

Siguiente sprint operativo: `FUNC-SPRINT-34 — Security readiness operacional y cierre de Fase B`.


## Transición posterior a FUNC-SPRINT-34 — Cierre Fase B

`FUNC-SPRINT-34` cierra Fase B con security readiness operacional. DevPilot ya cuenta con approval workflow, policy binding, SafeSubprocessRunner, `tests.run`, guards contra secretos/prompt/tool injection, checklist de salida y closure report.

Estado real: Fase B queda cerrada como baseline local-first `implemented-initial`, no como certificación de seguridad industrial completa.

Siguiente línea de trabajo recomendada: Fase C — ingeniería de repositorio y sandbox controlado. Antes de habilitar patch apply, refactor execution, Git write o deploy deben implementarse sandbox real, rollback, trazabilidad operacional v2 y readiness específico de acciones mutantes.

- `tests.run` hereda hardening de entorno para pytest controlado: sin autoload de plugins externos ni user site en subprocess.


## Aprobación de backlog Fase C posterior a FUNC-SPRINT-34

Tras verificar el cierre de Fase B mediante `security readiness`, el backlog `docs/devpilot_backlog_fase_C_ingenieria_repositorio.md` queda elevado a estado `approved`. El siguiente sprint operativo es `FUNC-SPRINT-35 — GitAdapter v2 read-only: ramas, tags, log y diff-report`.

Esta transición mantiene bloqueadas las capacidades destructivas hasta que existan sandbox real, ChangeSet, rollback y gates específicos de calidad de repositorio.


## Transición posterior a FUNC-SPRINT-35 — GitAdapter v2 read-only

`FUNC-SPRINT-35` inicia Fase C con lectura ampliada de Git: ramas, tags, commits recientes y diff-report estructurado. La capacidad es read-only, local-first y preliminar. No habilita patch apply, refactor execution, Git write, deploy ni sandbox real.

Siguiente sprint operativo: `FUNC-SPRINT-36 — DependencyGraph e import graph Python`.


## Transición posterior a FUNC-SPRINT-36 — DependencyGraph e import graph Python

`FUNC-SPRINT-36` agrega DependencyGraph inicial para Python mediante AST. La capacidad es read-only, local-first y preliminar: no ejecuta código analizado, no importa módulos, no usa red, no llama APIs externas y no modifica archivos.

Estado real:

- implementado `DependencyGraphBuilder`;
- implementado comando `repo dependency-graph`;
- salida con nodos, edges, imports externos, fan-in/fan-out y findings de syntax error;
- reportes opcionales JSON/Markdown mediante `--write-report`;
- tool `repo.dependency_graph` declarada en MIASI;
- no habilita patch apply, refactor execution, Git write, deploy ni sandbox real.

Siguiente sprint operativo: `FUNC-SPRINT-37 — RepoAnalyzer v2: estructura, riesgos y salud del repositorio`.


## Transición posterior a FUNC-SPRINT-37 — RepoAnalyzer v2

`FUNC-SPRINT-37` agrega `RepoAnalyzer` como primera consolidación de salud del repositorio. La capacidad integra inventario, DependencyGraph y GitAdapter en modo read-only y produce un `health_score` heurístico, secciones `source/tests/docs/config`, hotspots y riesgos básicos.

Estado real:

- implementado comando `repo analyze`;
- salida `CommandResult` con `--json`;
- reportes opcionales JSON/Markdown mediante `--write-report`;
- tool `repo.analyze` declarada en MIASI;
- análisis parcial si Git no está disponible;
- no emite secretos crudos;
- no ejecuta código analizado;
- no habilita patch apply, refactor execution, Git write, deploy ni sandbox real.

Siguiente sprint operativo: `FUNC-SPRINT-38 — Architecture/code drift inicial`.


## Transición posterior a FUNC-SPRINT-38 — Architecture/code drift inicial

`FUNC-SPRINT-38` agrega `ArchitectureDriftDetector` bajo el comando `repo architecture-drift`. La capacidad compara documentación arquitectónica contra módulos reales del código usando extracción Markdown/Mermaid, DependencyGraph y señales de RepoAnalyzer.

Estado real:

- implementado comando `repo architecture-drift`;
- salida `CommandResult` con `--json`;
- reportes opcionales JSON/Markdown mediante `--write-report`;
- tool `repo.architecture_drift` declarada en MIASI;
- matriz de estado `documented ↔ code` con `confidence` y `drift_type`;
- findings separados `doc_missing`, `code_missing` y `name_mismatch`;
- no ejecuta código analizado;
- no modifica documentación;
- no usa LLM, red ni APIs externas;
- no habilita patch apply, refactor execution, Git write, deploy ni sandbox real.

Siguiente sprint operativo: `FUNC-SPRINT-39 — ReviewRulePacks y quality gate de revisión`.


## Transición posterior a FUNC-SPRINT-39 — Review Rule Packs y Repo Quality Gate dry-run

`FUNC-SPRINT-39` agrega `ReviewRulePack` y `repo quality-gate` en modo dry-run. La capacidad consolida `RepoAnalyzer`, `CodeReviewEngine`, `PatchReviewEngine` opcional y `PolicyEngine` para entregar estado `PASS`, `FAIL`, `BLOCK` o `ERROR` sin modificar el repositorio.

Estado real:

- implementado `ReviewRulePack` versionable;
- implementado `RepoQualityGate`;
- implementado comando `repo quality-gate`;
- reportes opcionales JSON/Markdown mediante `--write-report`;
- tool `repo.quality_gate` declarada en MIASI;
- warnings no bloquean por defecto;
- findings `FAIL` y `BLOCK` de motores integrados se propagan;
- no aplica patches;
- no ejecuta Git write;
- no modifica archivos;
- no usa LLM, red ni APIs externas.

Siguiente sprint operativo: `FUNC-SPRINT-40 — Patch preflight con verificación segura`.


## Transición posterior a FUNC-SPRINT-40 — Patch preflight con verificación segura

`FUNC-SPRINT-40` agrega `PatchPreflightEngine` y `patch check` como preflight seguro de patches. La capacidad ejecuta revisión determinística del patch, evaluación de política y `git apply --check` mediante `SafeSubprocessRunner` y allowlist explícita.

Estado real:

- implementado `PatchPreflightEngine`;
- implementado comando `patch check`;
- `patch check --patch-file ... --json` reporta aplicabilidad y findings;
- `--write-report` genera evidencia JSON/Markdown;
- tool `patch.check` declarada en MIASI;
- regla `PATCH_CHECK_DRY_RUN_ALLOW` declarada en Policy Matrix;
- allowlist de `SafeSubprocessRunner` ampliada solo para `git apply --check`;
- `safe.patch` corregido como muestra operativa aplicable;
- no aplica patches;
- no ejecuta Git write;
- no modifica archivos del workspace productivo;
- no crea sandbox ni ChangeSet todavía;
- no usa LLM, red ni APIs externas.

Siguiente sprint operativo: `FUNC-SPRINT-41 — PatchSandbox y ChangeSet model`.


## Transición posterior a FUNC-SPRINT-41

`FUNC-SPRINT-41` habilita `PatchSandboxManager` y `ChangeSet` como primera capacidad de sandbox de Fase C. La implementación aplica patches solo en `outputs/sandbox`, no aplica patches al workspace productivo, no ejecuta Git write, no habilita refactor execution y el rollback ejecutable sigue fuera de alcance hasta `FUNC-SPRINT-42`.

Capacidad nueva: `patch sandbox --patch-file ...` genera evidencia y `ChangeSet` preliminar. `--run-tests` queda approval-gated porque ejecuta código dentro de la copia del workspace.

Git write sigue bloqueado en esta transición; no hay commit, tag, push ni checkout automático.


## Transición posterior a FUNC-SPRINT-42

`FUNC-SPRINT-42` habilita `RollbackManager` como primera versión local de backup/rollback controlado. La implementación crea rollback plans desde `ChangeSet`, registra rollback points runtime bajo `.devpilot/rollback/`, permite `rollback list/show` en modo read-only y mantiene `rollback execute` bloqueado sin aprobación y no-mutating incluso cuando se prepare su evolución.

La transición hacia `FUNC-SPRINT-43` queda condicionada a mantener Git write bloqueado, no restaurar archivos automáticamente, no ejecutar acciones destructivas y usar rollback metadata como insumo para refactor sandbox controlado.


## Transición posterior a FUNC-SPRINT-43

`FUNC-SPRINT-43` habilita `RefactorExecutor` como primera ejecución controlada de refactor en sandbox. La implementación exige approval de `refactor.sandbox`, limita el cambio a transformaciones mecánicas determinísticas en archivos Python, emite `ChangeSet`, crea rollback plan y mantiene el workspace productivo intacto.

La transición hacia `FUNC-SPRINT-44` queda condicionada a consolidar Fase C en un gate integral de ingeniería de repositorio. Sigue fuera de alcance aplicar refactors al workspace real, restaurar automáticamente rollback points, ejecutar Git write o aceptar planes no determinísticos.


## Transición posterior a FUNC-SPRINT-44

`FUNC-SPRINT-44` cierra Fase C mediante `repo engineering-gate`. A partir de este punto, el backlog funcional posterior al pre-code debe abrir una nueva unidad de planificación para `FASE-D — IA local gobernada`, manteniendo como restricciones heredadas: local-first, multi-modelo, sin API externa por defecto, approval para acciones críticas, trazabilidad, sandbox antes de ejecución, y evidencias reproducibles.

No se habilita todavía ejecución autónoma de agentes sobre repositorios reales. La siguiente fase deberá definir explícitamente proveedores locales, ModelAdapter operativo, límites de costo, evaluación y observabilidad antes de permitir cualquier flujo agent-assisted con modelos.


## Transición a Fase D — IA local gobernada

Tras el cierre de `FUNC-SPRINT-44`, Fase C queda completada mediante `repo engineering-gate`. El siguiente sprint operativo aprobado es `FUNC-SPRINT-45 — ADR y contratos de proveedores locales`, correspondiente a la Fase D.

La Fase D se aprueba bajo restricciones local-first: proveedor `mock` obligatorio/default, Ollama/LM Studio opcionales, APIs externas deshabilitadas por defecto, sin multiagente funcional y sin acciones críticas sin Approval Workflow.


## Transición posterior a FUNC-SPRINT-45

`FUNC-SPRINT-45` inicia Fase D con contratos de proveedores locales antes de implementar adapters reales. El sprint crea `ADR-0011`, actualiza el provider config schema a v2, mantiene `mock` como proveedor obligatorio/default, declara Ollama/LM Studio como locales opcionales y conserva proveedores externos en estado `disabled`.

La transición hacia `FUNC-SPRINT-46` queda condicionada a no requerir Ollama para la suite base, no habilitar APIs externas, no versionar secretos y mantener todo modelo futuro detrás de `ModelAdapterRouter`, `PolicyEngine`, `SecretGuard` y `CostGuard`.


## Transición posterior a FUNC-SPRINT-46

`FUNC-SPRINT-46` completa la integración inicial opcional de Ollama como proveedor local. La transición hacia `FUNC-SPRINT-47` queda condicionada a mantener Ollama opcional, no requerir modelos locales en la suite base, no habilitar APIs externas y extender el mismo patrón localhost-only/timeouts/fake-server hacia LM Studio.


## Transición posterior a FUNC-SPRINT-47

`FUNC-SPRINT-47` completa la integración inicial opcional de LM Studio como proveedor local OpenAI-compatible, manteniendo `mock` como ruta obligatoria/default, Ollama y LM Studio deshabilitados por defecto, `localhost` como único alcance permitido para providers locales y APIs externas bloqueadas.

La transición hacia `FUNC-SPRINT-48` queda condicionada a no requerir modelos locales en la suite base, no habilitar APIs externas y consolidar gobierno operativo de modelos mediante health unificado, capability matrix y budget ledger local.


## Transición posterior a FUNC-SPRINT-48

`FUNC-SPRINT-48` consolida el gobierno operativo inicial de modelos locales mediante health unificado, capability matrix y budget ledger local. La transición hacia `FUNC-SPRINT-49` queda condicionada a mantener `mock` como ruta obligatoria/default, no requerir Ollama/LM Studio para pruebas base, no almacenar prompts o secretos en `cost_events`, no habilitar APIs externas y usar el nuevo gobierno como base para Prompt Registry y Prompt Packs gobernados.


## Transición posterior a FUNC-SPRINT-49

`FUNC-SPRINT-49` completa el Prompt Registry inicial: prompts versionados como docs-as-code, schema `Prompt`, comandos read-only `prompt list/show/validate`, checks básicos de `PromptSafetyChecker` y trazabilidad `prompt_id/version` en llamadas `model generate --prompt-id`.

La transición hacia `FUNC-SPRINT-50` queda condicionada a evaluar modelos usando prompts versionados, no prompts embebidos sin trazabilidad, mantener `mock` como baseline reproducible, no almacenar prompts/completions crudos y conservar APIs externas bloqueadas salvo ADR/aprobación futura.


## Transición posterior a FUNC-SPRINT-50

`FUNC-SPRINT-50` cierra la primera matriz de evaluación local de modelos. La transición hacia `FUNC-SPRINT-51` queda condicionada a mantener `mock` como proveedor hermético obligatorio, no exigir Ollama/LM Studio para la suite base, preservar reportes redacted y usar `PromptRegistry`, `ModelAdapterRouter`, `BudgetLedger` y `ModelEvalRunner` como base para AgentRuntime v2 model-aware en modo monoagente.


## Transición posterior a FUNC-SPRINT-51

`FUNC-SPRINT-51` habilita `AgentRuntime v2` model-aware en modo monoagente. La transición hacia `FUNC-SPRINT-52` queda condicionada a que los agentes especializados usen exclusivamente `AgentRuntime`, `PromptRegistry`, `ModelAdapterRouter`, `BudgetLedger` y MIASI, sin llamadas directas a adapters, sin provider local obligatorio, sin APIs externas y sin handoffs/multiagente.


## Transición posterior a FUNC-SPRINT-52

`FUNC-SPRINT-52` implementa `RepoAnalysisAgent` como primer agente especializado monoagente sobre motores de Fase C. La transición hacia `FUNC-SPRINT-53` queda condicionada a mantener `RepoAnalysisAgent` read-only, sin APIs externas, sin cambios productivos, sin handoffs y con evidencia en `EvalRunner`; los próximos agentes de revisión deben seguir el mismo patrón: motor determinístico existente + AgentRuntime v2 + PromptRegistry + MIASI + evals offline.

## Transición posterior a FUNC-SPRINT-53

Después de `FUNC-SPRINT-53`, DevPilot dispone de agentes gobernados para análisis de repositorio, revisión de código y revisión de patches. El siguiente incremento funcional debe avanzar hacia agentes plan-only para refactor seguro y planeación de pruebas, manteniendo el mismo patrón: `AgentRuntime v2`, MIASI, prompts versionados, dry-run por defecto, evals offline y ausencia de APIs externas.

Siguiente sprint: `FUNC-SPRINT-54 — SafeRefactorAgent y TestPlannerAgent gobernados`.


## Transición posterior a FUNC-SPRINT-54

Después de `FUNC-SPRINT-54`, DevPilot cuenta con agentes especializados plan-only para refactor seguro y planificación de pruebas. Esta transición no habilita ejecución autónoma: `SafeRefactorAgent` no ejecuta cambios reales y `TestPlannerAgent` no ejecuta `tests.run`; ambos preparan planes auditables para una evolución futura con aprobación, sandbox, rollback y perfiles de prueba controlados.

El siguiente sprint operativo es `FUNC-SPRINT-55 — Requirements/Architecture/Security agents y cierre Fase D`.


## Transición posterior a FUNC-SPRINT-55

Después de `FUNC-SPRINT-55`, DevPilot cierra la Fase D de IA local gobernada. La plataforma cuenta con `ModelAdapter` mock/local, proveedores locales gobernados, PromptRegistry, BudgetLedger, AgentRuntime v2 y agentes monoagente especializados para repositorio, revisión de código, revisión de patches, refactor plan-only, planificación de pruebas, requisitos, arquitectura y seguridad.

La transición no habilita multiagente, handoffs, APIs externas ni ejecución autónoma. El backlog `docs/devpilot_backlog_fase_E_agentops_observabilidad.md` queda promovido a `approved` después de la revisión de cierre de Fase D. El siguiente sprint operativo es `FUNC-SPRINT-56 — ADR de observabilidad v2 y modelo AgentOps`, dentro de la Fase E, para instrumentar trazas, spans y métricas agentic/model con telemetría local-first y sin exfiltración por defecto.


## Transición posterior a FUNC-SPRINT-56

`FUNC-SPRINT-56 — ADR de observabilidad v2 y modelo AgentOps` queda implementado como inicio de Fase E. El sprint no agrega runtime nuevo; formaliza la decisión arquitectónica `ADR-0012`, actualiza los contratos de observabilidad operacional y MIASI, crea el catálogo preliminar de señales v2 y habilita el inicio de `FUNC-SPRINT-57 — TraceContext y modelo de spans`.

La transición mantiene explícitamente bloqueados: telemetría remota, exporters activos, SDKs externos obligatorios, multiagente funcional, handoffs, RAG, MCP y ejecución remota. La siguiente unidad de trabajo debe implementar `TraceContext`/`SpanRecord` internos manteniendo compatibilidad con `EventLogger` actual.


## Transición posterior a FUNC-SPRINT-57

`FUNC-SPRINT-57 — TraceContext y modelo de spans` queda implementado como primera capacidad runtime de observabilidad v2. Se incorporan contratos internos serializables para `TraceContext`, `SpanRecord`, `SpanStatus`, generación de ids y redacción de payloads sensibles, sin persistencia, sin CLI de consulta y sin dependencias externas.

El siguiente sprint operativo es `FUNC-SPRINT-58 — TraceStore y EventLogger v2 compatible`, que deberá persistir spans/eventos de forma local y mantener compatibilidad con JSONL actual.


## Transición posterior a FUNC-SPRINT-58

`FUNC-SPRINT-58 — TraceStore y EventLogger v2 compatible` queda implementado como primera persistencia consultable de observabilidad v2. DevPilot conserva `EventLogger` JSONL como evidencia append-only y agrega `TraceStore`/SQLite para spans y eventos correlacionables por `trace_id`.

El siguiente sprint operativo es `FUNC-SPRINT-59 — MetricsCollector para comandos, agentes, tools y modelos`, que deberá agregar métricas locales sobre la base de `TraceContext`, `SpanRecord`, `TraceStore` y `LocalStore`.


## Transición posterior a FUNC-SPRINT-59

`FUNC-SPRINT-59` agrega la capa inicial de métricas locales de AgentOps mediante `MetricRecord`, `MetricsCollector`, extensión de `LocalStore` y registro best-effort de comandos/model calls mock. El siguiente sprint operativo es `FUNC-SPRINT-60 — Instrumentación agentic: agentes, tools, approvals y model calls`, que deberá conectar estas métricas y spans con el runtime agentic real sin cambiar semántica funcional ni persistir payloads crudos.


## Transición posterior a FUNC-SPRINT-60

`FUNC-SPRINT-60` conecta la observabilidad local con la superficie agentic real de DevPilot. Desde este sprint, AgentRuntime, tool calls, policy checks, approvals y model calls generan evidencia local best-effort mediante spans, eventos y métricas correlacionadas.

La transición hacia `FUNC-SPRINT-61` queda condicionada a exponer consulta operacional segura: `trace report`, `trace inspect` y `metrics summary`, sin requerir UI, sin servicios externos, sin exponer secretos y manteniendo respuestas controladas cuando no existan trazas.


## Transición posterior a FUNC-SPRINT-61

`FUNC-SPRINT-61` expone por CLI la evidencia AgentOps local generada por los sprints anteriores. Desde este punto, DevPilot puede consultar trazas recientes, inspeccionar una traza específica como árbol de spans y resumir métricas locales sin UI ni servicios externos.

La transición hacia `FUNC-SPRINT-62` queda condicionada a mantener estas consultas como fuente local de verdad para cualquier exporter futuro: OpenTelemetry debe iniciar como dry-run/local, sin envío remoto, sin dependencia obligatoria y con redacción obligatoria de secretos, prompts, completions, diffs y salidas crudas.


## Transición posterior a FUNC-SPRINT-62

Con `FUNC-SPRINT-62`, DevPilot completa el nivel FE-L5 inicial: payload OTel-like local, opcional y dry-run. El siguiente paso funcional es `FUNC-SPRINT-63 — AgentOps Quality Gate operacional`, que debe evaluar salud operacional usando trazas, spans, métricas, warnings, bloqueos y evidencia local sin depender de servicios externos.


## Transición posterior a FUNC-SPRINT-63 — Cierre Fase E

Con `FUNC-SPRINT-63`, DevPilot cierra Fase E de AgentOps y observabilidad. El core dispone de trazas v2, spans, eventos, métricas, instrumentación agentic, CLI de consulta, exporter OpenTelemetry dry-run y AgentOps Quality Gate.

La transición hacia `FUNC-SPRINT-64` queda condicionada a mantener las señales AgentOps como fuente de verdad para Fase F. La futura API/Web UI local debe consumir `CommandResult`, reportes y servicios del core sin duplicar lógica ni saltarse `ApplicationService`, `PolicyEngine`, MIASI, `ReportEngine`, `TraceStore` o `MetricsCollector`. La estrategia visual vigente es web-first: Web UI local primero, Web UI real después, Desktop diferido por ADR posterior.


## Transición posterior a FUNC-SPRINT-64 — Gate UI/API de Fase F

`FUNC-SPRINT-64` cierra la decisión arquitectónica inicial de Fase F: Web UI local como interfaz visual canónica, API local segura como frontera, Web UI real como evolución posterior y Desktop diferido fuera de Fase F. El siguiente sprint funcional es `FUNC-SPRINT-65 — ApplicationService v2 por dominios`.

La implementación es `implemented-initial`: no agrega servidor, frontend ni dependencias runtime. Su valor es reducir riesgo antes de construir API/UI y mantener el core gobernado por ApplicationService, PolicyEngine, MIASI, ReportEngine, LocalStore y observabilidad.


## Transición posterior a FUNC-SPRINT-71

Fase F avanza con Approval Center y acciones dry-run desde UI. `next_sprint: "FUNC-SPRINT-78"`.
