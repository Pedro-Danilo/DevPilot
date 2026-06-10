---
title: "DevPilot Local — Backlog ejecutable Fase A: Baseline industrial mínima"
doc_id: "DEVPL-FUNC-BACKLOG-FASE-A-001"
status: "draft-for-review"
version: "0.1.0"
owner: "Ordóñez"
standard: "MIPSoftware"
extension: "MIASI"
phase: "FASE-A-BASELINE-INDUSTRIAL-MINIMA"
updated: "2026-06-10"
source_repo: "repo_DevPilot_Local_25.zip"
source_report: "Informe de avance DevPilot - sprint 0 - 18.docx"
source_backlog_model: "docs/functional_backlog_after_precode.md"
baseline_previous_sprint: "FUNC-SPRINT-20"
first_sprint: "FUNC-SPRINT-19"
last_planned_sprint: "FUNC-SPRINT-27"
change_policy: "controlled_changes_allowed_via_docs_as_code"
approval_scope: "phase_a_executable_backlog_review"
first_open_sprint: "FUNC-SPRINT-22"
---

# DevPilot Local — Backlog ejecutable Fase A: Baseline industrial mínima

## Estado de aprobación funcional

Este documento se entrega en estado `draft-for-review`. Su propósito es convertir la **Fase A — Baseline industrial mínima** en un backlog de implementación ejecutable, siguiendo el mismo modelo operativo usado en `docs/functional_backlog_after_precode.md`.

La Fase A agrupa:

- **Ola 0 — Cierre y estabilización del ciclo 00–18**.
- **Ola 1 — Consolidación contractual y Schema Engine**.
- **Ola 2 — Trazabilidad SDLC ejecutable**.

La fase parte del estado real de `repo_DevPilot_Local_22.zip`, donde DevPilot ya cuenta con core CLI local-first, validadores, readiness strict, Standards Registry, PolicyEngine, MIASI executable registry, agentes documentales iniciales, Evaluation Harness, Git read-only, RepoInventory, Patch/Code Review en dry-run, Safe Refactor Planner plan-only, ModelAdapter mock y ApplicationService para futura UI.

## 1. Propósito

Este backlog define los sprints necesarios para transformar el cierre del primer ciclo funcional de DevPilot en una **baseline industrial mínima**: reconciliada, versionada, contractualmente validable y trazable de extremo a extremo.

En lenguaje operativo, esta fase busca que DevPilot deje de ser únicamente un core funcional con documentación amplia y pase a tener una base industrial verificable mediante:

- release interno limpio;
- documentación reconciliada;
- schemas versionados;
- validación estructural de contratos;
- manifests verificables;
- trazabilidad ejecutable entre producto, requisitos, arquitectura, pruebas y evidencias;
- cierre formal del ciclo 00–18.

## 2. Regla central de Fase A

Fase A no debe introducir automatización destructiva, agentes autónomos, APIs externas reales, UI productiva ni ejecución de cambios sobre repositorios. Su propósito es fortalecer el **contrato de ingeniería** antes de ampliar el poder operativo de DevPilot.

Reglas obligatorias:

1. Todo nuevo contrato debe tener schema o quedar marcado explícitamente como pendiente de schema.
2. Todo nuevo comando debe devolver `CommandResult`.
3. Todo nuevo comando debe soportar `--json`; `--write-report` cuando aplique.
4. Todo nuevo reporte debe generarse bajo `outputs/reports/`.
5. Todo cambio documental debe actualizar README, runbook, backlog y ADR si aplica.
6. Ningún output runtime debe formar parte del ZIP/release limpio.
7. Ningún sprint puede cerrar con pruebas rotas.
8. Ninguna regla de trazabilidad debe modificar artefactos: solo validar, reportar y sugerir.
9. Los schemas no sustituyen reglas de negocio: las complementan.

## 3. Alcance de Fase A

Fase A implementa capacidades de consolidación, contratos y trazabilidad. Incluye:

- cierre formal del ciclo funcional `FUNC-SPRINT-00` a `FUNC-SPRINT-18`;
- release técnico interno v0.1.0;
- reconciliación documental post-18;
- Schema Registry;
- Schema Validator;
- schemas para contratos internos;
- schemas para MIASI, workspace, providers y manifests;
- transición de perfiles hardcoded hacia perfiles configurables;
- ValidationGateway inicial;
- Traceability Model;
- Traceability Engine;
- reportes de cobertura SDLC;
- drift inicial arquitectura/código;
- checklist de salida de Baseline Industrial Mínima.

No incluye:

- approval workflow;
- `tests.run`;
- patch apply;
- refactor execution;
- UI real;
- APIs externas;
- modelos locales reales;
- multiagentes;
- RAG;
- MCP;
- CI/CD remoto.

## 4. Niveles de implementación de Fase A

| Nivel | Nombre | Objetivo | Estado esperado al cierre |
|---|---|---|---|
| FA-L0 | Cierre formal | Consolidar ciclo 00–18 como baseline verificable | Release técnico interno y documentación reconciliada |
| FA-L1 | Contratos versionados | Formalizar contratos JSON/Markdown centrales | Schema Registry + schemas base |
| FA-L2 | Validación de contratos | Validar instancias y manifests | Schema Validator operativo |
| FA-L3 | Validación transversal | Unificar ejecución de validadores | ValidationGateway inicial |
| FA-L4 | Trazabilidad SDLC | Conectar producto, requisitos, arquitectura, pruebas y evidencia | Traceability Engine y reportes |
| FA-L5 | Baseline industrial mínima | Cierre auditado de Fase A | Criterios de salida documentados y verificables |

