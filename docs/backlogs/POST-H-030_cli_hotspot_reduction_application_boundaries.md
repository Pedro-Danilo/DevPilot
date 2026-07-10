---
doc_id: POST-H-030-BACKLOG
title: "POST-H-030 - CLI hotspot reduction y boundaries de aplicacion"
status: approved
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-07-09"
approval: approved
---

# POST-H-030 - CLI hotspot reduction y boundaries de aplicacion

```yaml
doc_id: DEVPL-BACKLOG-POST-H-030-CLI-HOTSPOT-REDUCTION-APPLICATION-BOUNDARIES-V1
status: approved
roadmap_wave: "Ola 5"
roadmap_source: "devpilot_post_h_025_roadmap_detallado_v3_agentes_validadores.md"
repo_baseline: "repo_DevPilot_Local_262_POST_H_025_E.zip"
onboarding_report_source: "devpilot_onboarding_report_final_compilado.md"
target_repo_path: "docs/backlogs/POST-H-030_cli_hotspot_reduction_application_boundaries.md"
created_for: "DevPilot Local"
scope: "local-first / deterministic / compatibility-preserving CLI refactor"
implementation_status: "closed/cli-boundary-hotspot-reduction"
current_micro_sprint: "POST-H-030-E"
next_micro_sprint: "POST-H-031-A"
```

## 1. Proposito del backlog

POST-H-030 convierte la Ola 5 del roadmap post POST-H-025 en un backlog ejecutable para reducir el riesgo de mantenibilidad concentrado en `src/devpilot_core/cli.py` y reforzar los boundaries de aplicacion de DevPilot.

El objetivo no es reescribir la CLI ni cambiar el comportamiento publico de los comandos. El objetivo industrial es extraer familias de comandos de mayor riesgo hacia modulos propietarios por dominio, mantener compatibilidad de invocacion, salida JSON, codigos de salida y mensajes operativos, y hacer que las operaciones nuevas o migradas pasen por fronteras explicitas como `ApplicationService`, `ApplicationOperationCatalog`, `CommandDescriptor` y los servicios de dominio existentes.

Este backlog debe ejecutarse como refactor incremental y verificable, no como migracion disruptiva.

## 2. Fuentes consultadas

Se consultaron como fuentes de verdad para formular este backlog:

- `devpilot_post_h_025_roadmap_detallado_v3_agentes_validadores.md`.
- `devpilot_onboarding_report_final_compilado.md`.
- `repo_DevPilot_Local_262_POST_H_025_E.zip`, descomprimido en entorno local de trabajo.

Evidencia tecnica relevante observada:

- El roadmap define la Ola 5 como `POST-H-030: CLI hotspot reduction y boundaries de aplicacion`.
- El roadmap fija cinco micro-sprints: `POST-H-030-A` a `POST-H-030-E`.
- El informe final identifica `src/devpilot_core/cli.py` como el mayor hotspot de mantenibilidad.
- En el repo base, `src/devpilot_core/cli.py` tiene 7554 lineas fisicas.
- Ya existen bases previas de control: `src/devpilot_core/cli_registry`, `src/devpilot_core/cli_commands`, `src/devpilot_core/application`, `ApplicationService`, `ApplicationOperationCatalog`, `ApplicationBoundaryPolicy` y el no-growth gate de POST-H-006.
- Ya existen extracciones parciales en `src/devpilot_core/cli_commands/workspace.py` y `src/devpilot_core/cli_commands/validation.py`.
- Ya existen tests acumulativos relevantes: `test_cli_core.py`, `test_post_h_006_cli_command_registry.py`, `test_post_h_006_c_handler_migration.py`, `test_post_h_006_d_cli_hotspot_ownership.py`, `test_post_h_006_e_cli_no_growth_gate.py`, `test_post_h_007_application_service_boundary.py`, `test_application_services.py`, `test_application_services_v2.py`, `test_application_cli_boundary_integration.py`, `test_application_operation_catalog_schema.py` y `test_application_boundary_policy.py`.

## 3. Estado base y problema a resolver

DevPilot ya alcanzo un estado local `production-ready-local` acotado mediante POST-H-025, con evidencia, no-go gates, claims validator y reporte final. Sin embargo, el informe final deja explicito que el CLI sigue siendo la superficie operacional mas amplia y el punto de mayor concentracion tecnica.

El estado base combina tres realidades:

1. La CLI es funcionalmente madura y contiene una superficie amplia de operacion local.
2. Existen registries, command descriptors y no-growth gate que ya reducen crecimiento no gobernado.
3. `cli.py` todavia mezcla parser, wiring, adaptadores de salida, handlers, llamadas directas a core historico y delegacion parcial a servicios.

