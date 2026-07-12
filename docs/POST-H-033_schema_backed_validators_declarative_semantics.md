---
doc_id: POST-H-033-TOPLEVEL
title: "POST-H-033 — Validadores schema-backed y semántica declarativa"
status: approved
version: 1.0.0
owner: Ordóñez
updated: 2026-07-11
approval: approved
---

# POST-H-033 - Validadores schema-backed y semantica declarativa

```yaml
doc_id: DEVPL-BACKLOG-POST-H-033-SCHEMA-BACKED-VALIDATORS-DECLARATIVE-SEMANTICS-V1
status: approved
roadmap_wave: "Ola 8"
roadmap_source: "devpilot_post_h_025_roadmap_detallado_v3_agentes_validadores.md"
repo_baseline: "repo_DevPilot_Local_262_POST_H_025_E.zip"
onboarding_report_source: "devpilot_onboarding_report_final_compilado.md"
target_repo_path: "docs/backlogs/POST-H-033_schema_backed_validators_declarative_semantics.md"
created_for: "DevPilot Local"
scope: "deterministic validators / schema-backed catalogs / declarative semantics / compatibility-preserving migration"
implementation_status: "active/post-h-033-d-implemented-initial"
current_micro_sprint: "POST-H-033-D"
next_micro_sprint: "POST-H-033-E"
```

## 1. Proposito del backlog

POST-H-033 convierte la Ola 8 del roadmap post POST-H-025 en un backlog ejecutable para reducir hardcoding residual en validadores, conservando determinismo, compatibilidad y capacidad de bloqueo.

La intencion no es hacer que los validadores sean mas blandos ni reemplazar validacion deterministica por LLM. La intencion industrial es mover reglas configurables y auditables hacia schemas, registries y catalogos versionados, manteniendo en codigo los parsers, defensas base y fallbacks de seguridad que no deben poder deshabilitarse por configuracion.

El backlog debe preservar estas propiedades:

- validacion local-first;
- ejecucion deterministic;
- read-only por defecto;
- outputs schema-backed;
- severidades auditables;
- compatibilidad historica;
- fallbacks temporales controlados;
- defensa base no removible para seguridad;
- no relajacion de no-go gates.

## 2. Fuentes consultadas

Se consultaron como fuentes de verdad para formular este backlog:

- `devpilot_post_h_025_roadmap_detallado_v3_agentes_validadores.md`.
- `devpilot_onboarding_report_final_compilado.md`.
- `repo_DevPilot_Local_262_POST_H_025_E.zip`, descomprimido en entorno local de trabajo.

Evidencia tecnica relevante observada:

- El roadmap define la Ola 8 como `POST-H-033: Validadores schema-backed y semantica declarativa`.
- El objetivo del roadmap es reducir hardcoding residual en validadores, conservando determinismo y compatibilidad.
- El roadmap identifica hardcoding residual en `validators/frontmatter.py`, `validators/readiness.py`, `miasi/registry.py`, `miasi/semantic.py`, `docs_governance/validator.py`, `policy/prompt_guard.py` y otros guards.
- El repo ya usa `docs/validation/artifact_profiles.json` como fuente primaria para perfiles de artefactos, manteniendo fallback Python en `validators/artifact_profiles.py`.
- El repo contiene validadores y schemas acumulativos en `src/devpilot_core/validators`, `src/devpilot_core/validation`, `src/devpilot_core/miasi`, `src/devpilot_core/docs_governance`, `src/devpilot_core/policy`, `src/devpilot_core/schemas`.
- El informe final identifica que los validadores y la gobernanza local son una de las zonas mas solidas de DevPilot, pero tambien senala complejidad creciente en `miasi/semantic.py`.
- `src/devpilot_core/miasi/semantic.py` concentra reglas semanticas programaticas, tokens de guardas/no-go, fixtures requeridos y validaciones de policy/approval/RBAC.
- `src/devpilot_core/validators/frontmatter.py` conserva campos requeridos, statuses y regex en codigo.
- `src/devpilot_core/validators/readiness.py` conserva listas de artifacts requeridos en codigo.
- `src/devpilot_core/policy/prompt_guard.py` conserva patrones regex de prompt injection en codigo, lo cual es aceptable como defensa base, pero requiere catalogo extensible.
- Ya existen tests relevantes: `test_frontmatter_validator.py`, `test_precode_readiness.py`, `test_artifact_profile_registry.py`, `test_artifact_validator.py`, `test_validation_gateway.py`, `test_miasi_registry.py`, `test_miasi_semantic_validator.py`, `test_miasi_semantic_validator_fixtures.py`, `test_miasi_semantic_report_model.py`, `test_documentation_governance_validator.py`, `test_documentation_source_registry_schema.py`, `test_policy_engine.py`, `test_prompt_injection_guard.py`, `test_secret_guard_hardening.py`, `test_schema_registry.py` y `test_schema_validator.py`.

