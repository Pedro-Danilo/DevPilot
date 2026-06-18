---
title: "ADR-0016 — Arquitectura avanzada agentic/enterprise"
doc_id: "DEVPL-ADR-0016"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
standard: "MIPSoftware"
extension: "MIASI"
phase: "FUNC-SPRINT-85"
updated: "2026-06-18"
source_repo: "repo_DevPilot_Local_108.zip"
source_backlog: "docs/devpilot_backlog_fase_H_capacidades_avanzadas.md"
source_report: "Informe de avance DevPilot - sprint 0 - 18.docx"
decision_scope: "advanced_agentic_enterprise_architecture"
change_policy: "controlled_changes_allowed_via_docs_as_code"
approval: "approved_by_func_sprint_85"
operationalized_by: "FUNC-SPRINT-85"
---

# ADR-0016 — Arquitectura avanzada agentic/enterprise

## Estado

`approved` y operacionalizada por `FUNC-SPRINT-85 — ADR de arquitectura avanzada agentic/enterprise`.

Esta ADR es una decisión arquitectónica de **primera versión** para Fase H. No habilita todavía runtime multiagente, RAG, MCP, plugins, remote runners ni capacidades enterprise completas. Define los límites, patrones permitidos, patrones rechazados, estados y controles que deben respetar los sprints `FUNC-SPRINT-86` a `FUNC-SPRINT-99`.

## Contexto

DevPilot llega a Fase H después de cerrar Fases A-G. La plataforma ya dispone de core CLI, `CommandResult`, validadores, `PolicyEngine`, MIASI, AgentRuntime gobernado, agentes especializados iniciales, observabilidad local, API/Web UI local, quality gates, release manifest, SBOM, checksums, smoke release, instalación plan-only, backup/restore/upgrade y `ReleaseAgent` dry-run.

El informe de avance Sprint 0-18 identificaba como capacidades no iniciadas o inmaduras: multiagente funcional, RAG documental, MCP/conectores externos, RBAC, multiworkspace, plugin architecture, remote runners, compliance packs y reporting enterprise. La recomendación técnica era no saltar directamente a multiagentes, APIs externas o ejecución avanzada sin consolidar gates, policy, approval, evals y trazabilidad.

Fase H debe avanzar hacia una plataforma agentic/enterprise sin debilitar los controles ya construidos. Por tanto, la arquitectura objetivo adopta esta cadena obligatoria:

```text
Workspace -> PolicyEngine -> MIASI -> Approval -> TraceEngine -> EvalHarness -> ReportEngine -> LocalStore
```

## Decisión

DevPilot adopta una arquitectura avanzada basada en **capabilities gobernadas por estado**. Cada capacidad debe declarar si está `implemented`, `implemented-initial`, `planned`, `experimental`, `disabled` o `future`, y no puede cruzar a ejecución real sin policy, trazabilidad, evaluación, documentación y criterios PASS/BLOCK.

### Patrones agentic permitidos

| Patrón | Estado en Fase H | Uso permitido | Condición |
|---|---|---|---|
| Pipeline secuencial | `planned` | Workflows SDLC determinísticos, paso a paso. | Sin acciones destructivas por defecto. |
| Supervisor controlado | `planned` | Coordinación de agentes especializados. | Handoffs explícitos y trazados. |
| Handoffs gobernados | `planned` | Transferencia entre Requirements/Architecture/Security/Test/Review agents. | MIASI + PolicyEngine + TraceEngine por handoff. |
| Graph orchestration | `experimental` | Modelar DAGs de workflows complejos. | Solo después de workflow schema y evals. |
| Autonomía abierta | `disabled` | No permitida. | Requiere ADR futura y aprobación explícita. |
| Remote/distributed agents | `future` | No operativo en Fase H inicial. | Requiere threat model y sandbox remoto. |

### Capabilities de Fase H

| Capability | Estado al Sprint 85 | Primer sprint previsto | Regla de habilitación |
|---|---|---:|---|
| AgentSession/memoria operativa | `planned` | 86 | Retención, redacción y session_id. |
| RAG documental lexical | `planned` | 87 | Fuentes/citas/metadatos obligatorios. |
| MCP/Connector Registry | `planned` | 88 | Deny-by-default, schema y policy. |
| MCP read-only MVP | `planned` | 89 | Sin shell, sin red externa por defecto. |
| MultiAgentCoordinator | `planned` | 90 | Handoffs explícitos, trazas y evals. |
| Multiagent SDLC workflows | `planned` | 91 | Workflow schema y report-only. |
| Advanced evals/red-team | `planned` | 92 | Casos adversariales y safety scoring. |
| Plugin/connector ecosystem | `planned` | 93 | Manifest, permisos y loader dry-run. |
| Multiworkspace/portfolio | `planned` | 94 | Aislamiento de paths, state y secretos. |
| RBAC local | `planned` | 95 | Enforced en API/UI/CLI donde aplique. |
| Audit packs | `planned` | 96 | SecretGuard, manifest y checksums. |
| Compliance packs | `planned` | 97 | Declarativo sobre gates existentes. |
| Remote runners | `experimental/future` | 98 | Disabled-by-default. |
| Industrial readiness | `planned` | 99 | Distinguir production-ready vs experimental. |

### Arquitectura de referencia