El riesgo industrial no es que la CLI no funcione. El riesgo es que cualquier cambio en comandos, salida JSON, wiring o imports puede producir regresiones amplias, dificultar ownership por dominio, duplicar logica con API/UI y debilitar el boundary `ApplicationService`.

## 4. Objetivos industriales

POST-H-030 debe lograr:

- Reducir concentracion de `src/devpilot_core/cli.py` sin romper compatibilidad publica.
- Definir ownership explicito por comando y familia de comandos.
- Extraer familias prioritarias a modulos de `src/devpilot_core/cli_commands/`.
- Mantener `cli.py` como parser/orquestador fino y no como contenedor de logica pesada.
- Alinear comandos migrados con `ApplicationService` cuando exista caso de uso de aplicacion.
- Evitar bypasses nuevos de CLI hacia core cuando exista boundary de aplicacion.
- Mantener salida JSON, salida humana, codigos de salida y nombres de comandos.
- Formalizar tests de compatibilidad CLI antes de seguir ampliando superficie.
- Fortalecer los contratos que habilitan futura equivalencia CLI/API/UI sin forzar que todo comando tenga UI.

## 5. No objetivos

Este backlog no debe:

- Reescribir completamente `cli.py`.
- Cambiar nombres de comandos publicos existentes.
- Romper scripts de operador basados en CLI.
- Activar ejecucion remota.
- Activar escritura en conectores.
- Activar ejecucion de plugins.
- Introducir dependencias externas nuevas sin justificacion separada.
- Convertir todos los comandos CLI en endpoints API o pantallas UI.
- Implementar router dinamico de handlers que cargue codigo arbitrario.
- Eliminar de golpe comandos legacy permitidos por el allowlist.
- Declarar que el CLI queda completamente desacoplado al final del primer sprint.

## 6. Principios de diseno

### 6.1 Compatibilidad antes que limpieza interna

La reduccion del hotspot solo es aceptable si preserva compatibilidad observable. Cada extraccion debe probar:

- nombre del comando;
- argumentos relevantes;
- formato JSON;
- campos principales de respuesta;
- codigos `PASS`, `FAIL`, `BLOCK`, `WARNING` o equivalentes;
- comportamiento ante errores esperados;
- ausencia de red, APIs externas y mutaciones no solicitadas.

### 6.2 Extraccion por ownership de dominio

Los comandos deben migrarse por bounded context, no por conveniencia textual. La matriz de ownership debe indicar:

- command id;
- familia;
- modulo propietario;
- handler actual;
- handler objetivo;
- mapping a `ApplicationOperation` cuando exista;
- riesgo;
- criticidad;
- contrato de compatibilidad;
- estrategia de test;
- estado de migracion.

### 6.3 Boundary de aplicacion preferente

Para operaciones consumibles por CLI/API/UI, el camino objetivo debe ser:

```text
CLI parser -> cli_commands/<domain>.py -> ApplicationService/ApplicationOperation -> domain service -> CommandResult/ApplicationResponse
```

Cuando un comando sea puramente operacional CLI y no corresponda a API/UI, puede permanecer CLI-only, pero debe quedar justificado en la matriz.

### 6.4 Refactor reversible

Cada micro-sprint debe poder validarse y revertirse sin afectar otros dominios. No se permite una migracion que obligue a tocar decenas de handlers sin tests de compatibilidad previos.

## 7. Artefactos globales previstos

### 7.1 Nuevos artefactos de contrato

- `docs/schemas/cli_command_ownership_matrix.schema.json`
- `docs/schemas/cli_extraction_plan.schema.json`
- `docs/schemas/cli_compatibility_report.schema.json`
- `.devpilot/cli_registry/command_ownership_matrix.json`
- `.devpilot/cli_registry/cli_extraction_plan.json`

### 7.2 Nuevos modulos previstos

- `src/devpilot_core/cli_commands/industrial_readiness.py`
- `src/devpilot_core/cli_commands/release.py`
- `src/devpilot_core/cli_commands/workspace_onboarding.py`
- `src/devpilot_core/cli_registry/ownership.py`
- `src/devpilot_core/cli_registry/compatibility.py`

Los nombres concretos podran ajustarse durante implementacion si el repo revela un patron local mas apropiado, pero la separacion por dominio debe conservarse.

### 7.3 Reportes y manifests

- `docs/audits/post_h_030_a_cli_command_ownership_matrix_report.md`
- `docs/audits/post_h_030_b_industrial_readiness_command_extraction_report.md`
- `docs/audits/post_h_030_c_release_command_extraction_report.md`
- `docs/audits/post_h_030_d_workspace_onboarding_command_extraction_report.md`
- `docs/audits/post_h_030_e_cli_compatibility_contract_report.md`
- `docs/post_h_030_a_manifest.json`
- `docs/post_h_030_b_manifest.json`
- `docs/post_h_030_c_manifest.json`
- `docs/post_h_030_d_manifest.json`
- `docs/post_h_030_e_manifest.json`

