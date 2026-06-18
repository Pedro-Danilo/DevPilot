---
title: "MCP Connector Threat Model — DevPilot Local"
doc_id: "DEVPL-SEC-MCP-CONNECTOR-THREAT-MODEL"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
standard: "MIPSoftware"
extension: "MIASI"
sprint: "FUNC-SPRINT-88"
updated: "2026-06-18"
approval: "approved_by_owner_direction"
---

# MCP Connector Threat Model — DevPilot Local

## Estado

`implemented-initial`. Este documento habilita únicamente diseño, registro y validación de conectores. No habilita cliente MCP, servidor MCP, llamadas reales ni ejecución remota.

## Propósito

Definir el modelo de amenazas y los controles mínimos para integrar MCP/conectores en DevPilot sin romper los principios local-first, deny-by-default, trazabilidad, MIASI, PolicyEngine, Approval y seguridad de workspace.

## Alcance

Incluye:

- Connector Registry local bajo `.devpilot/connectors/connector_registry.json`.
- JSON Schema `docs/schemas/connector_registry.schema.json`.
- Validación CLI `python -m devpilot_core connector validate --json`.
- Estados `disabled`, `planned`, `implemented` y `experimental`.
- Policy rule ids obligatorios por conector.
- MCP deshabilitado por defecto.

No incluye:

- cliente MCP real;
- servidor MCP real;
- ejecución de herramientas MCP;
- conectores externos con red;
- shell/stdin/stdout arbitrario;
- secretos en registry;
- marketplace o plugins dinámicos.

## Activos

| Activo | Riesgo | Control |
|---|---|---|
| Workspace local | Lectura fuera de alcance | `PathGuard` |
| Secretos locales | Exfiltración por tool output | `SecretGuard` |
| Connector Registry | Tool poisoning | JSON Schema + MIASI + PolicyEngine |
| MCP discovery | Enumeración de tools no aprobadas | deny-by-default |
| Trazas/reportes | Fuga de payloads | redacción y reportes controlados |
| Future connector calls | Mutación no autorizada | approval + sandbox futuro |

## Amenazas

| ID | Amenaza | Vector | Impacto | Control mínimo |
|---|---|---|---|---|
| MCP-T01 | Tool poisoning | Conector declara una tool engañosa | Ejecución indebida | registry + schema + policy ids |
| MCP-T02 | Connector abuse | Tool discovery sin control | Exfiltración o bypass | deny-by-default + MIASI |
| MCP-T03 | Data leakage | Output del conector contiene secretos | Fuga de credenciales | SecretGuard + no raw outputs |
| MCP-T04 | Privilege escalation | Conector pide permisos no registrados | Acciones críticas | ApprovalPolicyChecker |
| MCP-T05 | Prompt injection | Output del conector contiene instrucciones maliciosas | Uso indebido de herramientas | PromptInjectionGuard + evals futuras |
| MCP-T06 | Workspace confusion | Conector mezcla rutas de proyectos | Mezcla de estado/secretos | WorkspaceManager + PathGuard |
| MCP-T07 | Network misuse | Conector externo se habilita por defecto | Costos/fuga | external_api deny + CostGuard futuro |
| MCP-T08 | Shell execution | Conector invoca comandos | Daño local | SafeSubprocessRunner solo futuro y gated |

## Controles

### Controles actuales de Sprint 88

- `ConnectorRegistry` valida `.devpilot/connectors/connector_registry.json`.
- `connector_registry.schema.json` exige `default_effect=deny`.
- Todos los conectores deben declarar `policy_rule_ids`.
- MCP declara `enabled_by_default=false`, `execution_enabled=false`, `network_enabled=false` y `shell_enabled=false`.
- El CLI `connector validate` es read-only: no ejecuta conectores.
- `SecretGuard` bloquea material sensible en el registry.
- `PathGuard` limita lectura a workspace.

### Controles obligatorios para sprints posteriores

- Sprint 89 no podrá llamar conectores sin registry PASS.
- Todo adapter debe registrar tool calls, policy checks y trazas.
- Todo conector externo requiere ADR o regla explícita futura.
- Toda operación con side effects debe requerir aprobación humana y sandbox.
- Todo output de conector debe ser tratado como untrusted.

## Criterios PASS

- Registry distingue estados `disabled`, `planned`, `implemented` y `experimental`.
- Todos los conectores declaran `policy_rule_ids`.
- MCP queda deshabilitado por defecto.
- `connector validate --json` retorna `ok=true` sin ejecutar conectores.
- No hay red, API externa, shell ni runtime MCP real.

## Criterios de bloqueo

- Permitir conectores sin policy.
- Permitir MCP allow-by-default.
- Marcar `client_implemented=true` o `server_implemented=true` en Sprint 88.
- Habilitar `execution_enabled=true`, red externa o shell.
- Guardar secretos crudos en registry, reportes o trazas.
- Ejecutar conectores reales antes de Sprint 89.

## Riesgos residuales

- El registry es una primera versión y aún no ejecuta llamadas.
- No existe todavía ConnectorAdapter.
- No hay pruebas adversariales de output MCP hasta sprints de red-team.
- No hay UI/API para administración del registry.
- Sprints futuros deben evitar convertir este registry en allowlist implícita sin policy.


## Actualización FUNC-SPRINT-89 — MVP read-only gobernado

Sprint 89 habilita una primera ruta de llamada a conector local read-only mediante `ConnectorAdapter`. La amenaza principal pasa de diseño documental a control operacional: evitar que una llamada de conector derive en shell, red externa, stdio arbitrario, lectura fuera del workspace o salida sin trazabilidad.

Controles añadidos:

- `connector call --dry-run` obligatorio.
- `PolicyEngine` antes de entregar resultados.
- `PathGuard` y `SecretGuard` sobre fuentes locales.
- Evento `connector.call.evaluated` por intento de llamada.
- Bloqueo de conectores no registrados, no implementados o no read-only.

Persisten como BLOCK: cliente/servidor MCP real sin nueva política, ejecución remota, shell arbitrario, red externa y conectores sin policy/evidencia.
