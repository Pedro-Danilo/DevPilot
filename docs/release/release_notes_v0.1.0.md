---
title: "Release notes v0.1.0 — DevPilot Local"
doc_id: "DEVPL-REL-NOTES-V0-1-0"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
standard: "MIPSoftware"
extension: "MIASI"
phase: "FASE-A-OLA-0"
sprint: "FUNC-SPRINT-19"
release: "v0.1.0"
updated: "2026-06-10"
approval: "approved_by_owner_for_internal_release"
---

# Release notes v0.1.0 — DevPilot Local

## 1. Propósito

`v0.1.0` es el primer **release técnico interno** de DevPilot Local después del cierre funcional `FUNC-SPRINT-00` a `FUNC-SPRINT-18`.

No es una distribución productiva final. Es una baseline local-first, reproducible y auditable para continuar la Fase A.

## 2. Estado

| Campo | Valor |
|---|---|
| Release | `v0.1.0` |
| Estado | `internal-technical-release` |
| Sprint | `FUNC-SPRINT-19` |
| Ciclo cerrado | `FUNC-SPRINT-00` a `FUNC-SPRINT-18` |
| Próximo sprint | `FUNC-SPRINT-20` |

## 3. Resumen funcional

Este release consolida:

- CLI local y contratos `CommandResult`/`Finding`/`ExitCode`.
- Validadores documentales, checklist pre-code y readiness strict.
- Standards Registry MIPSoftware/MIASI.
- ReportEngine JSON/Markdown.
- EventLogger JSONL.
- Workspace Manager.
- PolicyEngine, PathGuard, SecretGuard y CostGuard.
- SQLite LocalStore v0.
- MIASI Agent/Tool/Policy registries ejecutables.
- AgentRuntime documental mock/local.
- Evaluation Harness offline.
- Git status read-only y RepoInventory.
- Patch review y code review en dry-run.
- Safe Refactor Planner plan-only.
- ModelAdapter mock y ProviderRegistry.
- ApplicationService y contrato interno para Desktop/Web futuro.

## 4. Cambios incorporados por FUNC-SPRINT-19

| Tipo | Cambio |
|---|---|
| Auditoría | Se creó `docs/audits/functional_cycle_00_18_closure_report.md`. |
| Release | Se creó `docs/release/release_manifest_v0.1.0.json`. |
| Release notes | Se creó este documento. |
| Verificación | Se creó `scripts/verify_release_v0_1_0.py`. |
| Pruebas | Se creó `tests/test_release_manifest.py`. |
| Documentación | Se sincronizaron README, runbook y backlog funcional histórico. |
| Manifest | Se creó `docs/functional_sprint_19_manifest.json`. |

## 5. Límites explícitos

Este release **no** implementa:

- UI desktop real.
- UI web real.
- Servidor HTTP o IPC.
- Clientes reales Ollama/LM Studio/OpenAI/Gemini.
- APIs externas activas.
- Approval workflow operativo.
- Aplicación real de patches.
- Refactor execution.
- Sandbox real.
- Rollback automático.
- RAG, MCP o multiagentes avanzados.
- CI/CD remoto.

## 6. Comandos de verificación

```powershell
$env:PYTHONPATH="src"
python -m pytest -q
python -m devpilot_core --version
python -m devpilot_core workspace status --json
python -m devpilot_core standards status --json
python -m devpilot_core readiness-check --strict --json
python -m devpilot_core miasi validate --json
python -m devpilot_core eval run --json
python -m devpilot_core app contract --json
```

Verificación agrupada opcional:

```powershell
$env:PYTHONPATH="src"
python scripts/verify_release_v0_1_0.py --json
```

## 7. Criterios PASS

- `pytest -q` en PASS.
- Comandos smoke en PASS.
- El release manifest no referencia outputs runtime como fuente.
- El ZIP limpio excluye `outputs/`, `.pytest_cache/`, `__pycache__/`, `.venv/`, `.git/` y `.devpilot/devpilot.db`.
- README y runbook describen el último hito real como `FUNC-SPRINT-19`.

## 8. Criterios BLOCK

- Falla la regresión general.
- El release incluye outputs runtime o DB local.
- Se documenta como implementado algo que está planned, disabled o future.
- Se introduce dependencia externa, API key o red sin ADR.
- Falta trazabilidad entre sprint, manifest y release.

## 9. Próximo paso

Continuar con:

```text
FUNC-SPRINT-20 — Reconciliación documental post-18 y roadmap vivo
```
