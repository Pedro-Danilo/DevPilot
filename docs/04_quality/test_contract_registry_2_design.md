---
doc_id: "POST-H-003-A-DESIGN"
title: "POST-H-003 — Test Contract Registry v2 design and migration"
status: "approved"
version: "1.3.0"
owner: "Ordóñez"
updated: "2026-06-24"
approval: "internal"
---

# POST-H-003 — Test Contract Registry v2 design and migration

## Propósito

Definir el contrato estructural inicial de `Test Contract Registry 2.0` sin reemplazar el registry v1 vigente. El objetivo es separar explícitamente **dominio**, **criticidad**, **riesgo**, **costo**, **perfil de ejecución**, **tipo de prueba**, **impacto** y **restricciones de seguridad** para evitar que la cantidad de tests o el predominio de pruebas históricas/documentales se interprete como cobertura industrial suficiente.

## Estado

Estado: `implemented-initial`.

Este diseño registra el schema `SCHEMA-DEVPL-TEST-CONTRACT-REGISTRY-V2`, fixtures válidos/ inválidos y, desde `POST-H-003-B`, una migración determinística dry-run de los 88 contratos v1 hacia `.devpilot/testing/test_contract_registry_v2.json`. No ejecuta tests desde JSON, no sustituye `.devpilot/testing/test_contract_registry.json` y ya dispone de validator v2, perfiles de selección e impact analyzer v2 en modo no ejecutante.

## Alcance implementado

Se implementa:

```text
docs/schemas/test_contract_registry_v2.schema.json
tests/fixtures/test_contract_registry_v2/valid_minimal_registry.json
tests/fixtures/test_contract_registry_v2/invalid_missing_safety_flags.json
tests/fixtures/test_contract_registry_v2/invalid_network_without_exception.json
src/devpilot_core/testing/contracts_v2.py
tests/test_test_contract_registry_v2.py
```

También se registra el schema v2 en `docs/schemas/schema_catalog.json` y se actualiza el backlog `POST-H-003` a `approved`.

## Compatibilidad v1/v2

`POST-H-003-A` usa modo `parallel-read`: el registry v1 sigue siendo la fuente operativa de `python -m devpilot_core test-contracts validate --json`. El schema v2 queda disponible para diseño, pruebas focales y migración futura.

Reglas de compatibilidad:

```text
- No se elimina el registry v1.
- No se cambia el contrato de TestContractRegistry v1.
- No se sobrescribe .devpilot/testing/test_contract_registry.json.
- El schema v2 exige metadata de compatibilidad hacia v1.
- La migración v1 → v2 queda para POST-H-003-B.
- El validator CLI validate-v2 queda para POST-H-003-C.
```

## Modelo de clasificación

El contrato v2 separa dimensiones que antes quedaban implícitas:

| Dimensión | Propósito |
|---|---|
| `domain` | Ubicar el contrato por área técnica o capability. |
| `criticality` | Definir prioridad operacional `P0/P1/P2/P3`. |
| `risk_level` | Definir exposición de riesgo independiente de la prioridad. |
| `test_type` | Distinguir unit, integration, contract, security, release, documentation, schema o quality-gate. |
| `execution_profile` | Decidir si se ejecuta always, impact, release, manual o nightly-local. |
| `cost_class` | Modelar costo local/tiempo esperado. |
| `expected_duration_seconds` | Preparar planificación de suites selectivas. |
| `watched_paths` | Conectar con test-impact analyzer v2. |
| `network_allowed`, `external_api_allowed`, `mutations_allowed` | Declarar explícitamente riesgos de ejecución. |

## Reglas de seguridad

El schema exige flags explícitos para red, APIs externas y mutaciones. Si alguno de estos flags se declara en `true`, el contrato debe incluir `safety_exception`, `requires_human_approval=true` y un perfil `manual` o `release`.

Esto evita contratos ambiguos que permitan network/external API/mutaciones sin trazabilidad.

## Funcionamiento

`TestContractRegistryV2Design` usa `SchemaValidator` para validar payloads o archivos JSON contra `docs/schemas/test_contract_registry_v2.schema.json`.