## 3. Estado base y problema a resolver

DevPilot ya tiene una capa de validacion amplia y funcional. El problema industrial no es falta de validadores; el problema es que parte de las reglas declarativas todavia vive dentro de codigo Python.

Ese hardcoding residual tiene riesgos:

- dificulta auditar que regla cambio entre versiones;
- mezcla parser/engine con policy/rules;
- obliga a tocar codigo para modificar reglas no estructurales;
- aumenta riesgo de regresiones cuando se editan validadores grandes;
- dificulta explicar al operador de donde salio una severidad;
- dificulta que source registry, TCR y docs governance declaren ownership granular;
- genera concentracion en `miasi/semantic.py` y `docs_governance/validator.py`.

POST-H-033 debe resolver esto con migracion progresiva, no con refactor masivo.

## 4. Objetivos industriales

POST-H-033 debe lograr:

- Inventariar validadores hardcodeados y clasificar que debe migrarse.
- Hacer que frontmatter use schema/catalogo como fuente primaria.
- Mover readiness requirements a registry versionado.
- Crear registry declarativo para reglas semanticas MIASI.
- Crear catalogos versionados para guards/patterns sin desactivar defensas base.
- Crear registry de reglas docs-governance integrado con source registry.
- Mantener determinismo y compatibilidad de outputs.
- Mantener fallback Python temporal con deprecation plan.
- Reportar rule source, version, severity y owner.
- Fortalecer tests adversariales y de drift.

## 5. No objetivos

Este backlog no debe:

- Reemplazar validadores deterministas por LLM.
- Relajar no-go gates.
- Permitir desactivar reglas criticas por configuracion local.
- Romper documentos existentes sin migracion explicita.
- Eliminar fallbacks sin periodo de compatibilidad.
- Habilitar remote execution, connector write o plugin execution.
- Convertir catalogos en codigo ejecutable dinamico inseguro.
- Introducir dependencias externas nuevas si el repo puede validar con JSON/stdlib.
- Reducir severidades de reglas criticas sin ADR/backlog.
- Versionar outputs runtime.

## 6. Principios de diseno

### 6.1 Schema-backed no significa configurable sin limites

Las reglas migradas a JSON deben validar contra schema. Pero las reglas criticas de seguridad deben conservar una capa base no removible en codigo.

### 6.2 Fallback temporal, no doble fuente permanente

Cuando exista fallback Python, debe quedar marcado con:

- motivo;
- version de deprecation;
- owner;
- tests de equivalencia;
- criterio para remover fallback.

### 6.3 Engine estable, reglas declarativas

El codigo debe contener parser, engine y validacion defensiva. El contenido de reglas debe moverse gradualmente a catalogos cuando sea seguro.

### 6.4 Regla con identidad

Toda regla declarativa debe tener:

- `rule_id`;
- `owner`;
- `source_catalog`;
- `version`;
- `severity`;
- `category`;
- `subject_type`;
- `description`;
- `enabled`;
- `critical`;
- `cannot_disable_without_adr`, cuando aplique;
- `tests`.

### 6.5 Compatibilidad observable

La migracion no puede cambiar resultados sin declararlo. Cada sprint debe comparar comportamiento previo y nuevo para casos positivos, negativos y edge cases.

## 7. Artefactos globales previstos

### 7.1 Nuevos schemas

- `docs/schemas/validator_inventory.schema.json`
- `docs/schemas/frontmatter_metadata.schema.json`
- `docs/schemas/readiness_requirements.schema.json`
- `docs/schemas/miasi_semantic_rules.schema.json`
- `docs/schemas/policy_guard_pattern_catalog.schema.json`
- `docs/schemas/docs_governance_rule_registry.schema.json`
- `docs/schemas/validator_migration_report.schema.json`

### 7.2 Nuevos artefactos `.devpilot`

- `.devpilot/validation/validator_inventory.json`
- `.devpilot/validation/validator_migration_plan.json`
- `.devpilot/validation/frontmatter_catalog.json`
- `.devpilot/readiness/readiness_requirements.json`
- `.devpilot/miasi/semantic_rules.json`
- `.devpilot/policy/guard_pattern_catalog.json`
- `.devpilot/docs_governance/rule_registry.json`