### 7.4 Tests previstos

- `tests/test_post_h_030_cli_command_ownership_matrix.py`
- `tests/test_post_h_030_industrial_readiness_command_extraction.py`
- `tests/test_post_h_030_release_command_extraction.py`
- `tests/test_post_h_030_workspace_onboarding_command_extraction.py`
- `tests/test_post_h_030_cli_compatibility_contracts.py`

## 8. Micro-sprints

## POST-H-030-A - CLI command ownership matrix

### Objetivo

Crear una matriz machine-readable de ownership de comandos CLI que haga explicito que dominio posee cada comando, que handler lo atiende, que riesgo tiene, que contrato observable debe preservar y si debe migrar a `ApplicationService`.

### Alcance

Este sprint es read-only respecto del comportamiento CLI. No debe extraer handlers todavia. Su salida principal es inventario, schema y plan de migracion.

### Entregables

- Schema `CliCommandOwnershipMatrix`.
- Schema `CliExtractionPlan`.
- Matriz `.devpilot/cli_registry/command_ownership_matrix.json`.
- Plan `.devpilot/cli_registry/cli_extraction_plan.json`.
- Modulo `cli_registry/ownership.py` para cargar y validar matriz.
- Reporte de auditoria POST-H-030-A.
- Manifest POST-H-030-A.
- Tests focales.
- Actualizacion de README, runbook, backlog y test contracts.

### Campos minimos de la matriz

Cada entrada debe incluir:

- `command_id`;
- `command_path`;
- `public_name`;
- `domain_owner`;
- `current_handler`;
- `target_handler`;
- `current_module`;
- `target_module`;
- `registry_phase`;
- `migration_state`;
- `application_operation_id`, cuando aplique;
- `cli_only_reason`, cuando no aplique `ApplicationService`;
- `risk_level`;
- `compatibility_contract_id`;
- `json_output_contract`;
- `exit_code_contract`;
- `human_output_contract`;
- `test_coverage_refs`;
- `planned_micro_sprint`.

### Criterios PASS

- Todos los comandos registrados y legacy permitidos por POST-H-006 aparecen en la matriz.
- Todo comando high/critical tiene owner explicito.
- Todo comando migrable tiene target module.
- Todo comando no migrable tiene justificacion CLI-only.
- La matriz valida contra schema.
- El plan no ejecuta comandos publicos ni carga handlers dinamicamente.
- `cli-registry guard` sigue pasando.
- No hay mutaciones en runtime fuera de outputs si se generan reportes.

### Criterios BLOCK

- Comandos publicos sin owner.
- Comandos high/critical sin contrato de compatibilidad.
- Comandos con target module inexistente sin plan de creacion.
- Mapping a `ApplicationOperation` inventado que no exista o no este planeado.
- Introduccion de router dinamico inseguro.

### Validacion focal esperada

```powershell
$env:PYTHONPATH="src"
python -m pytest -p no:ddtrace --assert=plain `
  tests/test_post_h_030_cli_command_ownership_matrix.py `
  tests/test_post_h_006_cli_command_registry.py `
  tests/test_post_h_006_d_cli_hotspot_ownership.py `
  tests/test_post_h_006_e_cli_no_growth_gate.py `
  tests/test_application_operation_catalog_schema.py `
  -q

python -m devpilot_core cli-registry guard --json
python -m devpilot_core schema validate --schema-id CliCommandOwnershipMatrix --instance .devpilot/cli_registry/command_ownership_matrix.json --json
python -m devpilot_core schema validate --schema-id CliExtractionPlan --instance .devpilot/cli_registry/cli_extraction_plan.json --json
```

## POST-H-030-B - Industrial readiness command extraction

### Objetivo

Extraer la familia de comandos relacionada con production readiness, industrial readiness, declaration gate, claims validator y evidence aggregation desde `cli.py` hacia un modulo propietario, preservando el comportamiento externo.

### Justificacion

POST-H-025 dejo un conjunto de comandos industrialmente criticos para claims, no-go gates, evidencia y declaracion `production-ready-local`. Estos comandos tienen riesgo alto porque un cambio accidental puede producir overclaim, falsos PASS o BLOCK incorrectos. Deben quedar separados de la masa de `cli.py` y anclados al boundary de aplicacion cuando corresponda.

### Alcance

Incluir comandos relacionados con:

- production-ready criteria;
- evidence aggregator;
- declaration gate;
- no-go gates;
- claims validator;
- final declaration;
- industrial readiness report/gate si ya existe comando relacionado.

