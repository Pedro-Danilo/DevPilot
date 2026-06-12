# Patch FUNC-SPRINT-51 — AgentRuntime v2 model-aware

Incluye los componentes nuevos/modificados para implementar `FUNC-SPRINT-51 — AgentRuntime v2 model-aware en modo monoagente`.

## Limpieza esperada antes de versionar

No versionar:

- `outputs/`
- `.devpilot/devpilot.db`
- `.devpilot/providers.yaml`
- `.devpilot/rollback/`
- `__pycache__/`
- `.pytest_cache/`
- `Log_consola*`
- `DELETE_MANIFEST.md`
- `PATCH_COMPONENTS_MANIFEST*`
- `func_sprint_47.diff`
- `func_sprint_50.diff`

## Comandos de validación sugeridos

```powershell
python -m pytest tests/test_agent_runtime.py tests/test_agent_runtime_v2.py tests/test_sprint_51_documentation.py -q
python -m devpilot_core agent run documentation-audit --target docs/01_requirements --provider mock --json
python -m devpilot_core eval run --json
python -m devpilot_core validate all --json
python -m devpilot_core miasi validate --json
python -m devpilot_core readiness-check --strict --json
```
