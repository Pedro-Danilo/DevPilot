---
title: "Agent Card — DevPilot Local"
doc_id: "DEVPL-MIASI-AGENT"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
standard: "MIASI"
parent_standard: "MIPSoftware"
phase: "SPRINT-PRECODE-07"
updated: "2026-06-05"
approval: "approved_by_owner_direction"
source_baseline: "00_product approved + 01_requirements approved + 02_architecture approved + 03_security approved + 04_quality approved + 05_operations approved"
change_policy: "controlled_changes_allowed_until_precode_baseline"
baseline_role: "precode_approved_baseline"
---

# Agent Card — DevPilot Local

## 1. Propósito

Este documento formaliza los agentes previstos para **DevPilot Local / Agent-assisted SDLC personal** y activa MIASI para el proyecto. La plataforma no se limita a validadores documentales; su evolución comprometida incluye agentes especializados para asistir el ciclo de vida completo del software: planeación, documentación pre-code, requerimientos, arquitectura, seguridad, pruebas, análisis de repositorios, revisión de código, validación de patches, refactor seguro, release y operación.

La regla central es:

> Los agentes de DevPilot asisten, recomiendan, auditan y preparan acciones; los gates determinísticos, las políticas y la aprobación humana controlan la ejecución.

## 2. Alcance por etapa

| Etapa | Agentes permitidos | Nivel de autonomía máximo | Estado |
|---|---|---:|---|
| MVP | PreCodeDocumentationAgent, DocumentationAuditAgent | A2 — agente con herramientas en dry-run | Obligatorio |
| MVP+ | RequirementsAgent, ArchitectureAgent, SecurityAgent, TestPlannerAgent, RepoAnalysisAgent, CodeReviewAgent, PatchReviewAgent, SafeRefactorAgent | A4 — agente con aprobación humana | Planeado |
| Post-MVP | ReleaseAgent, OperationsAgent, DeploymentAssistantAgent, DocumentationAgent, CostOptimizationAgent, MultiAgentCoordinator | A5/A6 controlado | Futuro |
| Producción industrial | Agentes integrados a workflows con observabilidad, evaluación, policy-as-code, approvals y rollback | A6/A7 controlado | No en MVP |

## 3. Taxonomía de agentes

| Agente | Propósito | Entradas principales | Salidas | Herramientas | Riesgo | Fase |
|---|---|---|---|---|---:|---|
| PreCodeDocumentationAgent | Construir borradores de documentos MIPSoftware/MIASI desde una idea inicial. | idea, contexto, estándar, plantillas | propuesta Markdown, brechas, preguntas | read templates, generate draft, report | Medio | MVP |
| DocumentationAuditAgent | Auditar documentos pre-code contra MIPSoftware/MIASI. | docs, checklist, estándares | hallazgos, recomendaciones, PASS/FAIL | read docs, validate structure, report | Medio | MVP |
| RequirementsAgent | Transformar visión en requerimientos verificables. | product docs, stakeholders, MVP scope | RF/RNF, historias, criterios | read docs, generate requirements, traceability | Medio | MVP+ |
| ArchitectureAgent | Proponer arquitectura, C4 y ADRs. | requerimientos, restricciones, riesgos | arquitectura, ADRs, riesgos | read docs, C4 draft, ADR draft | Medio/Alto | MVP+ |
| SecurityAgent | Revisar amenazas, privacidad, secretos, políticas y controles. | arquitectura, tools, agentes, datos | threat findings, policies, gates | scan docs, secret check, policy validate | Alto | MVP+ |
| TestPlannerAgent | Generar estrategia de pruebas y quality gates. | requisitos, aceptación, arquitectura | test plan, eval plan, traceability | read docs, generate tests | Medio | MVP+ |
| RepoAnalysisAgent | Analizar repos reales sin modificar archivos. | repo path, git status, config | inventario, riesgos, estructura | git status, read tree, repo scan | Medio | MVP+ |
| CodeReviewAgent | Revisar código y proponer ajustes sin aplicar cambios. | diff, archivos, reglas | review report, risks, suggestions | read files, diff parse, static checks | Alto | MVP+ |
| PatchReviewAgent | Validar patches antes de aplicarlos. | patch, target repo, policy | verdict, riesgos, rollback notes | patch parse, dry-run apply, tests plan | Alto | MVP+ |
| SafeRefactorAgent | Proponer refactor seguro, reversible y testeable. | code, tests, goals | plan de refactor, patch candidate | code read, tests, patch draft | Alto | MVP+ |
| ReleaseAgent | Asistir release notes, gates, rollback y despliegue. | version, tests, changelog | release checklist, rollback plan | git tags, reports | Alto | Post-MVP |
| OperationsAgent | Asistir operación, incidentes, runbooks y postmortems. | logs, events, incidents | diagnóstico, runbook update | logs read, incident report | Alto | Post-MVP |

