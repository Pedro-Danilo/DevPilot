---
title: "ADR-0010 — Dependencia jsonschema para SchemaValidator"
doc_id: "DEVPL-ADR-0010"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
standard: "MIPSoftware"
extension: "MIASI"
phase: "FUNC-SPRINT-22"
updated: "2026-06-10"
accepted_by: "Ordóñez"
accepted_at: "2026-06-10"
acceptance_scope: "FUNC-SPRINT-22 Schema Validator"
approval: "approved_by_owner"
---
# ADR-0010 — Dependencia jsonschema para SchemaValidator

## Estado

Accepted.

## Contexto

`FUNC-SPRINT-21` creó un `Schema Registry` local para contratos transversales de DevPilot, pero dejó explícito que no validaba instancias JSON. `FUNC-SPRINT-22` debe implementar `schema validate` para validar `CommandResult`, `Finding`, `ApplicationResponse` y reportes de evidencia contra JSON Schemas.

Los schemas registrados declaran JSON Schema Draft 2020-12. Python estándar no incluye un validador JSON Schema completo, y una implementación manual parcial aumentaría el riesgo de aceptar instancias inválidas o divergir de la especificación.

## Decisión

Agregar `jsonschema>=4.22,<5` como dependencia runtime de DevPilot y usarla dentro de `src/devpilot_core/schemas/validator.py`.

La validación debe mantenerse local-first:

- no debe hacer llamadas de red;
- no debe requerir API keys;
- debe resolver referencias locales desde `docs/schemas/`;
- debe convertir errores en `CommandResult` y `Finding`;
- debe generar reportes solo bajo `outputs/reports/` cuando se use `--write-report`.

## Alternativas consideradas

| Alternativa | Evaluación |
|---|---|
| Implementar validador propio con stdlib | Menor dependencia, pero alto riesgo de cobertura incompleta y falsos positivos. |
| Usar validación mínima de tipos manuales | Útil para prototipo, insuficiente para Draft 2020-12 y referencias `$ref`. |
| Usar `jsonschema` | Opción madura, compatible con Draft 2020-12 y referencias, con costo operativo bajo. |

## Consecuencias positivas

- DevPilot puede validar contratos estructurales reales.
- Se reduce el riesgo de drift entre CLI, reportes, DTOs y futura UI/API.
- Se soportan `$ref`, `required`, `enum`, `type`, `items`, `additionalProperties` y validadores estándar.
- La implementación queda alineada con JSON Schema en vez de una variante casera.

## Consecuencias negativas

- El proyecto deja de tener `dependencies = []`.
- Hay que instalar la dependencia al ejecutar `pip install -e .[dev]`.
- Futuras actualizaciones mayores de `jsonschema` deben evaluarse antes de subir a `5.x`.

## Funcionamiento esperado

`SchemaValidator` carga el schema y la instancia desde archivos locales, construye un registry de recursos en memoria para resolver referencias locales como `finding.schema.json`, ejecuta `jsonschema` y traduce cada error en findings accionables.

## Criterios PASS

- `schema validate` valida instancias correctas.
- Instancias inválidas generan `SCHEMA_VALIDATION_ERROR`.
- JSON inválido genera `SCHEMA_INSTANCE_INVALID_JSON`.
- La dependencia se declara en `pyproject.toml`.
- No hay resolución remota de referencias.
- `pytest -q` pasa.

## Criterios BLOCK

- Agregar dependencia sin declararla en `pyproject.toml`.
- Permitir resolución de referencias por red.
- Aceptar instancias inválidas sin findings.
- Fallar con stacktrace sin convertir a `CommandResult`.

## Riesgos

- La validación estructural no prueba semántica de negocio.
- Los schemas iniciales pueden ser demasiado permisivos por `additionalProperties=true`.
- Debe mantenerse vigilancia sobre cambios futuros de `jsonschema` y `referencing`.

## Relación con DevPilot

Esta ADR habilita la transición de `Schema Registry` a `Schema Engine` inicial. Es prerrequisito para `FUNC-SPRINT-23`, `FUNC-SPRINT-24` y la futura validación unificada de contratos bajo `ValidationGateway`.
