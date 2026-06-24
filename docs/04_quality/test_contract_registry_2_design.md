---
doc_id: "POST-H-003-A-DESIGN"
title: "POST-H-003-A — Test Contract Registry v2 schema design"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-06-24"
approval: "internal"
---

# POST-H-003-A — Test Contract Registry v2 schema design

## Propósito

Definir el contrato estructural inicial de `Test Contract Registry 2.0` sin reemplazar el registry v1 vigente. El objetivo es separar explícitamente **dominio**, **criticidad**, **riesgo**, **costo**, **perfil de ejecución**, **tipo de prueba**, **impacto** y **restricciones de seguridad** para evitar que la cantidad de tests o el predominio de pruebas históricas/documentales se interprete como cobertura industrial suficiente.

## Estado

Estado: `implemented-initial`.

Este diseño registra el schema `SCHEMA-DEVPL-TEST-CONTRACT-REGISTRY-V2` y fixtures válidos/ inválidos. No ejecuta tests desde JSON, no migra los 87 contratos vigentes, no sustituye `.devpilot/testing/test_contract_registry.json` y no agrega todavía CLI `validate-v2`.

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

## Criterios PASS

```text
PASS si el schema v2 está registrado en schema_catalog.
PASS si el fixture válido cumple el schema.
PASS si fixtures inválidos son rechazados.
PASS si v1 sigue validando con test-contracts validate.
PASS si criticality y risk_level son campos separados y obligatorios.
PASS si red/API/mutaciones no pueden quedar sin declaración.
```

## Criterios BLOCK

```text
BLOCK si se rompe test-contracts validate v1.
BLOCK si se elimina o reemplaza el registry v1.
BLOCK si el schema no diferencia criticidad de riesgo.
BLOCK si un contrato puede omitir network_allowed/external_api_allowed/mutations_allowed.
BLOCK si se permite network/API/mutaciones sin safety_exception.
```

## Comandos de validación

```powershell
python -m pytest tests/test_test_contract_registry_v2.py tests/test_test_contract_registry.py tests/test_schema_registry.py -q
python -m devpilot_core test-contracts validate --json
python -m devpilot_core validate docs --json
python -m devpilot_core quality-gate run --profile hardening --json
```

## Limitaciones

Esta entrega es una primera versión de diseño industrial del contrato v2. La migración determinística, el validator CLI v2, los perfiles ejecutables y la integración con impact analyzer quedan para `POST-H-003-B` a `POST-H-003-E`.

## Relación con el roadmap

`POST-H-003-A` habilita la base contractual para que DevPilot pueda priorizar pruebas por riesgo/costo/impacto antes de endurecer Policy/MIASI, arquitectura y claims `production-ready-local`.
