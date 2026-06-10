---
title: "FUNC-SPRINT-22 — Auditoría Schema Validator"
doc_id: "DEVPL-AUDIT-FUNC-SPRINT-22-SCHEMA-VALIDATOR"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
standard: "MIPSoftware"
extension: "MIASI"
phase: "FASE-A-OLA-1"
sprint: "FUNC-SPRINT-22"
updated: "2026-06-10"
approval: "approved_by_owner_for_internal_progress"
---
# FUNC-SPRINT-22 — Auditoría Schema Validator

## 1. Propósito

Documentar la implementación de `FUNC-SPRINT-22 — Schema Validator y schemas de contratos transversales`, explicando propósito, funcionamiento, integración, comandos, pruebas, criterios PASS/BLOCK, riesgos y evolución posterior.

## 2. Estado

`implemented-initial`.

Sprint 22 implementa validación estructural de instancias JSON contra JSON Schemas locales. No implementa validación semántica de negocio, policy, MIASI, trazabilidad ni autorización.

## 3. Alcance implementado

| Elemento | Estado |
|---|---|
| `SchemaValidator` | Implementado. |
| Comando `schema validate` | Implementado. |
| Validación de `CommandResult` | Implementada mediante schema y pruebas. |
| Validación de `Finding` | Implementada mediante schema y pruebas. |
| Validación de `ApplicationResponse` | Implementada mediante schema y pruebas. |
| Validación de `EvidenceReport` | Implementada para reportes persistidos. |
| Dependencia `jsonschema` | Aprobada por ADR-0010 y declarada en `pyproject.toml`. |
| Resolución de `$ref` local | Implementada mediante registry en memoria. |
| Validación semántica | Fuera de alcance. |

## 4. Artefactos creados

| Artefacto | Propósito | Integración | Rol dentro de DevPilot |
|---|---|---|---|
| `src/devpilot_core/schemas/validator.py` | Validar instancias JSON contra schemas locales. | Usado por CLI `schema validate`. | Motor inicial de Schema Validator. |
| `src/devpilot_core/schemas/errors.py` | Definir errores controlados de dependencia e inputs. | Consumido por `SchemaValidator`. | Evita stacktraces no controlados. |
| `docs/02_architecture/adrs/ADR-0010-schema-validation-dependency.md` | Justificar `jsonschema`. | Vincula arquitectura, dependencia y backlog. | Control de decisión arquitectónica. |
| `docs/audits/func_sprint_22_schema_validator_audit.md` | Auditar el sprint. | Referencia para cierre y revisión. | Evidencia técnica del sprint. |
| `docs/functional_sprint_22_manifest.json` | Manifest de sprint. | Docs-as-code y trazabilidad. | Registro formal de entregables. |
| `tests/test_schema_validator.py` | Probar validación y CLI. | Suite pytest. | Gate automatizado del sprint. |

## 5. Artefactos modificados

| Artefacto | Ajuste | Propósito |
|---|---|---|
| `pyproject.toml` | Agrega `jsonschema>=4.22,<5`. | Dependencia runtime para Draft 2020-12. |
| `src/devpilot_core/cli.py` | Agrega `schema validate`. | Exponer validador por CLI. |
| `src/devpilot_core/schemas/__init__.py` | Exporta `SchemaValidator`. | Integración del paquete. |
| `src/devpilot_core/schemas/models.py` | Agrega `validation_enabled_sprint`. | Reflejar activación de validación por Sprint 22. |
| `docs/schemas/schema_catalog.json` | Marca schemas como validables. | Catálogo actualizado. |
| `docs/schemas/*.schema.json` | Actualiza metadata y `$ref` de findings. | Preparar validación real. |
| `README.md` | Sincroniza hito y comandos. | Entrada operativa rápida. |
| `docs/05_operations/runbook.md` | Agrega procedimiento Sprint 22. | Guía de operación local. |
| `docs/devpilot_backlog_fase_A_baseline_industrial_minima.md` | Marca Sprint 22 implementado. | Backlog vigente. |
| `docs/functional_backlog_after_precode.md` | Agrega transición post-Sprint 22. | Trazabilidad histórica. |
| `tests/test_release_manifest.py` | Permite evolución de `pyproject.toml`. | Evita regresión falsa por dependencia ADR-gobernada. |

## 6. Funcionamiento técnico

`SchemaValidator` ejecuta el siguiente flujo:

```text
schema validate
  -> resolve schema por ruta, schema_id o contract
  -> leer schema JSON local
  -> leer instancia JSON local
  -> construir registry local de schemas docs/schemas/*.schema.json
  -> ejecutar jsonschema Draft 2020-12
  -> convertir errores a Finding
  -> devolver CommandResult
  -> opcionalmente escribir EvidenceReport con --write-report
```

No se ejecuta red, no se leen secretos, no se llama a modelos y no se modifica el archivo validado.

## 7. Comandos de uso

```powershell
$env:PYTHONPATH="src"
python -m devpilot_core schema validate --schema docs/schemas/command_result.schema.json --instance <archivo-command-result.json> --json
python -m devpilot_core schema validate --schema CommandResult --instance <archivo-command-result.json> --json
python -m devpilot_core schema validate --schema SCHEMA-DEVPL-FINDING-V1 --instance <archivo-finding.json> --json
python -m devpilot_core schema validate --schema EvidenceReport --instance outputs/reports/schema_list.json --json
python -m devpilot_core schema validate --schema docs/schemas/application_response.schema.json --instance <archivo-application-response.json> --json --write-report
```

## 8. Pruebas implementadas

`tests/test_schema_validator.py` cubre:

- instancia válida de `CommandResult`;
- instancia inválida de `Finding`;
- instancia válida de `ApplicationResponse`;
- JSON inválido sin stacktrace;
- CLI JSON parseable;
- CLI con instancia inválida en BLOCK;
- `--write-report` de validación;
- validación de `EvidenceReport` persistido.

## 9. Criterios PASS

- `pytest -q` pasa.
- Instancias válidas pasan.
- Instancias inválidas generan findings accionables.
- Errores de parseo no exponen stacktrace.
- `schema validate` soporta `--json`.
- `schema validate` soporta `--write-report`.
- La dependencia externa tiene ADR.
- La resolución de `$ref` es local.

## 10. Criterios BLOCK

- El validador acepta instancias inválidas sin findings.
- El validador falla con excepción no controlada.
- Se intenta resolver `$ref` por red.
- Se agrega dependencia sin ADR.
- Se documenta validación semántica como implementada.

## 11. Riesgos y limitaciones

- Primera versión: `implemented-initial`.
- Los schemas son estructurales y pueden requerir endurecimiento.
- `additionalProperties=true` mantiene compatibilidad, pero permite campos extra.
- JSON Schema no reemplaza reglas de MIASI, readiness, policy, approval ni trazabilidad.
- El validador no procesa YAML; eso queda para Sprint 23 si se validan workspace/providers.

## 12. Evolución recomendada

- Sprint 23: schemas MIASI, workspace, providers y sprint manifests.
- Sprint 24: `ValidationGateway` para unificar validadores.
- Futuros sprints: drift checks entre dataclasses Python y schemas.

## 13. Veredicto

`FUNC-SPRINT-22` queda implementado y preparado para cierre si la suite completa y los comandos smoke permanecen en PASS.
