---
doc_id: POST-H-031-BACKLOG
title: "POST-H-031 - Observabilidad, evidence graph y operador"
status: approved
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-07-10"
approval: approved
---

# POST-H-031 - Observabilidad, evidence graph y operador

```yaml
doc_id: DEVPL-BACKLOG-POST-H-031-OBSERVABILITY-EVIDENCE-GRAPH-OPERATOR-V1
status: approved
roadmap_wave: "Ola 6"
roadmap_source: "devpilot_post_h_025_roadmap_detallado_v3_agentes_validadores.md"
repo_baseline: "repo_DevPilot_Local_262_POST_H_025_E.zip"
onboarding_report_source: "devpilot_onboarding_report_final_compilado.md"
target_repo_path: "docs/backlogs/POST-H-031_observability_evidence_graph_operator.md"
created_for: "DevPilot Local"
scope: "local-first / read-only by default / operator evidence UX / no overclaims"
implementation_status: "active/implemented-initial-post-h-031-d"
current_micro_sprint: "POST-H-031-D"
next_micro_sprint: "POST-H-031-E"
```

## 1. Proposito del backlog

POST-H-031 convierte la Ola 6 del roadmap post POST-H-025 en un backlog ejecutable orientado a que el operador local pueda entender la salud real de DevPilot, sus gaps, claims permitidos/prohibidos, no-go gates y evidencia disponible sin leer manualmente todo el repo.

La Ola 6 no debe crear un segundo sistema paralelo de observabilidad ni reemplazar POST-H-010, POST-H-015 o POST-H-025. Debe consolidar esas capacidades en una capa de lectura operacional, trazable y explicable:

- POST-H-010 aporta observabilidad, runtime state, retention, hygiene y export redacted.
- POST-H-015 aporta operator dashboard y aggregator local.
- POST-H-025 aporta criteria, evidence map, aggregator, declaration gate, claims validator y final declaration report.
- El repo actual aporta `ApplicationService`, API/UI local inicial, quality gates, traceability y reportes regenerables.

El resultado esperado es un modelo operacional donde DevPilot pueda explicar al operador:

- que evidencia existe;
- que evidencia falta;
- que claims estan permitidos;
- que claims siguen bloqueados;
- que no-go gates estan activos;
- que gaps requieren accion;
- que reportes se pueden exportar de forma segura y redactada;
- que acciones son siguientes, concretas y verificables.

## 2. Fuentes consultadas

Se consultaron como fuentes de verdad para formular este backlog:

- `devpilot_post_h_025_roadmap_detallado_v3_agentes_validadores.md`.
- `devpilot_onboarding_report_final_compilado.md`.
- `repo_DevPilot_Local_262_POST_H_025_E.zip`, descomprimido en entorno local de trabajo.

Evidencia tecnica relevante observada:

- El roadmap define la Ola 6 como `POST-H-031: Observabilidad, evidence graph y operador`.
- El objetivo del roadmap es: hacer que el operador entienda salud, gaps, claims, no-go gates y evidencia sin leer todo el repo.
- El roadmap fija cinco micro-sprints: `POST-H-031-A` a `POST-H-031-E`.
- El repo base contiene `src/devpilot_core/observability`, `src/devpilot_core/runtime_state`, `src/devpilot_core/application/observability_service.py`, `src/devpilot_core/application/operator_dashboard_service.py`, `src/devpilot_core/portfolio/operator_dashboard.py`, `src/devpilot_core/industrial/production_ready.py`, `src/devpilot_core/traceability` y schemas relacionados.
- Ya existen schemas como `operator_dashboard_snapshot.schema.json`, `observability_inventory.schema.json`, `observability_redacted_export.schema.json`, `runtime_state_inventory.schema.json`, `runtime_state_hygiene_report.schema.json`, `production_ready_local_report.schema.json`, `production_ready_local_criteria.schema.json` y `evidence_report.schema.json`.
- Ya existen tests relevantes: `test_observability_inventory.py`, `test_observability_export.py`, `test_observability_cli.py`, `test_observability_hygiene_gate.py`, `test_runtime_state_inventory.py`, `test_runtime_state_export.py`, `test_runtime_state_hygiene.py`, `test_post_h_015_operator_dashboard_aggregator.py`, `test_post_h_015_operator_dashboard_application_api.py`, `test_post_h_015_operator_dashboard_ready_gate.py`, `test_post_h_025_production_ready_aggregator.py`, `test_post_h_025_production_ready_claims_validator.py`, `test_post_h_025_production_ready_final_declaration.py`, `test_quality_gate.py`, `test_trace_store.py`, `test_traceability_engine.py` y `test_api_reports_traces.py`.

## 3. Estado base y problema a resolver

