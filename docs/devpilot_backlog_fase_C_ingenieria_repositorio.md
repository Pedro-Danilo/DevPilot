---
title: "DevPilot Local — Backlog ejecutable Fase C: Ingeniería de repositorio"
doc_id: "DEVPL-FUNC-BACKLOG-FASE-C-001"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
standard: "MIPSoftware"
extension: "MIASI"
phase: "FASE-C-INGENIERIA-DE-REPOSITORIO"
updated: "2026-06-11"
source_repo: "repo_DevPilot_Local_41.zip"
source_report: "Informe de avance DevPilot - sprint 0 - 18.docx"
source_backlog_model: "docs/functional_backlog_after_precode.md"
baseline_dependency: "Fase A cerrada por FUNC-SPRINT-27 y Fase B cerrada por FUNC-SPRINT-34"
first_sprint: "FUNC-SPRINT-35"
last_planned_sprint: "FUNC-SPRINT-44"
change_policy: "controlled_changes_allowed_via_docs_as_code"
approval_scope: "phase_c_executable_backlog_review"
approved_on: "2026-06-11"
approval: "approved_by_owner_direction_after_phase_b_closure"
---

# DevPilot Local — Backlog ejecutable Fase C: Ingeniería de repositorio

## Estado de aprobación funcional

Este documento queda en estado `approved` después de verificar el cierre de Fase B mediante `FUNC-SPRINT-34 — Security readiness operacional y cierre de Fase B`. Su propósito es convertir la **Fase C — Ingeniería de repositorio** en un backlog de implementación ejecutable, siguiendo el modelo operativo usado en `docs/functional_backlog_after_precode.md`.

La Fase C agrupa:

- **Ola 4 — Repo intelligence y revisión industrial**.
- **Ola 5 — Sandbox, patch/refactor ejecutable y rollback**.

Esta fase parte del estado real de `repo_DevPilot_Local_41.zip`, donde DevPilot ya tiene `GitAdapter` read-only inicial, `repo-inventory`, `PatchReviewEngine` dry-run, `CodeReviewEngine` dry-run, `RefactorPlanner` plan-only y los prerequisitos de seguridad operacional cerrados en Fase B: Approval Workflow, PolicyEngine binding, SafeSubprocessRunner, `tests.run`, guards de seguridad textual, `security readiness`, checklist de salida y closure report. La Fase C busca transformar esas capacidades iniciales en una capa robusta de ingeniería de repositorio, sin habilitar cambios destructivos fuera de sandbox, sin Git write y sin deploy.


## Estado aprobado posterior a Fase B

La revisión posterior al cierre de `FUNC-SPRINT-34` confirma que este backlog es una continuación apropiada del desarrollo de DevPilot porque toma como entrada los prerequisitos mínimos de seguridad operacional ya cerrados: approvals, policy binding, `tests.run`, SafeSubprocessRunner, guards, readiness y reportes.

La Fase C queda aprobada para iniciar en `FUNC-SPRINT-35 — GitAdapter v2 read-only: ramas, tags, log y diff-report`. Esta aprobación no habilita todavía `patch apply`, `refactor execution`, Git write ni deploy. Es una autorización documental para empezar por capacidades read-only y avanzar hacia sandbox/rollback bajo los gates definidos en este documento.

## 1. Propósito

La Fase C busca que DevPilot pueda comprender un repositorio de software con mayor profundidad, revisar cambios con criterios industriales y, posteriormente, ejecutar cambios controlados dentro de sandbox con trazabilidad y reversibilidad.

En lenguaje operativo, esta fase busca avanzar desde:

```text
Git status + inventario + review dry-run + refactor plan-only
```

hacia:

```text
Git read-only ampliado + repo analysis profundo + dependency graph + architecture drift + patch preflight + sandbox + changesets + rollback + quality gate de repositorio
```

## 2. Regla central de Fase C

La Fase C no debe convertir DevPilot en una herramienta que modifica repositorios de forma libre. Toda transición desde análisis hacia ejecución debe seguir esta cadena:

```text
análisis → plan → política → aprobación → sandbox → tests.run → reporte → ejecución controlada → rollback disponible
```

Reglas obligatorias:

1. Todo comando de análisis debe ser read-only por defecto.
2. Todo comando que pueda modificar archivos debe exigir `approval_id` válido.
3. Todo comando de ejecución debe operar primero en sandbox.
4. Ningún comando debe usar `shell=True`.
5. Ningún comando debe escribir fuera del workspace.
6. Ningún patch debe aplicarse sin `git apply --check` o verificación equivalente.
7. Todo changeset debe tener reporte, trazas y rollback plan.
8. Todo refactor ejecutable debe requerir `tests.run` antes y después.
9. Todo cambio en Git debe permanecer bloqueado salvo decisión explícita posterior.
10. La Fase C no incluye despliegue ni release productivo.

## 3. Alcance de Fase C

Incluye:

- ampliación del `GitAdapter` en modo read-only;
- reportes detallados de diff;
- análisis de branches, tags y log;
- DependencyGraph inicial;
- import graph Python;
- repo analysis profundo;
- architecture/code drift inicial;
- rule packs de revisión de código;
- quality gate de cambios;
- patch preflight con `git apply --check`;
- patch sandbox;
- ChangeSet model;
- rollback manager;
- refactor execution controlado;
- cierre auditado de ingeniería de repositorio.

No incluye:

- Git push;
- deploy;
- release assist;
- APIs externas;
- multiagente;
- UI real;
- RAG;
- MCP;
- ejecución destructiva sin aprobación.

