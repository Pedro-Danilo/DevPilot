---
title: "Auditoría FUNC-SPRINT-60 — Instrumentación agentic"
doc_id: "DEVPL-AUDIT-FUNC-SPRINT-60-AGENTIC-INSTRUMENTATION"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-06-13"
approval: "approved_by_owner_direction"
phase: "FASE-E-AGENTOPS-OBSERVABILIDAD"
sprint: "FUNC-SPRINT-60"
---

# Auditoría FUNC-SPRINT-60 — Instrumentación agentic

## 1. Propósito

Verificar que `FUNC-SPRINT-60 — Instrumentación agentic: agentes, tools, approvals y model calls` conecta la observabilidad v2 con la superficie agentic real sin cambiar comportamiento funcional, sin habilitar telemetría remota y sin persistir payloads sensibles crudos.

## 2. Alcance

Incluye instrumentación best-effort de `AgentRuntime`, `AgentToolCall`, `PolicyEngine`, `ApprovalService` y `ModelAdapterRouter` mediante `AgentOpsInstrumentor`, `TraceStore` y `MetricsCollector`.

No incluye CLI pública de consulta de trazas/métricas, dashboard, OpenTelemetry remoto, multiagente, handoffs, RAG, MCP ni ejecución remota.

## 3. Resultado

Veredicto: `PASS`.

Estado: `implemented-initial`.

La implementación produce spans, eventos y métricas locales correlacionadas. La consulta operacional avanzada queda diferida a `FUNC-SPRINT-61`.

## 4. Evidencia de implementación

Archivos creados:

- `src/devpilot_core/observability/agentops.py`
- `tests/test_agentops_instrumentation.py`
- `docs/audits/func_sprint_60_agentic_instrumentation_audit.md`
- `docs/functional_sprint_60_manifest.json`
- `tests/test_sprint_60_documentation.py`

Archivos modificados principales:

- `src/devpilot_core/agents/runtime.py`
- `src/devpilot_core/agents/models.py`
- `src/devpilot_core/policy/engine.py`
- `src/devpilot_core/approval/service.py`
- `src/devpilot_core/modeling/router.py`
- `src/devpilot_core/observability/__init__.py`
- `README.md`
- `docs/05_operations/runbook.md`
- `docs/05_operations/observability_plan.md`
- `docs/06_miasi/observability_card.md`
- `docs/devpilot_backlog_fase_E_agentops_observabilidad.md`
- `docs/functional_backlog_after_precode.md`

## 5. Criterios PASS

- `AgentRuntime` genera `TraceContext` y metadatos `agentops`.
- `AgentToolCall` incluye `tool_call_id`.
- Existen spans `agent.run`, `tool.call`, `policy.check`, `approval.workflow` y `model.call`.
- Existen métricas para categorías `agent`, `tool`, `policy`, `approval` y `model`.
- La instrumentación es best-effort.
- No se agregan dependencias externas.
- No se habilita telemetría remota.
- No se registran prompts, completions, secretos, diffs, stdout ni stderr crudos.

## 6. Criterios BLOCK

- Observabilidad cambia `ok`, `exit_code` o semántica de comandos.
- Se requiere red, API externa o exporter.
- Se versiona `.devpilot/devpilot.db`.
- Agentes no implementados generan trazas inconsistentes.
- Se activa multiagente, handoffs, RAG, MCP o ejecución remota.

## 7. Riesgos

- Ruido de spans/métricas antes de existir CLI de consulta.
- Persistencia best-effort puede fallar silenciosamente si SQLite no está disponible.
- Falta política de retención y filtros operativos.

Mitigación: mantener instrumentación local, redacted, no crítica y preparar `FUNC-SPRINT-61` para consulta controlada.

## 8. Comandos de verificación

```powershell
python -m devpilot_core state init --json
python -m devpilot_core agent run documentation-audit --target docs/01_requirements --provider mock --json --write-report
python -m devpilot_core model generate --provider mock --prompt "hello" --json
python -m pytest tests/test_agentops_instrumentation.py -q
python -m pytest tests/test_agentops_instrumentation.py tests/test_agent_runtime.py tests/test_agent_runtime_v2.py tests/test_policy_engine.py tests/test_approval_cli.py tests/test_model_governance.py -q
python -m devpilot_core validate-artifact docs/audits/func_sprint_60_agentic_instrumentation_audit.md --json
python -m devpilot_core schema validate-manifest docs/functional_sprint_60_manifest.json --json
python -m devpilot_core validate all --json
pytest -q
```

## 9. Estado de capacidades

Implementado:

- Instrumentación agentic local.
- Spans y métricas para agent/tool/policy/approval/model.
- Redacción de payloads.
- Metadatos correlacionables.

Pendiente:

- `trace report`.
- `trace inspect`.
- `metrics summary`.
- Reportes Markdown de trazas.
- Retención y compactación.
- Export OpenTelemetry dry-run/local opt-in.
- AgentOps Quality Gate.

## 10. Próximo paso

Siguiente sprint: `FUNC-SPRINT-61 — CLI de trazas y métricas: trace report, trace inspect, metrics summary`.