El alcance exacto se decide desde la matriz POST-H-030-A; no se deben incluir comandos de release ni workspace en este sprint.

### Entregables

- Modulo `src/devpilot_core/cli_commands/industrial_readiness.py`.
- Adaptadores finos desde `cli.py` hacia el nuevo modulo.
- Mapping actualizado en command ownership matrix.
- Tests de compatibilidad antes/despues para comandos POST-H-025.
- Reporte de auditoria POST-H-030-B.
- Manifest POST-H-030-B.
- Actualizacion de TCR, source registry, README y runbook.

### Criterios PASS

- Los comandos migrados conservan nombres, argumentos y codigos de salida.
- Las salidas JSON conservan campos estructurales principales.
- Los comandos siguen bloqueando overclaims.
- Los no-go gates siguen siendo estrictos.
- No se relaja ningun invariant de POST-H-025.
- `cli.py` reduce responsabilidades de handler para esta familia.
- No hay dependencias externas nuevas.
- No se habilita red, API externa, remote execution, connector write ni plugin execution.

### Criterios BLOCK

- Cambio no documentado de contrato CLI.
- Diferencia semantica en PASS/BLOCK.
- Cualquier overclaim permitido por regresion.
- Duplicacion de reglas de claims fuera del modulo propietario o service boundary.
- Falla de tests POST-H-025.

### Validacion focal esperada

```powershell
$env:PYTHONPATH="src"
python -m pytest -p no:ddtrace --assert=plain `
  tests/test_post_h_030_industrial_readiness_command_extraction.py `
  tests/test_post_h_025_production_ready_criteria.py `
  tests/test_post_h_025_production_ready_aggregator.py `
  tests/test_post_h_025_production_ready_declaration_gate.py `
  tests/test_post_h_025_production_ready_claims_validator.py `
  tests/test_post_h_025_production_ready_final_declaration.py `
  tests/test_application_cli_boundary_integration.py `
  tests/test_cli_core.py `
  -q

python -m devpilot_core cli-registry guard --json
python -m devpilot_core test-contracts validate --json
```

## POST-H-030-C - Release command extraction

### Objetivo

Extraer la familia de comandos de release, reproducibilidad, manifests, SBOM, changelog y verificacion de release hacia un modulo propietario `cli_commands/release.py`, manteniendo contratos publicos.

### Justificacion

La funcion de release es critica para preparar release candidate local y packaging reproducible. Mezclar handlers de release con el resto de `cli.py` aumenta riesgo de regresiones en distribucion, reproducibilidad y auditoria.

### Alcance

Incluir comandos relacionados con:

- release manifest;
- changelog;
- SBOM;
- environment snapshot;
- source archive manifest;
- reproducibility pack;
- release verification;
- package/release reports cuando su ownership sea release.

La inclusion de instalacion local, backup y upgrade debe evaluarse desde la matriz. Si su ownership pertenece mejor a POST-H-027, se dejan referenciados pero no migrados en este sprint.

### Entregables

- Modulo `src/devpilot_core/cli_commands/release.py`.
- Wrappers estables desde `cli.py`.
- Ownership matrix actualizada.
- Tests de compatibilidad release.
- Reporte de auditoria POST-H-030-C.
- Manifest POST-H-030-C.
- Actualizacion de docs operacionales.

### Criterios PASS

- Los comandos release siguen produciendo artifacts en las rutas esperadas.
- Los comandos dry-run mantienen comportamiento previo.
- Los manifests y schemas release siguen validando.
- No se versionan outputs generados.
- No se altera reproducibilidad por cambio de orden, nombres o campos contractuales.
- Tests de POST-H-017 y release siguen pasando.

### Criterios BLOCK

- Cambio de estructura en manifests sin versionado de schema.
- Comando release que escribe fuera de outputs o rutas permitidas.
- Ruptura de changelog, SBOM, archive manifest o verification report.
- Regresion en release reproducibility pack.

### Validacion focal esperada

```powershell
$env:PYTHONPATH="src"
python -m pytest -p no:ddtrace --assert=plain `
  tests/test_post_h_030_release_command_extraction.py `
  tests/test_release_manifest.py `
  tests/test_release_changelog.py `
  tests/test_release_sbom.py `
  tests/test_release_verification.py `
  tests/test_post_h_017_release_reproducibility_pack.py `
  tests/test_post_h_017_release_reproducibility_schema.py `
  tests/test_post_h_017_source_archive_manifest.py `
  tests/test_cli_core.py `
  -q