## 4. Contrato mínimo de agente

Todo agente debe declarar:

| Campo | Obligatorio | Descripción |
|---|---:|---|
| `agent_id` | Sí | Identificador estable. |
| `name` | Sí | Nombre funcional. |
| `purpose` | Sí | Propósito único y verificable. |
| `scope` | Sí | Qué puede hacer. |
| `out_of_scope` | Sí | Qué no puede hacer. |
| `autonomy_level` | Sí | A0–A7 según MIASI. |
| `allowed_tools` | Sí | Herramientas permitidas por policy. |
| `forbidden_tools` | Sí | Herramientas prohibidas. |
| `input_contract` | Sí | Entradas esperadas. |
| `output_contract` | Sí | Salidas esperadas. |
| `memory_policy` | Sí | Qué puede recordar o persistir. |
| `rag_policy` | Sí | Fuentes permitidas, citas y grounding. |
| `cost_policy` | Sí | Presupuesto y límites si usa APIs. |
| `security_policy` | Sí | Restricciones de secretos, rutas y acciones. |
| `approval_policy` | Sí | Acciones que requieren aprobación humana. |
| `eval_policy` | Sí | Evaluaciones mínimas antes de uso. |
| `observability_policy` | Sí | Eventos y trazas requeridas. |

## 5. Niveles de autonomía permitidos

| Nivel | Uso en DevPilot | Requiere aprobación humana |
|---|---|---:|
| A0 — asistente pasivo | Resumen o explicación sin herramientas. | No |
| A1 — recomendador | Sugiere estructura, riesgos o mejoras. | No |
| A2 — tool calling dry-run | Ejecuta herramientas de lectura/validación sin cambios. | Depende del tool |
| A3 — ejecutor controlado | Genera artefactos nuevos en zona segura. | Sí para escritura |
| A4 — ejecución con aprobación humana | Propone y espera confirmación. | Sí |
| A5 — operacional local-first | Opera flujos locales con policy gates. | Sí para acciones críticas |
| A6 — producción controlada | Acciones sobre sistemas reales. | Sí y con auditoría |
| A7 — industrial | Multiagente con gobernanza completa. | Sí, con gestión formal |

## 6. Relación con MIPSoftware

| Dominio MIPSoftware | Agentes relacionados |
|---|---|
| Producto y negocio | PreCodeDocumentationAgent, DocumentationAuditAgent |
| Requerimientos | RequirementsAgent |
| Arquitectura | ArchitectureAgent |
| Seguridad | SecurityAgent |
| Calidad | TestPlannerAgent |
| Operación | OperationsAgent |
| CI/CD y release | ReleaseAgent |
| MIASI | Todos los agentes |

## 7. Criterios PASS

Un agente queda aprobado para implementación si:

- tiene contrato completo;
- está vinculado a una fase del SDLC;
- tiene herramientas permitidas y prohibidas;
- opera en dry-run por defecto;
- tiene evaluación mínima;
- emite trazas;
- respeta CostGuard y SecretGuard;
- no puede ejecutar acciones destructivas sin aprobación;
- tiene fallback ante error;
- tiene pruebas herméticas.

## 8. Criterios BLOCK

Bloquear implementación o uso del agente si:

- no tiene Agent Card;
- no tiene Tool Card asociada;
- no tiene policy;
- puede escribir/borrar/sobrescribir sin aprobación;
- puede exponer secretos;
- puede usar API externa sin CostGuard;
- no genera trazas;
- no tiene evaluación mínima;
- no separa propuesta de ejecución.

