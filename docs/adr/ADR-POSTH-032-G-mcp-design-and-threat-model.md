---
doc_id: "ADR-POSTH-032-G"
title: "MCP design and local fake-server evaluation"
status: "proposed"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-07-11"
approval: "pending"
decision_status: "design-and-fake-server-only"
micro_sprint: "POST-H-032-G"
real_mcp_enabled_by_default: false
fake_server_required_for_tests: true
network_transport_enabled: false
connector_write_allowed: false
plugin_execution_allowed: false
remote_execution_allowed: false
---

# ADR-POSTH-032-G — MCP design and local fake-server evaluation

## Contexto

DevPilot ya cuenta con MIASI Tool Registry, PolicyEngine, Approval/RBAC hardening, connector sandbox, plugin execution blocked/design, remote disabled invariants y un contrato de tool calling gobernado. El siguiente riesgo industrial es confundir diseño MCP con una integración MCP productiva capaz de abrir transporte externo, exponer tools o ejecutar operaciones fuera del perímetro local-first.

## Decisión

Se adopta una decisión **design-only / fake-server-only** para POST-H-032-G:

```text
mcp_real_enabled=false
fake_server_only=true
network_transport_enabled=false
stdio_transport_enabled=false
http_transport_enabled=false
connector_write_allowed=false
plugin_execution_allowed=false
remote_execution_allowed=false
```

POST-H-032-G puede crear ADR, threat model, schema, contrato `.devpilot/mcp/mcp_fake_server_contract.json`, módulos `mcp/fake_server.py` y `mcp/contracts.py`, mapping MCP tools -> MIASI Tool Registry, permission model, audit trail, CLI/report y tests. No autoriza MCP real ni transportes MCP productivos.

## Modelo de permisos

- Default deny.
- Solo MCP tools mapeadas explícitamente a MIASI Tool Registry son visibles.
- Read-only fake tools pueden producir respuestas contractuales.
- Tools con escritura o ejecución requieren policy/approval y quedan bloqueadas como fake response.
- Ninguna MCP tool puede usar connector write, plugin execution, remote execution, network, external APIs o LLMs.
- Cada request fake debe dejar audit trail.

## Threat model

| Amenaza | Impacto | Mitigación |
| --- | --- | --- |
| MCP real habilitado por drift | Crítico | `mcp_real_enabled=false`, fake server local, ADR futura obligatoria |
| Tool injection cambia target MCP | Crítico | ToolInjectionGuard, allowlist y mapping MCP->MIASI |
| Write/execute sin approval | Crítico | side effects write/execute requieren approval y quedan bloqueados |
| Falta de audit trail | Alto | evento por request fake con método, request id y policy decision |
| Exposición de secrets | Crítico | no raw secret arguments, payload redacted |

## Criterios PASS

- MCP real no se habilita por defecto.
- Fake server prueba contratos sin red externa.
- MCP tools están mapeadas a MIASI Tool Registry.
- Permission model y audit trail existen.
- Tools MCP de escritura/ejecución requieren policy/approval.
- Connector write, plugin execution y remote execution permanecen bloqueados.

## Criterios BLOCK

- MCP real queda habilitado por defecto.
- Se abre transporte de red/stdio/http real.
- MCP tool no mapeada a MIASI queda visible.
- Tool de escritura/ejecución queda permitida sin approval.
- Prompt/tool injection consigue cambiar target.
- Falta audit trail por request.

## Consecuencias

DevPilot obtiene una base ejecutable para evaluar MCP sin ampliar superficie de ataque real. El sistema puede evolucionar hacia integración MCP futura solo si se crea backlog separado, quality gate, pruebas de transporte y aprobación explícita del owner.

## Comandos de verificación

```powershell
$env:PYTHONPATH="src"
python -m devpilot_core agent mcp-fake-server evaluate --json
python -m devpilot_core agent mcp-fake-server evaluate --json --write-report
python -m devpilot_core schema validate --schema-id McpFakeServerEvaluation --instance outputs\reports\mcp_fake_server_evaluation_report.json --json
python -m pytest -p no:ddtrace --assert=plain tests/test_post_h_032_mcp_design_fake_server.py -q
```

## Estado

`proposed` en POST-H-032-G. Esta ADR existe para bloquear enablement implícito y definir el camino seguro. No autoriza MCP real ni llamadas a servidores MCP externos.
