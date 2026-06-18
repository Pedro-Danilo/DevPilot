---
title: "Auditoría FUNC-SPRINT-89 — MCP MVP controlado y herramientas read-only"
doc_id: "DEVPL-AUDIT-FUNC-SPRINT-89"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
standard: "MIPSoftware"
extension: "MIASI"
sprint: "FUNC-SPRINT-89"
updated: "2026-06-18"
approval: "approved_by_owner_direction"
---

# Auditoría FUNC-SPRINT-89 — MCP MVP controlado y herramientas read-only

## Estado

`implemented-initial`.

## Propósito

Validar que DevPilot incorpora un MVP controlado de conectores/MCP sin habilitar cliente MCP real, servidor MCP real, red externa, shell, stdio arbitrario ni ejecución remota. La capacidad se limita a un `ConnectorAdapter` local read-only, invocado en modo `--dry-run`, con policy y trazas obligatorias.

## Alcance implementado

- `src/devpilot_core/connectors/adapter.py`: adapter local read-only para conectores gobernados.
- `connector call --connector local-docs --operation list --dry-run --json`: CLI de llamada controlada.
- `.devpilot/connectors/connector_registry.json`: `local.docs` queda `implemented` solo para operaciones read-only declaradas.
- `.devpilot/miasi/tool_registry.json`: se registra `connector.call` y herramienta local de docs.
- `.devpilot/miasi/policy_matrix.json`: se registran reglas para llamada read-only y bloqueo de execute mode.
- `tests/test_connector_adapter.py`: pruebas de PASS y bloqueo.

## Funcionamiento

`ConnectorAdapter` valida primero el Connector Registry, resuelve alias seguros (`local-docs` → `local.docs`), verifica que el conector y la operación estén implementados, exige `--dry-run`, bloquea conectores no read-only, evalúa `PolicyEngine`, aplica `PathGuard`/`SecretGuard` y emite evento local `connector.call.evaluated`.

El MVP soporta `local.docs:list_sources` y `local.docs:query_sources` como operaciones locales read-only. No ejecuta comandos arbitrarios, no usa red, no usa API externa, no llama LLM, no invoca proceso MCP real y no abre stdio.

## Integración

- CLI: `src/devpilot_core/cli.py`.
- Registry: `.devpilot/connectors/connector_registry.json`.
- Seguridad: `PolicyEngine`, `PathGuard`, `SecretGuard`.
- Observabilidad: `EventLogger` con evento `connector.call.evaluated`.
- MIASI: Tool Registry y Policy Matrix.
- Documentación: README, runbook, backlog H, changelog y manifest funcional.

## Criterios PASS

- `connector call --connector local-docs --operation list --dry-run --json` retorna PASS.
- La llamada usa `PolicyEngine` antes de entregar resultados.
- La llamada genera evento de traza local.
- La operación es read-only.
- La ejecución remota queda deshabilitada.
- Red externa, API externa, shell y MCP client/server reales quedan deshabilitados.

## Criterios BLOCK

- Ejecutar sin `--dry-run`.
- Llamar conectores no registrados.
- Llamar conectores deshabilitados o no implementados.
- Llamar operaciones no registradas o no implementadas.
- Permitir `network_allowed=true`, `external_api_allowed=true` o `execution_enabled=true`.
- Permitir shell, stdio arbitrario o cliente/servidor MCP real.

## Riesgos

- El adapter es un MVP local inicial, no un runtime MCP industrial.
- La operación `query_sources` es lexical/simple; no reemplaza RAG ni evaluación semántica avanzada.
- Evals adversariales MCP y sandbox de conectores quedan pendientes para sprints posteriores.
- La UI/API todavía no expone gestión de conectores.

## Comandos de verificación

```powershell
python -m devpilot_core connector validate --json
python -m devpilot_core connector call --connector local-docs --operation list --dry-run --json
python -m devpilot_core connector call --connector local-docs --operation query --query "readiness strict" --dry-run --json
python -m pytest tests\test_connector_adapter.py tests\test_sprint_89_documentation.py -q
```

## Veredicto

PASS focalizado. Sprint 89 habilita un MVP controlado de llamada a conector local read-only y conserva límites de seguridad: dry-run obligatorio, PolicyEngine obligatorio, trazas obligatorias, sin red externa, sin shell y sin cliente/servidor MCP real.