## Actualización FUNC-SPRINT-12 — Agent Runtime mock/local

DevPilot incorpora una primera versión ejecutable de agentes documentales MVP. Esta versión implementa únicamente agentes locales/rule-based, sin LLM externo, sin API keys y con `dry-run` por defecto.

Agentes habilitados inicialmente:

- `precode.audit` mediante alias CLI `documentation-audit`.
- `precode.documentation` mediante alias CLI `precode-documentation`.

Criterios PASS:

- El agente existe en `.devpilot/miasi/agent_registry.json`.
- El agente pertenece a fase MVP.
- El runtime tiene implementación local explícita.
- Toda operación tipo herramienta pasa por Policy Engine.
- El resultado se emite como `CommandResult`, reporte opcional, evento JSONL y registro SQLite best-effort.

Criterios BLOCK:

- Agente no registrado.
- Agente no MVP en Sprint 12.
- Falta de contrato MIASI ejecutable.
- Intento de usar herramienta no permitida o acción bloqueada por política.
- Secreto sintético detectado.

Riesgo: esta capa no implementa todavía agentes autónomos industriales, memoria, planificación multi-step, evaluación formal ni aprobación humana persistente.


## FUNC-SPRINT-51 — AgentRuntime v2 model-aware monoagente

Sprint 51 extiende el contrato operativo de agentes: `precode.audit` y `precode.documentation` pueden usar model calls opcionales por medio de `AgentRuntime v2`, pero siguen operando sin modelo por defecto. Toda llamada model-aware debe registrar `AgentModelCall`, usar `PromptRegistry`, pasar por `ModelAdapterRouter` y quedar registrada en `BudgetLedger`.

Restricciones: no se permiten handoffs, supervisor, comunicación agente-a-agente ni MultiAgentCoordinator. Los agentes especializados de repositorio/código/refactor siguen planificados para sprints posteriores.


## Actualización FUNC-SPRINT-52 — RepoAnalysisAgent

`repo.analysis` queda en estado `implemented-initial` como agente monoagente especializado. Su autonomía máxima es A3, opera read-only sobre motores de repositorio, no modifica archivos, no ejecuta Git write y no realiza handoffs. El agente puede usar `agent.model.generate` solo mediante `AgentRuntime v2`, `PromptRegistry`, `ModelAdapterRouter` y `BudgetLedger`.

## Actualización FUNC-SPRINT-53 — CodeReviewAgent y PatchReviewAgent

`FUNC-SPRINT-53` registra `code.review` y `patch.review` como agentes `implemented-initial` de Fase D.

Contratos:

- monoagente;
- `max_autonomy=A3`;
- dry-run/read-only;
- sin handoffs;
- sin APIs externas;
- sin modificación de código;
- sin aplicación de patches;
- prompts versionados;
- evals offline obligatorios.

`CodeReviewAgent` usa `CodeReviewEngine` para priorizar hallazgos. `PatchReviewAgent` usa `PatchReviewEngine` y `PatchPreflightEngine` para explicar riesgos y aplicabilidad sin mutar el workspace.

## Actualización FUNC-SPRINT-54 — SafeRefactorAgent y TestPlannerAgent gobernados

Sprint 54 registra `safe.refactor` y `testplanner.agent` como agentes `implemented-initial`, monoagente y plan-only. Se agregan las tools `agent.safe_refactor.run`, `agent.test_planner.run` y `traceability.coverage`, junto con reglas de política para mantener refactor/test planning sin mutaciones, sin ejecución de tests por defecto, sin APIs externas y sin handoffs.

Criterios PASS: agentes registrados en MIASI, prompts versionados, evals offline, `mock` como ruta de prueba, `mutations_performed=false`, `tests_run_executed=false` y `refactor_executor_invoked=false`. Criterios BLOCK: ejecución real sin approval, comandos arbitrarios, prompts no versionados o pérdida de modo monoagente.


## Actualización FUNC-SPRINT-55 — Requirements/Architecture/Security agents y cierre Fase D