DevPilot ya genera evidencia y reportes en muchas capas. El problema industrial no es ausencia de evidencia, sino dispersión operacional:

- la evidencia esta distribuida entre `.devpilot/`, `docs/`, `outputs/`, schemas, registries y reportes regenerables;
- el operador debe conocer rutas y comandos para interpretar salud real;
- hay claims permitidos y prohibidos, pero la lectura integrada requiere consultar varios documentos;
- los no-go gates existen, pero no estan necesariamente presentados como tablero unico;
- los gaps tienen evidencia tecnica, pero no siempre se traducen en acciones concretas;
- los exports redactados existen en observabilidad, pero falta una experiencia integrada de evidence export para operador;
- los reportes bajo `outputs/` son regenerables y no versionados, lo cual es correcto, pero obliga a explicar que es fuente versionada y que es evidencia runtime.

POST-H-031 debe resolver esta fragmentacion con un modelo de evidence graph y vistas de operador, manteniendo el principio `evidence-before-claims`.

## 4. Objetivos industriales

POST-H-031 debe lograr:

- Crear un evidence graph local, deterministic, schema-backed y read-only.
- Unificar referencias a evidencia versionada y evidencia runtime regenerable.
- Exponer un resumen de salud para operador que no requiera leer todo el repo.
- Mapear gaps a acciones concretas, comandos de verificacion y backlog recomendado.
- Mostrar claims permitidos, claims prohibidos y no-go gates activos en una vista consistente.
- Producir exports redactados de evidencia para auditoria interna, sin secretos ni payloads sensibles.
- Mantener compatibilidad con observabilidad POST-H-010, dashboard POST-H-015 y production readiness POST-H-025.
- Integrar la capa con `ApplicationService` y, donde corresponda, con API/UI local.
- Evitar overclaims y mantener `enterprise_ready=false`, `remote_ready=false`, `compliance_certified=false` y `saas_ready=false` salvo backlog futuro aprobado.

## 5. No objetivos

Este backlog no debe:

- Implementar observabilidad cloud.
- Habilitar telemetria remota.
- Exportar datos sin redaccion.
- Versionar outputs runtime.
- Declarar compliance certification.
- Declarar enterprise-ready, SaaS-ready o remote-ready.
- Ejecutar comandos destructivos para generar evidencia.
- Leer secretos, `.env`, bases SQLite completas o payloads crudos de prompts/outputs.
- Reemplazar `ProductionReadyEvidenceAggregator`; debe complementarlo.
- Reemplazar `OperatorDashboardAggregator`; debe enriquecerlo.
- Crear UI completa de todos los reportes si no existe API/contract previo.

## 6. Principios de diseno

### 6.1 Read-only por defecto

La construccion de grafo, resumen de salud, gap mapping y dashboard debe ser read-only. La escritura de reportes debe requerir flag explicito y limitarse a `outputs/reports` o `outputs/audit_exports`.

### 6.2 Fuentes clasificadas

Toda evidencia debe clasificarse al menos como:

- `versioned_source`: evidencia versionada en repo limpio;
- `runtime_generated`: evidencia regenerable bajo `outputs/`;
- `operator_supplied`: evidencia aportada manualmente por operador;
- `derived_summary`: resumen calculado por DevPilot;
- `missing_expected`: evidencia esperada pero ausente;
- `blocked_or_forbidden`: evidencia no permitida o claim prohibido.

### 6.3 Evidence graph no equivale a PASS

El evidence graph puede mostrar completitud, gaps y relaciones. No puede declarar readiness por si solo. Las declaraciones siguen perteneciendo a gates formales como POST-H-025.

### 6.4 Acciones verificables

Todo gap relevante debe apuntar a:

- razon del gap;
- severidad;
- evidencia faltante;
- comando recomendado de verificacion;
- backlog o micro-sprint recomendado;
- owner sugerido;
- criterio de cierre.

### 6.5 Redaccion obligatoria

Ningun export de operador debe incluir secretos, tokens, `.env`, prompts crudos, outputs crudos, trazas sensibles o bytes de `.devpilot/devpilot.db`.

## 7. Artefactos globales previstos

### 7.1 Nuevos schemas

- `docs/schemas/evidence_graph.schema.json`
- `docs/schemas/operator_health_summary.schema.json`
- `docs/schemas/gap_action_map.schema.json`
- `docs/schemas/claims_no_go_dashboard.schema.json`
- `docs/schemas/operator_evidence_export.schema.json`

Si durante implementacion se concluye que alguno ya queda cubierto por schemas existentes, se debe extender el schema existente con versionado claro en vez de duplicarlo.

### 7.2 Nuevos artefactos `.devpilot`

