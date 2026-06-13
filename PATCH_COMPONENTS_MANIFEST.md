# PATCH FUNC-SPRINT-52 — RepoAnalysisAgent gobernado

## Propósito

Este paquete contiene únicamente los componentes nuevos o modificados para `FUNC-SPRINT-52 — RepoAnalysisAgent gobernado`.

## Contenido principal

- Nuevo `RepoAnalysisAgent` monoagente, read-only y gobernado por MIASI.
- Integración con `AgentRuntime v2`, `RepoAnalyzer`, `DependencyGraphBuilder`, `GitAdapter`, `PromptRegistry`, `ModelAdapterRouter` y `BudgetLedger`.
- Prompt versionado `repo.analysis.agent` como contrato JSON validado por Prompt Registry.
- Caso de evaluación `agent.repo_analysis_model_aware` con `mock`.
- Actualización MIASI: agent registry, tool registry y policy matrix.
- Ajuste del schema MIASI Agent Registry para admitir estado `implemented-initial`.
- Documentación, auditoría, manifest y pruebas Sprint 52.

## Comandos mínimos de verificación

```powershell
python -m pytest tests/test_repo_analysis_agent.py tests/test_sprint_52_documentation.py -q
python -m pytest tests/test_agent_runtime.py tests/test_agent_runtime_v2.py tests/test_eval_runner.py -q
python -m devpilot_core agent run repo-analysis --target . --provider mock --json
python -m devpilot_core eval run --json
python -m devpilot_core prompt validate --json
python -m devpilot_core validate all --json
python -m devpilot_core miasi validate --json
python -m devpilot_core readiness-check --strict --json
```

## Restricciones preservadas

- No incluye `outputs/`.
- No incluye base de datos `.devpilot/devpilot.db`.
- No incluye `.devpilot/providers.yaml` local.
- No incluye `.git/`, `.venv/`, caches ni logs.
- No habilita APIs externas.
- No habilita handoffs ni multiagente.