### 7.3 Modulos previstos

- `src/devpilot_core/validation/validator_inventory.py`
- `src/devpilot_core/validators/frontmatter_catalog.py`
- `src/devpilot_core/validators/readiness_requirements.py`
- `src/devpilot_core/miasi/declarative_semantic_rules.py`
- `src/devpilot_core/policy/guard_catalog.py`
- `src/devpilot_core/docs_governance/rule_registry.py`

Los nombres pueden ajustarse durante implementacion si el repo revela un patron mas adecuado, pero el boundary debe conservarse: reglas versionadas separadas de engines deterministicos.

### 7.4 Reportes y manifests

- `docs/audits/post_h_033_a_validator_inventory_migration_plan_report.md`
- `docs/audits/post_h_033_b_frontmatter_schema_backed_validator_report.md`
- `docs/audits/post_h_033_c_readiness_requirements_registry_report.md`
- `docs/audits/post_h_033_d_miasi_semantic_rules_registry_report.md`
- `docs/audits/post_h_033_e_policy_guard_pattern_catalogs_report.md`
- `docs/audits/post_h_033_f_docs_governance_rule_registry_report.md`
- `docs/post_h_033_a_manifest.json`
- `docs/post_h_033_b_manifest.json`
- `docs/post_h_033_c_manifest.json`
- `docs/post_h_033_d_manifest.json`
- `docs/post_h_033_e_manifest.json`
- `docs/post_h_033_f_manifest.json`

### 7.5 Tests previstos

- `tests/test_post_h_033_validator_inventory_migration_plan.py`
- `tests/test_post_h_033_frontmatter_schema_backed_validator.py`
- `tests/test_post_h_033_readiness_requirements_registry.py`
- `tests/test_post_h_033_miasi_semantic_rules_registry.py`
- `tests/test_post_h_033_policy_guard_pattern_catalogs.py`
- `tests/test_post_h_033_docs_governance_rule_registry.py`

## 8. Micro-sprints

## POST-H-033-A - Validator inventory and migration plan

### Objetivo

Crear un inventario machine-readable de validadores y un plan de migracion que clasifique cada regla hardcodeada como schema, semantic rule, security guard, fallback compatibility, parser o engine.

### Alcance

Este sprint no cambia comportamiento de validadores. Debe producir inventario, schema, plan y tests de cobertura documental.

### Entregables

- Schema `ValidatorInventory`.
- Schema `ValidatorMigrationReport`.
- `.devpilot/validation/validator_inventory.json`.
- `.devpilot/validation/validator_migration_plan.json`.
- Modulo `validation/validator_inventory.py`.
- Reporte de auditoria POST-H-033-A.
- Manifest POST-H-033-A.
- Tests focales.
- Actualizacion de README, runbook, TCR, source registry y project_state.

### Validadores minimos a inventariar

- `validators/artifact_profiles.py`;
- `validators/frontmatter.py`;
- `validators/readiness.py`;
- `miasi/registry.py`;
- `miasi/semantic.py`;
- `miasi/semantic_rules.py`;
- `docs_governance/validator.py`;
- `docs_governance/backlogs.py`;
- `docs_governance/drift.py`;
- `policy/prompt_guard.py`;
- `policy/tool_injection_guard.py`;
- `policy/secrets.py`;
- `validation/artifact_profile_registry.py`;
- `schemas/validator.py`.

### Campos minimos

- `validator_id`;
- `module_path`;
- `owner`;
- `domain`;
- `status`;
- `rule_types`;
- `hardcoded_elements`;
- `migration_target`;
- `must_remain_in_code`;
- `fallback_required`;
- `criticality`;
- `inputs`;
- `outputs`;
- `schemas`;
- `tests`;
- `migration_micro_sprint`;
- `compatibility_strategy`.

### Criterios PASS

- Cada validador identificado tiene owner, contrato, severidad, inputs, outputs, tests y estado de migracion.
- Cada hardcoded element tiene decision: migrate, keep, fallback, parser, security-core.
- No se altera comportamiento runtime.
- El inventario valida contra schema.
- El plan identifica orden de migracion y riesgos.

### Criterios BLOCK

- Validador critico sin owner.
- Regla hardcodeada sin decision.
- Plan que propone desactivar defensa critica.
- Plan que requiere LLM judge para reemplazar validador deterministico.

### Validacion focal esperada