La clase no ejecuta pruebas, no migra datos y no muta archivos. Su función es estabilizar el contrato estructural v2 para los siguientes micro-sprints.


## Migración v1 → v2 dry-run

`POST-H-003-B` agrega `TestContractRegistryV2Migrator` y el comando:

```powershell
python -m devpilot_core test-contracts migrate-v2 --dry-run --json
python -m devpilot_core test-contracts migrate-v2 --write-output .devpilot/testing/test_contract_registry_v2.json --json
```

La migración es determinística y local. Por defecto no escribe archivos; cuando se usa `--write-output`, escribe únicamente el path explícito y rechaza sobrescribir `.devpilot/testing/test_contract_registry.json`. El resultado migrado conserva `source_contract_id`, clasifica por dominio/criticidad/riesgo/tipo/costo/perfil, y genera findings `TEST_CONTRACT_V2_CLASSIFICATION_GAP` para dejar trazabilidad de inferencias y revisiones pendientes.

La versión generada en `.devpilot/testing/test_contract_registry_v2.json` incluye 88 contratos v2 y valida contra `TestContractRegistryV2`. Las clasificaciones `needs-review` no bloquean el micro-sprint B: son deuda explícita para `POST-H-003-C` y `POST-H-003-D`.

## Criterios PASS

```text
PASS si el schema v2 está registrado en schema_catalog.
PASS si el fixture válido cumple el schema.
PASS si fixtures inválidos son rechazados.
PASS si v1 sigue validando con test-contracts validate.
PASS si migrate-v2 representa los 88 contratos v1 en v2.
PASS si el output `.devpilot/testing/test_contract_registry_v2.json` valida contra schema v2.
PASS si criticality y risk_level son campos separados y obligatorios.
PASS si red/API/mutaciones no pueden quedar sin declaración.
```

## Criterios BLOCK

```text
BLOCK si se rompe test-contracts validate v1.
BLOCK si se elimina o reemplaza el registry v1.
BLOCK si migrate-v2 intenta sobrescribir el registry v1.
BLOCK si el schema no diferencia criticidad de riesgo.
BLOCK si un contrato puede omitir network_allowed/external_api_allowed/mutations_allowed.
BLOCK si se permite network/API/mutaciones sin safety_exception.
```

## Comandos de validación

```powershell
python -m pytest tests/test_test_contract_registry_v2.py tests/test_test_contract_registry.py tests/test_schema_registry.py -q
python -m devpilot_core test-contracts validate --json
python -m devpilot_core test-contracts migrate-v2 --dry-run --json
python -m devpilot_core test-contracts migrate-v2 --write-output .devpilot/testing/test_contract_registry_v2.json --json
python -m devpilot_core schema validate --schema-id TestContractRegistryV2 --instance .devpilot/testing/test_contract_registry_v2.json --json
python -m devpilot_core validate docs --json
python -m devpilot_core quality-gate run --profile hardening --json
```

## Limitaciones

Esta entrega es una primera versión de diseño industrial del contrato v2. El validator CLI v2, los perfiles ejecutables y la integración con impact analyzer quedan para `POST-H-003-C` a `POST-H-003-E`.

## Relación con el roadmap

`POST-H-003-A` habilita la base contractual para que DevPilot pueda priorizar pruebas por riesgo/costo/impacto antes de endurecer Policy/MIASI, arquitectura y claims `production-ready-local`.


## POST-H-003-C — Validator v2 y perfiles de ejecución

### Propósito

`POST-H-003-C` convierte el registry v2 migrado en un artefacto validable semánticamente. La validación cubre estructura JSON, paths locales, comandos recomendados, no-go gates de red/API/mutaciones y selección por perfiles.

### Comandos

```powershell
python -m devpilot_core test-contracts validate-v2 --json
python -m devpilot_core test-contracts profile --profile p0-critical --json
python -m devpilot_core test-contracts profile --profile security --json
python -m devpilot_core test-contracts profile --profile release --json
python -m devpilot_core test-contracts profile --profile impact --json
python -m devpilot_core test-contracts profile --profile docs-historical --json
```