```text
UI/API/CLI
  -> ApplicationService
  -> AgentRuntime / WorkflowRunner / RAG / ConnectorAdapter
  -> PolicyEngine + MIASI + ApprovalPolicyChecker
  -> TraceEngine + Metrics + EvalHarness
  -> ReportEngine + LocalStore
  -> Workspace-bound filesystem and registries
```

### Reglas de diseño no negociables

1. Ningún agente puede ejecutar herramientas críticas sin policy, approval y traza.
2. Ningún flujo multiagente puede ocultar handoffs.
3. Ningún RAG puede responder sin referencias o evidencia local.
4. Ningún conector MCP queda allow-by-default.
5. Ningún plugin puede cargar código arbitrario sin manifest y policy binding.
6. Ningún workspace puede leer o escribir state de otro workspace sin registro explícito.
7. Ningún RBAC puede ser solo decorativo; debe influir en decisiones donde aplique.
8. Ningún remote runner puede ejecutar comandos reales durante Fase H sin nueva ADR.
9. Ninguna capacidad experimental puede presentarse como production-ready.

## Alternativas consideradas

| Alternativa | Veredicto | Razón |
|---|---|---|
| Implementar MultiAgentCoordinator inmediatamente | Rechazada para Sprint 85 | Riesgo de orquestación sin threat model y sin session state. |
| Implementar RAG antes de ADR | Rechazada | RAG requiere política de fuentes, SecretGuard e índice local. |
| Activar MCP directamente | Rechazada | MCP introduce connector abuse, tool poisoning y exfiltración. |
| Diseñar todo como SaaS/enterprise cloud | Rechazada | Contradice local-first y aumenta superficie de amenaza. |
| Mantener solo agentes monoagente indefinidamente | Rechazada | No cubre la visión de Fase H ni los gaps históricos. |
| Graph orchestration como núcleo inmediato | Diferida | Demasiado potente antes de workflows secuenciales y evals. |
| Capability-driven architecture por estados | Aceptada | Permite avanzar con controles, evidencias y límites explícitos. |

## Consecuencias

Positivas:

- Fase H inicia con límites claros antes de runtime avanzado.
- Multiagente, RAG, MCP, plugins y enterprise features quedan gobernados por estados.
- DevPilot conserva local-first, deny-by-default y dry-run-first.
- Las futuras implementaciones tienen criterios arquitectónicos verificables.
- MIASI, PolicyEngine, Approval, trazas y evals quedan como frontera obligatoria.

Negativas o limitaciones:

- Sprint 85 no entrega runtime nuevo.
- Algunas capacidades quedan bloqueadas hasta sprints posteriores.
- La arquitectura requiere mantener sincronizados C4, MIASI cards, threat models y manifests.
- Graph orchestration, remote runners y SaaS quedan diferidos.

## Criterios de aplicación

Toda historia futura de Fase H debe declarar:

- capability y estado inicial;
- registry/policy aplicable;
- si requiere approval;
- eventos/trazas mínimos;
- evals mínimos;
- artefactos generados;
- límites de red, filesystem y secretos;
- criterios PASS/BLOCK.

## Criterios PASS

- La ADR compara supervisor, handoffs, graph orchestration y pipeline sequential.
- Capacidades avanzadas quedan marcadas por estado.
- Multiagente, RAG, MCP y plugins quedan deny-by-default hasta sprint específico.
- Remote runners quedan `experimental/future` y disabled-by-default.
- No se introduce runtime avanzado en Sprint 85.

## Criterios BLOCK

- Autorizar multiagente sin observabilidad/evals/approval.
- Dejar MCP allow-by-default.
- Habilitar conectores sin registry/policy.
- Presentar capabilities experimentales como producción.
- Saltarse `PolicyEngine`, MIASI o `ApprovalPolicyChecker`.

## Riesgos

| ID | Riesgo | Mitigación |
|---|---|---|
| RISK-FUNC-85-001 | Arquitectura demasiado ambiciosa | Capability states y sprints por incremento. |
| RISK-FUNC-85-002 | Conectores inseguros | MCP threat model + deny-by-default. |
| RISK-FUNC-85-003 | Multiagente opaco | Handoffs explícitos, traces y evals. |
| RISK-FUNC-85-004 | RAG sin evidencia | Sources/citations obligatorias. |
| RISK-FUNC-85-005 | Enterprise features prematuras | RBAC/multiworkspace/compliance por sprints separados. |

## Relación con sprints posteriores

- `FUNC-SPRINT-86`: AgentSession antes de memoria semántica o multiagente.
- `FUNC-SPRINT-87`: RAG lexical local con fuentes.
- `FUNC-SPRINT-88`: Connector Registry y threat model MCP.
- `FUNC-SPRINT-89`: MCP MVP read-only.
- `FUNC-SPRINT-90`: MultiAgentCoordinator.
- `FUNC-SPRINT-91`: Workflows SDLC dry-run.
- `FUNC-SPRINT-92`: Advanced evals/red-team.
- `FUNC-SPRINT-93`: Plugin ecosystem controlado.
- `FUNC-SPRINT-94` a `99`: enterprise local y cierre de readiness.

## Decisión final

`FUNC-SPRINT-85` queda limitado a arquitectura, seguridad y sincronización documental. La ejecución avanzada empieza únicamente cuando cada capability tenga su propio contrato, registry, policy, tests y documentación.