- `.devpilot/evidence/evidence_graph_sources.json`
- `.devpilot/evidence/gap_action_rules.json`
- `.devpilot/operator/operator_health_config.json`
- `.devpilot/operator/claims_no_go_dashboard_config.json`

### 7.3 Nuevos modulos previstos

- `src/devpilot_core/evidence_graph/models.py`
- `src/devpilot_core/evidence_graph/builder.py`
- `src/devpilot_core/evidence_graph/sources.py`
- `src/devpilot_core/evidence_graph/gap_actions.py`
- `src/devpilot_core/evidence_graph/claims_dashboard.py`
- `src/devpilot_core/evidence_graph/export.py`
- `src/devpilot_core/application/evidence_service.py`

Los nombres podran ajustarse si el repo revela un patron local mas apropiado. La condicion de cierre es conservar un bounded context claro para evidence graph, sin mezclarlo dentro de `cli.py`.

### 7.4 Reportes y manifests

- `docs/audits/post_h_031_a_evidence_graph_model_report.md`
- `docs/audits/post_h_031_b_operator_health_summary_report.md`
- `docs/audits/post_h_031_c_gap_to_action_mapping_report.md`
- `docs/audits/post_h_031_d_claims_no_go_dashboard_report.md`
- `docs/audits/post_h_031_e_redacted_evidence_export_ux_report.md`
- `docs/post_h_031_a_manifest.json`
- `docs/post_h_031_b_manifest.json`
- `docs/post_h_031_c_manifest.json`
- `docs/post_h_031_d_manifest.json`
- `docs/post_h_031_e_manifest.json`

### 7.5 Tests previstos

- `tests/test_post_h_031_evidence_graph_model.py`
- `tests/test_post_h_031_operator_health_summary.py`
- `tests/test_post_h_031_gap_to_action_mapping.py`
- `tests/test_post_h_031_claims_no_go_dashboard.py`
- `tests/test_post_h_031_redacted_evidence_export_ux.py`

## 8. Micro-sprints

## Estado de implementación POST-H-031-A

`POST-H-031-A` queda implementado como versión inicial (`implemented-initial/local-first`). El micro-sprint crea el modelo base `EvidenceGraph`, su schema, configuración de fuentes, builder local/read-only, método de `ApplicationService`, comando CLI `python -m devpilot_core evidence graph --json`, pruebas focales y artefactos de auditoría.

El grafo no declara readiness por sí mismo: representa evidencia, claims, no-go gates, gaps y runtime signals para consumo de operador. Las declaraciones PASS/BLOCK siguen perteneciendo a gates formales como production-ready-local, quality-gate y los próximos micro-sprints de POST-H-031.

No ejecuta comandos, no lee secretos, no lee `.devpilot/devpilot.db`, no usa red, no usa APIs externas, no habilita telemetría remota, no activa connector write, no activa plugin execution y solo escribe reportes bajo `outputs/reports` cuando se usa `--write-report`.

## POST-H-031-A - Evidence graph model

### Objetivo

Crear el modelo base de evidence graph para representar fuentes, reportes, claims, gaps, no-go gates, runtime signals y relaciones entre evidencias de forma local, schema-backed y read-only.

### Alcance

Este sprint debe producir el grafo y sus contratos, no una UI completa. El grafo debe ser consumible por CLI/API/ApplicationService y por futuros dashboards.

### Fuentes iniciales del grafo

El grafo debe integrar, como minimo:

- `.devpilot/project_state.json`;
- `.devpilot/production/production_ready_local_criteria.json`;
- `docs/audits/devpilot_local_production_ready_declaration.md`;
- `docs/schemas/production_ready_local_report.schema.json`;
- `docs/schemas/operator_dashboard_snapshot.schema.json`;
- `.devpilot/testing/test_contract_registry.json`;
- `.devpilot/testing/test_contract_registry_v2.json`;
- `.devpilot/docs_governance/source_registry.json`;
- `outputs/reports/production_ready_local_report.json`, si existe;
- `outputs/reports/operator_dashboard_snapshot.json`, si existe;
- `outputs/reports/observability_redacted_export.json`, si existe;
- observability inventory y runtime state inventory cuando existan.

### Entregables

- Schema `EvidenceGraph`.
- Config `.devpilot/evidence/evidence_graph_sources.json`.
- Modulo builder read-only.
- Carga de nodos y aristas con tipos estables.
- Clasificacion de evidencia versionada/runtime/missing/derived.
- CLI/API interno o ApplicationService method para construir grafo sin escribir.
- Reporte de auditoria POST-H-031-A.
- Manifest POST-H-031-A.
- Tests focales.

### Modelo minimo

El grafo debe incluir:

- `nodes`: evidencia, claim, gate, gap, report, schema, test, backlog, command, runtime_signal;
- `edges`: supports, blocks, requires, generated_by, validates_against, derived_from, remediated_by, supersedes;
- `summary`: counts, missing evidence, blocking gaps, no-go gates, claims status;
- `safety`: read-only, no network, no external API, no source mutation;
- `limitations`: que el grafo no declara readiness.

### Criterios PASS

- El grafo valida contra schema.
- Toda fuente inexistente se marca como missing, no como success.
- Las evidencias runtime bajo `outputs/` se tratan como regenerables.
- El grafo no ejecuta comandos para producir evidencia.
- No se leen secretos ni bytes de `.devpilot/devpilot.db`.
- No se producen claims nuevos.
- Los no-go gates se representan como nodos bloqueantes.

### Criterios BLOCK

- Missing evidence clasificada como PASS.
- Cualquier export sin redaccion.
- Cualquier mutacion de fuente versionada.
- Lectura de secretos o payload crudo.
- Declaracion `production-ready-local` emitida directamente por el graph builder.

### Validacion focal esperada

```powershell
$env:PYTHONPATH="src"
python -m pytest -p no:ddtrace --assert=plain `
  tests/test_post_h_031_evidence_graph_model.py `
  tests/test_post_h_025_production_ready_aggregator.py `
  tests/test_post_h_015_operator_dashboard_aggregator.py `
  tests/test_observability_inventory.py `
  tests/test_runtime_state_inventory.py `
  tests/test_schema_registry.py `
  -q

python -m devpilot_core schema validate --schema-id EvidenceGraph --instance outputs/reports/evidence_graph.json --json
```

Nota: el comando de validacion de schema sobre `outputs/reports/evidence_graph.json` aplica solo cuando el reporte se genere explicitamente. El test unitario debe validar payloads en memoria sin depender de outputs.

## POST-H-031-B - Operator health summary

### Objetivo

Crear un resumen de salud operacional para operador que sintetice estado, riesgos, gaps, claims, no-go gates, calidad de evidencia y acciones prioritarias en una vista unica.

### Justificacion

El operador local necesita una lectura ejecutiva y accionable. El dashboard POST-H-015 ya agrega señales, pero POST-H-031-B debe cruzarlas con evidence graph y production readiness para responder: "Que tan saludable esta DevPilot ahora y que debo revisar primero?".

### Alcance

Incluir:

- estado global;
- estado por dominios;
- evidencia disponible/faltante;
- quality gates relevantes;
- test contract status;
- docs governance status;
- production-ready-local status;
- claims permitidos/prohibidos;
- no-go gates;
- runtime state hygiene;
- observability hygiene;
- top actions.

### Entregables

- Schema `OperatorHealthSummary`.
- Config `.devpilot/operator/operator_health_config.json`.
- Modulo `operator_health` o extension controlada de `OperatorDashboardApplicationService`.
- Integracion con evidence graph.
- CLI/API/ApplicationService method read-only.
- Reporte markdown/json opcional bajo `outputs/reports`.
- Reporte de auditoria POST-H-031-B.
- Manifest POST-H-031-B.
- Tests focales.

### Semaforo recomendado

El summary debe usar estados controlados:

- `green`: sin blocking gaps y evidencia critica presente;
- `yellow`: warnings o evidencia runtime no regenerada;
- `red`: blocking gaps, no-go violation o claims prohibidos;
- `unknown`: evidencia no disponible;
- `not_applicable`: claim o capacidad fuera de alcance.

### Criterios PASS

- El summary valida contra schema.
- Los estados son derivados de evidencia, no hardcodeados.
- Gaps bloqueantes se reflejan en salud global.
- Claims prohibidos no aparecen como capacidades disponibles.
- Output JSON es estable.
- Report writing es explicito y limitado a outputs.
- ApplicationService expone el summary sin que API/UI importen internals.

### Criterios BLOCK

- Salud global green con gaps bloqueantes.
- Claims prohibidos mostrados como disponibles.
- Estado derivado de texto libre no validado.
- Lectura obligatoria de outputs inexistentes.
- Mutacion no solicitada.

### Validacion focal esperada

```powershell
$env:PYTHONPATH="src"
python -m pytest -p no:ddtrace --assert=plain `
  tests/test_post_h_031_operator_health_summary.py `
  tests/test_post_h_031_evidence_graph_model.py `
  tests/test_post_h_015_operator_dashboard_aggregator.py `
  tests/test_post_h_015_operator_dashboard_application_api.py `
  tests/test_application_services.py `
  tests/test_quality_gate.py `
  -q
```


## Estado de implementación POST-H-031-B