## 4. Niveles de implementación de Fase C

| Nivel | Nombre | Objetivo | Estado esperado al cierre |
|---|---|---|---|
| FC-L0 | Git read-only ampliado | Leer estado, ramas, tags, log y diff con evidencia | GitAdapter v2 |
| FC-L1 | Repo intelligence | Entender estructura, dependencias y riesgos | RepoAnalyzer v2 + DependencyGraph |
| FC-L2 | Drift y review industrial | Comparar arquitectura/código y aplicar reglas de revisión | DriftDetector + ReviewRulePacks |
| FC-L3 | Patch preflight | Verificar patches antes de sandbox | PatchPreflight con `git apply --check` |
| FC-L4 | Sandbox y changesets | Probar cambios en área controlada | PatchSandbox + ChangeSet |
| FC-L5 | Refactor ejecutable controlado | Pasar de plan a ejecución reversible | RefactorExecutor + RollbackManager |
| FC-L6 | Quality gate repo | Cierre integral de cambios | RepoQualityGate |

## 5. Definition of Done transversal

Un sprint de Fase C solo puede cerrarse si cumple:

- actualiza README y runbook si agrega comandos;
- actualiza MIASI si agrega o cambia tools/policies;
- conserva acciones write/execute bloqueadas sin approval;
- todo comando nuevo devuelve `CommandResult`;
- todo comando nuevo soporta `--json`;
- todo comando con evidencia soporta `--write-report`;
- los cambios con side effects generan eventos y persistencia;
- no se versionan outputs ni sandboxes runtime;
- `pytest -q` pasa;
- se documentan riesgos, límites y condición preliminar si la capacidad no es industrial completa.

## 6. Convenciones de IDs

| Tipo | Prefijo | Ejemplo |
|---|---|---|
| Sprint funcional | `FUNC-SPRINT-XX` | `FUNC-SPRINT-35` |
| Historia | `US-FUNC-XX-YYY` | `US-FUNC-35-001` |
| Tarea | `FUNC-XX-YYY` | `FUNC-35-003` |
| Prueba | `TEST-FUNC-XX-YYY` | `TEST-FUNC-35-002` |
| Gate | `GATE-FUNC-XX` | `GATE-FUNC-35` |
| Riesgo | `RISK-FUNC-XX-YYY` | `RISK-FUNC-35-001` |
| Repo analysis | `REPO-*` | `REPO-DEPENDENCY-GRAPH` |
| ChangeSet | `CHANGESET-*` | `CHANGESET-PATCH-SANDBOX` |

## 7. Roadmap funcional de Fase C

| Ola | Sprints | Resultado esperado |
|---|---|---|
| Ola 4 | FUNC-SPRINT-35 a 39 | GitAdapter ampliado, repo intelligence, drift y review gate |
| Ola 5 | FUNC-SPRINT-40 a 44 | Patch preflight, sandbox, changesets, refactor execution controlado y rollback |

## 8. Referencias técnicas externas de apoyo

- Git permite inspeccionar diferencias mediante `git diff` y aplicar/verificar parches mediante `git apply`; DevPilot debe usar estas capacidades bajo allowlist, cwd controlado y dry-run/sandbox.
- La validación de cambios debe distinguir preflight, sandbox, apply y rollback; estas etapas no deben fusionarse.
- La ejecución controlada depende de Fase B: Approval Workflow y `tests.run` son prerequisitos para cualquier modificación real.


# FUNC-SPRINT-35 — GitAdapter v2 read-only: ramas, tags, log y diff-report

## Objetivo

Ampliar el adaptador Git sin introducir operaciones de escritura, incorporando ramas, tags, log y reportes de diff ricos para alimentar análisis de repositorio y quality gates.

## Entradas

- `src/devpilot_core/repo/git_adapter.py`
- `src/devpilot_core/repo/inventory.py`
- `docs/functional_backlog_after_precode.md`
- Fase B aprobada para SafeSubprocessRunner si se reutiliza ejecución controlada

## Historias

| ID | Historia | Criterio de aceptación |
|---|---|---|
| US-FUNC-35-001 | Como desarrollador, quiero consultar ramas, tags y commits recientes sin modificar el repo. | Existen comandos read-only para branches/tags/log con `ok=true`. |
| US-FUNC-35-002 | Como arquitecto, quiero un diff report estructurado para revisar cambios con evidencia. | Existe `git diff-report --json --write-report`. |
| US-FUNC-35-003 | Como auditor, quiero asegurar que GitAdapter no pueda ejecutar write commands. | Las pruebas bloquean comandos no permitidos. |

## Tareas

| ID | Tarea | Entregable | PASS |
|---|---|---|---|
| FUNC-35-001 | Extender GitAdapter con allowlist read-only | `src/devpilot_core/repo/git_adapter.py` | No acepta add/commit/reset/checkout/push. |
| FUNC-35-002 | Crear comandos `git branches`, `git tags`, `git log` | `src/devpilot_core/cli.py o módulo CLI repo` | Devuelven JSON parseable. |
| FUNC-35-003 | Crear `git diff-report` | `src/devpilot_core/repo/diff_report.py` | Incluye archivos, líneas, tipo de cambio y riesgos básicos. |
| FUNC-35-004 | Actualizar MIASI Tool Registry | `.devpilot/miasi/tool_registry.json` | Tools Git read-only quedan declaradas. |
| FUNC-35-005 | Actualizar runbook/README | `README.md; docs/05_operations/runbook.md` | Comandos nuevos documentados. |

