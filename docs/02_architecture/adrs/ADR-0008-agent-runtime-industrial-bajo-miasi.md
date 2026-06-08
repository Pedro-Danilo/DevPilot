---
title: "ADR-0008 — Agent Runtime industrial bajo MIASI"
doc_id: "DEVPL-ADR-0008"
status: "accepted"
version: "1.1.0"
owner: "Ordóñez"
standard: "MIPSoftware"
extension: "MIASI"
phase: "SPRINT-PRECODE-03"
updated: "2026-06-08"
approval: "approved_by_owner_direction"
accepted_by: "Ordóñez"
accepted_at: "2026-06-04"
acceptance_scope: "SPRINT-PRECODE-03 architecture baseline"
---
# ADR-0008 — Agent Runtime industrial bajo MIASI

## Estado

Proposed.

## Contexto

DevPilot debe ser una plataforma agent-assisted SDLC, no solo una herramienta determinística. El owner requiere agentes profesionales de nivel industrial, incorporando lo aprendido en AI_agents LAB-AI-001 a LAB-AI-080: tool calling, ModelAdapter, memoria, RAG, evaluación, observabilidad, guardrails, policy-as-code, approval, CI/CD y AgentOps.

## Decisión

Diseñar un Industrial Agent Runtime con Agent Orchestrator, ModelAdapter, Tool Registry, Policy Engine, Eval Harness, Memory/RAG Layer, Observability Layer, Approval Queue y CostGuard. La implementación será incremental: agentes documentales en MVP; agentes de requisitos, arquitectura, seguridad, código y refactor en MVP+; multiagentes avanzados en post-MVP.

## Consecuencias positivas

- La inteligencia queda integrada al core del producto.
- Permite agentes con controles industriales.
- Evita que los agentes reemplacen gates determinísticos.
- Prepara evolución multiagente.

## Consecuencias negativas / riesgos

- Incrementa complejidad técnica.
- Requiere datasets/evals.
- Requiere supervisión humana.
- Requiere hardening de tools.

## Controles obligatorios

- Ningún agente sin Agent Card, Tool Card, Policy Card, Eval Card y Observability Card.
- Dry-run por defecto.
- Separación entre recomendación y decisión.
- Human approval para side effects.
- Observabilidad por run/session/tool.

## Criterios de aceptación

- Agentes MVP producen borradores/hallazgos sin escribir automáticamente.
- Evals offline existen antes de agentes especializados.
- Tool Registry bloquea herramientas no declaradas.
- Agent runs dejan trazas.


## Actualización FUNC-SPRINT-11 — MIASI ejecutable

Estado de implementación: `implemented-initial`.

La decisión de Agent Runtime industrial bajo MIASI empieza a materializarse con contratos ejecutables determinísticos, sin activar aún runtime de agentes. Sprint 11 introduce:

```text
.devpilot/miasi/agent_registry.json
.devpilot/miasi/tool_registry.json
.devpilot/miasi/policy_matrix.json
src/devpilot_core/miasi/registry.py
```

Estos contratos permiten validar que ningún agente avance hacia ejecución sin herramientas declaradas, policy coverage, evaluación, observabilidad y aprobación cuando la autonomía/riesgo lo exige. La implementación es local-first, sin APIs externas, sin dependencias nuevas y sin ejecución de herramientas.

La decisión arquitectónica se mantiene: los agentes futuros deberán pasar por Agent Registry, Tool Registry, Policy Matrix, Policy Engine, Eval Harness, Observability y Human Approval antes de habilitar capacidades de runtime.

### Riesgo residual

La implementación sigue siendo preliminar: aún no existe Agent Runtime, no hay ejecución de tools, no hay eval harness ni aprobación humana persistente. Sprint 11 reduce riesgo de drift documental, pero no sustituye controles industriales completos.

## Actualización 2026-06-08 — FUNC-SPRINT-12

Estado de implementación: `implemented-initial`.

FUNC-SPRINT-12 materializa la primera capa de Agent Runtime bajo MIASI, limitada a agentes documentales MVP, ejecución local/mock y `dry-run` por defecto. La decisión arquitectónica original se mantiene: ningún agente puede operar por fuera de los registros MIASI, del Policy Engine, de la observabilidad local y del contrato `CommandResult`.

Componentes implementados:

- `src/devpilot_core/agents/models.py`: contratos `AgentMessage`, `AgentToolCall`, `AgentSuggestion` y `AgentRunResult`.
- `src/devpilot_core/agents/runtime.py`: `AgentRuntime`, `DocumentationAuditAgent` y `PreCodeDocumentationAgent`.
- `agent run`: comando CLI para ejecución controlada de agentes.

Restricciones preservadas:

- Sin LLM externo obligatorio.
- Sin API keys.
- Sin llamadas de red.
- Sin modificación de documentos aprobados.
- Escritura opcional únicamente bajo `outputs/drafts` y con bloqueo de sobrescritura.
- Policy check antes de cada operación tipo herramienta.

Riesgo residual: esta implementación no es todavía un runtime industrial completo. Faltan evaluación agentic formal, memoria, ModelAdapter, aprobación humana persistente, ejecución de herramientas reales y monitoreo operacional avanzado.