`POST-H-031-B` queda implementado como versión inicial (`implemented-initial/local-first`). El micro-sprint crea `OperatorHealthSummary`, su schema, configuración, builder local/read-only, método de `ApplicationService`, comando CLI `python -m devpilot_core evidence health --json`, ruta API local protegida `GET /api/v1/operator/health`, pruebas focales y artefactos de auditoría.

El summary sintetiza estado global, estado por dominios, evidencia disponible/faltante, claims permitidos/prohibidos, no-go gates, calidad de evidencia y top actions. Las acciones son recomendaciones operator-facing y no son ejecutadas por el builder.

No reemplaza quality gates, no declara readiness por sí mismo, no ejecuta comandos, no lee secretos, no lee `.devpilot/devpilot.db`, no usa red, no usa APIs externas, no habilita telemetría remota, no activa connector write ni plugin execution. Los reportes se escriben únicamente bajo `outputs/reports` cuando se usa `--write-report`.

## POST-H-031-C - Gap-to-action mapping

### Objetivo

Convertir gaps detectados por evidence graph, production readiness, docs governance, testing, observability y runtime state en acciones concretas, priorizadas y verificables.

### Justificacion

Un gap sin accion asociada obliga al operador a interpretar internals. Para un producto industrial local, cada gap relevante debe explicar que hacer, como verificarlo y que backlog o micro-sprint deberia resolverlo.

### Alcance

Crear reglas para mapear gaps hacia:

- accion recomendada;
- severidad;
- owner sugerido;
- comandos de verificacion;
- artifacts a revisar;
- backlog/micro-sprint sugerido;
- criterio de cierre;
- riesgo si se ignora.

### Entregables

- Schema `GapActionMap`.
- Reglas `.devpilot/evidence/gap_action_rules.json`.
- Modulo `gap_actions.py`.
- Integracion con evidence graph y operator health summary.
- Reporte `gap_action_map.json/md` bajo outputs si se solicita.
- Reporte de auditoria POST-H-031-C.
- Manifest POST-H-031-C.
- Tests focales.

### Reglas minimas requeridas

Debe existir mapping para gaps de:

- missing required evidence;
- failed schema validation;
- docs governance blocking finding;
- test contract registry invalid;
- no-go gate violation;
- forbidden claim detected;
- stale runtime evidence;
- missing operator dashboard source;
- observability export not redacted;
- runtime state hygiene failure;
- release reproducibility missing.

### Criterios PASS

- Todo gap `block` tiene accion concreta.
- Toda accion tiene comando o criterio de verificacion.
- Las acciones no recomiendan habilitar capacidades prohibidas.
- Las reglas validan contra schema.
- Los gaps unknown se reportan como unknown, no se ocultan.
- La salida es deterministica para el mismo input.

### Criterios BLOCK

- Blocking gap sin accion.
- Accion que relaja no-go gates.
- Accion que recomienda versionar outputs runtime.
- Comando sugerido destructivo sin approval o dry-run.
- Mapping por string fragil sin IDs estables cuando existan IDs.

### Validacion focal esperada

```powershell
$env:PYTHONPATH="src"
python -m pytest -p no:ddtrace --assert=plain `
  tests/test_post_h_031_gap_to_action_mapping.py `
  tests/test_post_h_031_evidence_graph_model.py `
  tests/test_post_h_031_operator_health_summary.py `
  tests/test_post_h_025_production_ready_claims_validator.py `
  tests/test_documentation_governance_validator.py `
  tests/test_test_contract_registry_v2.py `
  -q
