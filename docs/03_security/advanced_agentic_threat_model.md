---
title: "Threat Model — Arquitectura avanzada agentic/enterprise"
doc_id: "DEVPL-SEC-ADVANCED-AGENTIC-001"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
standard: "MIPSoftware"
extension: "MIASI"
phase: "FUNC-SPRINT-85"
updated: "2026-06-18"
source_repo: "repo_DevPilot_Local_108.zip"
source_backlog: "docs/devpilot_backlog_fase_H_capacidades_avanzadas.md"
source_adr: "docs/02_architecture/adrs/ADR-0016-advanced-agentic-enterprise.md"
change_policy: "controlled_changes_allowed_via_docs_as_code"
approval: "approved_by_func_sprint_85"
---

# Threat Model — Arquitectura avanzada agentic/enterprise

## Estado

`approved` para iniciar Fase H desde `FUNC-SPRINT-85`.

Este threat model es una **primera versión implementable**. Cubre riesgos de multiagente, RAG documental, MCP/conectores, plugins, multiworkspace, RBAC, compliance, audit packs y remote runners experimentales. No autoriza todavía runtime avanzado; define condiciones de seguridad para los sprints posteriores.

## Propósito

Definir amenazas, límites de confianza, controles y criterios de bloqueo antes de introducir capacidades avanzadas en DevPilot.

El objetivo es impedir que nuevas capacidades agentic/enterprise debiliten la cadena de control existente:

```text
Workspace -> PolicyEngine -> MIASI -> Approval -> TraceEngine -> EvalHarness -> ReportEngine -> LocalStore
```

## Alcance

Incluye:

- AgentSession y memoria operativa.
- RAG documental local sobre `docs/` y reportes seleccionados.
- MCP threat model, connector registry y MCP MVP read-only futuro.
- MultiAgentCoordinator y handoffs gobernados.
- Workflows multiagente SDLC en dry-run.
- Red-team/evals avanzadas.
- Plugin/connector ecosystem controlado.
- Multiworkspace/portfolio local.
- RBAC local.
- Audit packs y compliance packs.
- Enterprise reporting local.
- Remote runner stub experimental disabled.

No incluye:

- autonomía total;
- conectores allow-by-default;
- shell remoto;
- ejecución cloud;
- SaaS obligatorio;
- marketplace público;
- RAG sin fuentes;
- agentes que escriban en repos sin sandbox/rollback;
- despliegues sin Release/Approval gates.

## Activos

| Activo | Sensibilidad | Riesgo principal |
|---|---|---|
| `.devpilot/` | Alta | Estado, policies, providers, approvals, SQLite. |
| Registros MIASI | Alta | Autorización incorrecta de agentes/tools. |
| Workspaces | Alta | Mezcla de state, secretos o reportes entre proyectos. |
| Índices RAG | Media-alta | Indexación de secretos o contenido fuera de alcance. |
| Fuentes RAG | Media-alta | Respuestas sin evidencia o con fuentes incorrectas. |
| Connectors/MCP | Alta | Tool poisoning, connector abuse, exfiltración. |
| Plugins | Alta | Ejecución dinámica arbitraria. |
| Traces/evals/reports | Media-alta | Fuga de datos, rutas, prompts o hallazgos. |
| Approval decisions | Alta | Escalada de privilegios. |
| Remote runners | Crítica | Ejecución remota no autorizada. |

## Límites de confianza

```text
Usuario / UI / CLI
  -> ApplicationService / AgentRuntime / WorkflowRunner
    -> PolicyEngine + MIASI + ApprovalPolicyChecker
      -> Tools / RAG / Connectors / Plugins / Workspace APIs
        -> Filesystem local / LocalStore / Reports / Traces
```

Límites específicos:

- RAG: frontera entre documentos indexables y contenido prohibido.
- MCP: frontera entre tool discovery y tool execution.
- Multiagente: frontera entre agente supervisor, agentes especializados y handoffs.
- Multiworkspace: frontera entre workspace activo, registry de workspaces y paths externos.
- RBAC: frontera entre actor local y acción sensible.
- Remote runners: frontera experimental, disabled-by-default.

## Amenazas

| ID | Amenaza | Vector | Impacto | Control mínimo |
|---|---|---|---|---|
| T-ADV-001 | Prompt injection | Docs, RAG chunks, connector output | Tool misuse, data leakage | PromptInjectionGuard + source metadata + evals. |
| T-ADV-002 | Tool poisoning | Registry o connector output manipulado | Ejecución indebida | Connector Registry + policy IDs + schema. |
| T-ADV-003 | Data leakage | Reportes/trazas/RAG index | Exposición de secretos | SecretGuard + redacción + path allowlist. |
| T-ADV-004 | Privilege escalation | RBAC decorativo o approval bypass | Acciones críticas no autorizadas | RBAC integrado con PolicyEngine. |
| T-ADV-005 | Connector abuse | MCP tool discovery no gobernado | Exfiltración o shell | Deny-by-default + no shell + no red externa. |
| T-ADV-006 | Handoff oculto | Multiagente sin trazas | Auditoría incompleta | Handoff model + TraceEngine por paso. |
| T-ADV-007 | RAG hallucination | Respuestas sin fuentes | Decisiones erróneas | Fuentes obligatorias + groundedness evals. |
| T-ADV-008 | Workspace confusion | Paths cruzados | Mezcla de secretos/estado | Workspace Registry + PathGuard. |
| T-ADV-009 | Plugin arbitrary execution | Loader dinámico | Código no confiable | Plugin manifest + loader dry-run. |
| T-ADV-010 | Remote runner misuse | Ejecución remota | Daño sistémico | Remote disabled + ADR futura. |
| T-ADV-011 | Eval blind spots | Solo happy path | Falsa confianza | Red-team fixtures. |
| T-ADV-012 | Over-autonomy | Agentes sin límites | Mutaciones no controladas | Autonomía máxima por MIASI. |