```powershell
$env:PYTHONPATH="src"
python -m pytest -p no:ddtrace --assert=plain `
  tests/test_post_h_033_validator_inventory_migration_plan.py `
  tests/test_schema_registry.py `
  tests/test_validation_gateway.py `
  tests/test_project_global_state.py `
  -q

python -m devpilot_core schema validate --schema-id ValidatorInventory --instance .devpilot/validation/validator_inventory.json --json
python -m devpilot_core schema validate --schema-id ValidatorMigrationReport --instance docs/post_h_033_a_manifest.json --json
```

## POST-H-033-B - Frontmatter schema-backed validator

### Objetivo

Migrar reglas configurables de frontmatter a schema/catalogo versionado, manteniendo el parser dependency-free y la compatibilidad de hallazgos.

### Alcance

El parser simple de frontmatter puede permanecer en codigo. Deben migrarse los campos requeridos, statuses permitidos, regex declarativas y severidades configurables.

### Entregables

- `docs/schemas/frontmatter_metadata.schema.json`.
- `.devpilot/validation/frontmatter_catalog.json`.
- Modulo `validators/frontmatter_catalog.py`.
- Integracion progresiva con `validators/frontmatter.py`.
- Tests de compatibilidad con documentos existentes.
- Tests negativos para status, semver, date y doc_id.
- Reporte de auditoria POST-H-033-B.
- Manifest POST-H-033-B.

### Reglas a migrar

- `REQUIRED_FRONTMATTER_FIELDS`;
- `ALLOWED_STATUSES`;
- `SEMVER_PATTERN`;
- `DATE_PATTERN`;
- `DOC_ID_PATTERN`;
- severidades por finding;
- strict/non-strict behavior cuando aplique.

### Criterios PASS

- Frontmatter sigue deterministic.
- Los documentos existentes validan igual o con migracion explicitamente documentada.
- El catalogo valida contra schema.
- Python conserva fallback temporal si el catalogo falta o es invalido.
- El reporte indica `rule_source` y `catalog_version`.
- No se introduce dependencia YAML externa.

### Criterios BLOCK

- Documento invalido pasa por falta de catalogo.
- Se reduce severidad de campos requeridos sin ADR/backlog.
- Parser deja de soportar frontmatter actual.
- Regex declarativa permite IDs peligrosos o ambiguos.

### Validacion focal esperada

```powershell
$env:PYTHONPATH="src"
python -m pytest -p no:ddtrace --assert=plain `
  tests/test_post_h_033_frontmatter_schema_backed_validator.py `
  tests/test_frontmatter_validator.py `
  tests/test_artifact_validator.py `
  tests/test_documentation_governance_validator.py `
  tests/test_schema_validator.py `
  -q

python -m devpilot_core schema validate --schema-id FrontmatterMetadata --instance .devpilot/validation/frontmatter_catalog.json --json
```


## Estado de implementación POST-H-033-B

Estado: `implemented-initial`. Se implementó el validador de frontmatter schema-backed sin cambiar el parser dependency-free ni relajar reglas críticas. Los artefactos nuevos son `docs/schemas/frontmatter_metadata.schema.json`, `.devpilot/validation/frontmatter_catalog.json`, `src/devpilot_core/validators/frontmatter_catalog.py`, `docs/audits/post_h_033_b_frontmatter_schema_backed_validator_report.md`, `docs/post_h_033_b_manifest.json` y `tests/test_post_h_033_frontmatter_schema_backed_validator.py`.

La migración es progresiva: `validators/frontmatter.py` usa el catálogo como fuente primaria para campos requeridos, statuses, regex y severidades, pero conserva fallback Python temporal. El resultado reporta `rule_source` y `catalog_version`. No se agregó dependencia YAML externa, no se usa LLM judge, no se habilitan capacidades sensibles y las reglas críticas no son desactivables desde JSON sin ADR/backlog.

## POST-H-033-C - Readiness requirements registry

### Objetivo

Mover listas de artifacts requeridos de readiness a un registry versionado, con schema y compatibilidad.

### Alcance

Debe reemplazar progresivamente:

- `REQUIRED_PRE_CODE_ARTIFACTS`;
- `REQUIRED_MIASI_ARTIFACTS`;
- `STRICT_REQUIRED_ARTIFACTS`.

El comportamiento de readiness debe permanecer deterministic y local.

### Entregables

- `docs/schemas/readiness_requirements.schema.json`.
- `.devpilot/readiness/readiness_requirements.json`.
- Modulo `validators/readiness_requirements.py`.
- Integracion progresiva con `validators/readiness.py`.
- Tests de ausencia, drift y compatibilidad.
- Reporte de auditoria POST-H-033-C.
- Manifest POST-H-033-C.

### Modelo minimo del registry

- `profile_id`;
- `description`;
- `required_artifacts`;
- `required_miasi_artifacts`;
- `strict_required_artifacts`;
- `optional_artifacts`;
- `artifact_type`;
- `requires_frontmatter`;
- `requires_approval_status`;
- `severity_if_missing`;
- `fallback_compatibility_group`;
- `tests`.

### Criterios PASS

- Readiness usa registry como fuente primaria.
- Python conserva fallback temporal.
- Missing registry produce warning/block controlado, no success falso.
- Tests prueban ausencia, drift y compatibilidad.
- MIASI faltante sigue bloqueando strict readiness cuando corresponde.
- No se versionan outputs.

### Criterios BLOCK

- Missing artifact tratado como pass.
- Strict readiness pierde artifacts requeridos.
- MIASI artifacts dejan de ser requeridos sin ADR/backlog.
- Registry invalido produce success.

### Validacion focal esperada

```powershell
$env:PYTHONPATH="src"
python -m pytest -p no:ddtrace --assert=plain `
  tests/test_post_h_033_readiness_requirements_registry.py `
  tests/test_precode_readiness.py `
  tests/test_post_h_024_onboarding_readiness_preview.py `
  tests/test_validation_gateway.py `
  tests/test_schema_validator.py `
  -q

