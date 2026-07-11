---
doc_id: POST-H-032-G-MCP-FAKE-SERVER-EVALUATION-REPORT
title: POST-H-032-G — MCP design and local fake-server evaluation report
status: approved
version: 1.0.0
owner: Ordóñez
updated: 2026-07-11
approval: local-owner
---

# POST-H-032-G — MCP design and local fake-server evaluation report

## Resultado

`POST-H-032-G` queda implementado como versión `implemented-initial` del diseño MCP con evaluación local fake-server.

## Alcance implementado

La implementación agrega:

- ADR `ADR-POSTH-032-G-mcp-design-and-threat-model.md`;
- schema `McpFakeServerEvaluation`;
- contrato `.devpilot/mcp/mcp_fake_server_contract.json`;
- módulo `src/devpilot_core/mcp/fake_server.py`;
- módulo `src/devpilot_core/mcp/contracts.py`;
- mapping MCP tools -> MIASI Tool Registry;
- permission model default-deny;
- audit trail por request fake;
- pruebas con fake MCP server local;
- CLI `agent mcp-fake-server evaluate`;
- ApplicationService `mcp_fake_server_evaluation`.

## Límites explícitos

Esta versión no habilita MCP real, no abre transportes MCP, no usa red, no usa stdio/http/websocket, no ejecuta tools reales, no habilita connector write, plugin execution, remote execution, external APIs ni LLM calls. La salida es un contrato fake/local para reducir riesgo antes de cualquier integración real.

## Validación esperada

```powershell
$env:PYTHONPATH="src"
python -m pytest -p no:ddtrace --assert=plain tests/test_post_h_032_mcp_design_fake_server.py -q
python -m devpilot_core agent mcp-fake-server evaluate --json
python -m devpilot_core agent mcp-fake-server evaluate --json --write-report
python -m devpilot_core schema validate --schema-id McpFakeServerEvaluation --instance outputs\reports\mcp_fake_server_evaluation_report.json --json
```

## PASS/BLOCK

PASS requiere MCP real disabled, fake server local, mapping MCP->MIASI, permission model, audit trail, ToolInjectionGuard y bloqueo de connector write/plugin execution/remote execution.

BLOCK aplica si MCP real queda enabled por defecto, si se abre transporte externo, si una MCP tool no mapeada queda visible, si una tool write/execute no exige approval o si una inyección consigue cambiar el target.