```


## Estado de implementación POST-H-031-C

`POST-H-031-C` queda implementado como versión inicial (`implemented-initial/local-first`). El micro-sprint crea `GapActionMap`, su schema, reglas declarativas de mapeo, builder local/read-only, método de `ApplicationService`, comando CLI `python -m devpilot_core evidence gaps --json`, ruta API local protegida `GET /api/v1/operator/gaps`, pruebas focales y artefactos de auditoría.

El mapeo convierte gaps detectados por `EvidenceGraph` y `OperatorHealthSummary` en acciones concretas, priorizadas, verificables y seguras para el operador. Cada acción incluye prioridad, owner sugerido, comando recomendado, verificación, criterio de cierre, backlog/micro-sprint recomendado y riesgo si se ignora.

La capacidad es advisory/operator-facing: no ejecuta comandos recomendados, no reemplaza quality gates, no declara readiness, no relaja no-go gates, no versiona outputs runtime, no lee secretos, no lee `.devpilot/devpilot.db`, no usa red, no usa APIs externas, no habilita telemetría remota, no activa connector write ni plugin execution. Los reportes se escriben únicamente bajo `outputs/reports` cuando se usa `--write-report`.

## POST-H-031-D - Claims and no-go dashboard

### Objetivo

Crear una vista operacional especifica para claims y no-go gates que permita al operador ver que puede afirmar DevPilot, que no puede afirmar, que evidencia lo respalda y que gates bloquearian una sobredeclaracion.

### Justificacion

POST-H-025 ya implemento criteria, claims validator y declaracion final. POST-H-031-D debe hacer esa informacion consumible para operador y UI/API local sin que el usuario tenga que leer manualmente criterios, reportes y docs.

### Alcance

Incluir:

- claims permitidos;
- claims condicionados;
- claims prohibidos;
- no-go gates activos;
- evidencia que soporta cada claim permitido;
- razon de bloqueo de cada claim prohibido;
- relacion con `production_ready_local_report`;
- estado de overclaim scanning en documentos clave;
- advertencias sobre enterprise/SaaS/remote/compliance.

### Entregables

- Schema `ClaimsNoGoDashboard`.
- Config `.devpilot/operator/claims_no_go_dashboard_config.json`.
- Modulo `claims_dashboard.py`.
- Integracion con `ProductionReadyClaimsValidator`.
- ApplicationService method.
- Endpoint API local opcional si ya existe patron seguro.
- Vista UI inicial opcional solo si el contrato API ya esta cubierto.
- Reporte de auditoria POST-H-031-D.
- Manifest POST-H-031-D.
- Tests focales.

### Claims baseline

La vista debe conservar estos limites:

- `production-ready-local`: permitido solo bajo evidencia POST-H-025 y alcance local.
- `audit-friendly`: permitido como auditoria interna/evidencia tecnica, no certificacion.
- `enterprise-ready`: prohibido.
- `remote-ready`: prohibido.
- `compliance-certified`: prohibido.
- `saas-ready`: prohibido.

### Criterios PASS

- Claims prohibidos aparecen claramente como bloqueados.
- No-go gates aparecen con estado y razon.
- Evidencia soporte apunta a artifacts concretos.
- No se crea un claim nuevo por inferencia.
- La vista valida contra schema.
- Los documentos clave siguen libres de overclaims.
- API/UI, si se exponen, usan ApplicationService y no importan internals.

### Criterios BLOCK

- Vista que muestre enterprise/remote/compliance/SaaS como disponible.
- Omision de no-go gate violado.
- Claim permitido sin evidencia.
- Endpoint o UI que permita modificar claims.
- Redaccion insuficiente en evidencia presentada.

### Validacion focal esperada

```powershell
$env:PYTHONPATH="src"
python -m pytest -p no:ddtrace --assert=plain `
  tests/test_post_h_031_claims_no_go_dashboard.py `
  tests/test_post_h_025_production_ready_claims_validator.py `
  tests/test_post_h_025_production_ready_declaration_gate.py `
  tests/test_post_h_025_production_ready_final_declaration.py `
  tests/test_application_services.py `
  tests/test_api_security.py `
  -q
```

## POST-H-031-E - Redacted evidence export UX

### Objetivo

Crear una experiencia de export redactado de evidencia para operador, basada en el evidence graph y en las capacidades existentes de observability redacted export, que permita compartir evidencia tecnica sin exponer secretos, payloads sensibles ni runtime state completo.

### Justificacion

El repo ya contiene `observability_redacted_export.schema.json` y exportador de observabilidad redactado. POST-H-031-E debe extender el concepto a un paquete de evidencia operacional mas amplio, con UX clara para operador, manteniendo redaccion obligatoria.

### Alcance

El export debe poder incluir:

- evidence graph summary;
- operator health summary;
- gap action map;
- claims/no-go dashboard;
- observability redacted export summary;
- runtime state inventory summary;
- production-ready final declaration summary;
- checksums de artifacts exportados;
- manifest de redaccion;
- instrucciones de interpretacion.

No debe incluir:

- `.env`;
- secretos;
- tokens;
- prompts crudos;
- outputs crudos;
- bases SQLite completas;
- archivos bajo `outputs/` no seleccionados;
- datos personales no redaccionados;
- contenido completo de trazas si no pasa SecretGuard/redaction.

### Entregables

- Schema `OperatorEvidenceExport`.
- Modulo `evidence_graph/export.py`.
- CLI/ApplicationService method para export dry-run y write-report.
- Paquete bajo `outputs/audit_exports/operator_evidence_export/` cuando se solicite.
- Manifest con checksums.
- Markdown de lectura para auditor interno.
- Reporte de auditoria POST-H-031-E.
- Manifest POST-H-031-E.
- Tests focales.

### UX minima esperada

La UX puede ser CLI/API inicialmente:

```text
devpilot operator evidence-export --redacted --dry-run --json
devpilot operator evidence-export --redacted --write-report --json
```

Si se expone en UI, debe ser una accion local explicita y no debe descargar informacion no redaccionada.

### Criterios PASS

