---
doc_id: "POST-H-003-B-AUDIT"
title: "POST-H-003-B — Migrador v1 → v2 dry-run"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-06-24"
approval: "internal"
---

# POST-H-003-B — Migrador v1 → v2 dry-run

## Propósito

Implementar una migración determinística, local y segura desde el `Test Contract Registry` v1 hacia una representación v2 schema-backed, sin reemplazar el registry v1 ni ejecutar pruebas desde JSON.

## Estado

Estado: `implemented-initial`.

El micro-sprint crea el migrador, expone el comando `test-contracts migrate-v2`, genera `.devpilot/testing/test_contract_registry_v2.json` de forma explícita y conserva `.devpilot/testing/test_contract_registry.json` como fuente operativa v1.

## Alcance implementado

```text
src/devpilot_core/testing/migration.py
src/devpilot_core/testing/__init__.py
src/devpilot_core/cli.py
.devpilot/testing/test_contract_registry_v2.json
tests/test_test_contract_registry_migration.py
docs/post_h_003_b_manifest.json
docs/audits/post_h_003_b_test_contract_registry_v2_migration_report.md
docs/04_quality/test_contract_registry_2_design.md
docs/backlogs/POST-H-003_test_contract_registry_2.md
README.md
docs/05_operations/runbook.md
docs/release/CHANGELOG.md
```

## Funcionamiento

El comando principal es:

```powershell
python -m devpilot_core test-contracts migrate-v2 --dry-run --json
```

Por defecto, el comando no escribe archivos. Lee `.devpilot/testing/test_contract_registry.json`, transforma cada contrato v1 a contrato v2, valida el payload en memoria contra `TestContractRegistryV2` y reporta gaps de clasificación.

La escritura se habilita únicamente con:

```powershell
python -m devpilot_core test-contracts migrate-v2 --write-output .devpilot/testing/test_contract_registry_v2.json --json
```

El migrador rechaza sobrescribir `.devpilot/testing/test_contract_registry.json` y exige que el output quede dentro del workspace.

## Integración dentro de DevPilot

`TestContractRegistryV2Migrator` se integra con:

```text
SchemaValidator
CommandResult
Finding
CLI test-contracts
schema TestContractRegistryV2
TestContractRegistry v1
```

No se integra todavía con `quality-gate`, `TestContractRegistryV2Validator`, perfiles ejecutables ni `test-impact analyze-v2`; esas capacidades quedan para `POST-H-003-C` y `POST-H-003-D`.

## Criterios PASS

```text
PASS si los 87 contratos v1 tienen representación v2.
PASS si el payload migrado valida contra TestContractRegistryV2.
PASS si los gaps de clasificación quedan como findings explícitos.
PASS si .devpilot/testing/test_contract_registry.json no se sobrescribe.
PASS si test-contracts validate v1 sigue PASS.
PASS si no se ejecutan tests desde JSON.
PASS si no hay red, APIs externas, remote execution, connector write ni plugin execution.
```

## Criterios BLOCK

```text
BLOCK si se intenta escribir sobre .devpilot/testing/test_contract_registry.json.
BLOCK si el output apunta fuera del workspace.
BLOCK si el payload migrado no cumple el schema v2.
BLOCK si la migración requiere red, APIs externas o ejecución remota.
BLOCK si se habilita ejecución automática de pruebas desde el registry.
```

## Riesgos y limitaciones

La clasificación de `POST-H-003-B` es determinística e inicial. Muchos campos se infieren desde metadata v1 limitada; por eso se emiten findings `TEST_CONTRACT_V2_CLASSIFICATION_GAP`. Esos gaps no bloquean B, pero deben ser revisados y endurecidos en `POST-H-003-C`, `POST-H-003-D` y `POST-H-003-E`.

Limitaciones vigentes:

```text
No existe validate-v2 CLI todavía.
No hay perfiles ejecutables p0-critical/security/release.
No hay integración impact_v2.
No hay subgate TCR v2 en quality-gate.
V1 sigue siendo la fuente operativa.
```

## Comandos de validación

```powershell
$env:PYTHONPATH="src"
python -m pytest tests/test_test_contract_registry_migration.py tests/test_test_contract_registry_v2.py tests/test_test_contract_registry.py tests/test_schema_registry.py -q
python -m devpilot_core test-contracts migrate-v2 --dry-run --json
python -m devpilot_core test-contracts migrate-v2 --write-output .devpilot/testing/test_contract_registry_v2.json --json
python -m devpilot_core schema validate --schema-id TestContractRegistryV2 --instance .devpilot/testing/test_contract_registry_v2.json --json
python -m devpilot_core test-contracts validate --json
python -m devpilot_core validate docs --json
python -m devpilot_core quality-gate run --profile hardening --json
```

## No-go gates

```text
NO-GO si se elimina registry v1.
NO-GO si se sobrescribe registry v1.
NO-GO si se ejecutan pruebas desde JSON.
NO-GO si se habilita network/external API/remote execution.
NO-GO si se declara que la clasificación v2 ya es definitiva.
```

## Próximo paso

`POST-H-003-C — Validator v2 y perfiles de ejecución` debe implementar `test-contracts validate-v2` y perfiles `p0-critical`, `security`, `release`, `impact` y `docs-historical`, conservando compatibilidad v1.
