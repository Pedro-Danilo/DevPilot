---
doc_id: POST-H-032-F-TOOL-CALLING-CONTRACT-REPORT
title: POST-H-032-F — Tool calling contract report
status: approved
version: 1.0.0
owner: Ordóñez
updated: 2026-07-11
approval: local-owner
---

# POST-H-032-F — Tool calling contract report

## Resultado

`POST-H-032-F` queda implementado como versión `implemented-initial` del contrato de tool calling gobernado para agentes DevPilot.

## Alcance implementado

La implementación agrega un contrato local-first y contract-only para tool calls de agentes:

- schema `AgentToolCall`;
- policy `.devpilot/agents/tool_call_policy.json`;
- módulo `src/devpilot_core/agents/tool_calls.py`;
- derivación del executable subset desde `.devpilot/miasi/tool_registry.json`;
- validación de allowlist por agente contra `.devpilot/agents/agent_capability_inventory.json`;
- dry-run-first como default obligatorio;
- approval binding contractual para tools de riesgo;
- observability por tool call mediante campos trazables `agent.tool_call.planned` y `policy.decision`;
- tests adversariales de prompt/tool injection.

## Límites explícitos

Esta versión no habilita un scheduler genérico de herramientas ni ejecución real de herramientas. No habilita connector write, plugin execution, remote execution, network, external APIs ni LLM calls. La salida es contractual/fake-local y debe evolucionar antes de permitir ejecución genérica en producción.

## Validación esperada

```powershell
$env:PYTHONPATH="src"
python -m pytest -p no:ddtrace --assert=plain tests/test_post_h_032_tool_calling_contract.py -q
python -m devpilot_core agent tool-calls validate --json
python -m devpilot_core agent tool-calls validate --json --write-report
python -m devpilot_core schema validate --schema-id AgentToolCall --instance outputs\reports\agent_tool_call_contract_report.json --json
```

## PASS/BLOCK

PASS requiere que todo agent/tool pair esté allowlisted, que toda tool de riesgo requiera approval binding, que dry-run-first sea default, que ToolInjectionGuard bloquee payloads adversariales y que no se habiliten connector write, plugin execution ni remote execution.

BLOCK aplica si una tool se ejecuta sin allowlist, si una tool de riesgo no requiere approval, si se habilita write externo/plugin/remote, o si una inyección consigue cambiar tool target.