- `--redacted` es obligatorio.
- Dry-run no escribe.
- Write-report escribe solo en outputs.
- Export contiene manifest y checksums.
- SecretGuard no detecta secretos en payload exportado.
- No se exporta `.devpilot/devpilot.db`.
- No se exportan prompts/outputs crudos.
- Export valida contra schema.
- La documentacion explica que el paquete no es certificacion externa.

### Criterios BLOCK

- Export sin redaccion.
- Export de secretos o `.env`.
- Export de DB completa.
- Escritura fuera de outputs.
- Inclusion de claims prohibidos como capacidades.
- Falta de checksums.

### Validacion focal esperada

```powershell
$env:PYTHONPATH="src"
python -m pytest -p no:ddtrace --assert=plain `
  tests/test_post_h_031_redacted_evidence_export_ux.py `
  tests/test_post_h_031_evidence_graph_model.py `
  tests/test_post_h_031_operator_health_summary.py `
  tests/test_post_h_031_gap_to_action_mapping.py `
  tests/test_post_h_031_claims_no_go_dashboard.py `
  tests/test_observability_export.py `
  tests/test_runtime_state_export.py `
  tests/test_secret_guard_hardening.py `
  -q
```

## 9. Definition of Done del backlog POST-H-031

El backlog completo se puede cerrar solo si:

- Existe un evidence graph local, validable y read-only.
- El operador cuenta con resumen de salud consolidado.
- Los gaps bloqueantes tienen acciones concretas y verificables.
- Los claims permitidos/prohibidos y no-go gates se visualizan sin ambiguedad.
- El export de evidencia es redactado, seguro y reproducible.
- Los outputs generados no se versionan en ZIPs limpios.
- Las nuevas capacidades pasan por `ApplicationService` cuando se expongan a API/UI.
- No se habilita telemetria remota.
- No se habilitan APIs externas.
- No se exponen secretos ni prompts/outputs crudos.
- README, runbook, backlog, manifests, source registry, TCR y schema catalog quedan sincronizados.
- La validacion focal ampliada pasa.

## 10. Quality gates requeridos

### Gates existentes obligatorios

Deben seguir pasando:

```powershell
python -m devpilot_core docs-governance validate --json
python -m devpilot_core test-contracts validate --json
python -m devpilot_core test-contracts validate-v2 --json
python -m devpilot_core project-state validate --json
python -m devpilot_core schema list --json
```

### Gate nuevo recomendado

Crear subgate:

```text
operator-evidence-readiness
```

El gate debe verificar:

- evidence graph valida contra schema;
- operator health summary no oculta blockers;
- claims/no-go dashboard no sobredeclara;
- gap action map cubre blocking gaps;
- redacted evidence export bloquea datos sensibles;
- write-report limitado a outputs;
- no network, no external API, no remote telemetry.

## 11. Regresion focal acumulada recomendada

Durante POST-H-031 no se recomienda usar `pytest -q` completo como validacion primaria de cada micro-sprint. La validacion focal acumulada debe incluir:

```powershell
$env:PYTHONPATH="src"
python -m pytest -p no:ddtrace --assert=plain `
  tests/test_post_h_031_evidence_graph_model.py `
  tests/test_post_h_031_operator_health_summary.py `
  tests/test_post_h_031_gap_to_action_mapping.py `
  tests/test_post_h_031_claims_no_go_dashboard.py `
  tests/test_post_h_031_redacted_evidence_export_ux.py `
  tests/test_observability_inventory.py `
  tests/test_observability_export.py `
  tests/test_observability_cli.py `
  tests/test_observability_hygiene_gate.py `
  tests/test_runtime_state_inventory.py `
  tests/test_runtime_state_export.py `
  tests/test_runtime_state_hygiene.py `
  tests/test_post_h_015_operator_dashboard_aggregator.py `
  tests/test_post_h_015_operator_dashboard_application_api.py `
  tests/test_post_h_015_operator_dashboard_ready_gate.py `
  tests/test_post_h_025_production_ready_aggregator.py `
  tests/test_post_h_025_production_ready_claims_validator.py `
  tests/test_post_h_025_production_ready_final_declaration.py `
  tests/test_quality_gate.py `
  tests/test_trace_store.py `
  tests/test_traceability_engine.py `
  tests/test_api_reports_traces.py `
  -q
```

Validaciones CLI/documentales:

```powershell
python -m devpilot_core docs-governance validate --json
python -m devpilot_core test-contracts validate --json
python -m devpilot_core test-contracts validate-v2 --json
python -m devpilot_core project-state validate --json
python -m devpilot_core schema list --json
python -m devpilot_core cli-registry guard --json
```

## 12. Riesgos y mitigaciones