## Archivos previstos

```text
src/devpilot_core/repo/git_adapter.py
src/devpilot_core/repo/diff_report.py
tests/test_git_adapter_v2.py
docs/audits/func_sprint_35_git_adapter_v2_audit.md
docs/functional_sprint_35_manifest.json
```

## Comandos objetivo

```powershell
python -m devpilot_core git branches --json
python -m devpilot_core git tags --json
python -m devpilot_core git log --limit 20 --json
python -m devpilot_core git diff-report --json --write-report
python -m pytest -q
```

## Criterios PASS

- GitAdapter v2 opera solo en modo read-only.
- Los comandos no modifican working tree ni index.
- `git diff-report` genera JSON/Markdown si se usa `--write-report`.
- MIASI refleja las nuevas tools Git.

## Criterios BLOCK

- Cualquier operación Git write está bloqueada.
- No cerrar si un comando usa shell libre o argumentos no allowlisted.
- No cerrar si un repo no Git provoca excepción no controlada.

## Riesgos

| ID | Riesgo | Mitigación |
|---|---|---|
| RISK-FUNC-35-001 | Exposición accidental de comandos write | Allowlist estricta y pruebas negativas. |
| RISK-FUNC-35-002 | Diff muy grande consume memoria | Agregar límites y truncamiento documentado. |
| RISK-FUNC-35-003 | Repos sin Git fallan | Devolver CommandResult controlado con warning/fail no crash. |

## Pruebas mínimas

- TEST-FUNC-35-001: Branches/tags/log en repo temporal Git.
- TEST-FUNC-35-002: Diff report con archivos modificados, añadidos y eliminados.
- TEST-FUNC-35-003: Bloqueo de comandos write simulados.
- TEST-FUNC-35-004: Repo no Git devuelve resultado controlado.

## Prompt operativo sugerido

```text
Implementa FUNC-SPRINT-35: amplía GitAdapter en modo read-only con branches/tags/log/diff-report. Mantén allowlist estricta, sin operaciones write, sin shell libre, con pruebas, README, runbook, auditoría y manifest.
```


# FUNC-SPRINT-36 — DependencyGraph e import graph Python

## Objetivo

Crear un grafo inicial de dependencias internas del repositorio, comenzando por imports Python, para entender acoplamientos, módulos críticos y riesgos de cambio.

## Entradas

- `src/devpilot_core/`
- `tests/`
- Resultado de `repo-inventory`
- GitAdapter v2

## Historias

| ID | Historia | Criterio de aceptación |
|---|---|---|
| US-FUNC-36-001 | Como arquitecto, quiero visualizar dependencias internas para detectar acoplamientos. | Existe `repo dependency-graph --json`. |
| US-FUNC-36-002 | Como desarrollador, quiero saber qué módulos pueden verse afectados por un cambio. | El reporte lista dependientes/dependencias por módulo. |
| US-FUNC-36-003 | Como auditor, quiero que el análisis sea local y determinístico. | No usa red ni modelos externos. |

## Tareas

| ID | Tarea | Entregable | PASS |
|---|---|---|---|
| FUNC-36-001 | Crear parser de imports Python con AST | `src/devpilot_core/repo/dependency_graph.py` | Extrae imports locales sin ejecutar código. |
| FUNC-36-002 | Crear modelo DependencyGraph | `src/devpilot_core/repo/models.py` | Nodos y edges serializables. |
| FUNC-36-003 | Crear comando `repo dependency-graph` | `CLI` | Devuelve CommandResult. |
| FUNC-36-004 | Agregar métricas básicas | `dependency report` | Módulos con mayor fan-in/fan-out. |
| FUNC-36-005 | Documentar límites | `runbook` | No analiza imports dinámicos complejos como certeza absoluta. |

## Archivos previstos

```text
src/devpilot_core/repo/dependency_graph.py
src/devpilot_core/repo/models.py
tests/test_dependency_graph.py
docs/audits/func_sprint_36_dependency_graph_audit.md
docs/functional_sprint_36_manifest.json
```

## Comandos objetivo

```powershell
python -m devpilot_core repo dependency-graph --target src/devpilot_core --json
python -m devpilot_core repo dependency-graph --target src/devpilot_core --json --write-report
python -m pytest -q
```

## Criterios PASS

- Extrae imports sin ejecutar código.
- Reporta nodos, edges, fan-in y fan-out.
- Ignora outputs/caches/venv.
- Incluye limitaciones explícitas.

## Criterios BLOCK

- No cerrar si ejecuta módulos para analizarlos.
- No cerrar si sigue symlinks fuera del workspace.
- No cerrar si falla con archivos Python inválidos sin reportar finding.

## Riesgos

| ID | Riesgo | Mitigación |
|---|---|---|
| RISK-FUNC-36-001 | Imports dinámicos no detectados | Marcar como limitación y no inventar certeza. |
| RISK-FUNC-36-002 | Grafos muy grandes | Límites de nodos/edges y paginación futura. |
| RISK-FUNC-36-003 | Falsos positivos en paquetes externos | Separar imports internos vs externos. |

## Pruebas mínimas

- TEST-FUNC-36-001: Fixture con imports locales simples.
- TEST-FUNC-36-002: Fixture con import externo excluido del grafo interno.
- TEST-FUNC-36-003: Archivo con syntax error reportado como finding.
- TEST-FUNC-36-004: Comando CLI JSON parseable.

## Prompt operativo sugerido