`requirements.agent`, `architecture.agent` y `security.agent` pasan a `implemented-initial` como agentes SDLC monoagente, read-only y model-aware opcional vía `mock`. No habilitan escritura ni aprobación automática.

Estado: `implemented-initial`; las capacidades son preliminares y deberán evolucionar con trazas AgentOps v2, métricas y reportes persistidos por agente.

## Actualización FUNC-SPRINT-85 — Fase H agentic/enterprise

`FUNC-SPRINT-85` sincroniza esta tarjeta MIASI con `ADR-0016 — Arquitectura avanzada agentic/enterprise` y `advanced_agentic_threat_model.md`.

Estados aplicables a Fase H:

| Estado | Uso permitido |
|---|---|
| `implemented` | Capacidad funcional y cubierta por pruebas. |
| `implemented-initial` | Primera versión operacional con límites explícitos. |
| `planned` | Diseñada, no operativa. |
| `experimental` | Solo con controles, flags y ADR futura cuando aplique. |
| `disabled` | Bloqueada por política. |
| `future` | Fuera del alcance actual. |

Reglas obligatorias:

- Multiagente requiere handoffs explícitos, trazas, policy y evals.
- RAG requiere fuentes, citas o metadatos de evidencia.
- MCP/conectores requieren registry, schema, policy y deny-by-default.
- Plugins requieren manifest, permisos, policy binding y loader no arbitrario.
- Multiworkspace requiere aislamiento de estado, reportes y secretos.
- RBAC debe influir en decisiones, no ser decorativo.
- Remote runners quedan `experimental/future` y disabled-by-default.

Criterio BLOCK: ninguna capacidad avanzada puede saltarse `PolicyEngine`, MIASI, Approval cuando aplique, trazas, evals y ReportEngine.

## Actualización FUNC-SPRINT-90 — MultiAgentCoordinator MVP

Sprint 90 registra `multiagent.coordinator` como agente `implemented-initial` para coordinación secuencial y dry-run. El coordinador solo puede ejecutar workflows allowlisted, usar agentes `implemented` o `implemented-initial`, crear `HandoffRecord` explícitos, evaluar `PolicyEngine` antes del handoff y emitir eventos `multiagent.handoff.evaluated`.

Criterios PASS: handoffs explícitos, trazas por handoff, MIASI/policy por agente, sin mutaciones, sin shell, sin red externa, sin API externa y sin ejecución remota.

Criterios BLOCK: agentes `planned/future`, handoff implícito, ejecución sin `--dry-run`, workflow no registrado o cualquier intento de acción destructiva.


## Actualización FUNC-SPRINT-91 — Workflows SDLC gobernados

`multiagent.coordinator` conserva estado `implemented-initial` y amplía su alcance desde el allowlist interno `repo-review` hacia workflows SDLC definidos por JSON, empezando por `sdlc-review`. El agente coordinador no gana autonomía abierta: `MultiAgentWorkflowRunner` valida schema, safety flags, MIASI y policy antes de ejecutar cada paso con handoffs trazados.

Criterios PASS: workflow validado por schema, `dry-run/report-only`, agentes implementados, handoffs trazados y reporte consolidado. Criterios BLOCK: workflow sin schema, ejecución sin `--dry-run`, agentes futuros, políticas faltantes, shell, red/API externa o mutaciones.


## Actualización FUNC-SPRINT-92 — Safety scoring para agentes avanzados

`security.agent`, `testplanner.agent` y `multiagent.coordinator` pueden referenciar `eval.safety.run` como herramienta de evaluación/reporting local. Esta autorización no incrementa autonomía ni permite ejecución correctiva: solo consume fixtures sintéticos y safety scores para detectar regresiones en prompt injection, secretos, tool misuse, RAG, MCP/conectores y workflows multiagente.

Criterios PASS: suites `advanced-agentic` y `red-team` con `safety_score >= 90`, falsos negativos en cero, sin secretos reales, sin red/API externa y sin LLM judge. Criterios BLOCK: fixtures con secretos reales, workflow no dry-run no detectado, tool misuse no bloqueado o evaluación adversarial inexistente.
