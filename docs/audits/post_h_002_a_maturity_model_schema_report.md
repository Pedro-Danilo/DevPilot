---
title: "POST-H-002-A — Modelo de madurez y schema"
doc_id: "POST-H-002-A-AUDIT"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-06-23"
approval: "internal"
---

# POST-H-002-A — Modelo de madurez y schema

## Propósito

Documentar la implementación inicial del modelo de madurez y del contrato estructural `MaturityDashboard`, primer micro-sprint del hito `POST-H-002 — Maturity dashboard local basado en assessment post-H`.

## Estado

Estado del micro-sprint: `implemented-initial`.

Esta entrega prepara el dashboard local, pero no implementa todavía los lectores de fuentes post-H, el generador de reportes, el comando CLI `maturity dashboard` ni integración ApplicationService. Es una base de modelo/schema para los micro-sprints siguientes.

## Alcance implementado

- Paquete `src/devpilot_core/maturity/`.
- Enums controlados para estado de capacidad, madurez, cobertura de pruebas y riesgo.
- Dataclasses `MaturityCapability`, `MaturityDashboard`, `RoadmapDependency` y `SafetySignal`.
- Schema `docs/schemas/maturity_dashboard.schema.json`.
- Registro `SCHEMA-DEVPL-MATURITY-DASHBOARD-V1` en `docs/schemas/schema_catalog.json`.
- Pruebas focales en `tests/test_post_h_002_maturity_dashboard.py`.

## Criterios PASS

- El schema valida una instancia mínima generada desde el modelo.
- El vocabulario diferencia `production-ready-local` de un claim genérico `production-ready`.
- Los estados `blocked`, `stub` y `planned` están disponibles.
- Las señales de seguridad mantienen `remote_execution_enabled=false`, `connector_write_enabled=false`, `plugin_execution_enabled=false` y `external_apis_enabled_by_default=false`.
- El catálogo de schemas lista el nuevo contrato.

## Criterios BLOCK

- Cualquier instancia que use `production-ready` como estado genérico.
- Cualquier instancia que active remote execution, connector write, plugin execution o APIs externas por defecto.
- Cualquier implementación que escriba reportes del dashboard antes de `POST-H-002-C/D`.

## Riesgos y limitaciones

- El modelo todavía no infiere madurez desde fuentes reales. Esa responsabilidad queda para `POST-H-002-B` y `POST-H-002-C`.
- El dashboard no tiene CLI todavía. Esa responsabilidad queda para `POST-H-002-D`.
- El estado `production-ready-local` es solo vocabulario permitido; no constituye declaración de producto listo. La declaración final queda en `POST-H-025`.

## Artefactos

```text
src/devpilot_core/maturity/__init__.py
src/devpilot_core/maturity/models.py
docs/schemas/maturity_dashboard.schema.json
tests/test_post_h_002_maturity_dashboard.py
docs/post_h_002_a_manifest.json
```

## Comandos de validación

```powershell
$env:PYTHONPATH="src"
python -m pytest tests/test_post_h_002_maturity_dashboard.py -q
python -m pytest tests/test_schema_registry.py tests/test_post_h_002_maturity_dashboard.py -q
python -m devpilot_core schema list --json
python -m devpilot_core quality-gate run --profile hardening --json
```