## 5. Definition of Done transversal

Un sprint de Fase A solo puede cerrarse si cumple:

- código integrado en `src/devpilot_core/` cuando aplique;
- documentación actualizada en `README.md` y `docs/05_operations/runbook.md` si agrega comandos o procedimientos;
- auditoría del sprint en `docs/audits/`;
- manifiesto JSON del sprint en `docs/functional_sprint_XX_manifest.json`;
- pruebas nuevas o actualizadas en `tests/`;
- comandos objetivo ejecutables con `--json`;
- reportes con `--write-report` cuando aplique;
- sin dependencias externas obligatorias salvo que estén justificadas por ADR;
- sin llamadas de red;
- sin API keys;
- sin outputs versionados;
- `python -m pytest -q` en PASS;
- actualización de MIASI si se agregan tools, policies o agentes;
- actualización de ADR si se introduce arquitectura, dependencia o política nueva.

## 6. Convenciones de IDs

| Tipo | Prefijo | Ejemplo |
|---|---|---|
| Sprint funcional | `FUNC-SPRINT-XX` | `FUNC-SPRINT-21` |
| Historia | `US-FUNC-XX-YYY` | `US-FUNC-21-001` |
| Tarea | `FUNC-XX-YYY` | `FUNC-21-003` |
| Prueba | `TEST-FUNC-XX-YYY` | `TEST-FUNC-21-002` |
| Gate | `GATE-FUNC-XX` | `GATE-FUNC-21` |
| Riesgo | `RISK-FUNC-XX-YYY` | `RISK-FUNC-21-001` |
| Schema | `SCHEMA-DEVPL-*` | `SCHEMA-DEVPL-COMMAND-RESULT-V1` |
| Trazabilidad | `TRACE-*` | `TRACE-REQ-TO-TEST` |

## 7. Roadmap funcional de Fase A

| Ola | Sprints | Resultado esperado |
|---|---|---|
| Ola 0 | FUNC-SPRINT-19 a 20 | Ciclo 00–18 cerrado, documentación reconciliada y release técnico interno |
| Ola 1 | FUNC-SPRINT-21 a 24 | Contratos y schemas versionados, validables y listables |
| Ola 2 | FUNC-SPRINT-25 a 27 | Trazabilidad SDLC ejecutable y baseline industrial mínima cerrada |

---

# FUNC-SPRINT-19 — Cierre formal del ciclo 00–18 y release técnico interno

## Objetivo

Crear el cierre formal del ciclo `FUNC-SPRINT-00` a `FUNC-SPRINT-18`, dejando un release técnico interno limpio, reproducible y auditable.

## Estado

`implemented` el 2026-06-10 mediante `docs/audits/functional_cycle_00_18_closure_report.md`, `docs/release/release_manifest_v0.1.0.json`, `docs/release/release_notes_v0.1.0.md`, `docs/functional_sprint_19_manifest.json`, `scripts/verify_release_v0_1_0.py` y `tests/test_release_manifest.py`.


## Entradas

- `repo_DevPilot_Local_22.zip`.
- `Informe de avance DevPilot - sprint 0 - 18.docx`.
- `docs/functional_backlog_after_precode.md`.
- `Log_consola_sprint_18.txt`.
- Manifests `docs/functional_sprint_00_manifest.json` a `docs/functional_sprint_18_manifest.json`.

## Historias

| ID | Historia | Criterio de aceptación |
|---|---|---|
| US-FUNC-19-001 | Como arquitecto, quiero un cierre formal del ciclo 00–18 para transferir el proyecto sin depender de conversaciones previas. | Existe `functional_cycle_00_18_closure_report.md`. |
| US-FUNC-19-002 | Como desarrollador, quiero un release técnico interno limpio para instalar y verificar DevPilot. | Existe release manifest con checksums y comandos de verificación. |
| US-FUNC-19-003 | Como auditor, quiero saber exactamente qué capacidades quedaron implementadas, parciales, planeadas y futuras. | El reporte clasifica capacidades por estado. |

## Tareas

| ID | Tarea | Entregable | PASS |
|---|---|---|---|
| FUNC-19-001 | Crear reporte de cierre ciclo 00–18 | `docs/audits/functional_cycle_00_18_closure_report.md` | Incluye capacidades, pruebas, riesgos, deuda y brechas. |
| FUNC-19-002 | Crear release manifest v0.1.0 | `docs/release/release_manifest_v0.1.0.json` | Incluye versión, fuentes, checksums, exclusiones y comandos smoke. |
| FUNC-19-003 | Crear release notes v0.1.0 | `docs/release/release_notes_v0.1.0.md` | Resume cambios funcionales y límites. |
| FUNC-19-004 | Crear script o comando de verificación de release interno | script o documentación operativa | Ejecuta versión, pytest, readiness, MIASI, eval, app contract. |
| FUNC-19-005 | Asegurar exclusión de outputs/runtime | `.gitignore` y/o script de cleanup | `outputs/`, `.pytest_cache`, `__pycache__`, `.devpilot/devpilot.db` no van al ZIP limpio. |
| FUNC-19-006 | Actualizar README/runbook | docs sincronizados | README y runbook indican último hito real y comandos de release interno. |

