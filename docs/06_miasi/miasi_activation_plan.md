---
title: "MIASI Activation Plan — DevPilot Local"
doc_id: "DEVPL-MIASI-ACTIVATION"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
standard: "MIASI"
parent_standard: "MIPSoftware"
phase: "SPRINT-PRECODE-07"
updated: "2026-06-05"
approval: "approved_by_owner_direction"
baseline_role: "precode_approved_baseline"
---

# MIASI Activation Plan — DevPilot Local

## 1. Veredicto

MIASI queda **activado obligatoriamente** para DevPilot Local porque el producto incluye agentes IA, herramientas, validadores asistidos, análisis de repositorios, revisión de código, generación documental, evaluación agentic, policy-as-code, human approval, observabilidad AgentOps y posible integración con modelos locales o APIs externas.

## 2. Razones de activación

| Criterio MIASI | Aplica | Evidencia |
|---|---:|---|
| Uso de agentes IA | Sí | `agent_card.md` |
| Tool calling | Sí | `tool_card.md` |
| Políticas de ejecución | Sí | `policy_card.md` |
| Evaluación agentic | Sí | `eval_card.md` |
| Human approval | Sí | `human_approval_card.md` |
| Observabilidad AgentOps | Sí | `observability_card.md` |
| ModelAdapter | Sí | arquitectura aprobada |
| CostGuard y SecretGuard | Sí | arquitectura + seguridad |
| RAG/memoria futura | Sí | arquitectura + roadmap |
| Integraciones MCP/API futuras | Sí | arquitectura post-MVP |

## 3. Activación por etapa

| Etapa | Activación MIASI |
|---|---|
| MVP | Agentes documentales controlados, tools de lectura/validación, policy gates y evals básicas. |
| MVP+ | Agentes especializados para requerimientos, arquitectura, seguridad, repos, code review y patch review. |
| Post-MVP | Multiagentes, desktop/web, MCP/API adapters, RAG/memoria y operación avanzada. |

## 4. Controles obligatorios

- Agent Card por agente.
- Tool Card por herramienta.
- Policy Card por dominio.
- Eval Card por capacidad agentic.
- Human Approval Card para acciones críticas.
- Observability Card para AgentOps.
- CostGuard si hay APIs externas.
- SecretGuard en toda lectura de repos/código.
- Reportes JSON/Markdown.
- Trazas JSONL.
- Dry-run por defecto.

## 5. Criterio PASS

MIASI está correctamente activado si todos los artefactos de `docs/06_miasi/` quedan revisados y no contradicen producto, requerimientos, arquitectura, seguridad, calidad ni operación.

## 6. Criterio BLOCK

Bloquear avance funcional si cualquier agente o tool se implementa sin artefacto MIASI, policy, evaluación y observabilidad mínima.
