---
title: "Tool Card — ficha operativa de herramienta"
version: "1.0.0"
status: "approved"
owner: "AI_agents"
updated: "2026-05-31"
related_documents:
  - "01_modelo_ingenieria_sistemas_agenticos.md"
  - "02_arquitectura_referencia.md"
  - "03_agentic_sdlc.md"
  - "04_estandares_tecnicos_transversales.md"
related_labs: "LAB-AI-001..LAB-AI-080"
related_projects:
  - "DevPilot Local"
  - "FreelanceOps Agent"
  - "MicroVenta Agent"
doc_type: "template"
scope: "engineering-model-template"
audience:
  - "arquitectos de sistemas agénticos"
  - "desarrolladores de agentes IA"
  - "responsables de seguridad, evaluación y operación"
---
# Tool Card — ficha operativa de herramienta

## 1. Propósito

Estandariza cada herramienta que un agente puede invocar, incluyendo contrato de entrada/salida, side effects, nivel de riesgo, dry-run, permisos, timeouts, rollback y pruebas.

Esta plantilla es un artefacto operativo MIASI. Debe completarse antes de que el agente, herramienta, componente o control relacionado avance hacia operación controlada. No sustituye pruebas, evaluación ni revisión de seguridad; las hace trazables.

## 2. Cuándo usarla

- Antes de registrar una herramienta en ToolRegistry.
- Cuando una herramienta accede a archivos, red, base de datos o APIs.
- Antes de permitir ejecución con `execute=true`.

## 3. Campos obligatorios

| Campo | Descripción | Evidencia mínima |
| --- | --- | --- |
| id | Identificador único y estable. | Valor único versionado. |
| owner | Responsable técnico o funcional. | Nombre o rol responsable. |
| status | Estado documental u operativo. | draft/reviewed/approved/deprecated. |
| scope | Alcance explícito del artefacto. | Incluye inclusiones y exclusiones. |
| tool_id | Identificador único de herramienta. | Convención `tool.<dominio>.<acción>`. |
| input_schema | Schema de entrada. | JSON Schema o equivalente. |
| output_schema | Schema de salida. | Incluye errores esperados. |
| side_effects | Efectos secundarios posibles. | read/write/execute/network/delete. |
| risk_level | Nivel de riesgo. | low/medium/high/critical. |
| dry_run_supported | Soporte de simulación. | true/false y comportamiento. |
| approval_required | Aprobación requerida. | Reglas asociadas. |

## 4. Campos opcionales

| Campo | Descripción | Cuándo usarlo |
| --- | --- | --- |
| tags | Etiquetas de clasificación. | Útil para búsqueda y filtros. |
| external_references | Referencias a estándares o documentación externa. | Cuando el artefacto dependa de tecnología, estándar o proveedor. |
| rollback_strategy | Cómo revertir cambios. | Obligatorio si hay escritura. |
| idempotency_key | Clave o estrategia de idempotencia. | Para operaciones repetibles. |
| rate_limits | Límites de frecuencia. | Para APIs externas. |

## 5. Ejemplo completo

```yaml
tool_id: tool.filesystem.write_report
name: write_report
owner: AI_agents
status: draft
input_schema:
  type: object
  required: [path, content, dry_run]
  properties:
    path: {type: string}
    content: {type: string}
    dry_run: {type: boolean}
output_schema:
  type: object
  required: [ok, path, written]
side_effects: [write]
risk_level: medium
dry_run_supported: true
approval_required: false
permissions:
  allowed_paths: ["outputs/", "docs/generated/"]
  forbidden_paths: [".env", ".git/", "src/"]
rollback_strategy: "No sobrescribir; crear backup si el archivo existe."
tests:
  - tests/test_tool_write_report.py
```

## 6. Criterios de revisión

- El schema permite validación automática.
- Los side effects son explícitos.
- El riesgo está justificado.
- Dry-run tiene semántica clara.
- Permisos y rutas están restringidos.

## 7. Criterios de rechazo o bloqueo

- No declara side effects.
- Escribe fuera de rutas permitidas.
- No soporta dry-run cuando debería.
- No tiene pruebas.
- Acepta entradas arbitrarias sin validación.

## 8. Relación con Agentic SDLC

| Fase SDLC | Uso de la plantilla |
| --- | --- |
| Fase 5 — Diseño de herramientas | Debe completarse, revisarse o actualizarse en esta fase. |
| Fase 7 — Diseño de seguridad | Debe completarse, revisarse o actualizarse en esta fase. |
| Fase 10 — Implementación | Debe completarse, revisarse o actualizarse en esta fase. |
| Fase 12 — Pruebas de seguridad | Debe completarse, revisarse o actualizarse en esta fase. |

## 9. Relación con quality gates

| Quality gate | Condición PASS | Condición FAIL/BLOCK |
| --- | --- | --- |
| tool_schema_valid | Existe evidencia verificable, versionada y revisada. | Falta evidencia, hay ambigüedad crítica o el riesgo no está mitigado. |
| side_effects_declared | Existe evidencia verificable, versionada y revisada. | Falta evidencia, hay ambigüedad crítica o el riesgo no está mitigado. |
| dry_run_defined | Existe evidencia verificable, versionada y revisada. | Falta evidencia, hay ambigüedad crítica o el riesgo no está mitigado. |
| permissions_scoped | Existe evidencia verificable, versionada y revisada. | Falta evidencia, hay ambigüedad crítica o el riesgo no está mitigado. |
| tool_tests_pass | Existe evidencia verificable, versionada y revisada. | Falta evidencia, hay ambigüedad crítica o el riesgo no está mitigado. |

## 10. Criterios de automatización futura en DevPilot Local

- Debe poder convertirse en formulario validable.
- Debe poder serializarse a YAML/JSON.
- Debe poder enlazarse con `run_id`, `agent_id`, `tool_id`, `eval_id` o `release_id`.
- Debe poder participar en un `readiness-check` automático.
- Debe conservar historial de cambios por Git.



## 11. Referencias base

- OpenAI Agents SDK — Agents, tools, handoffs, guardrails, tracing and human review. https://developers.openai.com/api/docs/guides/agents
- LangGraph durable execution, persistence and human-in-the-loop. https://docs.langchain.com/oss/python/langgraph/durable-execution
- Model Context Protocol Specification — resources, prompts and tools. https://modelcontextprotocol.io/specification/2025-06-18
- OpenTelemetry Semantic Conventions for GenAI systems and agents. https://opentelemetry.io/docs/specs/semconv/gen-ai/
- Microsoft Foundry Agent Evaluators. https://learn.microsoft.com/en-us/azure/foundry/concepts/evaluation-evaluators/agent-evaluators
- OWASP Top 10 for LLM Applications. https://owasp.org/www-project-top-10-for-large-language-model-applications/
- NIST AI Risk Management Framework. https://www.nist.gov/itl/ai-risk-management-framework
- NIST SSDF SP 800-218. https://csrc.nist.gov/pubs/sp/800/218/final
- SLSA — Supply-chain Levels for Software Artifacts. https://slsa.dev/
- CycloneDX Software Bill of Materials. https://cyclonedx.org/