## Archivos previstos

```text
docs/audits/functional_cycle_00_18_closure_report.md
docs/release/release_manifest_v0.1.0.json
docs/release/release_notes_v0.1.0.md
docs/functional_sprint_19_manifest.json
README.md
docs/05_operations/runbook.md
tests/test_release_manifest.py
```

## Comandos objetivo

```powershell
python -m devpilot_core --version
python -m pytest -q
python -m devpilot_core workspace status --json
python -m devpilot_core readiness-check --strict --json
python -m devpilot_core miasi validate --json
python -m devpilot_core eval run --json
python -m devpilot_core app contract --json
```

## Criterios PASS

```text
Existe reporte de cierre 00–18.
Existe manifest de release técnico interno.
El release manifest no referencia outputs runtime como fuente.
Los comandos smoke están documentados.
pytest -q pasa.
README y runbook quedan sincronizados.
```

## Criterios BLOCK

```text
El release incluye outputs runtime o .devpilot/devpilot.db.
La documentación afirma capacidades no implementadas como implementadas.
Falta trazabilidad entre release y sprints 00–18.
pytest falla.
```

## Riesgos y límites

- Este sprint no crea nuevas capacidades funcionales del core.
- La release v0.1.0 es técnica/interna, no distribución productiva final.
- Los checksums no reemplazan firma criptográfica ni supply-chain security.

## Pruebas

```text
tests/test_release_manifest.py
Smoke test manual documentado en runbook.
pytest -q
```

## Prompt operativo

```text
Implementa FUNC-SPRINT-19: cierre formal del ciclo 00–18 y release técnico interno v0.1.0. No agregues capacidades de negocio nuevas. Produce reporte de cierre, release manifest, release notes, pruebas de manifest y sincronización README/runbook. Excluye outputs/runtime.
```

---

# FUNC-SPRINT-20 — Reconciliación documental post-18 y roadmap vivo

## Objetivo

Corregir desalineaciones entre README, roadmap, backlog, C4, runbook y estado real del código, dejando una vista clara para Fase A/B/C.

## Historias

| ID | Historia | Criterio de aceptación |
|---|---|---|
| US-FUNC-20-001 | Como nuevo desarrollador, quiero distinguir capacidades implementadas, parciales, planeadas, bloqueadas y futuras. | Existe matriz reconciliada de capacidades. |
| US-FUNC-20-002 | Como arquitecto, quiero que el roadmap histórico no contradiga el backlog actualizado. | Existe `roadmap_reconciliation_after_sprint_18.md`. |
| US-FUNC-20-003 | Como operador, quiero comandos actuales documentados sin nombres históricos incorrectos. | README/runbook usan nombres reales de CLI. |

## Tareas

| ID | Tarea | Entregable | PASS |
|---|---|---|---|
| FUNC-20-001 | Crear matriz de estado de capacidades | `docs/audits/capability_status_matrix_after_sprint_18.md` | Clasifica implemented/partial/planned/disabled/future. |
| FUNC-20-002 | Reconciliar roadmap histórico | `docs/audits/roadmap_reconciliation_after_sprint_18.md` | Mapea nombres planeados vs comandos reales. |
| FUNC-20-003 | Actualizar README | `README.md` | Elimina pendientes obsoletos y marca límites reales. |
| FUNC-20-004 | Actualizar runbook | `docs/05_operations/runbook.md` | Incluye comandos actuales agrupados por dominio. |
| FUNC-20-005 | Actualizar C4 Context/Container | docs de arquitectura | Marca nodos implemented/partial/planned/disabled/future. |
| FUNC-20-006 | Crear o planear `c4_component.md` | `docs/02_architecture/c4_component.md` | Representa el core real del repo 22/23. |

## Archivos previstos

```text
docs/audits/capability_status_matrix_after_sprint_18.md
docs/audits/roadmap_reconciliation_after_sprint_18.md
docs/02_architecture/c4_context.md
docs/02_architecture/c4_container.md
docs/02_architecture/c4_component.md
README.md
docs/05_operations/runbook.md
docs/functional_sprint_20_manifest.json
```

## Comandos objetivo

```powershell
python -m devpilot_core --version
python -m devpilot_core readiness-check --strict --json
python -m devpilot_core validate-artifact docs/02_architecture/c4_component.md --json
python -m pytest -q
```

## Criterios PASS

```text
No quedan nombres de comandos planeados presentados como implementados si no existen.
El roadmap queda marcado como histórico + reconciliado.
C4 distingue explícitamente estado real vs objetivo.
README y runbook quedan sincronizados.
pytest -q pasa.
```

## Criterios BLOCK

```text
La documentación sobredeclara capacidades agentic no implementadas.
Se documenta UI real cuando solo existe app contract.
Se documenta ModelAdapter local/API real cuando solo existe mock y placeholders.
```

## Riesgos y límites

- La reconciliación documental no sustituye implementación.
- Debe preservarse la historia del roadmap; no borrar intención original sin trazabilidad.

## Pruebas

```text
Validación de frontmatter/artefactos documentales modificados.
Smoke test de comandos documentados.
pytest -q.
```

## Prompt operativo

