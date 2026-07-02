---
doc_id: "NEW-PROJECT-TEST-STRATEGY-TEMPLATE"
title: "Template — Test strategy for new DevPilot project"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-07-02"
approval: "approved_by_owner"
phase: "POST-FASE-H"
template_id: "test_strategy"
artifact_kind: "new_project_template"
created_by: "POST-H-024-B"
implementation_status: "implemented-initial"
preliminary: true
local_first: true
dry_run: true
no_external_apis_required: true
no_secrets_allowed: true
---

# Test strategy — {{project_name}}

## 1. Objetivo de calidad

```text
Objetivo: demostrar que el MVP cumple requisitos, seguridad y trazabilidad sin depender de red ni APIs externas.
Estrategia base: pruebas determinísticas + fixtures locales + contratos de artefactos.
```

## 2. Capas de prueba

| Capa | Propósito | Ejemplo de comando | Criterio PASS |
|---|---|---|---|
| Unit | Lógica aislada | `python -m pytest tests/unit -q` | sin fallos |
| Contract | JSON/schema/docs | `python -m devpilot_core schema list --json` | schemas existentes |
| Integration | flujo local | `python -m pytest tests/integration -q` | sin red ni mutaciones no aprobadas |
| Safety | no-go gates | `python -m pytest tests/safety -q` | flags bloqueados |

## 3. Fixtures locales

```text
fixtures permitidos: datos sintéticos, mínimos y no sensibles
fixtures prohibidos: datos personales reales, tokens, claves, credenciales, dumps productivos
```

## 4. Evaluación de agentes

Si el proyecto incluye agentes, la evaluación debe separar:

```text
mock agent determinístico
modelo local opcional
API externa futura con costo y aprobación
```

## 5. Comandos iniciales recomendados

```powershell
python -m pytest -q
python -m devpilot_core docs-governance validate --json
python -m devpilot_core test-contracts validate --json
python -m devpilot_core test-contracts validate-v2 --json
```

## 6. Criterios PASS/BLOCK

PASS si cada capacidad del MVP tiene una prueba o contrato verificable.

BLOCK si las pruebas requieren credenciales reales, red obligatoria, datos sensibles o ejecución destructiva.