### Reglas de validación

```text
- El payload debe cumplir TestContractRegistryV2.
- contract_id debe ser único.
- test_files y watched_paths deben existir localmente.
- recommended_commands solo se validan como datos; no se ejecutan.
- recommended_commands se limitan a comandos locales conocidos como python -m pytest, python -m devpilot_core o el smoke fijo npm --prefix ui/web test.
- network_allowed/external_api_allowed deben permanecer false en esta etapa.
- mutations_allowed/source_mutations_allowed requieren safety_exception, aprobación humana y perfil manual/release.
```

### Perfiles

```text
p0-critical: contratos con criticality P0.
security: contratos de dominios o riesgos sensibles, o required_for_security_gate.
release: contratos required_for_release o execution_profile release.
impact: contratos con execution_profile impact.
docs-historical: contratos documentales/históricos.
```

### Limitación

Los perfiles son selectores de contratos y comandos recomendados, no ejecutores. `POST-H-003-D` agregará cruce por paths cambiados e impacto; `POST-H-003-E` integrará el cierre documental y quality gate.


## POST-H-003-D — Integración con Test Impact Analyzer

`POST-H-003-D` agrega `TestImpactAnalyzerV2` y el comando:

```powershell
python -m devpilot_core test-impact analyze-v2 --changed-paths src/devpilot_core/policy --json
```

El analyzer v2 opera así:

```text
1. Valida primero .devpilot/testing/test_contract_registry_v2.json con TestContractRegistryV2Validator.
2. Normaliza changed_paths.
3. Cruza cada ruta con test_files, watched_paths y validates de los contratos v2.
4. Aplica heurísticas explícitas para hotspots: policy/security, schemas, CLI/API, agentic runtime y release.
5. Emite matched_contracts, heuristic_recommendations, recommended_tests, recommended_commands y recommended_profiles.
6. Declara siempre tests_executed=false.
```

Reglas de seguridad:

```text
- No ejecuta pytest.
- No lanza subprocesses.
- No usa red ni APIs externas.
- No modifica fuentes.
- No convierte recomendaciones en approval automático.
- No trata los contratos históricos como cobertura funcional industrial.
```

La heurística de policy/security existe porque el registry v2 migrado todavía no contiene contratos dedicados para `governance.policy` o `security.*`. Por eso `POST-H-003-D` recomienda pruebas de policy/security como recomendaciones heurísticas y selecciona contratos P0/P1 existentes, sin inventar nuevos contratos en el registry.


## POST-H-003-E — Quality gate y cierre documental

`POST-H-003-E` integra el contrato v2 como señal de calidad local en `quality-gate run --profile hardening` mediante el subgate `test-contract-registry-v2`. Esta señal ejecuta validación estructural y semántica del registry v2, pero no ejecuta pruebas desde JSON ni invoca subprocesses de `pytest`.

Comandos de cierre:

```powershell
python -m devpilot_core test-contracts validate --json
python -m devpilot_core test-contracts validate-v2 --json
python -m devpilot_core test-impact analyze-v2 --changed-paths src/devpilot_core/policy --json
python -m devpilot_core quality-gate run --profile hardening --json
```

El hito queda cerrado como `implemented-initial`: el registry v2 está disponible para selección, validación e impacto, pero el registry v1 se mantiene por compatibilidad y la ejecución de pruebas sigue siendo explícita por operador o por flujos approval-gated.

### Criterios PASS/BLOCK de cierre

PASS si v1 y v2 validan, `quality-gate hardening` incluye `test-contract-registry-v2`, el contrato `post-h-003-test-contract-registry-2` existe y no se habilitan red, APIs externas, remote execution, connector write ni plugin execution.

BLOCK si se rompe v1, si v2 ejecuta pruebas automáticamente, si el subgate hace mutaciones de fuentes, si se ocultan contratos `needs-review` o si se declara madurez productiva local completa antes de `POST-H-025`.
