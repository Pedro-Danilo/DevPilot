---
title: "FUNC-SPRINT-21 — Schema Registry y catálogo de contratos DevPilot"
doc_id: "DEVPL-AUDIT-FUNC-SPRINT-21-SCHEMA-REGISTRY-001"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-06-10"
approval: "technical-review"
phase: "FASE-A-BASELINE-INDUSTRIAL-MINIMA"
sprint: "FUNC-SPRINT-21"
---

# FUNC-SPRINT-21 — Schema Registry y catálogo de contratos DevPilot

## 1. Propósito

Implementar el primer nivel contractual de Fase A: un **Schema Registry local, versionado y listable** para contratos internos de DevPilot.

Este sprint no valida todavía instancias JSON contra schemas. Su propósito es crear el catálogo, los archivos `.schema.json`, el módulo Python `src/devpilot_core/schemas/`, el comando `schema list` y las pruebas de integridad del catálogo. La validación profunda queda expresamente diferida a `FUNC-SPRINT-22 — Schema Validator y schemas de contratos transversales`.

## 2. Estado

`FUNC-SPRINT-21` queda implementado como primera versión del Schema Registry.

Estado técnico:

```text
implemented-initial
```

La implementación es local-first, dependency-free, sin llamadas de red, sin API keys, sin ejecución destructiva y sin validación de instancias.

## 3. Alcance implementado

Se implementaron los entregables definidos por el backlog Fase A:

| Tarea | Estado | Evidencia |
|---|---:|---|
| Crear paquete `schemas` | PASS | `src/devpilot_core/schemas/` |
| Crear `SchemaSpec` y `SchemaRegistry` | PASS | `models.py`, `registry.py` |
| Crear carpeta de schemas | PASS | `docs/schemas/` |
| Crear comando `schema list` | PASS | `python -m devpilot_core schema list --json` |
| Crear tests de registry | PASS | `tests/test_schema_registry.py` |
| Documentar README/runbook | PASS | `README.md`, `docs/05_operations/runbook.md` |

## 4. Contratos registrados

El catálogo inicial registra siete schemas base:

| Schema | Contrato | Estado |
|---|---|---|
| `command_result.schema.json` | `CommandResult` | draft/registered |
| `finding.schema.json` | `Finding` | draft/registered |
| `evidence_report.schema.json` | `EvidenceReport` | draft/registered |
| `application_request.schema.json` | `ApplicationRequest` | draft/registered |
| `application_response.schema.json` | `ApplicationResponse` | draft/registered |
| `service_capability.schema.json` | `ServiceCapability` | draft/registered |
| `interface_route_contract.schema.json` | `InterfaceRouteContract` | draft/registered |

Todos los schemas están bajo `docs/schemas/` y son referenciados desde `docs/schemas/schema_catalog.json`.

## 5. Funcionamiento

El flujo de `schema list` es:

```text
CLI schema list
  -> SchemaRegistry(root).list()
  -> carga docs/schemas/schema_catalog.json
  -> construye SchemaSpec por entrada
  -> detecta schema_id duplicados
  -> detecta archivos .schema.json faltantes
  -> detecta metadata obligatoria vacía
  -> devuelve CommandResult
  -> opcionalmente genera EvidenceReport con --write-report
```

La salida incluye:

- `summary.schemas_total`;
- `summary.schemas_existing`;
- `summary.duplicate_schema_ids`;
- `summary.missing_schema_paths`;
- `schemas[]` con `schema_id`, `title`, `version`, `path`, `description`, `status`, `owner`, `sprint`, `dialect`, `validates_instances` y `contract`.

## 6. Integración y rol dentro de DevPilot

El Schema Registry cumple tres roles dentro de DevPilot:

1. **Contrato:** enumera los contratos JSON que serán usados por CLI, reportes, ApplicationService y futuras UI/API.
2. **Trazabilidad:** cada schema queda versionado con ID estable y ruta reproducible.
3. **Preparación industrial:** habilita la transición hacia Schema Validator, manifest validation, MIASI structural validation y ValidationGateway.

La implementación se integra con:

- `CommandResult` como contrato de salida;
- `ReportEngine` para `--write-report`;
- `EventLogger` para eventos de comando;
- `LocalStore` como persistencia best-effort;
- `README.md` y runbook como guías operativas.

## 7. Comandos de uso

Listar schemas registrados:

```powershell
python -m devpilot_core schema list --json
```

Listar schemas y generar evidencia local:

```powershell
python -m devpilot_core schema list --json --write-report
```

Validar la suite completa:

```powershell
python -m pytest -q
```

Pruebas específicas:

```powershell
python -m pytest tests/test_schema_registry.py -q
```

## 8. Criterios PASS

El sprint pasa si:

- `schema list` devuelve `CommandResult` JSON parseable.
- Todos los schemas declarados en `schema_catalog.json` existen.
- No hay `schema_id` duplicados.
- Cada schema tiene versión y descripción.
- `--write-report` genera `outputs/reports/schema_list.json` y `outputs/reports/schema_list.md`.
- No se introducen dependencias externas.
- No se hacen llamadas de red.
- `python -m pytest -q` pasa.

## 9. Criterios BLOCK

El sprint se bloquea si:

- Un schema listado no existe.
- Hay IDs duplicados.
- El comando no devuelve JSON válido.
- El catálogo rompe local-first o requiere red.
- Se afirma que Sprint 21 valida instancias JSON, porque esa capacidad corresponde a Sprint 22.

## 10. Riesgos y límites

| Riesgo | Tratamiento |
|---|---|
| Confundir registro con validación | Todos los artefactos declaran que `validates_instances=false` y que la validación queda para Sprint 22. |
| Schemas preliminares incompletos | Se marcan como `draft/registered`; la estabilización se hará al introducir `SchemaValidator`. |
| Drift entre dataclasses y schemas | Se mitiga con tests de catálogo y se resolverá mejor con validación de instancias. |
| Aumentar acoplamiento del CLI | La lógica queda en `src/devpilot_core/schemas/`; el CLI solo orquesta. |

## 11. Pruebas implementadas

`tests/test_schema_registry.py` cubre:

- listado exitoso del catálogo real;
- detección de `schema_id` duplicado en fixture temporal;
- detección de archivo schema faltante;
- verificación de existencia de archivos registrados;
- salida CLI JSON parseable;
- generación de reportes con `--write-report`.

## 12. ADR

No se creó una ADR nueva porque este sprint no introduce dependencias externas ni cambia la arquitectura de validación. El uso de JSON Schema es documental/catalogado; todavía no se incorpora una librería de validación como `jsonschema`.

Una ADR sí será necesaria si en Sprint 22 se decide agregar una dependencia externa para validación JSON Schema completa.

## 13. Evolución posterior

Pendiente para próximos sprints:

- `FUNC-SPRINT-22`: `schema validate` para validar instancias JSON.
- `FUNC-SPRINT-23`: schemas MIASI, workspace, providers y manifests.
- `FUNC-SPRINT-24`: perfiles documentales data-driven y `ValidationGateway`.
- `FUNC-SPRINT-25+`: trazabilidad SDLC ejecutable y validación transversal.
