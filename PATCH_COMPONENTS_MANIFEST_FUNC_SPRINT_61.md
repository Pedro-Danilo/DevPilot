# PATCH_COMPONENTS_MANIFEST_FUNC_SPRINT_61

## Propósito

Componentes nuevos y modificados para `FUNC-SPRINT-61 — CLI de trazas y métricas: trace report, trace inspect, metrics summary`.

## Alcance

Este patch agrega consulta CLI local de trazas y métricas, sin UI, sin red, sin exporters y sin dependencias externas obligatorias.

## Archivos incluidos

- `README.md`
- `docs/05_operations/runbook.md`
- `docs/05_operations/observability_plan.md`
- `docs/06_miasi/observability_card.md`
- `docs/devpilot_backlog_fase_E_agentops_observabilidad.md`
- `docs/functional_backlog_after_precode.md`
- `docs/audits/func_sprint_61_trace_metrics_cli_audit.md`
- `docs/functional_sprint_61_manifest.json`
- `src/devpilot_core/cli.py`
- `src/devpilot_core/observability/__init__.py`
- `src/devpilot_core/observability/trace_queries.py`
- `tests/test_observability_cli.py`
- `tests/test_sprint_61_documentation.py`
- `tests/test_sprint_32_documentation.py`
- `tests/test_sprint_33_documentation.py`
- `tests/test_sprint_34_documentation.py`
- `tests/test_sprint_35_documentation.py`
- `tests/test_sprint_36_documentation.py`
- `tests/test_sprint_37_documentation.py`
- `tests/test_sprint_38_documentation.py`
- `tests/test_sprint_39_documentation.py`
- `tests/test_sprint_40_documentation.py`
- `tests/test_sprint_41_documentation.py`
- `tests/test_sprint_42_documentation.py`
- `tests/test_sprint_43_documentation.py`
- `tests/test_sprint_44_documentation.py`
- `tests/test_sprint_45_documentation.py`
- `tests/test_sprint_46_documentation.py`
- `tests/test_sprint_47_documentation.py`
- `tests/test_sprint_48_documentation.py`
- `tests/test_sprint_49_documentation.py`
- `tests/test_sprint_50_documentation.py`
- `tests/test_sprint_51_documentation.py`
- `tests/test_sprint_52_documentation.py`
- `tests/test_sprint_53_documentation.py`
- `tests/test_sprint_54_documentation.py`
- `tests/test_sprint_55_documentation.py`
- `tests/test_sprint_56_documentation.py`
- `tests/test_sprint_57_documentation.py`
- `tests/test_sprint_58_documentation.py`
- `tests/test_sprint_59_documentation.py`
- `tests/test_sprint_60_documentation.py`

## Patch unificado

- `unified_diff_FUNC_SPRINT_61_trace_metrics_cli.patch`

## Validaciones ejecutadas

```text
PYTHONPATH=src pytest tests/test_observability_cli.py -q                  # 4 passed
PYTHONPATH=src pytest tests/test_sprint_61_documentation.py -q           # 3 passed
PYTHONPATH=src pytest tests/test_sprint_*_documentation.py -q            # 143 passed
PYTHONPATH=src pytest tests/test_observability_cli.py tests/test_trace_store.py tests/test_event_logger.py tests/test_trace_context.py tests/test_local_store.py tests/test_metrics_collector.py tests/test_agentops_instrumentation.py tests/test_agent_runtime.py tests/test_agent_runtime_v2.py tests/test_policy_engine.py tests/test_approval_cli.py tests/test_model_governance.py -q # 68 passed
PYTHONPATH=src python -m devpilot_core validate-artifact docs/audits/func_sprint_61_trace_metrics_cli_audit.md --json # PASS
PYTHONPATH=src python -m devpilot_core schema validate-manifest docs/functional_sprint_61_manifest.json --json # PASS
PYTHONPATH=src python -m devpilot_core miasi validate --json # PASS
PYTHONPATH=src python -m devpilot_core validate all --json # PASS
```

## Notas

Los reportes generados en `outputs/`, la base `.devpilot/devpilot.db`, cachés y logs de consola no se incluyen en este patch.
