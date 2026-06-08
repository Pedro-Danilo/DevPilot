---
title: "FUNC-SPRINT-12 — Agent Runtime mock/local para agentes documentales MVP"
doc_id: "DEVPL-AUDIT-FUNC-012"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-06-08"
approval: "approved_by_owner_direction"
---

# FUNC-SPRINT-12 — Agent Runtime mock/local para agentes documentales MVP

## 1. Propósito

Implementar la primera capa ejecutable de agentes de DevPilot Local bajo MIASI, manteniendo la estrategia local-first, multi-modelo futura y sin dependencia de APIs externas. El sprint habilita agentes documentales controlados, determinísticos y en `dry-run` por defecto.

## 2. Alcance implementado

Se implementan dos agentes MVP:

- `documentation-audit` / `precode.audit`: audita documentación Markdown usando validadores existentes y checklist pre-code.
- `precode-documentation` / `precode.documentation`: genera un borrador documental desde una idea sin modificar documentos aprobados.

No se implementan LLMs, llamadas externas, modelos locales, memoria agentic, agentes autónomos de larga duración ni herramientas destructivas.

## 3. Scripts y módulos creados

### `src/devpilot_core/agents/models.py`

Propósito: definir contratos internos de Agent Runtime.

Funcionamiento: contiene `AgentMessage`, `AgentToolCall`, `AgentSuggestion` y `AgentRunResult`. Estos modelos separan entrada, tool calls, sugerencias, hallazgos y artefactos generados.

Integración: `runtime.py` los usa para producir resultados internos antes de adaptarlos a `CommandResult`.

Rol dentro de DevPilot: base para trazabilidad agentic y futura evaluación de agentes.

Criterios PASS: modelos serializables, sin dependencias externas, compatibles con JSON.

Criterios BLOCK: payload opaco, falta de dry-run o ausencia de tool calls auditables.

Riesgos: contrato inicial; podrá cambiar cuando se agreguen memoria, spans y evaluación avanzada.

### `src/devpilot_core/agents/runtime.py`

Propósito: ejecutar agentes documentales MVP en modo local/mock.

Funcionamiento: `AgentRuntime` resuelve alias CLI, valida MIASI, bloquea agentes no registrados/no MVP/no implementados, ejecuta agentes locales y transforma resultados a `CommandResult`. `DocumentationAuditAgent` usa validadores; `PreCodeDocumentationAgent` genera drafts en memoria o bajo `outputs/drafts` solo si se ejecuta explícitamente.

Integración: usa `MiasiRegistryValidator`, `PolicyEngine`, validadores documentales, ReportEngine vía CLI, EventLogger vía CLI y LocalStore vía CLI.

Rol dentro de DevPilot: primera materialización de agentes ejecutables controlados.

Comandos de uso:

```powershell
python -m devpilot_core agent run documentation-audit --target docs/01_requirements --json
python -m devpilot_core agent run precode-documentation --idea "Agregar trazabilidad" --dry-run --json
```

Criterios PASS: agente registrado, fase MVP, policy check por tool call, dry-run sin escritura, salida `CommandResult`.

Criterios BLOCK: agente desconocido, registros MIASI inválidos, path bloqueado, secreto sintético, draft existente.

Riesgos: agentes rule-based; sin LLM, sin planificación autónoma, sin memoria y sin aprobación persistente.

### `src/devpilot_core/agents/__init__.py`

Propósito: exponer API pública del paquete `agents`.

Funcionamiento: reexporta runtime y modelos.

Integración: permite `from devpilot_core.agents import AgentRuntime`.

Rol: boundary estable para futuros agentes.

Criterios PASS: imports sin ciclos.

Criterios BLOCK: API pública rota o dependencia circular.

## 4. Archivos modificados

### `src/devpilot_core/cli.py`

Propósito: agregar comando `agent run`.

Funcionamiento: recibe agente, target/idea, dry-run/execute, JSON y reportes. Emite eventos, persiste resultado y respeta `CommandResult`.

Criterios PASS: JSON parseable, reportes opcionales, no regresión de comandos previos.

Criterios BLOCK: ejecución sin MIASI, cambio de exit codes previos o escritura implícita.

### `.devpilot/miasi/agent_registry.json`

Propósito: actualizar estado de agentes MVP implementados.

Cambio: `precode.audit` y `precode.documentation` pasan a `implemented`.

Criterios PASS: `miasi validate` sigue en PASS.

### `.devpilot/miasi/tool_registry.json`

Propósito: reflejar herramientas usadas por los agentes MVP.

Cambio: se marcan como `implemented` herramientas documentales ya usadas por runtime.

Criterios PASS: tools mantienen policy coverage y side effects válidos.

### `.devpilot/project.yaml` y `workspace/manager.py`

Propósito: declarar `outputs/drafts` como ruta operativa de borradores.

Criterios PASS: futuros workspaces exponen la ruta de drafts.

### `README.md`, `runbook.md`, backlog y ADR-0008

Propósito: sincronizar documentación operativa, backlog vivo y decisión arquitectónica de Agent Runtime bajo MIASI.

## 5. Pruebas implementadas

Archivo: `tests/test_agent_runtime.py`.

Casos:

- dry-run de `precode-documentation` no escribe archivos;
- payload con secreto sintético queda bloqueado;
- `documentation-audit` audita un target documental;
- agente desconocido queda bloqueado;
- CLI `agent run precode-documentation --write-report` produce reporte;
- CLI `agent run documentation-audit` emite JSON parseable.

## 6. Resultado esperado

```text
pytest -q -> 85 passed
agent run documentation-audit -> PASS
agent run precode-documentation --dry-run -> PASS sin escritura
miasi validate -> PASS
```

## 7. Naturaleza preliminar

Esta implementación es una primera versión educativa/industrializable. Es segura por diseño, pero todavía no alcanza nivel industrial completo porque faltan evaluación agentic formal, ModelAdapter, memoria, aprobación humana persistente, trazas jerárquicas, ejecución de herramientas reales, RBAC/IAM y red teaming.