python -m devpilot_core schema validate --schema-id ReadinessRequirements --instance .devpilot/readiness/readiness_requirements.json --json
```



## Estado de implementación POST-H-033-C

Estado: `implemented-initial`. Se implementó el registry schema-backed de readiness mediante `docs/schemas/readiness_requirements.schema.json`, `.devpilot/readiness/readiness_requirements.json` y `src/devpilot_core/validators/readiness_requirements.py`. `validators/readiness.py` usa el registry como fuente primaria para `REQUIRED_PRE_CODE_ARTIFACTS`, `REQUIRED_MIASI_ARTIFACTS` y `STRICT_REQUIRED_ARTIFACTS`, conservando fallback Python temporal.

La implementación mantiene comportamiento determinístico/local, no agrega dependencias externas, no usa LLM judge, no versiona outputs y no relaja MIASI strict readiness. Registry inválido bloquea PASS; registry faltante activa fallback con finding explícito. La versión es preliminar y debe evolucionar antes de retirar el fallback.

## POST-H-033-D - MIASI semantic rules registry

### Objetivo

Crear registry declarativo de reglas semanticas MIASI y migrar gradualmente reglas configurables desde `miasi/semantic.py`, manteniendo el engine deterministic y no ejecutante.

### Alcance

No se debe reemplazar todo `miasi/semantic.py` en un solo sprint. El sprint debe crear registry, schema, loader, rule engine inicial y migrar las reglas mas seguras de parametrizar.

### Entregables

- `docs/schemas/miasi_semantic_rules.schema.json`.
- `.devpilot/miasi/semantic_rules.json`.
- Modulo `miasi/declarative_semantic_rules.py`.
- Integracion con `MiasiSemanticValidator`.
- Rule source/version en reporte semantico.
- Tests de no-go, guard mappings y fixtures.
- Reporte de auditoria POST-H-033-D.
- Manifest POST-H-033-D.

### Reglas candidatas a migrar

- side effects sensibles;
- execution side effects;
- safe gated controlled write tokens;
- no-go action markers;
- approval gate tokens;
- RBAC gate tokens;
- SecretGuard tokens;
- network guard tokens;
- local guard tokens;
- required eval fixtures;
- severidades por categoria.

### Criterios PASS

- Reglas MIASI no-go siguen bloqueando.
- Tokens sensibles y guard mappings se versionan.
- El reporte semantico indica rule source y version.
- Registry invalido bloquea o activa fallback con finding explicito.
- Tests adversariales siguen pasando.
- El validator sigue sin ejecutar agentes, tools, red, plugins, conectores o subprocesses.

### Criterios BLOCK

- No-go remote/plugin/connector deja de bloquear.
- Reglas criticas pueden deshabilitarse localmente.
- Registry invalido produce pass silencioso.
- Se elimina cobertura de eval fixtures.
- Reporte semantico oculta fuente de regla.

### Validacion focal esperada

```powershell
$env:PYTHONPATH="src"
python -m pytest -p no:ddtrace --assert=plain `
  tests/test_post_h_033_miasi_semantic_rules_registry.py `
  tests/test_miasi_semantic_validator.py `
  tests/test_miasi_semantic_validator_fixtures.py `
  tests/test_miasi_semantic_report_model.py `
  tests/test_miasi_registry.py `
  tests/test_policy_engine.py `
  tests/test_post_h_021_remote_disabled_invariants.py `
  tests/test_post_h_019_plugin_execution_blocked.py `
  tests/test_post_h_018_connector_policy_binding.py `
  -q