```text
Implementa FUNC-SPRINT-20: reconciliación documental post-18. Actualiza README, runbook, C4 y roadmap sin crear capacidades nuevas. Marca estados implemented, partial, planned, disabled y future. Mantén trazabilidad histórica.
```

---


## Estado de implementación Sprint 20

`FUNC-SPRINT-20` queda implementado como reconciliación documental post-18. No introduce capacidades de core ni comandos nuevos. Sus entregables verificables son:

```text
docs/audits/capability_status_matrix_after_sprint_18.md
docs/audits/roadmap_reconciliation_after_sprint_18.md
docs/02_architecture/c4_component.md
docs/functional_sprint_20_manifest.json
tests/test_sprint_20_documentation_reconciliation.py
```

El siguiente sprint abierto de Fase A es `FUNC-SPRINT-21 — Schema Registry y catálogo de contratos DevPilot`.

---

# FUNC-SPRINT-21 — Schema Registry y catálogo de contratos DevPilot

## Objetivo

Crear un registro local de schemas para contratos internos de DevPilot, sin validar todavía todas las instancias de forma profunda.

## Historias

| ID | Historia | Criterio de aceptación |
|---|---|---|
| US-FUNC-21-001 | Como desarrollador, quiero listar schemas disponibles para saber qué contratos están formalizados. | `schema list --json` devuelve schemas registrados. |
| US-FUNC-21-002 | Como arquitecto, quiero versionar contratos para evitar ruptura silenciosa de CLI/UI/API futura. | Cada schema tiene `schema_id`, versión, ruta y estado. |

## Tareas

| ID | Tarea | Entregable | PASS |
|---|---|---|---|
| FUNC-21-001 | Crear paquete `schemas` | `src/devpilot_core/schemas/` | Módulo importable. |
| FUNC-21-002 | Crear `SchemaSpec` y `SchemaRegistry` | modelos/registry | Lista schemas locales. |
| FUNC-21-003 | Crear carpeta de schemas | `docs/schemas/` o `docs/standards/devpilot/schemas/` | Contiene catálogo inicial. |
| FUNC-21-004 | Crear comando `schema list` | CLI | JSON parseable con schemas. |
| FUNC-21-005 | Crear tests de registry | pytest | Detecta schemas faltantes/duplicados. |
| FUNC-21-006 | Documentar en README/runbook | docs | Comandos y límites documentados. |

## Schemas iniciales previstos

```text
command_result.schema.json
finding.schema.json
evidence_report.schema.json
application_request.schema.json
application_response.schema.json
service_capability.schema.json
interface_route_contract.schema.json
```

## Archivos previstos

```text
src/devpilot_core/schemas/__init__.py
src/devpilot_core/schemas/models.py
src/devpilot_core/schemas/registry.py
docs/schemas/schema_catalog.json
docs/schemas/*.schema.json
tests/test_schema_registry.py
docs/audits/func_sprint_21_schema_registry_audit.md
docs/functional_sprint_21_manifest.json
README.md
docs/05_operations/runbook.md
```

## Comandos objetivo

```powershell
python -m devpilot_core schema list --json
python -m devpilot_core schema list --json --write-report
python -m pytest -q
```

## Criterios PASS

```text
schema list devuelve CommandResult.
Todos los schemas del catálogo existen.
No hay schema_id duplicado.
Cada schema tiene versión y descripción.
No se introduce dependencia externa todavía.
pytest -q pasa.
```

## Criterios BLOCK

```text
Un schema listado no existe.
Hay IDs duplicados.
El comando no devuelve JSON válido.
El catálogo rompe local-first o requiere red.
```

## Riesgos y límites

- Sprint 21 solo registra schemas; no valida instancias complejas.
- Puede usarse validación mínima con biblioteca estándar, pero validación JSON Schema completa queda para Sprint 22.
- Si se decide agregar `jsonschema` como dependencia, debe abrirse ADR antes de implementarla.

## Pruebas

```text
tests/test_schema_registry.py
Pruebas de CLI JSON.
Pruebas de catálogo duplicado en tempdir.
```

## Prompt operativo

```text
Implementa FUNC-SPRINT-21: Schema Registry local para contratos DevPilot. Debe listar schemas versionados, no requerir red, devolver CommandResult, generar reporte opcional y quedar documentado en README/runbook.
```

## Estado de implementación Sprint 21

`FUNC-SPRINT-21` queda implementado como Schema Registry inicial. Entregables principales:

- `src/devpilot_core/schemas/` con `SchemaSpec`, `SchemaRegistrySummary` y `SchemaRegistry`;
- `docs/schemas/schema_catalog.json`;
- siete schemas iniciales para `CommandResult`, `Finding`, `EvidenceReport`, `ApplicationRequest`, `ApplicationResponse`, `ServiceCapability` e `InterfaceRouteContract`;
- comando `python -m devpilot_core schema list --json`;
- soporte de `--write-report`;
- `tests/test_schema_registry.py`;
- `docs/audits/func_sprint_21_schema_registry_audit.md`;
- `docs/functional_sprint_21_manifest.json`.

Límite explícito: Sprint 21 no valida instancias JSON. `FUNC-SPRINT-22` debe implementar `schema validate`.

El siguiente sprint abierto de Fase A es `FUNC-SPRINT-22 — Schema Validator y schemas de contratos transversales`.