```text
Implementa FUNC-SPRINT-36: crea DependencyGraph local con AST, comando repo dependency-graph, reportes, pruebas y documentación. No ejecutes código analizado.
```


# FUNC-SPRINT-37 — RepoAnalyzer v2: estructura, riesgos y salud del repositorio

## Objetivo

Evolucionar `repo-inventory` hacia un análisis de repositorio más profundo que consolide estructura, dependencias, documentación, pruebas, riesgos y señales de mantenibilidad.

## Entradas

- `repo-inventory`
- DependencyGraph
- GitAdapter v2
- docs/04_quality/test_strategy.md

## Historias

| ID | Historia | Criterio de aceptación |
|---|---|---|
| US-FUNC-37-001 | Como owner, quiero un resumen de salud del repositorio. | Existe `repo analyze --json --write-report`. |
| US-FUNC-37-002 | Como arquitecto, quiero ver módulos críticos y riesgos de mantenibilidad. | El reporte incluye hotspots y métricas básicas. |
| US-FUNC-37-003 | Como desarrollador, quiero saber si docs/tests/código están balanceados. | El análisis incluye secciones docs/src/tests. |

## Tareas

| ID | Tarea | Entregable | PASS |
|---|---|---|---|
| FUNC-37-001 | Crear RepoAnalyzer | `src/devpilot_core/repo/analyzer.py` | Consolida inventario, dependencia y Git. |
| FUNC-37-002 | Definir RepoHealthSummary | `repo models` | Métricas serializables. |
| FUNC-37-003 | Crear comando `repo analyze` | `CLI` | Genera JSON/Markdown. |
| FUNC-37-004 | Agregar heurísticas de riesgo | `analyzer` | Archivos grandes, módulos sin tests cercanos, secretos, TODOs. |
| FUNC-37-005 | Actualizar test strategy | `docs/04_quality/test_strategy.md` | Incluye pruebas de repo analyzer. |

## Archivos previstos

```text
src/devpilot_core/repo/analyzer.py
tests/test_repo_analyzer.py
docs/audits/func_sprint_37_repo_analyzer_v2_audit.md
docs/functional_sprint_37_manifest.json
```

## Comandos objetivo

```powershell
python -m devpilot_core repo analyze --json
python -m devpilot_core repo analyze --json --write-report
python -m pytest -q
```

## Criterios PASS

- RepoAnalyzer no modifica archivos.
- Produce resumen de salud con findings accionables.
- Integra inventario y DependencyGraph cuando esté disponible.
- Documenta que es heurístico, no certificación absoluta.

## Criterios BLOCK

- No cerrar si mezcla outputs runtime en el análisis.
- No cerrar si secretos crudos aparecen en reportes.
- No cerrar si una ausencia de Git rompe el análisis completo.

## Riesgos

| ID | Riesgo | Mitigación |
|---|---|---|
| RISK-FUNC-37-001 | Health score malinterpretado como verdad absoluta | Nombrarlo heurístico y explicar señales. |
| RISK-FUNC-37-002 | Reportes demasiado largos | Resúmenes y límites configurables. |
| RISK-FUNC-37-003 | Falsos positivos de tests faltantes | Usar severidad warning salvo señales fuertes. |

## Pruebas mínimas

- TEST-FUNC-37-001: Repo pequeño con src/tests/docs genera summary.
- TEST-FUNC-37-002: Repo con secreto sintético reporta redacted finding.
- TEST-FUNC-37-003: Repo sin Git aún produce análisis parcial.
- TEST-FUNC-37-004: CLI con --write-report genera archivos.

## Prompt operativo sugerido

```text
Implementa FUNC-SPRINT-37: crea RepoAnalyzer v2 que consolide inventario, dependencias, Git y riesgos básicos, todo read-only, local y con reportes.
```


# FUNC-SPRINT-38 — Architecture/code drift inicial

## Objetivo

Detectar divergencias iniciales entre arquitectura documentada y estructura real del código, sin pretender análisis semántico completo.

## Entradas

- docs/02_architecture/architecture_document.md
- docs/02_architecture/c4_container.md
- RepoAnalyzer v2
- DependencyGraph

## Historias

| ID | Historia | Criterio de aceptación |
|---|---|---|
| US-FUNC-38-001 | Como arquitecto, quiero detectar si los módulos reales coinciden con los componentes documentados. | Existe `repo architecture-drift --json`. |
| US-FUNC-38-002 | Como auditor, quiero diferenciar ausencia documental de ausencia de código. | Findings separan doc_missing/code_missing/name_mismatch. |
| US-FUNC-38-003 | Como nuevo desarrollador, quiero saber qué partes de C4 están implementadas, parciales o futuras. | Reporte incluye matriz de estado. |

## Tareas

| ID | Tarea | Entregable | PASS |
|---|---|---|---|
| FUNC-38-001 | Crear ArchitectureDriftDetector | `src/devpilot_core/repo/architecture_drift.py` | Extrae componentes documentados y módulos reales. |
| FUNC-38-002 | Crear reglas iniciales de matching | `drift rules` | Mapea nombres conocidos con tolerancia. |
| FUNC-38-003 | Crear comando `repo architecture-drift` | `CLI` | Devuelve matriz y findings. |
| FUNC-38-004 | Actualizar C4 docs si aplica | `docs/02_architecture` | Recomienda `c4_component.md` si falta. |
| FUNC-38-005 | Agregar auditoría | `docs/audits` | Explica límites del detector. |

## Archivos previstos

```text
src/devpilot_core/repo/architecture_drift.py
tests/test_architecture_drift.py
docs/audits/func_sprint_38_architecture_drift_audit.md
docs/functional_sprint_38_manifest.json
```

