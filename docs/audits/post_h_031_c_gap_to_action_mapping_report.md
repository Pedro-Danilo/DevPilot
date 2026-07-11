---
doc_id: POST-H-031-C-GAP-ACTION-MAPPING-REPORT
title: "POST-H-031-C - Gap-to-action mapping report"
status: approved
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-07-10"
approval: approved
---

# POST-H-031-C - Gap-to-action mapping report

## Decisión

PASS preliminar / implemented-initial local-first.

## Alcance implementado

POST-H-031-C implementa `GapActionMap` para convertir gaps detectados por `EvidenceGraph` y `OperatorHealthSummary` en acciones concretas, priorizadas, verificables y seguras para operador.

Artefactos principales:

- `docs/schemas/gap_action_map.schema.json`.
- `.devpilot/evidence/gap_action_rules.json`.
- `src/devpilot_core/evidence_graph/gap_actions.py`.
- `ApplicationService.gap_action_map(...)`.
- CLI `python -m devpilot_core evidence gaps --json`.
- API local protegida `GET /api/v1/operator/gaps`.
- `tests/test_post_h_031_gap_to_action_mapping.py`.

## Invariantes de seguridad

- `local_first=true`.
- `read_only=true`.
- `commands_executed=false`.
- `network_used=false`.
- `external_api_used=false`.
- `source_mutations_performed=false`.
- `secrets_read=false`.
- `devpilot_db_read=false`.
- Las acciones recomendadas son advisory y no se ejecutan automáticamente.
- No se relajan no-go gates.
- No se versionan outputs runtime.

## Criterios PASS

- `GapActionMap` valida contra schema.
- Todo gap blocking exige acción concreta.
- Las acciones incluyen comando, verificación, owner, criterio de cierre, backlog relacionado y riesgo si se ignora.
- Las reglas mínimas requeridas están presentes.
- Gaps unknown se exponen explícitamente.
- La salida es determinística para el mismo input.
- API/CLI/ApplicationService mantienen contrato local-first y read-only.

## Criterios BLOCK

- Blocking gap sin acción.
- Acción que recomiende `--execute` o mutación destructiva sin approval.
- Acción que relaje no-go gates.
- Acción que recomiende versionar outputs runtime.
- Mapping por texto frágil sin IDs estables cuando existan IDs.

## Validación focal

```powershell
$env:PYTHONPATH="src"
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD="1"
python -m pytest -p no:ddtrace --assert=plain tests/test_post_h_031_gap_to_action_mapping.py -q
python -m devpilot_core evidence gaps --json
python -m devpilot_core evidence gaps --json --write-report
python -m devpilot_core schema validate --schema-id GapActionMap --instance outputs/reports/gap_action_map.json --json
```

## Limitaciones

Esta es una primera versión de mapeo operacional. POST-H-031-D debe consolidar claims/no-go dashboard y POST-H-031-E debe producir UX de export redactado de evidencia. Este sprint no ejecuta acciones ni resuelve automáticamente gaps.