---

# FUNC-SPRINT-22 — Schema Validator y schemas de contratos transversales

## Objetivo

Implementar validación de instancias JSON contra schemas para los contratos transversales de DevPilot.

## Historias

| ID | Historia | Criterio de aceptación |
|---|---|---|
| US-FUNC-22-001 | Como desarrollador, quiero validar un reporte JSON contra su schema. | `schema validate` devuelve PASS/BLOCK con findings. |
| US-FUNC-22-002 | Como integrador de futura UI, quiero estabilidad de `ApplicationResponse`. | Existen schemas y pruebas para DTOs. |

## Tareas

| ID | Tarea | Entregable | PASS |
|---|---|---|---|
| FUNC-22-001 | Crear `SchemaValidator` | `validator.py` | Valida instancias contra schemas. |
| FUNC-22-002 | Definir estrategia de dependencia | ADR o implementación stdlib limitada | Decisión documentada. |
| FUNC-22-003 | Validar `CommandResult` | schema + tests | Reporte de readiness cumple schema. |
| FUNC-22-004 | Validar `Finding` | schema + tests | Hallazgos válidos/invalidos detectados. |
| FUNC-22-005 | Validar `ApplicationResponse` | schema + tests | `app contract` puede mapearse a schema. |
| FUNC-22-006 | Crear comando `schema validate` | CLI | Acepta `--schema`, `--instance`, `--json`. |

## Archivos previstos

```text
src/devpilot_core/schemas/validator.py
src/devpilot_core/schemas/errors.py
docs/02_architecture/adrs/ADR-0010-schema-validation-dependency.md  # si aplica
docs/schemas/command_result.schema.json
docs/schemas/finding.schema.json
docs/schemas/application_response.schema.json
tests/test_schema_validator.py
docs/audits/func_sprint_22_schema_validator_audit.md
docs/functional_sprint_22_manifest.json
README.md
docs/05_operations/runbook.md
```

## Comandos objetivo

```powershell
python -m devpilot_core schema validate --schema docs/schemas/command_result.schema.json --instance outputs/reports/readiness_check.json --json
python -m devpilot_core schema validate --schema docs/schemas/application_response.schema.json --instance outputs/reports/app_contract.json --json
python -m pytest -q
```

## Criterios PASS

```text
Instancias válidas pasan.
Instancias inválidas generan findings accionables.
El validador no oculta errores de parseo.
El comando no requiere red.
Los errores se convierten a CommandResult.
pytest -q pasa.
```

## Criterios BLOCK

```text
El validador acepta instancias inválidas sin findings.
El validador falla con stacktrace no controlado.
Se agrega dependencia externa sin ADR.
```

## Riesgos y límites

- Validación estructural no equivale a validación semántica.
- JSON Schema no reemplaza reglas de negocio de MIASI, readiness o policy.

## Pruebas

```text
tests/test_schema_validator.py
fixtures JSON válidos e inválidos.
CLI parseable.
```

## Prompt operativo

```text
Implementa FUNC-SPRINT-22: SchemaValidator para validar instancias JSON contra schemas de contratos transversales. Mantén local-first, CommandResult, findings claros y tests con fixtures válidos/invalidos.
```

---

# FUNC-SPRINT-23 — Schemas MIASI, Workspace, Providers y Sprint Manifests

## Objetivo

Formalizar y validar los contratos estructurales más críticos del sistema: MIASI registries, workspace config, provider metadata y sprint manifests.

## Historias

| ID | Historia | Criterio de aceptación |
|---|---|---|
| US-FUNC-23-001 | Como arquitecto, quiero validar `.devpilot/project.yaml` contra un contrato formal. | Existe schema y comando de validación workspace config. |
| US-FUNC-23-002 | Como supervisor MIASI, quiero validar agent/tool/policy registries estructuralmente antes de reglas de negocio. | MIASI JSON cumple schemas. |
| US-FUNC-23-003 | Como auditor, quiero validar manifests de sprint. | Los manifests tienen estructura esperada. |

## Tareas

| ID | Tarea | Entregable | PASS |
|---|---|---|---|
| FUNC-23-001 | Crear schemas MIASI | JSON schemas | Agent/Tool/Policy registry validables. |
| FUNC-23-002 | Crear schema workspace | `workspace_project.schema.json` | `.devpilot/project.yaml` validable tras conversión/parse. |
| FUNC-23-003 | Crear schema providers | `provider_config.schema.json` | Providers example cumple schema. |
| FUNC-23-004 | Crear schema sprint manifest | `functional_sprint_manifest.schema.json` | Manifests 19+ validables. |
| FUNC-23-005 | Integrar validaciones específicas | CLI | `schema validate-miasi`, `schema validate-workspace`, `schema validate-manifest`. |
| FUNC-23-006 | Tests de drift estructural | pytest | IDs faltantes/campos erróneos detectados. |

## Archivos previstos

```text
docs/schemas/miasi_agent_registry.schema.json
docs/schemas/miasi_tool_registry.schema.json
docs/schemas/miasi_policy_matrix.schema.json
docs/schemas/workspace_project.schema.json
docs/schemas/provider_config.schema.json
docs/schemas/functional_sprint_manifest.schema.json
src/devpilot_core/schemas/builtins.py
tests/test_contract_schemas.py
docs/audits/func_sprint_23_contract_schemas_audit.md
docs/functional_sprint_23_manifest.json
```