## Comandos objetivo

```powershell
python -m devpilot_core repo architecture-drift --json
python -m devpilot_core repo architecture-drift --json --write-report
python -m pytest -q
```

## Criterios PASS

- Detecta componentes documentados sin módulo evidente y módulos sin referencia arquitectónica.
- No modifica documentos automáticamente.
- Incluye niveles de confianza.
- Los hallazgos son accionables y no bloquean por defecto salvo ausencia crítica definida.

## Criterios BLOCK

- No cerrar si inventa relaciones no soportadas.
- No cerrar si marca como BLOCK componentes explícitamente future/planned.
- No cerrar si requiere LLM o red.

## Riesgos

| ID | Riesgo | Mitigación |
|---|---|---|
| RISK-FUNC-38-001 | Matching impreciso | Incluir confidence y allowlist de aliases. |
| RISK-FUNC-38-002 | Documentos C4 aspiracionales | Respetar etiquetas planned/future. |
| RISK-FUNC-38-003 | Falsos bloqueos | Usar warnings hasta madurar reglas. |

## Pruebas mínimas

- TEST-FUNC-38-001: Fixture con componente documentado y módulo existente.
- TEST-FUNC-38-002: Fixture con componente documentado sin código.
- TEST-FUNC-38-003: Fixture con módulo no documentado.
- TEST-FUNC-38-004: Comando genera reporte parseable.

## Prompt operativo sugerido

```text
Implementa FUNC-SPRINT-38: detector inicial de architecture/code drift local y heurístico, con confidence, sin LLM y sin modificar documentos.
```


# FUNC-SPRINT-39 — Review Rule Packs y Repo Quality Gate dry-run

## Objetivo

Consolidar reglas de code/patch/repo review en paquetes versionables y crear un quality gate dry-run para cambios de repositorio.

## Entradas

- CodeReviewEngine
- PatchReviewEngine
- RepoAnalyzer
- PolicyEngine
- MIASI Tool Registry

## Historias

| ID | Historia | Criterio de aceptación |
|---|---|---|
| US-FUNC-39-001 | Como revisor, quiero ejecutar un gate integral antes de aceptar cambios. | Existe `repo quality-gate --json`. |
| US-FUNC-39-002 | Como arquitecto, quiero reglas de revisión agrupadas por dominio. | Existen rule packs documentados. |
| US-FUNC-39-003 | Como auditor, quiero que el gate no modifique el repo. | El gate es dry-run y produce evidencia. |

## Tareas

| ID | Tarea | Entregable | PASS |
|---|---|---|---|
| FUNC-39-001 | Definir ReviewRulePack | `src/devpilot_core/review/rule_packs.py` | Reglas agrupadas y versionadas. |
| FUNC-39-002 | Integrar CodeReview/PatchReview/RepoAnalyzer | `quality gate` | Ejecuta motores existentes. |
| FUNC-39-003 | Crear comando `repo quality-gate` | `CLI` | Devuelve PASS/FAIL/BLOCK. |
| FUNC-39-004 | Actualizar MIASI | `tool_registry/policy_matrix` | Tool `repo.quality_gate` declarada. |
| FUNC-39-005 | Documentar criterios | `runbook` | Explica PASS/BLOCK. |

## Archivos previstos

```text
src/devpilot_core/review/rule_packs.py
src/devpilot_core/repo/quality_gate.py
tests/test_repo_quality_gate.py
docs/audits/func_sprint_39_repo_quality_gate_audit.md
docs/functional_sprint_39_manifest.json
```

## Comandos objetivo

```powershell
python -m devpilot_core repo quality-gate --json
python -m devpilot_core repo quality-gate --json --write-report
python -m pytest -q
```

## Criterios PASS

- Gate integra repo analyze, code review y políticas.
- No modifica archivos.
- Reglas están documentadas y testeadas.
- MIASI refleja la tool.

## Criterios BLOCK

- No cerrar si el gate ignora findings BLOCK.
- No cerrar si reporta secretos crudos.
- No cerrar si bloquea por warnings informativos.

## Riesgos

| ID | Riesgo | Mitigación |
|---|---|---|
| RISK-FUNC-39-001 | Gate demasiado estricto | Configurar severidades y documentar defaults. |
| RISK-FUNC-39-002 | Acoplamiento excesivo | Separar RulePack de motores concretos. |
| RISK-FUNC-39-003 | Tiempo de ejecución alto | Permitir target y límites. |

## Pruebas mínimas

- TEST-FUNC-39-001: Gate PASS en repo limpio fixture.
- TEST-FUNC-39-002: Gate FAIL/BLOCK con secreto/riesgo sintético.
- TEST-FUNC-39-003: Rule packs serializables.
- TEST-FUNC-39-004: CLI --write-report genera evidencia.

## Prompt operativo sugerido

```text
Implementa FUNC-SPRINT-39: ReviewRulePacks y repo quality-gate dry-run integrando review engines, repo analyzer y policy, con MIASI actualizado.
```


# FUNC-SPRINT-40 — Patch preflight con verificación segura

## Objetivo

Agregar una fase de preflight para patches que verifique aplicabilidad y riesgos sin aplicar cambios al workspace productivo.

## Entradas

- PatchReviewEngine
- GitAdapter v2
- SafeSubprocessRunner de Fase B
- Approval Workflow de Fase B

## Historias