python -m devpilot_core cli-registry guard --json
python -m devpilot_core schema list --json
```


## Estado de implementación POST-H-030-C

POST-H-030-C queda como `implemented-initial/local-first` para la familia release. Se extraen handlers de construcción de resultado hacia `src/devpilot_core/cli_commands/release.py` para comandos `release`, `release-candidate`, `package`, `install`, `backup` y `upgrade`, preservando el parser público, nombres de comandos, flags, salida JSON, códigos de salida, escritura opcional de reportes, eventos y persistencia desde `cli.py`.

La implementación no introduce router dinámico, carga dinámica de handlers, red, APIs externas, publicación, despliegue, firma obligatoria, remote execution, connector write ni plugin execution. La reducción es incremental: `cli.py` conserva wrappers públicos y la validación fuerte de contratos observables queda pendiente para POST-H-030-E.

## POST-H-030-D - Workspace/onboarding command extraction

### Objetivo

Completar la extraccion de comandos de workspace y onboarding hacia modulos propietarios, aprovechando las extracciones parciales ya existentes en `cli_commands/workspace.py` y manteniendo el flujo local-first de bootstrap, readiness preview y onboarding quality gate.

### Justificacion

POST-H-024 dejo workspace/onboarding como componente clave para operador y proyecto piloto. Esta familia debe quedar separada de `cli.py` porque combina filesystem, templates, readiness checks y evidencia operacional. Tambien es una candidata natural para futura equivalencia UI/API local, por lo que debe alinearse con `ApplicationService`.

### Alcance

Incluir comandos relacionados con:

- workspace registry/status;
- workspace bootstrap;
- onboarding templates;
- readiness preview;
- onboarding quality gate;
- project bootstrap planner;
- operator onboarding checks.

No se deben mover comandos de portfolio o multiworkspace si la matriz indica ownership diferente, salvo que ya formen parte directa del flujo workspace/onboarding.

### Entregables

- Modulo `src/devpilot_core/cli_commands/workspace_onboarding.py` o extension controlada de `cli_commands/workspace.py`.
- Wrappers estables desde `cli.py`.
- Mapping a `ApplicationService.workspace`, `ApplicationService.portfolio` u otros servicios existentes cuando aplique.
- Tests de compatibilidad workspace/onboarding.
- Reporte de auditoria POST-H-030-D.
- Manifest POST-H-030-D.
- Actualizacion de runbook y README.

### Criterios PASS

- Bootstrap dry-run sigue sin mutaciones.
- Bootstrap execute mantiene restricciones actuales.
- Readiness preview sigue clasificando MIASI faltante como pending cuando corresponda.
- Onboarding quality gate sigue bloqueando fixtures invalidos.
- Los outputs runtime siguen excluidos de entregables ZIP.
- No se rompe `ProjectBootstrapReport` ni `OnboardingReadinessPreviewReport`.
- No se habilita red ni APIs externas.

### Criterios BLOCK

- Readiness preview que declara success ante evidencias faltantes.
- Bootstrap que muta en dry-run.
- Cambio no versionado en schemas de onboarding.
- Ruptura de POST-H-024.
- Comando migrado que salta el boundary de aplicacion cuando ya existe servicio.

### Validacion focal esperada

```powershell
$env:PYTHONPATH="src"
python -m pytest -p no:ddtrace --assert=plain `
  tests/test_post_h_030_workspace_onboarding_command_extraction.py `
  tests/test_post_h_024_operator_onboarding.py `
  tests/test_post_h_024_project_bootstrap.py `
  tests/test_post_h_024_project_templates.py `
  tests/test_post_h_024_onboarding_readiness_preview.py `
  tests/test_post_h_024_onboarding_quality_gate.py `
  tests/test_workspace_manager.py `
  tests/test_post_h_016_workspace_registry_v2.py `
  tests/test_application_services.py `
  tests/test_cli_core.py `
  -q

python -m devpilot_core cli-registry guard --json
python -m devpilot_core project-state validate --json
```



## Estado de implementación POST-H-030-D

POST-H-030-D queda como `implemented-initial/local-first` para workspace/onboarding. Se extiende `src/devpilot_core/cli_commands/workspace.py` con handlers para `workspace register`, `workspace list`, `workspace select`, `workspace registry-validate` y `workspace isolation-check`; además se crea `src/devpilot_core/cli_commands/workspace_onboarding.py` para `portfolio status` y `portfolio hardening-gate`.

La extracción preserva parser público, nombres de comandos, flags, salida JSON, códigos de salida, escritura opcional de reportes, eventos y persistencia desde `cli.py`. Bootstrap sigue dry-run por defecto, readiness preview mantiene clasificación pending cuando falta evidencia, registry v2 se valida en memoria/read-only y portfolio status conserva `ApplicationService`.

La implementación no introduce router dinámico, carga dinámica de handlers, red, APIs externas, ejecución remota, connector write, plugin execution ni dependencias nuevas. La reducción sigue siendo incremental: `cli.py` conserva wrappers públicos y la validación fuerte de contratos observables queda pendiente para POST-H-030-E.