## Comandos objetivo

```powershell
python -m devpilot_core schema validate-miasi --json
python -m devpilot_core schema validate-workspace --json
python -m devpilot_core schema validate-manifest docs/functional_sprint_23_manifest.json --json
python -m pytest -q
```

## Criterios PASS

```text
MIASI registries pasan schema antes de reglas de negocio.
Workspace config pasa validación estructural.
providers.yaml.example pasa schema sin secretos reales.
Manifests de sprint nuevos pasan schema.
pytest -q pasa.
```

## Criterios BLOCK

```text
Un contrato crítico carece de schema.
Se aceptan providers con secretos reales.
Los manifests no declaran archivos creados/modificados/comandos/pruebas.
```

## Riesgos y límites

- El parser YAML actual es mínimo; si se requiere YAML completo, abrir ADR para PyYAML.
- La validación de schema no sustituye validación MIASI de negocio.

## Pruebas

```text
tests/test_contract_schemas.py
Validación con registries reales.
Validación con fixtures inválidos.
```

## Prompt operativo

```text
Implementa FUNC-SPRINT-23: schemas para MIASI, Workspace, Providers y Sprint Manifests. Integra comandos específicos de validación estructural y conserva validaciones de negocio existentes.
```

---

# FUNC-SPRINT-24 — Artifact Profiles data-driven y ValidationGateway inicial

## Objetivo

Reducir hardcoding de perfiles documentales y crear una fachada unificada para validaciones.

## Historias

| ID | Historia | Criterio de aceptación |
|---|---|---|
| US-FUNC-24-001 | Como arquitecto, quiero que los perfiles documentales puedan versionarse como datos. | Existe `artifact_profiles.json` validado por schema. |
| US-FUNC-24-002 | Como integrador, quiero ejecutar validaciones desde un gateway unificado. | Existe `validate all/docs/contracts` con CommandResult. |

## Tareas

| ID | Tarea | Entregable | PASS |
|---|---|---|---|
| FUNC-24-001 | Exportar perfiles actuales a JSON | `docs/validation/artifact_profiles.json` | Equivalente a perfiles Python existentes. |
| FUNC-24-002 | Crear schema de perfiles | `artifact_profiles.schema.json` | Valida perfiles. |
| FUNC-24-003 | Crear `ArtifactProfileRegistry` | módulo | Carga perfiles JSON con fallback seguro. |
| FUNC-24-004 | Crear `ValidationGateway` | módulo | Orquesta frontmatter, artifact, checklist, standards, schemas. |
| FUNC-24-005 | Crear comandos `validate docs/contracts/all` | CLI | Ejecutan grupos de validación. |
| FUNC-24-006 | Tests de compatibilidad | pytest | Resultados equivalentes a perfiles anteriores. |

## Archivos previstos

```text
src/devpilot_core/validation/__init__.py
src/devpilot_core/validation/gateway.py
src/devpilot_core/validation/artifact_profile_registry.py
docs/validation/artifact_profiles.json
docs/schemas/artifact_profiles.schema.json
tests/test_validation_gateway.py
tests/test_artifact_profile_registry.py
docs/audits/func_sprint_24_validation_gateway_audit.md
docs/functional_sprint_24_manifest.json
```

## Comandos objetivo

```powershell
python -m devpilot_core validate docs --json
python -m devpilot_core validate contracts --json
python -m devpilot_core validate all --json --write-report
python -m pytest -q
```

## Criterios PASS

```text
Los perfiles JSON cubren los perfiles actuales.
El gateway no duplica lógica ni rompe validadores existentes.
validate all produce resumen consolidado.
Los warnings no bloqueantes se conservan como warnings.
pytest -q pasa.
```

## Criterios BLOCK

```text
Cambiar perfiles rompe readiness strict.
El gateway oculta findings de validadores internos.
Se elimina compatibilidad con artifact_profiles.py sin migración.
```

## Riesgos y límites

- La migración debe ser conservadora.
- Puede mantenerse fallback Python hasta que perfiles JSON estén estabilizados.

## Pruebas

```text
tests/test_validation_gateway.py
tests/test_artifact_profile_registry.py
Comparación de findings antes/después.
```

## Prompt operativo

```text
Implementa FUNC-SPRINT-24: Artifact Profiles data-driven y ValidationGateway inicial. Migra perfiles a JSON validado sin romper compatibilidad ni readiness. Agrega validate docs/contracts/all.
```

---

# FUNC-SPRINT-25 — Traceability Model y extracción de entidades SDLC

## Objetivo

Crear el modelo de datos y extractores mínimos para identificar entidades de trazabilidad en documentos SDLC.

## Historias

| ID | Historia | Criterio de aceptación |
|---|---|---|
| US-FUNC-25-001 | Como arquitecto, quiero extraer requisitos, criterios, pruebas y artefactos desde docs. | El extractor produce entidades trazables. |
| US-FUNC-25-002 | Como auditor, quiero detectar IDs duplicados o mal formados. | Findings reportan duplicados o IDs inválidos. |

## Tareas