## Controles

### Controles obligatorios transversales

| Control | Aplicación |
|---|---|
| `PolicyEngine` | Toda tool/action sensible. |
| MIASI | Registry de agente/tool/policy obligatorio. |
| `ApprovalPolicyChecker` | Acciones críticas, writes, execution, deploy, remote. |
| `PathGuard` | Todo acceso filesystem/workspace. |
| `SecretGuard` | Indexing, reports, traces, prompts y connector output. |
| TraceEngine/EventLogger | Sesiones, handoffs, connector calls, workflow steps. |
| EvalHarness | Agentes, RAG, MCP, multiagent y red-team. |
| ReportEngine | Evidencia JSON/Markdown regenerable. |
| LocalStore | Estado local y auditable. |

### Controles por capability

| Capability | Control mínimo | Estado Sprint 85 |
|---|---|---|
| AgentSession | Retention + redaction + session_id | `planned` |
| RAG | Source metadata + SecretGuard + groundedness | `planned` |
| MCP/Connectors | Registry + schema + deny-by-default | `planned` |
| MultiAgentCoordinator | Handoffs explícitos + traces | `planned` |
| Workflows | Schema + dry-run + report-only | `planned` |
| Plugins | Manifest + permissions + no dynamic execution | `planned` |
| Multiworkspace | Path isolation + no state mixing | `planned` |
| RBAC | Role enforcement in actions | `planned` |
| Remote runners | Disabled-by-default | `experimental/future` |

## Abusos por escenario

### RAG documental

Riesgo: un documento contaminado instruye al agente a ignorar políticas o revelar secretos.

Mitigación:

- indexación allowlist;
- exclusión de `.env`, `.git`, `.venv`, `outputs`, DB runtime y providers locales;
- redacción de secretos;
- respuestas con referencias obligatorias;
- evaluación de groundedness.

### MCP/conectores

Riesgo: un conector declara tools engañosas o entrega output malicioso.

Mitigación:

- Connector Registry deny-by-default;
- schema de conector;
- policy_rule_ids obligatorios;
- no shell/stdin/stdout arbitrario en MVP;
- trazas por connector call.

### Multiagente

Riesgo: el supervisor delega acciones críticas sin evidencias o handoffs visibles.

Mitigación:

- workflow schema;
- handoff model explícito;
- límite de agentes implementados permitidos;
- no acciones destructivas por defecto;
- evals multiagente.

### Enterprise/RBAC

Riesgo: roles solo documentales y approvals sin actor.

Mitigación:

- identity model local;
- RBAC en PolicyEngine;
- actor binding en approvals;
- tests con roles ficticios.

## Criterios PASS

- Threat model cubre prompt injection, tool poisoning, data leakage, privilege escalation y connector abuse.
- MCP y conectores quedan deny-by-default.
- RAG exige fuentes/citas/metadatos.
- Multiagente exige handoffs trazados.
- Remote runners quedan experimental/future y disabled-by-default.
- Capabilities avanzadas quedan marcadas por estado.

## Criterios de bloqueo

- Autorizar conectores sin registry o policy.
- Permitir MCP allow-by-default.
- Permitir RAG sin fuentes.
- Permitir multiagente sin handoff trace.
- Permitir plugins con ejecución dinámica arbitraria.
- Permitir remote runner con ejecución real.
- Permitir acciones críticas sin approval.
- Guardar secretos crudos en sesiones, índices, reportes o trazas.

## Riesgos residuales

| Riesgo | Estado | Tratamiento |
|---|---|---|
| Red-team limitado | Residual | Cubrir en `FUNC-SPRINT-92`. |
| RAG lexical inicial | Residual | Mejorar con embeddings locales opcionales posteriores. |
| RBAC local básico | Residual | Integrar progresivamente con API/UI/CLI. |
| Remote runners | Bloqueado | Mantener disabled hasta ADR futura. |
| Plugin loader | Bloqueado | Loader real diferido hasta manifest/policy/evals. |

## Evolución pendiente

- Crear `AgentSession` con retención y redacción.
- Implementar RAG lexical con referencias.
- Crear Connector Registry y schema MCP.
- Implementar MultiAgentCoordinator dry-run.
- Crear red-team fixtures.
- Implementar RBAC local aplicado.
- Diseñar remote runner como stub disabled.