## POST-H-030-E - CLI compatibility contract tests

### Objetivo

Crear una capa de contratos de compatibilidad CLI que permita seguir extrayendo handlers sin romper automatizaciones, JSON output, exit codes ni help esencial.

### Justificacion

La extraccion incremental sin snapshots de compatibilidad crea riesgo de regresion silenciosa. POST-H-030-E debe dejar una base repetible para comparar contratos observables de comandos criticos y habilitar futuras extracciones con costo controlado.

### Alcance

Implementar contratos para:

- comandos migrados en POST-H-030-B/C/D;
- comandos high/critical marcados en ownership matrix;
- comandos de production readiness;
- comandos de release reproducibility;
- comandos workspace/onboarding;
- comandos `cli-registry` y quality gate relevantes.

No es obligatorio snapshotear todos los comandos en el primer cierre. Si el volumen es alto, se define tiering:

- `tier_0`: comandos criticos y migrados;
- `tier_1`: comandos de operador frecuente;
- `tier_2`: comandos legacy o baja criticidad.

### Entregables

- Schema `CliCompatibilityReport`.
- Fixtures de contratos CLI normalizados.
- Modulo `cli_registry/compatibility.py`.
- Test `tests/test_post_h_030_cli_compatibility_contracts.py`.
- Reporte de compatibilidad en outputs bajo ejecucion explicita.
- Quality gate/subgate `cli-boundary-hotspot-reduction` o equivalente.
- Manifest POST-H-030-E.
- Documentacion de como actualizar snapshots sin ocultar breaking changes.

### Criterios PASS

- Los comandos migrados tienen contrato observable.
- Las diferencias esperadas requieren fixture actualizado y justificacion.
- Las diferencias inesperadas bloquean.
- Se normalizan timestamps, rutas absolutas, duraciones y campos no deterministas.
- Los contratos no ejecutan acciones destructivas.
- Las ejecuciones de contrato usan dry-run o fixtures temporales cuando haya mutacion potencial.
- `cli-registry guard` sigue pasando.

### Criterios BLOCK

- Contratos que dependan de red o APIs externas.
- Snapshots fragiles con timestamps/rutas absolutas no normalizadas.
- Actualizacion de snapshots sin auditoria.
- Comandos criticos migrados sin contrato.
- Cambios de exit code no detectados.

### Validacion focal esperada

```powershell
$env:PYTHONPATH="src"
python -m pytest -p no:ddtrace --assert=plain `
  tests/test_post_h_030_cli_compatibility_contracts.py `
  tests/test_post_h_030_industrial_readiness_command_extraction.py `
  tests/test_post_h_030_release_command_extraction.py `
  tests/test_post_h_030_workspace_onboarding_command_extraction.py `
  tests/test_cli_core.py `
  tests/test_post_h_006_e_cli_no_growth_gate.py `
  tests/test_application_cli_boundary_integration.py `
  -q

python -m devpilot_core cli-registry guard --json
python -m devpilot_core test-contracts validate --json
python -m devpilot_core test-contracts validate-v2 --json
```


## Estado de implementación POST-H-030-E

POST-H-030-E queda como `implemented-initial/local-first` y cierra el backlog POST-H-030 como `closed/cli-boundary-hotspot-reduction`. Se agrega el schema `CliCompatibilityReport`, el fixture versionado `.devpilot/cli_registry/cli_compatibility_contracts.json`, el módulo `src/devpilot_core/cli_registry/compatibility.py`, el comando `python -m devpilot_core cli-registry compatibility --json` y el subgate `cli-boundary-hotspot-reduction` para perfiles hardening/industrial.

La capa de contratos cubre comandos migrados en POST-H-030-B/C/D, comandos high/critical de la ownership matrix y comandos de gobernanza relevantes como `cli-registry guard` y `quality-gate run`. La validación normaliza timestamps, rutas absolutas, duraciones, metadatos volátiles y outputs runtime para evitar snapshots frágiles.

Política para actualizar snapshots: cualquier diferencia esperada debe actualizar el fixture de compatibilidad junto con una justificación en reporte/manifest y revisión del owner. Está prohibido actualizar snapshots para no ocultar breaking changes; cambios de nombre público, argumentos, exit code, JSON envelope o semántica PASS/BLOCK deben tratarse como breaking changes salvo aprobación explícita y versionada.

La implementación no introduce router dinámico, importlib de handlers, carga de plugins, red, APIs externas, remote execution, connector write ni plugin execution. La ejecución de smoke es opt-in y solo usa argv curado/dry-run/read-only declarado en el fixture.

## 9. Definition of Done del backlog POST-H-030