| ID | Tarea | Entregable | PASS |
|---|---|---|---|
| FUNC-25-001 | Crear paquete `traceability` | módulo | Importable. |
| FUNC-25-002 | Crear modelos `TraceEntity`, `TraceLink`, `TraceGraph` | dataclasses | Serializables a JSON. |
| FUNC-25-003 | Crear extractor Markdown conservador | parser | Extrae IDs `FR-*`, `REQ-*`, `US-*`, `AC-*`, `TEST-*`, `ADR-*`. |
| FUNC-25-004 | Crear comando `traceability scan` | CLI | Lista entidades detectadas. |
| FUNC-25-005 | Tests con fixtures | pytest | Detecta IDs y duplicados. |

## Archivos previstos

```text
src/devpilot_core/traceability/__init__.py
src/devpilot_core/traceability/models.py
src/devpilot_core/traceability/extractors.py
src/devpilot_core/traceability/graph.py
tests/test_traceability_extractors.py
docs/audits/func_sprint_25_traceability_model_audit.md
docs/functional_sprint_25_manifest.json
```

## Comandos objetivo

```powershell
python -m devpilot_core traceability scan --json
python -m devpilot_core traceability scan --json --write-report
python -m pytest -q
```

## Criterios PASS

```text
Extrae entidades desde requirements, acceptance criteria, use cases, test strategy, ADRs y manifests.
Detecta IDs duplicados.
Produce CommandResult.
No modifica documentos.
pytest -q pasa.
```

## Criterios BLOCK

```text
El extractor inventa relaciones no presentes.
El comando modifica documentos.
No hay findings para IDs duplicados.
```

## Riesgos y límites

- La extracción es heurística y conservadora.
- No debe inferir relaciones semánticas complejas todavía.

## Pruebas

```text
tests/test_traceability_extractors.py
fixtures con IDs válidos, inválidos y duplicados.
```

## Prompt operativo

```text
Implementa FUNC-SPRINT-25: modelos de trazabilidad y extracción conservadora de entidades SDLC desde Markdown. No infieras relaciones complejas todavía; solo extrae, normaliza y reporta duplicados.
```

---

# FUNC-SPRINT-26 — Traceability Engine: validate, coverage y report

## Objetivo

Construir el motor ejecutable de trazabilidad SDLC con validación, cobertura y reportes.

## Historias

| ID | Historia | Criterio de aceptación |
|---|---|---|
| US-FUNC-26-001 | Como owner, quiero saber qué requisitos no tienen criterio de aceptación. | `traceability validate` reporta gaps. |
| US-FUNC-26-002 | Como QA, quiero saber qué requisitos no tienen prueba/eval asociada. | `traceability coverage` muestra cobertura. |
| US-FUNC-26-003 | Como arquitecto, quiero evidencias trazables por requisito. | `traceability report` genera JSON/Markdown. |

## Tareas

| ID | Tarea | Entregable | PASS |
|---|---|---|---|
| FUNC-26-001 | Crear `TraceabilityEngine` | módulo | Construye grafo de entidades y enlaces. |
| FUNC-26-002 | Implementar reglas de cobertura | reglas | Req→AC, Req→Test/Eval, Req→Doc. |
| FUNC-26-003 | Implementar `traceability validate` | CLI | Devuelve findings para gaps. |
| FUNC-26-004 | Implementar `traceability coverage` | CLI | Métricas por tipo de entidad. |
| FUNC-26-005 | Implementar `traceability report` | CLI/report | JSON/Markdown. |
| FUNC-26-006 | Tests con repo real y fixtures | pytest | Detecta gaps sin falsos críticos. |

## Archivos previstos

```text
src/devpilot_core/traceability/engine.py
src/devpilot_core/traceability/rules.py
src/devpilot_core/traceability/reports.py
tests/test_traceability_engine.py
docs/audits/func_sprint_26_traceability_engine_audit.md
docs/functional_sprint_26_manifest.json
README.md
docs/05_operations/runbook.md
```

## Comandos objetivo

```powershell
python -m devpilot_core traceability validate --json
python -m devpilot_core traceability coverage --json
python -m devpilot_core traceability report --json --write-report
python -m pytest -q
```

## Criterios PASS

```text
Detecta requisitos sin criterios.
Detecta criterios sin requisito.
Detecta requisitos sin prueba/eval cuando aplique.
Genera métricas de cobertura.
Reporta gaps como findings accionables.
pytest -q pasa.
```

## Criterios BLOCK

```text
El motor bloquea por gaps recomendados que aún deben ser warning.
El reporte no es reproducible.
El comando falla si un documento opcional no existe.
```

## Riesgos y límites

- El primer motor prioriza cobertura explícita, no razonamiento semántico.
- Las reglas de severidad deben ser configurables en fases futuras.

## Pruebas

```text
tests/test_traceability_engine.py
fixtures de cobertura completa/incompleta.
Smoke sobre docs reales.
```

## Prompt operativo

```text
Implementa FUNC-SPRINT-26: Traceability Engine con validate, coverage y report. Debe conectar requisitos, criterios, pruebas/evals y evidencias documentales con findings claros y reportes JSON/Markdown.
```

---

# FUNC-SPRINT-27 — Architecture/code drift inicial y cierre de Baseline Industrial Mínima

## Objetivo

Agregar una primera validación de drift arquitectura/código y cerrar formalmente Fase A con criterios verificables.

## Historias