python -m devpilot_core schema validate --schema-id MiasiSemanticRules --instance .devpilot/miasi/semantic_rules.json --json
```


## Estado de implementación POST-H-033-D

Estado: `implemented-initial`. Se implementó el registry schema-backed de reglas semánticas MIASI mediante `docs/schemas/miasi_semantic_rules.schema.json`, `.devpilot/miasi/semantic_rules.json` y `src/devpilot_core/miasi/declarative_semantic_rules.py`, con integración progresiva en `src/devpilot_core/miasi/semantic.py`.

La implementación migra únicamente reglas seguras de parametrizar: side effects sensibles, execution side effects, safe gated controlled write tokens, no-go action markers, approval/RBAC/SecretGuard/network/local guard tokens, fixtures requeridos y severidades base. El motor semántico permanece determinístico, local-first y no ejecutante. Registry inválido activa fallback explícito con finding bloqueante; registry faltante activa fallback con warning.

La versión es preliminar y debe evolucionar antes de retirar fallback Python. No se agregan dependencias externas, no se usa LLM judge, no se habilita red, plugin execution, connector write, remote execution ni subprocesses. Las reglas críticas no se pueden desactivar sin ADR/backlog posterior.

## POST-H-033-E - Policy/guard pattern catalogs

### Objetivo

Crear catalogos versionados para patrones de guards de seguridad, manteniendo patrones built-in no removibles para defensa base.

### Alcance

Aplicar a:

- `PromptInjectionGuard`;
- `ToolInjectionGuard`;
- `SecretGuard`, donde sea seguro;
- otros guards de policy que usen patrones extensibles.

No deben migrarse defensas base criticas a un catalogo que el operador pueda desactivar.

### Entregables

- `docs/schemas/policy_guard_pattern_catalog.schema.json`.
- `.devpilot/policy/guard_pattern_catalog.json`.
- Modulo `policy/guard_catalog.py`.
- Integracion con `prompt_guard.py`, `tool_injection_guard.py` y `secrets.py` donde aplique.
- Catalogo de patrones extensibles.
- Built-in mandatory patterns.
- Tests adversariales.
- Reporte de auditoria POST-H-033-E.
- Manifest POST-H-033-E.

### Politica minima

- Los patrones criticos built-in no se pueden eliminar.
- Las extensiones locales pueden agregar reglas, no debilitar reglas core.
- Un patron critico no puede cambiar a warning sin ADR/backlog.
- El catalogo debe declarar source, version y owner.
- Findings no deben incluir payload crudo.

### Criterios PASS

- No se puede deshabilitar una regla critica sin ADR/backlog.
- Catalogo valida contra schema.
- Tests adversariales siguen pasando.
- Payloads siguen redactados.
- Catalogo invalido no abre bypass.
- Pattern extensions se reportan con rule source.

### Criterios BLOCK

- Regla critica desactivable por JSON.
- Prompt injection pasa por catalogo invalido.
- SecretGuard filtra payload crudo.
- Tool injection logra cambiar target o tool.
- External API/remote/write se habilita por patron local.

### Validacion focal esperada

```powershell
$env:PYTHONPATH="src"
python -m pytest -p no:ddtrace --assert=plain `
  tests/test_post_h_033_policy_guard_pattern_catalogs.py `
  tests/test_prompt_injection_guard.py `
  tests/test_secret_guard_hardening.py `
  tests/test_policy_engine.py `
  tests/test_policy_engine_approval_rbac_enforcement.py `
  tests/test_post_h_032_tool_calling_contract.py `
  -q

python -m devpilot_core schema validate --schema-id PolicyGuardPatternCatalog --instance .devpilot/policy/guard_pattern_catalog.json --json
```

Si `tests/test_post_h_032_tool_calling_contract.py` aun no existe al ejecutar POST-H-033, se debe sustituir por los tests disponibles de policy/tool injection y registrar la dependencia en el TCR.

## POST-H-033-F - Docs governance rule registry

### Objetivo

Crear un registry declarativo para reglas de docs governance, integrado con source registry, que permita auditar severidad, criticality, required_tests, frontmatter requirements y lifecycle por dato/documento.

