---
title: "FUNC-SPRINT-23 — Contract Schemas Audit"
doc_id: "DEVPL-AUDIT-FUNC-SPRINT-23-CONTRACT-SCHEMAS"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
standard: "MIPSoftware"
extension: "MIASI"
phase: "FASE-A-BASELINE-INDUSTRIAL-MINIMA"
sprint: "FUNC-SPRINT-23"
updated: "2026-06-10"
approval: "approved_by_owner_for_internal_baseline"
---

# FUNC-SPRINT-23 — Contract Schemas Audit

## 1. Propósito

Este artefacto audita la implementación de `FUNC-SPRINT-23 — Schemas MIASI, Workspace, Providers y Sprint Manifests`.

El propósito del sprint es ampliar el motor de contratos de DevPilot desde los contratos transversales iniciales (`CommandResult`, `Finding`, `EvidenceReport`, `ApplicationResponse`) hacia contratos operativos críticos:

- MIASI Agent Registry;
- MIASI Tool Registry;
- MIASI Policy Matrix;
- `.devpilot/project.yaml`;
- `.devpilot/providers.yaml.example`;
- `docs/functional_sprint_XX_manifest.json`.

## 2. Estado

Estado del sprint: `implemented-initial`.

La implementación es local-first, estructural y no destructiva. No ejecuta agentes, no ejecuta herramientas, no llama APIs externas, no lee API keys reales y no modifica artefactos objetivo. Cuando se usa `--write-report`, únicamente escribe evidencia bajo `outputs/reports/`.

## 3. Funcionamiento técnico

`FUNC-SPRINT-23` agrega `BuiltinContractValidator`, una fachada pequeña sobre `SchemaValidator`.

Flujo general:

```text
CLI schema validate-* 
  -> BuiltinContractValidator
  -> SchemaValidator
  -> jsonschema Draft 2020-12 local
  -> CommandResult + Finding[]
  -> opcional ReportEngine bajo outputs/reports/
```

Para archivos YAML controlados por DevPilot, la implementación usa parsers estrechos y determinísticos:

- `parse_workspace_project_yaml()` para `.devpilot/project.yaml`;
- `parse_provider_config_yaml()` para `.devpilot/providers.yaml.example`.

Estos parsers no son YAML general. Solo soportan la forma que DevPilot ya genera o mantiene. Si el proyecto necesita YAML completo, se debe abrir una ADR para evaluar `PyYAML` u otra dependencia.

## 4. Integración y rol dentro de DevPilot

El sprint integra contratos estructurales antes de avanzar hacia `ValidationGateway` y `Traceability Engine`.

Rol dentro de DevPilot:

- fortalece MIASI con validación estructural previa a reglas de negocio;
- convierte workspace y providers en contratos verificables;
- exige que manifests funcionales declaren archivos, comandos, pruebas, criterios PASS/BLOCK, riesgos y siguiente sprint;
- prepara el terreno para `FUNC-SPRINT-24`, donde las validaciones deberán orquestarse desde un gateway inicial.

La validación estructural no sustituye validaciones semánticas existentes:

- `miasi validate` sigue validando reglas MIASI de negocio;
- `workspace status` sigue validando estado operativo;
- `model providers` sigue aplicando política de proveedores;
- `readiness-check` sigue componiendo gates pre-code.

## 5. Artefactos creados

- `src/devpilot_core/schemas/builtins.py`;
- `docs/schemas/miasi_agent_registry.schema.json`;
- `docs/schemas/miasi_tool_registry.schema.json`;
- `docs/schemas/miasi_policy_matrix.schema.json`;
- `docs/schemas/workspace_project.schema.json`;
- `docs/schemas/provider_config.schema.json`;
- `docs/schemas/functional_sprint_manifest.schema.json`;
- `tests/test_contract_schemas.py`;
- `tests/test_sprint_23_documentation.py`;
- `docs/audits/func_sprint_23_contract_schemas_audit.md`;
- `docs/functional_sprint_23_manifest.json`.

## 6. Artefactos modificados

- `src/devpilot_core/cli.py` para exponer comandos específicos;
- `src/devpilot_core/schemas/__init__.py` para exportar `BuiltinContractValidator`;
- `src/devpilot_core/schemas/validator.py` para permitir validación de payloads en memoria;
- `docs/schemas/schema_catalog.json` para registrar seis nuevos schemas;
- `README.md`;
- `docs/05_operations/runbook.md`;
- `docs/devpilot_backlog_fase_A_baseline_industrial_minima.md`;
- `docs/functional_backlog_after_precode.md`;
- `tests/test_sprint_22_documentation.py` para permitir el avance del `first_open_sprint` a Sprint 24.

## 7. Comandos de uso y verificación

```powershell
python -m devpilot_core schema validate-miasi --json
python -m devpilot_core schema validate-workspace --json
python -m devpilot_core schema validate-providers --json
python -m devpilot_core schema validate-manifest docs/functional_sprint_23_manifest.json --json
python -m devpilot_core schema validate-miasi --json --write-report
python -m pytest tests/test_contract_schemas.py -q
python -m pytest -q
```

## 8. Criterios PASS

- MIASI Agent Registry pasa schema estructural.
- MIASI Tool Registry pasa schema estructural.
- MIASI Policy Matrix pasa schema estructural.
- `.devpilot/project.yaml` pasa schema tras parseo controlado.
- `.devpilot/providers.yaml.example` pasa schema sin secretos reales.
- Manifests funcionales 19+ pasan schema.
- `schema validate-miasi`, `schema validate-workspace`, `schema validate-providers` y `schema validate-manifest` devuelven `CommandResult`.
- Todos los comandos soportan `--json`.
- Los comandos específicos soportan `--write-report`.
- `pytest -q` pasa.

## 9. Criterios BLOCK

- Un contrato crítico no está registrado en `schema_catalog.json`.
- Un contrato crítico no tiene archivo `.schema.json`.
- Un provider acepta campo `api_key` o secreto crudo.
- Un manifest funcional omite archivos, comandos, pruebas, criterios PASS/BLOCK o riesgos.
- Un comando nuevo no devuelve JSON parseable.
- Se sustituye validación de negocio MIASI por schema estructural.
- Se agrega dependencia YAML sin ADR.

## 10. Riesgos

- Los parsers YAML son estrechos; no deben usarse como parser YAML general.
- Los schemas siguen siendo estructurales; no expresan reglas de negocio complejas.
- Puede existir drift entre schemas y dataclasses si no se amplía la cobertura en próximos sprints.
- `provider_config.schema.json` bloquea campos de secreto crudo, pero no sustituye SecretGuard.
- `functional_sprint_manifest.schema.json` es compatible con manifests históricos 19+, por eso es flexible en algunos campos.

## 11. Pruebas implementadas

`tests/test_contract_schemas.py` verifica:

- validación estructural MIASI por CLI;
- validación de workspace por CLI;
- validación de providers por CLI;
- validación de manifests 19 a 23;
- bloqueo de registry MIASI inválido;
- bloqueo de provider con secreto crudo;
- parseo esperado de `.devpilot/project.yaml`;
- generación de reportes con `--write-report`.

`tests/test_sprint_23_documentation.py` verifica sincronización documental del sprint.

## 12. Evolución recomendada

`FUNC-SPRINT-24` debe usar estos contratos desde un `ValidationGateway` inicial y comenzar la migración de perfiles documentales hardcoded hacia configuración versionada.
