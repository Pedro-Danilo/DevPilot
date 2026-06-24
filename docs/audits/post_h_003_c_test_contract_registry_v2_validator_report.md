---
title: "POST-H-003-C — Validator v2 y perfiles de ejecución"
doc_id: "POST-H-003-C-AUDIT"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
approval: "internal"
updated: "2026-06-24"
---

# POST-H-003-C — Validator v2 y perfiles de ejecución

## Propósito

Registrar la evidencia técnica de `POST-H-003-C`, cuyo objetivo es convertir el Test Contract Registry v2 migrado en un artefacto validable semánticamente y seleccionable por perfiles operativos locales.

## Estado

`implemented-initial`.

El micro-sprint no cierra todavía `POST-H-003`. El hito continúa con `POST-H-003-D — Integración con Test Impact Analyzer` y `POST-H-003-E — Quality gate y documentación`.

## Alcance implementado

```text
- TestContractRegistryV2Validator.
- CLI test-contracts validate-v2.
- CLI test-contracts profile --profile <id>.
- Perfiles p0-critical, security, release, impact y docs-historical.
- Validación de paths, comandos recomendados y safety flags.
- Pruebas focales del validator, perfiles y CLI.
```

## Funcionamiento

`test-contracts validate-v2` lee `.devpilot/testing/test_contract_registry_v2.json`, valida el schema `TestContractRegistryV2` y aplica controles semánticos locales:

```text
- unicidad de contract_id;
- existencia de test_files;
- existencia de watched_paths;
- comandos recomendados dentro de allowlist local;
- ausencia de network/external_api en POST-H-003-C;
- safety_exception para mutaciones declaradas;
- separación entre criticality y risk_level;
- presencia de perfiles mínimos.
```

`test-contracts profile` selecciona contratos y comandos recomendados, pero no ejecuta pruebas.

## Integración dentro de DevPilot

La integración queda en la capa CLI y en `src/devpilot_core/testing/`. No modifica `QualityGate` todavía y no reemplaza `test-contracts validate` v1. La compatibilidad v1 se mantiene como requisito hasta cierre de `POST-H-003`.

## Criterios PASS

```text
PASS si validate-v2 retorna ok=true.
PASS si los perfiles seleccionan contratos sin ejecutar tests.
PASS si v1 sigue validando con 87 contratos.
PASS si hardening sigue sin findings bloqueantes.
PASS si no hay red, APIs externas, ejecución remota ni mutaciones de código.
```

## Criterios BLOCK

```text
BLOCK si falta un test_file.
BLOCK si recommended_commands contiene tokens de shell o comandos no permitidos.
BLOCK si network_allowed/external_api_allowed se activa.
BLOCK si una excepción de mutación no exige aprobación humana.
BLOCK si se intenta usar el perfil como executor de tests.
```

## Riesgos y limitaciones

```text
- Los perfiles son selectores, no ejecutores.
- Las clasificaciones needs-review siguen visibles hasta refinamiento posterior.
- impact_v2 aún no cruza paths cambiados; eso queda para POST-H-003-D.
- Quality gate TCR v2 queda para POST-H-003-E.
```

## Comandos de validación

```powershell
python -m pytest tests/test_test_contract_registry_profiles_v2.py tests/test_test_contract_registry_migration.py tests/test_test_contract_registry_v2.py tests/test_test_contract_registry.py tests/test_schema_registry.py -q
python -m devpilot_core test-contracts validate-v2 --json
python -m devpilot_core test-contracts profile --profile p0-critical --json
python -m devpilot_core test-contracts profile --profile security --json
python -m devpilot_core test-contracts profile --profile release --json
python -m devpilot_core test-contracts profile --profile impact --json
python -m devpilot_core test-contracts profile --profile docs-historical --json
python -m devpilot_core test-contracts validate --json
python -m devpilot_core validate docs --json
python -m devpilot_core project-state validate --json
python -m devpilot_core quality-gate run --profile hardening --json
```

## No-go gates

```text
No se ejecutan tests desde JSON.
No se habilita red.
No se habilitan APIs externas.
No se habilita ejecución remota.
No se habilita connector write.
No se habilita plugin execution.
```

## Próximo paso

`POST-H-003-D — Integración con Test Impact Analyzer`.