| ID | Historia | Criterio de aceptación |
|---|---|---|
| US-FUNC-40-001 | Como desarrollador, quiero saber si un patch aplica antes de intentar aplicarlo. | Existe `patch check --patch-file ... --json`. |
| US-FUNC-40-002 | Como revisor, quiero combinar patch-review y aplicabilidad Git. | El reporte incluye riesgo y apply-check. |
| US-FUNC-40-003 | Como auditor, quiero que preflight no modifique archivos. | Pruebas verifican working tree sin cambios. |

## Tareas

| ID | Tarea | Entregable | PASS |
|---|---|---|---|
| FUNC-40-001 | Crear PatchPreflightEngine | `src/devpilot_core/review/patch_preflight.py` | Combina parse, policy y apply-check. |
| FUNC-40-002 | Usar `git apply --check` en entorno controlado | `preflight` | Sin aplicar patch. |
| FUNC-40-003 | Crear comando `patch check` | `CLI` | Devuelve aplicabilidad y findings. |
| FUNC-40-004 | Actualizar MIASI tool | `tool_registry` | Tool `patch.check` declarada. |
| FUNC-40-005 | Documentar preflight vs apply | `runbook` | No confundir check con aplicación. |

## Archivos previstos

```text
src/devpilot_core/review/patch_preflight.py
tests/test_patch_preflight.py
docs/audits/func_sprint_40_patch_preflight_audit.md
docs/functional_sprint_40_manifest.json
```

## Comandos objetivo

```powershell
python -m devpilot_core patch check --patch-file safe.patch --json
python -m devpilot_core patch check --patch-file safe.patch --json --write-report
python -m pytest -q
```

## Criterios PASS

- `patch check` no modifica working tree.
- Reporta si el patch aplica o no.
- Integra SecretGuard/PathGuard/PolicyEngine.
- Diferencia BLOCK por seguridad de FAIL por aplicabilidad.

## Criterios BLOCK

- No cerrar si un patch check deja cambios en archivos.
- No cerrar si usa subprocess sin allowlist/cwd seguro.
- No cerrar si patches malformados causan crash.

## Riesgos

| ID | Riesgo | Mitigación |
|---|---|---|
| RISK-FUNC-40-001 | `git apply --check` depende de Git instalado | Devolver finding controlado si Git no está disponible. |
| RISK-FUNC-40-002 | Patch grande | Límites de tamaño. |
| RISK-FUNC-40-003 | Path traversal en patch | PathGuard antes de check. |

## Pruebas mínimas

- TEST-FUNC-40-001: Patch aplicable PASS.
- TEST-FUNC-40-002: Patch no aplicable FAIL.
- TEST-FUNC-40-003: Patch con path peligroso BLOCK.
- TEST-FUNC-40-004: Working tree permanece igual tras check.

## Prompt operativo sugerido

```text
Implementa FUNC-SPRINT-40: PatchPreflightEngine y comando patch check, usando verificación segura sin aplicar cambios, con políticas y pruebas de no modificación.
```


# FUNC-SPRINT-41 — PatchSandbox y ChangeSet model

## Objetivo

Crear una zona controlada para probar cambios de patch fuera del workspace productivo y representar los cambios como ChangeSet auditable.

## Entradas

- PatchPreflightEngine
- Approval Workflow
- SafeSubprocessRunner
- tests.run

## Historias

| ID | Historia | Criterio de aceptación |
|---|---|---|
| US-FUNC-41-001 | Como revisor, quiero aplicar un patch en sandbox antes de tocar el repo real. | Existe `patch sandbox` que escribe solo en sandbox. |
| US-FUNC-41-002 | Como auditor, quiero un ChangeSet que describa qué cambiaría. | Existe modelo serializable de ChangeSet. |
| US-FUNC-41-003 | Como desarrollador, quiero reportes de sandbox con resultados de tests opcionales. | Reporte incluye patch, files, tests y rollback plan preliminar. |

## Tareas

| ID | Tarea | Entregable | PASS |
|---|---|---|---|
| FUNC-41-001 | Crear PatchSandboxManager | `src/devpilot_core/sandbox/patch_sandbox.py` | Crea sandbox bajo outputs/sandbox o ruta runtime excluida. |
| FUNC-41-002 | Crear ChangeSet model | `src/devpilot_core/changes/models.py` | Describe archivos, acciones, hash antes/después. |
| FUNC-41-003 | Crear comando `patch sandbox` | `CLI` | Aplica patch solo en sandbox. |
| FUNC-41-004 | Integrar tests.run opcional | `sandbox` | Ejecuta pruebas en sandbox si se solicita. |
| FUNC-41-005 | Actualizar .gitignore/cleanup | `.gitignore/scripts` | Sandbox runtime excluido. |

## Archivos previstos

```text
src/devpilot_core/sandbox/patch_sandbox.py
src/devpilot_core/changes/models.py
tests/test_patch_sandbox.py
docs/audits/func_sprint_41_patch_sandbox_changeset_audit.md
docs/functional_sprint_41_manifest.json
```

## Comandos objetivo

```powershell
python -m devpilot_core patch sandbox --patch-file safe.patch --json
python -m devpilot_core patch sandbox --patch-file safe.patch --run-tests --json --write-report
python -m pytest -q
```

## Criterios PASS

- Patch se aplica únicamente en sandbox.
- Workspace productivo permanece sin cambios.
- ChangeSet se genera y no contiene secretos crudos.
- Sandbox está excluido de release/ZIP.

## Criterios BLOCK

- No cerrar si patch sandbox modifica el workspace real.
- No cerrar si requiere aprobación omitida cuando hay side effect.
- No cerrar si no hay forma de limpiar sandbox.