| ID | Historia | Criterio de aceptación |
|---|---|---|
| US-FUNC-27-001 | Como arquitecto, quiero detectar si módulos implementados no aparecen en arquitectura. | `architecture-drift` reporta gaps iniciales. |
| US-FUNC-27-002 | Como owner, quiero cerrar Fase A con evidencia. | Existe reporte de cierre de Baseline Industrial Mínima. |

## Tareas

| ID | Tarea | Entregable | PASS |
|---|---|---|---|
| FUNC-27-001 | Crear detector inicial architecture/code drift | módulo o subcomando | Compara módulos `src/devpilot_core/*` vs C4/component docs. |
| FUNC-27-002 | Integrar con Traceability Engine | findings | Drift aparece como finding no destructivo. |
| FUNC-27-003 | Crear checklist de salida Fase A | `docs/checklists/checklist_phase_a_exit.md` | Define PASS/BLOCK de Fase A. |
| FUNC-27-004 | Crear reporte de cierre Fase A | `docs/audits/phase_a_baseline_industrial_minima_closure_report.md` | Resume sprints 19–27. |
| FUNC-27-005 | Actualizar backlog next phase | docs | `next_sprint` apunta a Fase B. |
| FUNC-27-006 | Tests y smoke final | pytest | Todos los comandos Fase A pasan. |

## Archivos previstos

```text
src/devpilot_core/traceability/architecture_drift.py
tests/test_architecture_drift.py
docs/checklists/checklist_phase_a_exit.md
docs/audits/phase_a_baseline_industrial_minima_closure_report.md
docs/functional_sprint_27_manifest.json
README.md
docs/05_operations/runbook.md
```

## Comandos objetivo

```powershell
python -m devpilot_core traceability architecture-drift --json
python -m devpilot_core validate all --json
python -m devpilot_core traceability report --json --write-report
python -m devpilot_core readiness-check --strict --json
python -m devpilot_core miasi validate --json
python -m pytest -q
```

## Criterios PASS

```text
Existe checklist de salida Fase A.
Existe reporte de cierre Fase A.
Architecture drift inicial produce findings no destructivos.
Schemas críticos validan.
Traceability report se genera.
pytest -q pasa.
```

## Criterios BLOCK

```text
Fase A se marca cerrada sin schema validator operativo.
Fase A se marca cerrada sin Traceability Engine ejecutable.
No existe reporte de cierre.
La documentación sigue confundiendo estado real vs objetivo.
```

## Riesgos y límites

- Architecture/code drift inicial será heurístico.
- No reemplaza análisis arquitectónico manual.
- No debe bloquear por diferencias de naming menores sin configuración.

## Pruebas

```text
tests/test_architecture_drift.py
Smoke test completo de Fase A.
pytest -q.
```

## Prompt operativo

```text
Implementa FUNC-SPRINT-27: architecture/code drift inicial y cierre de Baseline Industrial Mínima. Debe producir checklist de salida, reporte de cierre, findings no destructivos y actualizar backlog hacia Fase B.
```

---

## 8. Criterios de salida de Fase A

Fase A se considera terminada si:

```text
1. Existe cierre formal 00–18.
2. README, runbook, roadmap y C4 están reconciliados.
3. Existe release técnico interno limpio.
4. Schema Registry lista contratos críticos.
5. Schema Validator valida instancias críticas.
6. MIASI/workspace/providers/manifests tienen schemas.
7. Artifact profiles pueden cargarse como datos o tienen migración documentada.
8. ValidationGateway ejecuta validaciones agrupadas.
9. Traceability Engine produce validate/coverage/report.
10. Architecture/code drift inicial funciona sin modificar archivos.
11. pytest -q pasa.
12. No se habilitaron acciones destructivas.
```

## 9. Riesgos transversales de Fase A

| ID | Riesgo | Mitigación |
|---|---|---|
| RISK-FA-001 | Intentar convertir schemas en sustituto de reglas de negocio | Mantener separación schema validation vs business validation |
| RISK-FA-002 | Romper validadores existentes al mover perfiles a JSON | Mantener fallback y tests de equivalencia |
| RISK-FA-003 | Sobrecargar traceability con inferencias semánticas tempranas | Primera versión solo explícita/conservadora |
| RISK-FA-004 | Documentar como cerrado algo que solo está parcial | Usar estados implemented/partial/planned/disabled/future |
| RISK-FA-005 | Agregar dependencia externa sin ADR | ADR obligatoria para `jsonschema`, PyYAML u otra dependencia |

## 10. Referencias internas

```text
repo_DevPilot_Local_22.zip
Informe de avance DevPilot - sprint 0 - 18.docx
docs/functional_backlog_after_precode.md
docs/00_product/product_vision.md
docs/00_product/mvp_scope.md
docs/01_requirements/requirements_specification.md
docs/02_architecture/architecture_document.md
docs/02_architecture/c4_context.md
docs/02_architecture/c4_container.md
docs/05_operations/runbook.md
docs/06_miasi/*.md
docs/07_interfaces/internal_application_contract.md
```

## 11. Referencias externas de alineación

```text
NIST SP 800-218 SSDF — Secure Software Development Framework.
JSON Schema — Validation vocabulary and keywords.
OpenTelemetry — Semantic conventions and observability model.
OWASP Top 10 for LLM Applications — prompt injection, sensitive information disclosure, insecure output handling, excessive agency and supply-chain concerns.
```