### Alcance

No debe reemplazar source registry. Debe complementarlo. Source registry sigue describiendo fuentes; rule registry describe como se gobiernan y validan.

### Entregables

- `docs/schemas/docs_governance_rule_registry.schema.json`.
- `.devpilot/docs_governance/rule_registry.json`.
- Modulo `docs_governance/rule_registry.py`.
- Integracion con `DocumentationGovernanceValidator`.
- Rule source/version en governance report.
- Tests de source-of-truth drift, required_tests, severity y lifecycle.
- Reporte de auditoria POST-H-033-F.
- Manifest POST-H-033-F.

### Reglas candidatas

- statuses que requieren frontmatter;
- severidades bloqueantes;
- reglas de required_tests para fuentes criticas;
- reglas de source-of-truth drift;
- reglas de historical/current authority;
- lifecycle permitido;
- criticality por dominio;
- sync requirements entre Markdown/JSON.

### Criterios PASS

- Docs governance sigue bloqueando source-of-truth drift.
- Reglas son auditables y versionadas.
- Source registry y rule registry validan en conjunto.
- Critical/source-of-truth sin tests sigue bloqueando.
- Frontmatter required sigue aplicando donde corresponda.
- Reporte indica rule source/version.

### Criterios BLOCK

- Drift de source-of-truth deja de bloquear.
- Critical docs sin required_tests pasan.
- Historical active authority deja de advertir.
- Rule registry invalido produce success.
- Source registry y rule registry se contradicen sin finding.

### Validacion focal esperada

```powershell
$env:PYTHONPATH="src"
python -m pytest -p no:ddtrace --assert=plain `
  tests/test_post_h_033_docs_governance_rule_registry.py `
  tests/test_documentation_governance_validator.py `
  tests/test_documentation_source_registry_schema.py `
  tests/test_documentation_governance_backlogs.py `
  tests/test_documentation_governance_sync.py `
  tests/test_schema_validator.py `
  -q

