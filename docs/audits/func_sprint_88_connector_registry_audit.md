---
title: "Auditoría FUNC-SPRINT-88 — MCP threat model y Connector Registry"
doc_id: "DEVPL-AUDIT-FUNC-SPRINT-88"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
standard: "MIPSoftware"
extension: "MIASI"
sprint: "FUNC-SPRINT-88"
updated: "2026-06-18"
approval: "approved_by_owner_direction"
---

# Auditoría FUNC-SPRINT-88 — MCP threat model y Connector Registry

## Estado

`implemented-initial`.

## Propósito

Verificar que DevPilot incorpora la base de gobernanza MCP/conectores sin implementar aún cliente, servidor ni ejecución de conectores.

## Alcance implementado

- `src/devpilot_core/connectors/registry.py`: validación del registry.
- `.devpilot/connectors/connector_registry.json`: registry deny-by-default.
- `docs/schemas/connector_registry.schema.json`: schema estructural.
- `docs/03_security/mcp_connector_threat_model.md`: threat model MCP.
- CLI `connector validate`.
- MIASI tool/policy registry para conectores.

## Funcionamiento

`ConnectorRegistry` carga el JSON local, valida contra schema, aplica `PathGuard`, revisa secretos con `SecretGuard` y ejecuta reglas semánticas: policy ids obligatorios, default deny, MCP disabled, sin red, sin API externa y sin ejecución.

## Integración

- CLI: `src/devpilot_core/cli.py`.
- Schema: `SchemaValidator` y `docs/schemas/schema_catalog.json`.
- Seguridad: `PathGuard`, `SecretGuard`, threat model MCP.
- MIASI: `.devpilot/miasi/tool_registry.json`, `.devpilot/miasi/policy_matrix.json`.
- Documentación: README, runbook, backlog H, changelog y manifest funcional.

## Criterios PASS

- `connector validate --json` retorna PASS.
- Registry distingue `disabled`, `planned`, `implemented`, `experimental`.
- Todos los conectores tienen `policy_rule_ids`.
- MCP queda deshabilitado por defecto.
- No hay ejecución real ni red externa.

## Criterios BLOCK

- Conector sin policy.
- MCP allow-by-default.
- Cliente/servidor MCP implementado en Sprint 88.
- Execution/network/external API activado.
- Secretos crudos en registry.

## Riesgos

La versión es primera base de gobernanza. Faltan adapter read-only, evals adversariales MCP, trazas de connector calls reales y UI/API de administración.

## Comandos de verificación

```powershell
python -m devpilot_core connector validate --json
python -m devpilot_core schema validate --schema docs\schemas\connector_registry.schema.json --instance .devpilot\connectors\connector_registry.json --json
python -m devpilot_core validate-artifact docs_security\mcp_connector_threat_model.md --json
python -m pytest tests	est_connector_registry.py tests	est_sprint_88_documentation.py -q
```

## Veredicto

PASS focalizado. La capacidad queda lista como registry/threat-model preliminar y debe evolucionar en Sprint 89 hacia un MCP MVP read-only, sin romper deny-by-default.