El backlog completo se puede cerrar solo si:

- La matriz de ownership cubre la superficie CLI registrada y legacy permitida.
- Las familias industrial readiness, release y workspace/onboarding estan extraidas o justificadas en plan versionado.
- Los comandos migrados conservan contratos observables.
- `cli.py` queda reducido en responsabilidades de handler para las familias migradas.
- No se introducen comandos legacy nuevos fuera de registry/no-growth gate.
- Los comandos criticos tienen tests de compatibilidad.
- POST-H-030-E registra `CliCompatibilityReport`, fixture de contratos y subgate `cli-boundary-hotspot-reduction`.
- `ApplicationService` queda como boundary preferente para operaciones consumibles por API/UI.
- Los comandos CLI-only quedan justificados.
- README, runbook, backlog, manifests, TCR y source registry quedan sincronizados.
- La validacion focal ampliada pasa sin ejecutar necesariamente `pytest -q` completo.

## 10. Quality gates requeridos

### Gate existente obligatorio

Debe seguir pasando:

```powershell
python -m devpilot_core cli-registry guard --json
```

### Gate nuevo recomendado

Crear subgate:

```text
cli-boundary-hotspot-reduction
```

El gate debe verificar:

- matriz de ownership valida;
- comandos criticos con contrato;
- comandos migrados con target module existente;
- no incremento de legacy-unregistered commands;
- no router dinamico inseguro;
- no bypass nuevo de ApplicationService en operaciones migrables;
- documentacion y TCR sincronizados.

## 11. Regresion focal acumulada recomendada

Durante POST-H-030 no se recomienda usar `pytest -q` como validacion primaria de cada micro-sprint por costo operativo. La validacion focal acumulada debe incluir:

```powershell
$env:PYTHONPATH="src"
python -m pytest -p no:ddtrace --assert=plain `
  tests/test_post_h_030_cli_command_ownership_matrix.py `
  tests/test_post_h_030_industrial_readiness_command_extraction.py `
  tests/test_post_h_030_release_command_extraction.py `
  tests/test_post_h_030_workspace_onboarding_command_extraction.py `
  tests/test_post_h_030_cli_compatibility_contracts.py `
  tests/test_post_h_006_cli_command_registry.py `
  tests/test_post_h_006_c_handler_migration.py `
  tests/test_post_h_006_d_cli_hotspot_ownership.py `
  tests/test_post_h_006_e_cli_no_growth_gate.py `
  tests/test_post_h_007_application_service_boundary.py `
  tests/test_application_services.py `
  tests/test_application_services_v2.py `
  tests/test_application_cli_boundary_integration.py `
  tests/test_application_operation_catalog_schema.py `
  tests/test_application_boundary_policy.py `
  tests/test_cli_core.py `
  -q
