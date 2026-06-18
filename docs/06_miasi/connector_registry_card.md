---
title: "MIASI Connector Registry Card — DevPilot Local"
doc_id: "DEVPL-MIASI-CONNECTOR-REGISTRY-CARD"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
standard: "MIPSoftware"
extension: "MIASI"
sprint: "FUNC-SPRINT-88"
updated: "2026-06-18"
---

# MIASI Connector Registry Card — DevPilot Local

## Estado

`implemented-initial` como registry y validación; no implementa runtime MCP ni llamadas a conectores.

## Propósito

Definir el contrato MIASI de conectores para que futuras herramientas MCP/API/locales sean declaradas, evaluables, trazables y deny-by-default antes de cualquier ejecución.

## Alcance

Incluye `connector validate`, JSON Schema, registry local y políticas declarativas. Excluye cliente/servidor MCP, adapter real, shell, red externa y ejecución de tools.

## Taxonomía

| Tipo | Estado permitido Sprint 88 | Regla |
|---|---|---|
| `documentation` | planned | read-only futuro |
| `git` | planned | read-only futuro |
| `mcp` | disabled | no runtime |
| `api` | disabled | no red externa |

## Contrato

Todo conector debe declarar `connector_id`, `status`, `default_effect=deny`, `policy_rule_ids`, operaciones permitidas, aprobación, observabilidad, schema, red, API externa y execution flag.

## Herramientas

| Tool | Estado | Side effect |
|---|---|---|
| `connector.validate` | implemented-initial | none |
| `connector.discover` | planned | read |

## Política

- `CONNECTOR_REGISTRY_VALIDATE_ALLOW` permite validar registry local.
- `CONNECTOR_DISCOVERY_DENY_BY_DEFAULT` deniega conectores no implementados/no aprobados.
- `MCP_EXECUTION_DENY` bloquea MCP runtime en Sprint 88.
- `CONNECTOR_EXTERNAL_API_DENY` bloquea API externa.

## Evaluación

Pruebas mínimas: schema valid, deny-by-default, policy ids obligatorios, MCP runtime disabled, CLI JSON parseable y docs sincronizados.

## Observabilidad

`connector validate` emite `CommandResult`, eventos y reportes opcionales. Futuras llamadas deberán registrar spans por connector/tool call.

## Criterios PASS

- Registry válido.
- No hay conectores sin policy.
- MCP disabled-by-default.
- No hay ejecución real.
- No hay red ni API externa.

## Criterios BLOCK

- Connector sin policy.
- `default_effect` distinto de `deny`.
- Runtime MCP activado.
- External API activada.
- Secretos en registry.

## Riesgos

Tool poisoning, connector abuse, data leakage, privilege escalation, workspace confusion y prompt injection desde output de conector.

## Evolución pendiente

Sprint 89 deberá crear un MCP/ConnectorAdapter read-only y mantener deny-by-default, trazas, evals y approval donde aplique.
