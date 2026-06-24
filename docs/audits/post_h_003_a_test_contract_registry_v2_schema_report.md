---
doc_id: "POST-H-003-A-AUDIT"
title: "POST-H-003-A — Diseño de schema v2 y compatibilidad"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-06-24"
approval: "internal"
---

# POST-H-003-A — Diseño de schema v2 y compatibilidad

## Propósito

Auditar la implementación inicial del schema `Test Contract Registry v2` y su compatibilidad con el registry v1 vigente.

## Estado

Estado: `implemented-initial`.

El micro-sprint registra el contrato estructural v2, fixtures de validación y pruebas focales, sin reemplazar el registry v1 y sin agregar ejecución automática de pruebas.

## Alcance implementado

```text
docs/schemas/test_contract_registry_v2.schema.json
docs/schemas/schema_catalog.json
docs/04_quality/test_contract_registry_2_design.md
src/devpilot_core/testing/contracts_v2.py
src/devpilot_core/testing/__init__.py
tests/fixtures/test_contract_registry_v2/*.json
tests/test_test_contract_registry_v2.py
docs/post_h_003_a_manifest.json
```

## Funcionamiento

`TestContractRegistryV2Design` valida archivos o payloads JSON contra el schema v2 usando `SchemaValidator`. El schema exige clasificación explícita por dominio, criticidad, riesgo, tipo de prueba, costo, perfil de ejecución, paths observados, comandos recomendados y flags de seguridad.

## Integración dentro de DevPilot

La integración se limita al catálogo de schemas y al paquete `devpilot_core.testing`. No se modifica la semántica de `TestContractRegistry` v1 ni el comando `python -m devpilot_core test-contracts validate --json`.

## Criterios PASS

```text
PASS si el schema v2 queda registrado y resoluble por SchemaValidator.
PASS si el fixture válido pasa.
PASS si fixtures inválidos fallan.
PASS si v1 sigue validando.
PASS si schema registry sigue PASS.
PASS si quality-gate hardening sigue PASS.
```

## Criterios BLOCK

```text
BLOCK si se rompe v1.
BLOCK si se migra o sobrescribe el registry v1 antes de POST-H-003-B.
BLOCK si no se diferencian criticality y risk_level.
BLOCK si red/API/mutaciones se permiten sin safety_exception.
```

## Riesgos y limitaciones

La clasificación v2 todavía no está aplicada a los 87 contratos reales. Las dimensiones de dominio/riesgo/costo pueden requerir calibración durante la migración. La ejecución selectiva por impacto no se habilita aún.

## Comandos de validación

```powershell
python -m pytest tests/test_test_contract_registry_v2.py tests/test_test_contract_registry.py tests/test_schema_registry.py -q
python -m devpilot_core test-contracts validate --json
python -m devpilot_core validate docs --json
python -m devpilot_core quality-gate run --profile hardening --json
```

## No-go gates

```text
No remote execution.
No connector write.
No plugin execution.
No external APIs.
No replacement of v1 registry.
No automatic test execution from registry JSON.
```

## Próximo paso

`POST-H-003-B — Migrador v1 → v2 dry-run` debe producir una migración determinística y un reporte de gaps sin sobrescribir v1 por defecto.