## Riesgos

| ID | Riesgo | Mitigación |
|---|---|---|
| RISK-FUNC-41-001 | Sandbox ocupa mucho espacio | Límites y cleanup. |
| RISK-FUNC-41-002 | Diferencias entre sandbox y workspace real | Documentar como pre-ejecución, no garantía absoluta. |
| RISK-FUNC-41-003 | Secretos en ChangeSet | Redacción obligatoria. |

## Pruebas mínimas

- TEST-FUNC-41-001: Patch aplicado en sandbox.
- TEST-FUNC-41-002: Workspace real intacto tras sandbox.
- TEST-FUNC-41-003: ChangeSet serializable.
- TEST-FUNC-41-004: Sandbox cleanup probado.

## Prompt operativo sugerido

```text
Implementa FUNC-SPRINT-41: PatchSandboxManager y ChangeSet model. Aplica patches solo en sandbox, con reportes, pruebas y limpieza runtime.
```


# FUNC-SPRINT-42 — RollbackManager y backup local controlado

## Objetivo

Crear un mecanismo local de backup/rollback para cambios controlados, empezando por changesets de sandbox y preparando ejecución real posterior.

## Entradas

- ChangeSet model
- PatchSandbox
- LocalStore
- Approval Workflow

## Historias

| ID | Historia | Criterio de aceptación |
|---|---|---|
| US-FUNC-42-001 | Como operador, quiero poder listar rollback points. | Existe `rollback list --json`. |
| US-FUNC-42-002 | Como desarrollador, quiero generar un rollback plan antes de aplicar un cambio. | ChangeSet incluye rollback plan. |
| US-FUNC-42-003 | Como auditor, quiero evidencia de backup/rollback. | Reportes y eventos registran rollback metadata. |

## Tareas

| ID | Tarea | Entregable | PASS |
|---|---|---|---|
| FUNC-42-001 | Crear RollbackManager | `src/devpilot_core/changes/rollback.py` | Gestiona rollback plans/points. |
| FUNC-42-002 | Crear modelos RollbackPlan/RollbackPoint | `changes/models.py` | Serializables. |
| FUNC-42-003 | Crear comandos `rollback list/show` | `CLI` | Read-only. |
| FUNC-42-004 | Preparar `rollback execute` gated | `CLI futuro` | Bloqueado sin approval y sin ejecución real si no procede. |
| FUNC-42-005 | Actualizar LocalStore | `store` | Persistencia de rollback metadata si aplica. |

## Archivos previstos

```text
src/devpilot_core/changes/rollback.py
tests/test_rollback_manager.py
docs/audits/func_sprint_42_rollback_manager_audit.md
docs/functional_sprint_42_manifest.json
```

## Comandos objetivo

```powershell
python -m devpilot_core rollback list --json
python -m devpilot_core rollback show <rollback_id> --json
python -m pytest -q
```

## Criterios PASS

- Rollback plans son serializables y auditables.
- Comandos list/show son read-only.
- No hay ejecución de rollback sin approval explícito.
- Documenta límites de rollback inicial.

## Criterios BLOCK

- No cerrar si rollback execute puede correr sin approval.
- No cerrar si backup guarda secretos sin redacción.
- No cerrar si rollback points se versionan accidentalmente.

## Riesgos

| ID | Riesgo | Mitigación |
|---|---|---|
| RISK-FUNC-42-001 | Rollback incompleto | Marcar alcance por tipo de change. |
| RISK-FUNC-42-002 | Backup de archivos grandes | Límites y exclusiones. |
| RISK-FUNC-42-003 | Confusión entre plan y ejecución | Comandos separados y documentación clara. |

## Pruebas mínimas

- TEST-FUNC-42-001: Crear rollback plan desde ChangeSet fixture.
- TEST-FUNC-42-002: List/show parseables.
- TEST-FUNC-42-003: Ejecución sin approval bloqueada.
- TEST-FUNC-42-004: Runtime artifacts excluidos.

## Prompt operativo sugerido

```text
Implementa FUNC-SPRINT-42: RollbackManager inicial con rollback plans y list/show. No habilites ejecución libre de rollback.
```


# FUNC-SPRINT-43 — RefactorExecutor controlado en sandbox

## Objetivo

Permitir que planes de refactor se conviertan en cambios controlados dentro de sandbox, con aprobación, tests y rollback plan.

## Entradas

- RefactorPlanner
- PatchSandbox
- ChangeSet
- RollbackManager
- tests.run
- Approval Workflow

## Historias

| ID | Historia | Criterio de aceptación |
|---|---|---|
| US-FUNC-43-001 | Como desarrollador, quiero probar un refactor plan en sandbox. | Existe `refactor sandbox` o `refactor execute --sandbox`. |
| US-FUNC-43-002 | Como revisor, quiero ver el ChangeSet del refactor antes de aplicarlo. | El comando produce ChangeSet y reporte. |
| US-FUNC-43-003 | Como auditor, quiero que todo refactor ejecutable requiera aprobación. | Sin approval válido se bloquea. |

## Tareas

| ID | Tarea | Entregable | PASS |
|---|---|---|---|
| FUNC-43-001 | Crear RefactorExecutor | `src/devpilot_core/refactor/executor.py` | Ejecuta refactor solo en sandbox. |
| FUNC-43-002 | Definir plan-to-changeset inicial | `refactor/executor.py` | Convierte pasos seguros en operaciones controladas. |
| FUNC-43-003 | Crear comando `refactor sandbox` | `CLI` | Produce ChangeSet. |
| FUNC-43-004 | Integrar tests.run | `executor` | Corre pruebas si se solicita. |
| FUNC-43-005 | Actualizar MIASI | `tool_registry/policy_matrix` | Tool `refactor.sandbox` declarada. |