python -m devpilot_core schema validate --schema-id DocsGovernanceRuleRegistry --instance .devpilot/docs_governance/rule_registry.json --json
python -m devpilot_core docs-governance validate --json
```

## 9. Definition of Done del backlog POST-H-033

El backlog completo se puede cerrar solo si:

- Existe inventario machine-readable de validadores y plan de migracion.
- Frontmatter usa schema/catalogo como fuente primaria con fallback temporal.
- Readiness usa requirements registry como fuente primaria con fallback temporal.
- MIASI semantic validator reporta rule source/version y conserva no-go gates.
- Guard catalogs permiten extensiones sin desactivar defensas core.
- Docs governance rule registry se integra con source registry.
- Los schemas nuevos estan registrados en `schema_catalog`.
- Los tests focales pasan.
- TCR v1/v2, source registry y project_state quedan sincronizados.
- README, runbook y changelog explican que la migracion es progresiva.
- No se introduce LLM judge ni dependencia remota.
- No se relajan severidades criticas.
- No se habilitan capacidades sensibles.

## 10. Quality gates requeridos

### Gates existentes obligatorios

Deben seguir pasando:

```powershell
python -m devpilot_core docs-governance validate --json
python -m devpilot_core test-contracts validate --json
python -m devpilot_core test-contracts validate-v2 --json
python -m devpilot_core project-state validate --json
python -m devpilot_core schema list --json
python -m devpilot_core cli-registry guard --json
```

### Gate nuevo recomendado

Crear subgate:

```text
schema-backed-validator-governance
```

El gate debe verificar:

- inventario de validadores completo;
- catalogos validos contra schema;
- fallbacks declarados;
- reglas criticas no desactivables;
- no-go gates preservados;
- docs governance sigue bloqueando drift;
- frontmatter/readiness mantienen compatibilidad;
- reports indican rule source/version.

## 11. Regresion focal acumulada recomendada

Durante POST-H-033 no se recomienda usar `pytest -q` completo como validacion primaria de cada micro-sprint. La validacion focal acumulada debe incluir:

```powershell
$env:PYTHONPATH="src"
python -m pytest -p no:ddtrace --assert=plain `
  tests/test_post_h_033_validator_inventory_migration_plan.py `
  tests/test_post_h_033_frontmatter_schema_backed_validator.py `
  tests/test_post_h_033_readiness_requirements_registry.py `
  tests/test_post_h_033_miasi_semantic_rules_registry.py `
  tests/test_post_h_033_policy_guard_pattern_catalogs.py `
  tests/test_post_h_033_docs_governance_rule_registry.py `
  tests/test_frontmatter_validator.py `
  tests/test_precode_readiness.py `
  tests/test_artifact_profile_registry.py `
  tests/test_artifact_validator.py `
  tests/test_validation_gateway.py `
  tests/test_miasi_registry.py `
  tests/test_miasi_semantic_validator.py `
  tests/test_miasi_semantic_validator_fixtures.py `
  tests/test_miasi_semantic_report_model.py `
  tests/test_documentation_governance_validator.py `
  tests/test_documentation_source_registry_schema.py `
  tests/test_policy_engine.py `
  tests/test_prompt_injection_guard.py `
  tests/test_secret_guard_hardening.py `
  tests/test_schema_registry.py `
  tests/test_schema_validator.py `
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
| Catalogo invalido abre bypass | Critico | Fallback seguro y finding BLOCK |
| Regla critica desactivable | Critico | `cannot_disable_without_adr` y built-in mandatory |
| Cambio de severidad rompe compatibilidad | Alto | Tests before/after y migration report |
| Doble fuente permanente | Medio/alto | Deprecation plan por fallback |
| MIASI no-go se relaja | Critico | Tests negativos remote/plugin/connector |
| Docs governance pierde blocking drift | Alto | Tests de source registry + rule registry |
| Validadores se vuelven demasiado configurables | Alto | Engine estable, schema estricto, defensas core en codigo |

## 13. Dependencias

- POST-H-004 MIASI semantic validator.
- POST-H-009 documentation governance.
- POST-H-012 policy/approval/RBAC hardening.
- POST-H-024 onboarding readiness preview.
- POST-H-025 production-ready declaration gate.
- POST-H-032 tool calling contract, si se usa para tests de guard catalogs.

POST-H-033 puede ejecutarse despues de POST-H-025, pero debe coordinarse con POST-H-032 si los catalogs afectan tool injection o agent tool calls.

## 14. Decisiones arquitectonicas

No se requiere ADR para iniciar POST-H-033 si se mantiene:

- validacion deterministic;
- catalogos locales versionados;
- fallbacks seguros;
- reglas criticas no desactivables;
- sin LLM judge;
- sin capacidades sensibles nuevas.

Debe crearse ADR si se propone:

- permitir desactivar reglas criticas;
- reemplazar validadores deterministas por LLM;
- cargar reglas ejecutables dinamicas;
- permitir plugins de validacion;
- reducir severidades de no-go gates.

## 15. Ruta recomendada en el repo

Guardar este backlog en:

```text
docs/backlogs/POST-H-033_schema_backed_validators_declarative_semantics.md
```

Opcionalmente, si se mantiene un documento top-level por backlog activo:

```text
docs/POST-H-033_schema_backed_validators_declarative_semantics.md
```

## 16. Commit sugerido para incorporar el backlog

```bash
git add docs/backlogs/POST-H-033_schema_backed_validators_declarative_semantics.md
git commit -m "Add POST-H-033 schema-backed validators backlog"
```

## 17. Cierre esperado de POST-H-033

POST-H-033 debe cerrar con DevPilot conservando la fortaleza de sus validadores deterministas, pero con reglas mas auditables, versionadas y explicables. El resultado correcto no es hacer todo configurable; es separar reglas declarativas de engines, preservar defensas base y hacer que cada PASS/BLOCK pueda rastrearse a un schema, registry, catalogo y version.


## Estado de implementación acumulado

### POST-H-033-A — Validator inventory and migration plan

Estado: `implemented-initial`.

Se agregan `ValidatorInventory` y `ValidatorMigrationReport` como contratos schema-backed para inventariar validadores determinísticos y planear la migración progresiva de reglas hardcodeadas hacia catálogos versionados. Este micro-sprint no cambia comportamiento runtime de validadores: frontmatter, readiness, MIASI semantic, docs governance, policy guards y schema validator conservan su ejecución actual.

Artefactos principales:

- `.devpilot/validation/validator_inventory.json`.
- `.devpilot/validation/validator_migration_plan.json`.
- `docs/schemas/validator_inventory.schema.json`.
- `docs/schemas/validator_migration_report.schema.json`.
- `src/devpilot_core/validation/validator_inventory.py`.
- `tests/test_post_h_033_validator_inventory_migration_plan.py`.

Restricciones explícitas: no se introduce LLM judge, no se agregan dependencias externas, no se relajan no-go gates, no se habilita red/API externa/remote/plugin/connector write y las defensas `security-core` no pueden ser deshabilitadas por configuración local.
