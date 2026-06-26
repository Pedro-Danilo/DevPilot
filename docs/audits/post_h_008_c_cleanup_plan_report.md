# POST-H-008-C — Cleanup plan dry-run report

Estado: `implemented-initial`.

## Veredicto

`POST-H-008-C` implementa una primera versión industrial y conservadora del planificador de limpieza runtime. La capacidad es local-first, dry-run por defecto y no habilita exportación, redacción ni ejecución remota.

## Artefactos implementados

```text
src/devpilot_core/runtime_state/cleanup.py
docs/schemas/runtime_state_cleanup_plan.schema.json
tests/test_runtime_state_cleanup_plan.py
docs/post_h_008_c_manifest.json
```

## Comandos

```powershell
python -m devpilot_core runtime-state cleanup-plan --json
python -m devpilot_core runtime-state cleanup-plan --write-report --json
python -m devpilot_core runtime-state cleanup --dry-run --json
python -m devpilot_core runtime-state cleanup --execute --confirm-cleanup --json
python -m devpilot_core schema validate --schema-id RuntimeStateCleanupPlan --instance outputs/reports/runtime_state_cleanup_plan.json --json
```

## Controles de seguridad

```text
- Dry-run por defecto.
- --execute sin --confirm-cleanup produce BLOCK.
- --execute solo borra safe-cleanup.
- docs/, src/, tests/, .devpilot/project_state.json, .devpilot/runtime_state_policy.json y .devpilot/testing/ son never-delete.
- Artefactos sensibles se clasifican como requires-approval.
- No red, no APIs externas, no remote execution.
```

## Alcance no implementado

```text
- Export/redacción: POST-H-008-D.
- Runtime-state hygiene quality gate: POST-H-008-E.
- Rotación industrial por cuotas/tamaño máximo: evolución posterior de POST-H-008 o POST-H-010.
```

## Riesgos mitigados

| Riesgo | Mitigación |
|---|---|
| Borrado accidental de source-of-truth | Clasificación never-delete y tests de bloqueo. |
| Limpieza destructiva por defecto | Dry-run default y confirmación explícita. |
| Borrado de trazas sensibles sin redacción | requires-approval, no safe-cleanup. |
| Auto-contaminación por trazas del comando | Runtime-state lifecycle commands omiten EventLogger normal. |

## Estado industrial

Primera versión gobernada. Es suficiente para planificar limpieza y ejecutar solo limpieza segura explícita, pero no reemplaza aún un sistema completo de retención, redacción, backup, cuotas, auditoría firmada o enforcement de release.
