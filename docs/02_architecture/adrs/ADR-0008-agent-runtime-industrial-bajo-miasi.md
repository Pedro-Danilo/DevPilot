---
title: "ADR-0008 — Agent Runtime industrial bajo MIASI"
doc_id: "DEVPL-ADR-0008"
status: "accepted"
version: "1.0.0"
owner: "Ordóñez"
standard: "MIPSoftware"
extension: "MIASI"
phase: "SPRINT-PRECODE-03"
updated: "2026-06-04"
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