```

Validaciones CLI/documentales:

```powershell
python -m devpilot_core cli-registry guard --json
python -m devpilot_core test-contracts validate --json
python -m devpilot_core test-contracts validate-v2 --json
python -m devpilot_core docs-governance validate --json
python -m devpilot_core project-state validate --json
python -m devpilot_core schema list --json
python -m devpilot_core cli-registry guard --json
```

## 12. Riesgos y mitigaciones

| Riesgo | Impacto | Mitigacion |
| --- | --- | --- |
| Ruptura de scripts de operador | Alto | Contratos CLI antes/despues y conservacion de comandos |
| Overclaim en production readiness | Critico | Migracion aislada con tests POST-H-025 completos |
| Cambios fragiles de JSON output | Alto | Normalizacion y snapshots contractuales |
| Extraccion demasiado amplia | Alto | Micro-sprints por familia y ownership matrix previa |
| Duplicacion de logica entre CLI y ApplicationService | Medio/alto | Boundary preferente y mapping a ApplicationOperation |
| No-growth gate debilitado | Alto | Mantener `cli-registry guard` como bloqueante |
| Tests demasiado costosos | Medio | Tiers focales y contratos por criticidad |

## 13. Dependencias

- POST-H-006 CLI command registry.
- POST-H-007 ApplicationService boundary.
- POST-H-017 release reproducibility.
- POST-H-024 onboarding bootstrap.
- POST-H-025 production-ready local declaration gate.
- Roadmap post POST-H-025 v3.

## 14. Decisiones arquitectonicas

No se requiere ADR nueva para iniciar POST-H-030 porque la decision base ya esta alineada con el modelo acumulativo del producto:

- CLI como interfaz local principal.
- `ApplicationService` como boundary de casos de uso.
- Registries/schemas/manifests como contratos.
- No-growth gate para impedir crecimiento no gobernado.
- Refactor incremental sin ruptura publica.

Si durante la implementacion se decide introducir un router dinamico de comandos, carga de plugins CLI, o una politica que obligue a que todos los comandos pasen por `ApplicationService`, entonces si debe crearse una ADR previa. Esas decisiones cambian arquitectura, riesgo y modelo de extensibilidad.

## 15. Ruta recomendada en el repo

Guardar este backlog en:

```text
docs/backlogs/POST-H-030_cli_hotspot_reduction_application_boundaries.md
```

Opcionalmente, si se mantiene un documento top-level por backlog activo:

```text
docs/POST-H-030_cli_hotspot_reduction_application_boundaries.md
```

## 16. Commit sugerido para incorporar el backlog

```bash
git add docs/backlogs/POST-H-030_cli_hotspot_reduction_application_boundaries.md
git commit -m "Add POST-H-030 CLI hotspot reduction backlog"
```

## 17. Cierre esperado de POST-H-030

POST-H-030 debe cerrar con DevPilot en un estado donde la CLI siga siendo compatible para operador, pero internamente menos concentrada, con ownership explicito, contratos observables y boundaries de aplicacion reforzados. El resultado deseable no es eliminar `cli.py`, sino convertirlo progresivamente en un punto de entrada estable y delgado, con handlers por dominio y evidencia automatizada de que cada migracion preserva comportamiento.


## Estado de implementación POST-H-030-A

Estado: `implemented-initial/local-first` para `POST-H-030-A - CLI command ownership matrix`.

POST-H-030-A no migra handlers ni cambia comportamiento público de CLI. Su alcance se limita a contratos machine-readable de ownership y plan de extracción para reducir el hotspot de `src/devpilot_core/cli.py` de forma incremental.

Artefactos iniciales:

- `docs/schemas/cli_command_ownership_matrix.schema.json`
- `docs/schemas/cli_extraction_plan.schema.json`
- `.devpilot/cli_registry/command_ownership_matrix.json`
- `.devpilot/cli_registry/cli_extraction_plan.json`
- `src/devpilot_core/cli_registry/ownership.py`
- `docs/audits/post_h_030_a_cli_command_ownership_matrix_report.md`
- `docs/post_h_030_a_manifest.json`
- `tests/test_post_h_030_cli_command_ownership_matrix.py`

Limitaciones de esta primera versión:

- no extrae comandos todavía;
- no introduce router dinámico;
- no ejecuta handlers ni comandos públicos desde la matriz;
- no habilita red, APIs externas, remote execution, connector write ni plugin execution;
- las extracciones reales quedan planificadas para POST-H-030-B/C/D y los contratos de compatibilidad runtime para POST-H-030-E.


## Estado de implementación POST-H-030-B

Estado: `implemented-initial/local-first` para `POST-H-030-B - Industrial readiness command extraction`.

POST-H-030-B extrae la familia `industrial-readiness` hacia `src/devpilot_core/cli_commands/industrial_readiness.py` sin cambiar nombres de comandos, argumentos públicos, salida JSON, códigos de salida, mensajes operativos, eventos, persistencia ni rutas de reportes. `src/devpilot_core/cli.py` conserva el parser y los wrappers públicos, pero delega la construcción de resultados al módulo propietario.

Comandos migrados:

- `industrial-readiness check` -> `handle_industrial_readiness_check`.
- `industrial-readiness production-ready-local` -> `handle_industrial_readiness_production_ready_local`.
- `industrial-readiness production-ready-local-final` -> `handle_industrial_readiness_production_ready_local_final`.

La extracción preserva el boundary `ApplicationService` para `production-ready-local` y `production-ready-local-final`; no duplica reglas de claims, no relaja no-go gates y no habilita overclaim de producción, enterprise, remote, SaaS ni certificación compliance.

Artefactos nuevos o actualizados:

- `src/devpilot_core/cli_commands/industrial_readiness.py`
- `src/devpilot_core/cli_commands/__init__.py`
- `src/devpilot_core/cli_registry/registry.py`
- `src/devpilot_core/cli_registry/ownership.py`
- `.devpilot/cli_registry/command_ownership_matrix.json`
- `.devpilot/cli_registry/cli_extraction_plan.json`
- `tests/test_post_h_030_industrial_readiness_command_extraction.py`
- `docs/audits/post_h_030_b_industrial_readiness_command_extraction_report.md`
- `docs/post_h_030_b_manifest.json`

Limitaciones de esta versión:

- no reduce todavía todas las familias grandes de `cli.py`;
- no introduce router dinámico ni runtime registry routing;
- no crea snapshots completos de compatibilidad CLI, que quedan para POST-H-030-E;
- no migra release, package, install, workspace ni onboarding, que quedan para POST-H-030-C/D;
- no habilita red, APIs externas, remote execution, connector write ni plugin execution.