| Riesgo | Impacto | Mitigacion |
| --- | --- | --- |
| Evidence graph duplica production readiness | Alto | El graph solo referencia y explica; no declara readiness |
| Missing evidence interpretada como success | Critico | Estado `missing_expected` y tests BLOCK |
| Export filtra secretos | Critico | Redaccion obligatoria, SecretGuard y tests negativos |
| Operador recibe demasiada informacion | Medio | Health summary y top actions priorizadas |
| UI/API importan internals | Medio/alto | ApplicationService como boundary |
| Outputs runtime versionados accidentalmente | Medio | Runbook y tests de ZIP limpio |
| Claims prohibidos aparecen en dashboard como capacidades | Critico | Claims validator y no-go dashboard tests |

## 13. Dependencias

- POST-H-010 observability retention, hygiene y export redacted.
- POST-H-015 local operator dashboard.
- POST-H-025 production-ready declaration gate.
- POST-H-029 testing tiers, si ya esta implementado al momento de ejecutar esta ola.
- POST-H-030 CLI boundaries, si ya esta implementado al momento de exponer nuevos comandos.

POST-H-031 puede iniciarse despues de POST-H-025, pero debe coordinarse con POST-H-030 si agrega comandos CLI nuevos para evitar crecimiento no gobernado de `cli.py`.

## 14. Decisiones arquitectonicas

No se requiere ADR nueva para iniciar POST-H-031 si se mantiene:

- local-only;
- read-only por defecto;
- report writing explicito;
- redaccion obligatoria;
- sin telemetria remota;
- sin APIs externas;
- sin cambios en claims permitidos/prohibidos.

Si se decide enviar telemetria fuera del equipo local, conectar dashboards externos, almacenar evidencia en servicios cloud, o compartir exports automaticamente, entonces debe crearse una ADR previa. Eso cambia el modelo de amenaza, privacidad, seguridad y claims del producto.

## 15. Ruta recomendada en el repo

Guardar este backlog en:

```text
docs/backlogs/POST-H-031_observability_evidence_graph_operator.md
```

Opcionalmente, si se mantiene un documento top-level por backlog activo:

```text
docs/POST-H-031_observability_evidence_graph_operator.md
```

## 16. Commit sugerido para incorporar el backlog

```bash
git add docs/backlogs/POST-H-031_observability_evidence_graph_operator.md
git commit -m "Add POST-H-031 operator evidence graph backlog"
```

## 17. Cierre esperado de POST-H-031

POST-H-031 debe cerrar con DevPilot capaz de explicar su estado operativo sin exigir al operador lectura manual del repo completo. La aplicacion debe mostrar evidencia, gaps, claims, no-go gates y acciones recomendadas de manera integrada, local, segura y validable. El cierre correcto no es una UI vistosa sin contratos; es una capa de evidencia operacional que preserve la disciplina acumulativa del producto: evidencia antes de claims, redaccion antes de export, y gaps convertidos en acciones verificables.


## Estado de implementación POST-H-031-D

POST-H-031-D queda en estado `implemented-initial/local-first`. Se agregó `ClaimsNoGoDashboard` como vista operacional read-only para claims permitidos, claims condicionados, claims prohibidos, no-go gates activos y escaneo determinístico de overclaims sobre documentos clave.

Artefactos principales:

- `docs/schemas/claims_no_go_dashboard.schema.json`;
- `.devpilot/operator/claims_no_go_dashboard_config.json`;
- `src/devpilot_core/evidence_graph/claims_dashboard.py`;
- `python -m devpilot_core evidence claims-dashboard --json`;
- `ApplicationService.claims_no_go_dashboard(...)`;
- `GET /api/v1/operator/claims-no-go`;
- `docs/audits/post_h_031_d_claims_no_go_dashboard_report.md`;
- `docs/post_h_031_d_manifest.json`;
- `tests/test_post_h_031_claims_no_go_dashboard.py`.

La implementación conserva `production-ready-local` como claim permitido solo bajo evidencia POST-H-025 y alcance local. `audit-friendly` queda como claim condicionado para auditoría técnica interna, sin certificación. `enterprise-ready`, `remote-ready`, `compliance-certified` y `saas-ready` permanecen prohibidos y visibles como bloqueados.

Límites explícitos: esta primera versión no muta claims, no muta no-go gates, no reemplaza `ProductionReadyClaimsValidator`, no declara readiness nueva, no usa LLM judge, no lee secretos, no lee `.devpilot/devpilot.db`, no usa red ni APIs externas, no habilita remote execution, connector write ni plugin execution. `--write-report` escribe únicamente evidencia regenerable bajo `outputs/reports`, que no debe incluirse en ZIPs limpios.

Siguiente micro-sprint: `POST-H-031-E — Redacted evidence export UX`.