## Archivos previstos

```text
src/devpilot_core/refactor/executor.py
tests/test_refactor_executor.py
docs/audits/func_sprint_43_refactor_executor_sandbox_audit.md
docs/functional_sprint_43_manifest.json
```

## Comandos objetivo

```powershell
python -m devpilot_core refactor sandbox --target src/devpilot_core/repo --plan-id <id> --approval-id <id> --json
python -m pytest -q
```

## Criterios PASS

- Refactor execution solo ocurre en sandbox.
- Requiere approval para side effects.
- Produce ChangeSet y rollback plan.
- tests.run puede ejecutarse en sandbox.

## Criterios BLOCK

- No cerrar si modifica workspace real.
- No cerrar si acepta planes ambiguos/no determinísticos.
- No cerrar si omite PolicyEngine.

## Riesgos

| ID | Riesgo | Mitigación |
|---|---|---|
| RISK-FUNC-43-001 | Plan-to-change demasiado complejo | Empezar con operaciones mecánicas y limitadas. |
| RISK-FUNC-43-002 | Falso sentido de seguridad | Exigir revisión humana y tests. |
| RISK-FUNC-43-003 | Conflictos con formato de código | Reportar como warning/pendiente. |

## Pruebas mínimas

- TEST-FUNC-43-001: Refactor simple en fixture sandbox.
- TEST-FUNC-43-002: Sin approval bloquea.
- TEST-FUNC-43-003: Workspace real intacto.
- TEST-FUNC-43-004: ChangeSet + rollback plan generados.

## Prompt operativo sugerido

```text
Implementa FUNC-SPRINT-43: RefactorExecutor controlado en sandbox, limitado a transformaciones mecánicas, con approval, ChangeSet, rollback y tests.
```


# FUNC-SPRINT-44 — Cierre Fase C: repository engineering quality gate

## Objetivo

Consolidar Fase C en un quality gate integral de ingeniería de repositorio y documentar límites antes de pasar a IA local gobernada.

## Entradas

- Sprints 35–43
- RepoQualityGate
- PatchSandbox
- RollbackManager
- RefactorExecutor

## Historias

| ID | Historia | Criterio de aceptación |
|---|---|---|
| US-FUNC-44-001 | Como owner, quiero saber si el repositorio está listo para IA local gobernada. | Existe reporte de cierre Fase C. |
| US-FUNC-44-002 | Como arquitecto, quiero ver capacidades repo implementadas/parciales/pendientes. | El cierre clasifica capacidades. |
| US-FUNC-44-003 | Como auditor, quiero un gate de repositorio reproducible. | Existe `repo engineering-gate --json`. |

## Tareas

| ID | Tarea | Entregable | PASS |
|---|---|---|---|
| FUNC-44-001 | Crear comando `repo engineering-gate` | `quality gate` | Ejecuta GitAdapter, RepoAnalyzer, Drift, ReviewGate. |
| FUNC-44-002 | Crear reporte cierre Fase C | `docs/audits/phase_c_repository_engineering_closure_report.md` | Incluye decisiones, riesgos y brechas. |
| FUNC-44-003 | Actualizar README/runbook | `docs` | Comandos Fase C documentados. |
| FUNC-44-004 | Actualizar backlog siguiente | `docs/backlogs` | Dependencias hacia Fase D. |
| FUNC-44-005 | Crear manifest Fase C | `docs/phase_c_manifest.json` | Resumen máquina-legible. |

## Archivos previstos

```text
src/devpilot_core/repo/engineering_gate.py
tests/test_repo_engineering_gate.py
docs/audits/phase_c_repository_engineering_closure_report.md
docs/phase_c_manifest.json
docs/functional_sprint_44_manifest.json
```

## Comandos objetivo

```powershell
python -m devpilot_core repo engineering-gate --json --write-report
python -m devpilot_core readiness-check --strict --json
python -m devpilot_core miasi validate --json
python -m pytest -q
```

## Criterios PASS

- Gate de ingeniería de repositorio pasa en baseline.
- Reporte de cierre clasifica capacidades C.
- No quedan comandos de ejecución sin approval.
- README/runbook actualizados.

## Criterios BLOCK

- No cerrar si patch/refactor pueden tocar workspace real sin approval.
- No cerrar si Fase C deja documentación C4/MIASI desactualizada.
- No cerrar si pytest falla.

## Riesgos

| ID | Riesgo | Mitigación |
|---|---|---|
| RISK-FUNC-44-001 | Gate demasiado lento | Permitir perfiles quick/full. |
| RISK-FUNC-44-002 | Dependencias con Fase B incompletas | Marcar como BLOCK si approval/tests.run no existen. |
| RISK-FUNC-44-003 | Cierre incompleto | Checklist de salida obligatorio. |

## Pruebas mínimas

- TEST-FUNC-44-001: Gate quick/full en fixtures.
- TEST-FUNC-44-002: Cierre documental existe.
- TEST-FUNC-44-003: MIASI validate PASS.
- TEST-FUNC-44-004: Regression completa PASS.

## Prompt operativo sugerido

```text
Implementa FUNC-SPRINT-44: cierre Fase C con repository engineering gate, reporte de cierre, manifest y sincronización documental.
```
