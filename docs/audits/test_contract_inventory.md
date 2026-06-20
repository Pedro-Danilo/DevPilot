---
title: "Inventario de contratos de test — POST-H-001"
doc_id: "DEVPL-AUDIT-POST-H-001-TEST-CONTRACT-INVENTORY"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
standard: "MIPSoftware"
extension: "MIASI"
phase: "POST-FASE-H"
created: "2026-06-19"
updated: "2026-06-19"
approval: "approved_by_owner"
---

# Inventario de contratos de test — POST-H-001

## Estado

`approved`. Inventario implementado como soporte documental del registry `.devpilot/testing/test_contract_registry.json`.

## Propósito

Este inventario clasifica la suite de pruebas de DevPilot después del cierre de Fase H. Su objetivo es separar contratos históricos, estado global mutable, contratos de schemas, gates y smoke tests.

## Capas

| Capa | Propósito | Ejemplos | Regla |
|---|---|---|---|
| `global-state` | Validar último hito y sincronización global | `tests/test_project_global_state.py` | Único dueño del estado global mutable. |
| `historical-sprint` | Validar artefactos propios de cada sprint | `tests/test_sprint_85_documentation.py` ... `tests/test_sprint_99_documentation.py` | No debe validar `last_completed_sprint` ni `next_sprint` global. |
| `quality-gate` | Validar gates y contratos agregados | `tests/test_quality_gate.py`, `tests/test_test_contract_registry.py` | Debe seguir siendo local/read-only por defecto. |
| `feature` | Validar nueva funcionalidad focal | `tests/test_test_impact.py` | Debe ser rápida y determinística. |
| `integration` | Validar contratos transversales | `tests/test_schema_registry.py` | Debe ejecutarse ante cambios de schemas. |
| `ui-smoke` | Smoke visual/local | `tests/test_visual_product_smoke.py` | No debe requerir red ni cloud. |

## Contrato operativo

La fuente declarativa es `.devpilot/testing/test_contract_registry.json`. El registry documenta intención y rutas, pero no ejecuta tests desde JSON. La ejecución sigue bajo `pytest`, `quality-gate` y comandos explícitos.

## Hallazgo principal

Antes de POST-H-001, múltiples tests históricos duplicaban expectativas globales del README, backlog, changelog y `next_sprint`. Después del sprint, esas expectativas quedan centralizadas en `tests/test_project_global_state.py`.

## Criterios PASS

- Registry valida por schema.
- Existe un único contrato `global-state`.
- Los contratos `historical-sprint` declaran `mutable_global_state_allowed=false`.
- El perfil `quality-gate hardening` incluye contratos de test, estado global e industrial readiness.

## Criterios BLOCK

- Tests históricos vuelven a validar último hito global.
- El impact analyzer no recomienda full pytest ante rutas desconocidas.
- Se elimina cobertura en lugar de mover responsabilidades.
