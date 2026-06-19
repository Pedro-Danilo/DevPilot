---
title: "DevPilot Local — Backlog ejecutable Fase H: Capacidades avanzadas"
doc_id: "DEVPL-FUNC-BACKLOG-FASE-H-001"
status: "approved"
version: "1.6.0"
owner: "Ordóñez"
standard: "MIPSoftware"
extension: "MIASI"
phase: "FASE-H-CAPACIDADES-AVANZADAS"
updated: "2026-06-19"
source_repo: "repo_DevPilot_Local_121.zip"
source_report: "Informe de avance DevPilot - sprint 0 - 18.docx"
source_backlog_model: "docs/functional_backlog_after_precode.md"
baseline_dependency: "Fases A-G cerradas; Fase G cerrada por FUNC-SPRINT-84 como implemented-initial"
first_sprint: "FUNC-SPRINT-85"
last_planned_sprint: "FUNC-SPRINT-99"
approved_on: "2026-06-17"
approval: "approved_after_phase_g_closure_validation"
phase_h_status: "in_progress"
first_open_sprint: "FUNC-SPRINT-94"
last_completed_sprint: "FUNC-SPRINT-93"
next_sprint: "FUNC-SPRINT-94"
change_policy: "controlled_changes_allowed_via_docs_as_code"
approval_scope: "phase_h_executable_backlog_review"
---

# DevPilot Local — Backlog ejecutable Fase H: Capacidades avanzadas

## Estado de aprobación funcional

### Aprobación posterior a Fase G

Después de la validación de `FUNC-SPRINT-84`, Fase G queda cerrada como baseline de productización/release local. Este backlog queda promovido a estado `approved` para iniciar implementación controlada desde `FUNC-SPRINT-85`.

La aprobación no autoriza runtime avanzado inmediato: `FUNC-SPRINT-85` debe formalizar primero la ADR y el threat model de capacidades avanzadas antes de habilitar multiagentes, RAG, MCP, plugins, remote runners o capacidades enterprise.

Este documento queda aprobado como backlog ejecutable de **Fase H — Capacidades avanzadas**, siguiendo el modelo operativo usado en `docs/functional_backlog_after_precode.md`.

La Fase H corresponde a la **Ola 11 — Multiagente, RAG, MCP y ecosistema** y a la **Ola 12 — Plataforma industrial/enterprise**. La fase se habilita porque DevPilot ya cerró contratos, trazabilidad, seguridad operacional, repo engineering, IA local gobernada, observabilidad avanzada, producto visual y productización/release local.

## 1. Propósito

La Fase H busca evolucionar DevPilot desde una plataforma local-first agent-assisted SDLC hacia una plataforma avanzada con multiagentes, RAG documental, MCP/conectores, multiworkspace, RBAC, colaboración, compliance packs, plugin ecosystem y capacidades enterprise opcionales.

En lenguaje operativo, esta fase avanza desde:

```text
agentes especializados monoagente + UI/API + observabilidad + release
```

hacia:

```text
multiagent orchestration + RAG + MCP governance + enterprise workflows + multiworkspace + collaboration + extensibility
```

## 2. Regla central de Fase H

Ninguna capacidad avanzada puede saltarse los controles ya construidos:

```text
Workspace → PolicyEngine → MIASI → Approval → TraceEngine → EvalHarness → ReportEngine → LocalStore
```

Reglas obligatorias:

1. Multiagente no puede ejecutarse sin trazas por agente/tool/handoff.
2. RAG no puede responder sin evidencia/citas o metadatos de fuente.
3. MCP/conectores no pueden ejecutarse sin registry, schema, policy, approval y sandbox cuando aplique.
4. Multiworkspace no puede mezclar estados, reportes ni secretos entre proyectos.
5. RBAC no puede ser solo documental; debe aplicarse en API/UI/CLI donde corresponda.
6. Remote runners y cloud control plane quedan como experimentales/future hasta nueva ADR.
7. Todo plugin/conector debe tener manifest, permisos, policy, evals y observabilidad.

## 3. Alcance de Fase H

Incluye:

- ADR de arquitectura avanzada agentic/enterprise;
- Agent session state y memoria operativa;
- RAG documental local;
- MCP threat model y connector registry;
- MCP MVP controlado;
- MultiAgentCoordinator;
- handoffs gobernados;
- workflows multiagente SDLC;
- evaluación/red teaming avanzada;
- plugin/connector registry;
- multiworkspace/portfolio;
- RBAC local;
- colaboración y audit packs;
- compliance packs;
- remote runners experimentales;
- enterprise reporting;
- cierre de industrial readiness.

No incluye:

- autonomía total sin supervisión;
- ejecución remota sin aprobación;
- SaaS obligatorio;
- marketplace público;
- conectores sin threat model;
- RAG sin citas/evidencia;
- agentes que modifiquen repositorios sin sandbox/rollback;
- despliegues automáticos sin Release/Approval gates.

## 3.1 Decisión de aprobación

El backlog H se considera apropiado como continuación de DevPilot porque respeta la secuencia industrial correcta: primero ADR/threat model, después sesión/memoria, luego RAG lexical local, después MCP/connector registry, y solo posteriormente multiagente, workflows, evaluación avanzada, plugins, multiworkspace, RBAC y reporting enterprise.

Ajustes de aprobación aplicados:

- el estado pasa de `draft-for-review` a `approved`;
- la fuente de verdad se actualiza a `repo_DevPilot_Local_108.zip` para el cierre de `FUNC-SPRINT-85`;
- `FUNC-SPRINT-85` queda como primera unidad autorizada;
- capacidades de alto riesgo siguen marcadas como `experimental` o `future` hasta contar con ADR, threat model, policy, registry, pruebas y trazabilidad;
- remote runners, marketplace público, SaaS y despliegues automáticos permanecen fuera de alcance operativo.


## 4. Niveles de implementación de Fase H

| Nivel | Nombre | Objetivo | Estado esperado al cierre |
|---|---|---|---|
| FH-L0 | Decisión avanzada | ADR agentic/enterprise | Límites aprobables |
| FH-L1 | Memoria/sesión | Estado agentic controlado | Agent sessions |
| FH-L2 | RAG local | Recuperación documental con evidencia | Repo/docs Q&A seguro |
| FH-L3 | MCP/conectores | Tool integration controlada | MCP MVP gated |
| FH-L4 | Multiagente | Coordinador y handoffs | Workflows gobernados |
| FH-L5 | Evaluación avanzada | Red teaming y evals multiagente | Safety scoring |
| FH-L6 | Enterprise local | Multiworkspace, RBAC, compliance | Plataforma ampliada |
| FH-L7 | Extensibilidad | Plugins/connectors | Ecosistema controlado |

## 5. Definition of Done transversal

Un sprint de Fase H solo puede cerrarse si cumple:

- no debilita PolicyEngine, MIASI ni Approval Workflow;
- todo agente/tool/conector tiene registry y policy;
- todo flujo agentic avanzado tiene trazas, métricas y evals;
- RAG incluye fuentes/citas/metadata;
- MCP/conectores están deny-by-default;
- RBAC se prueba con usuarios/roles ficticios;
- no hay secretos en reportes;
- README, runbook, MIASI cards y docs de arquitectura se actualizan;
- `pytest -q` y quality gate pasan;
- las capacidades experimentales quedan marcadas como `experimental` o `future`.

## 6. Convenciones de IDs

| Tipo | Prefijo | Ejemplo |
|---|---|---|
| Sprint funcional | `FUNC-SPRINT-XX` | `FUNC-SPRINT-85` |
| Historia | `US-FUNC-XX-YYY` | `US-FUNC-85-001` |
| Tarea | `FUNC-XX-YYY` | `FUNC-85-003` |
| Prueba | `TEST-FUNC-XX-YYY` | `TEST-FUNC-85-002` |
| Gate | `GATE-FUNC-XX` | `GATE-FUNC-85` |
| Riesgo | `RISK-FUNC-XX-YYY` | `RISK-FUNC-85-001` |
| Agent | `AGENT-*` | `AGENT-MULTI-SUPERVISOR` |
| Connector | `CONN-*` | `CONN-MCP-FS-READONLY` |
| RAG | `RAG-*` | `RAG-DOCS-INDEX` |

## 7. Roadmap funcional de Fase H

| Ola | Sprints | Resultado esperado |
|---|---|---|
| Ola 11 | FUNC-SPRINT-85 a 93 | Memoria/sesión, RAG, MCP, MultiAgentCoordinator, evals avanzadas, plugins/connectors |
| Ola 12 | FUNC-SPRINT-94 a 99 | Multiworkspace, RBAC, colaboración, compliance, remote runners experimentales, enterprise reporting |

## 8. Referencias técnicas externas de apoyo

- MCP define un estándar abierto para conectar aplicaciones de IA con datos, herramientas y workflows externos.
- Los sistemas multiagente modernos suelen usar handoffs, tool-calling supervisor y/o orquestación basada en grafos.
- RAG requiere recuperación de fuentes y control de groundedness para evitar respuestas sin evidencia.
- Capacidades enterprise exigen RBAC, auditoría, aislamiento, seguridad y gobierno operativo.

---

## FUNC-SPRINT-85 — ADR de arquitectura avanzada agentic/enterprise

## Objetivo

Definir la arquitectura objetivo de Fase H antes de introducir multiagentes, RAG, MCP, conectores y enterprise features.

## Historias

| ID | Historia | Criterio de aceptación |
|---|---|---|
| US-FUNC-85-001 | Como arquitecto, quiero delimitar qué significa “multiagente” en DevPilot. | ADR define patrones permitidos. |
| US-FUNC-85-002 | Como security reviewer, quiero threat model de capacidades avanzadas. | Existe threat model de MCP/RAG/multiagente. |
| US-FUNC-85-003 | Como owner, quiero saber qué queda experimental. | Capacidades `experimental/future` claras. |

## Tareas

| ID | Tarea | Entregable | PASS |
|---|---|---|---|
| FUNC-85-001 | Crear ADR avanzada | `docs/02_architecture/adrs/ADR-XXXX-advanced-agentic-enterprise.md` | Decisión. |
| FUNC-85-002 | Threat model avanzado | `docs/03_security/advanced_agentic_threat_model.md` | Riesgos. |
| FUNC-85-003 | Actualizar C4 | `c4_context`, `c4_container`, nuevo/actualizado `c4_component` | Estados claros. |
| FUNC-85-004 | Actualizar MIASI cards | `docs/06_miasi/*.md` | Multiagent/RAG/MCP. |
| FUNC-85-005 | Manifest | `docs/functional_sprint_85_manifest.json` | JSON válido. |

## Archivos previstos

```text
docs/02_architecture/adrs/ADR-XXXX-advanced-agentic-enterprise.md
docs/03_security/advanced_agentic_threat_model.md
docs/02_architecture/c4_component.md
docs/audits/func_sprint_85_advanced_architecture_audit.md
docs/functional_sprint_85_manifest.json
```

## Comandos objetivo

```powershell
python -m devpilot_core validate-artifact docs/03_security/advanced_agentic_threat_model.md --json
python -m devpilot_core miasi validate --json
python -m pytest -q
```

## Criterios PASS

- ADR compara patrones supervisor, handoffs, graph orchestration y pipeline sequential.
- Threat model cubre prompt injection, tool poisoning, data leakage, privilege escalation y connector abuse.
- Capacidades avanzadas quedan marcadas por estado.

## Criterios BLOCK

- No cerrar si autoriza multiagente sin observabilidad/evals/approval.
- No cerrar si MCP queda allow-by-default.
- No cerrar si no actualiza MIASI.

## Riesgos y mitigaciones

| ID | Riesgo | Mitigación |
|---|---|---|
| RISK-FUNC-85-001 | Arquitectura demasiado ambiciosa | ADR por estados. |
| RISK-FUNC-85-002 | Conectores inseguros | Threat model + deny-by-default. |
| RISK-FUNC-85-003 | Confundir experimental con producción | Etiquetas explícitas. |

## Prompt operativo sugerido

```text
Implementa FUNC-SPRINT-85. Crea ADR avanzada agentic/enterprise y threat model. No implementes todavía multiagentes ni MCP runtime. Actualiza MIASI y C4 con estados implemented/planned/experimental/future.
```

---

## Estado de implementación Sprint 85

`FUNC-SPRINT-85 — ADR de arquitectura avanzada agentic/enterprise` queda implementado en estado `implemented-initial` / `PASS focalizado`. Este sprint abre Fase H mediante arquitectura y seguridad, no mediante runtime avanzado.

Entregables de cierre:

- `docs/02_architecture/adrs/ADR-0016-advanced-agentic-enterprise.md`.
- `docs/03_security/advanced_agentic_threat_model.md`.
- `docs/02_architecture/c4_component.md` actualizado para Fase H.
- `docs/06_miasi/*.md` sincronizados con reglas multiagente/RAG/MCP/plugins/RBAC.
- `docs/audits/func_sprint_85_advanced_architecture_audit.md`.
- `docs/functional_sprint_85_manifest.json`.
- `tests/test_sprint_85_documentation.py`.

Límites explícitos: no se implementa MultiAgentCoordinator, RAG runtime, MCP runtime, plugin loader, RBAC runtime, multiworkspace ni remote runners. El siguiente sprint autorizado es `FUNC-SPRINT-86 — Agent session state y memoria operativa controlada`.


## FUNC-SPRINT-86 — Agent session state y memoria operativa controlada

## Objetivo

Crear una base de sesión/memoria operativa para agentes sin implementar memoria semántica ni RAG todavía.

## Historias

| ID | Historia | Criterio de aceptación |
|---|---|---|
| US-FUNC-86-001 | Como AgentRuntime, quiero session_id por ejecución. | Existe AgentSession. |
| US-FUNC-86-002 | Como auditor, quiero reconstruir pasos de una sesión. | Sesión se persiste/traza. |
| US-FUNC-86-003 | Como security reviewer, quiero límites de memoria. | Retención y redacción definidas. |

## Tareas

| ID | Tarea | Entregable | PASS |
|---|---|---|---|
| FUNC-86-001 | Crear AgentSession model | `src/devpilot_core/agents/session.py` | Session state. |
| FUNC-86-002 | Persistencia session | LocalStore/TraceStore | Consultable. |
| FUNC-86-003 | CLI session inspect | `agent session inspect` | JSON. |
| FUNC-86-004 | Retention policy | Docs | Límites. |
| FUNC-86-005 | Tests | `tests/test_agent_session.py` | PASS. |

## Archivos previstos

```text
src/devpilot_core/agents/session.py
tests/test_agent_session.py
docs/06_miasi/agent_session_card.md
docs/audits/func_sprint_86_agent_session_audit.md
docs/functional_sprint_86_manifest.json
```

## Comandos objetivo

```powershell
python -m devpilot_core agent session inspect --session-id <id> --json
python -m pytest -q
```

## Criterios PASS

- No guarda secretos crudos.
- Session state es local.
- Cada agent run puede asociarse a session_id.

## Criterios BLOCK

- No cerrar si sesión cruza workspaces sin permiso.
- No cerrar si guarda prompts/respuestas con secretos sin redacción.

## Prompt operativo sugerido

```text
Implementa FUNC-SPRINT-86. Crea AgentSession local con límites de retención y redacción. No implementes RAG ni memoria semántica todavía.
```

---

## Estado de implementación Sprint 86

`FUNC-SPRINT-86 — Agent session state y memoria operativa controlada` queda implementado en estado `implemented-initial` / `PASS focalizado`. Este sprint introduce memoria operativa local y redacted para ejecuciones agentic, asociando cada `agent run` con un `session_id` inspeccionable.

Entregables de cierre:

- `src/devpilot_core/agents/session.py`.
- `docs/06_miasi/agent_session_card.md`.
- `docs/audits/func_sprint_86_agent_session_audit.md`.
- `docs/functional_sprint_86_manifest.json`.
- `tests/test_agent_session.py`.
- `tests/test_sprint_86_documentation.py`.

Límites explícitos: no se implementa memoria semántica, embeddings, RAG, MCP runtime, MultiAgentCoordinator, plugins ni remote runners. El siguiente sprint autorizado es `FUNC-SPRINT-87 — RAG documental local MVP`.


## FUNC-SPRINT-87 — RAG documental local MVP

## Objetivo

Implementar RAG documental local sobre `docs/` y reportes seleccionados, inicialmente con índice lexical y opción posterior de embeddings locales.

## Historias

| ID | Historia | Criterio de aceptación |
|---|---|---|
| US-FUNC-87-001 | Como usuario, quiero consultar documentación del proyecto con fuentes. | `rag query` responde con referencias. |
| US-FUNC-87-002 | Como auditor, quiero que RAG cite documentos. | Respuestas incluyen source refs. |
| US-FUNC-87-003 | Como security reviewer, quiero evitar secretos en índice. | SecretGuard en indexing. |

## Tareas

| ID | Tarea | Entregable | PASS |
|---|---|---|---|
| FUNC-87-001 | RAG indexer lexical | `src/devpilot_core/rag/indexer.py` | Índice local. |
| FUNC-87-002 | Retriever | `src/devpilot_core/rag/retriever.py` | Top-k docs. |
| FUNC-87-003 | CLI | `rag index`, `rag query` | JSON. |
| FUNC-87-004 | Source metadata | Documento/rango/fragmento | Evidencia. |
| FUNC-87-005 | Tests | `tests/test_rag_local.py` | PASS. |

## Archivos previstos

```text
src/devpilot_core/rag/__init__.py
src/devpilot_core/rag/indexer.py
src/devpilot_core/rag/retriever.py
tests/test_rag_local.py
docs/audits/func_sprint_87_rag_local_audit.md
docs/functional_sprint_87_manifest.json
```

## Comandos objetivo

```powershell
python -m devpilot_core rag index --target docs --json
python -m devpilot_core rag query "Qué valida readiness strict" --json
python -m pytest -q
```

## Criterios PASS

- RAG no inventa fuentes.
- Cada respuesta incluye referencias a documentos o fragmentos.
- Índice se genera localmente.
- SecretGuard revisa contenido indexado.

## Criterios BLOCK

- No cerrar si responde sin fuentes.
- No cerrar si indexa `.env`, `.git`, `.venv` o secretos.
- No cerrar si requiere API externa.

## Prompt operativo sugerido

```text
Implementa FUNC-SPRINT-87. Crea RAG documental local lexical-first con índice local, retriever, referencias a fuentes y SecretGuard. No uses APIs externas.
```

### Estado de implementación Sprint 87

`FUNC-SPRINT-87 — RAG documental local MVP` queda implementado como baseline lexical local. Se agregan `rag index` y `rag query`, índice runtime bajo `.devpilot/rag/`, fuentes obligatorias, `SecretGuard`, `PathGuard`, MIASI tools/policies, auditoría y manifest. La capacidad queda `implemented-initial`: no usa embeddings obligatorios, LLM, red, APIs externas ni vector database externa. La siguiente unidad abierta es `FUNC-SPRINT-88 — MCP threat model y Connector Registry`.

---

## FUNC-SPRINT-88 — MCP threat model y Connector Registry

## Objetivo

Diseñar la integración MCP/conectores de DevPilot como capacidad deny-by-default, antes de crear cliente o servidor MCP.

## Historias

| ID | Historia | Criterio de aceptación |
|---|---|---|
| US-FUNC-88-001 | Como arquitecto, quiero un registry de conectores. | Existe Connector Registry. |
| US-FUNC-88-002 | Como security reviewer, quiero threat model MCP. | Riesgos MCP documentados. |
| US-FUNC-88-003 | Como agente, quiero descubrir tools permitidas. | Registry expone estado/policies. |

## Tareas

| ID | Tarea | Entregable | PASS |
|---|---|---|---|
| FUNC-88-001 | Crear connector schema | `docs/schemas/connector_registry.schema.json` | Validable. |
| FUNC-88-002 | Crear Connector Registry | `.devpilot/connectors/connector_registry.json` | Deny-by-default. |
| FUNC-88-003 | Threat model MCP | `docs/03_security/mcp_connector_threat_model.md` | Completo. |
| FUNC-88-004 | CLI validate connectors | `connector validate` | JSON. |
| FUNC-88-005 | Tests | `tests/test_connector_registry.py` | PASS. |

## Archivos previstos

```text
src/devpilot_core/connectors/__init__.py
src/devpilot_core/connectors/registry.py
.devpilot/connectors/connector_registry.json
docs/03_security/mcp_connector_threat_model.md
tests/test_connector_registry.py
docs/audits/func_sprint_88_connector_registry_audit.md
docs/functional_sprint_88_manifest.json
```

## Comandos objetivo

```powershell
python -m devpilot_core connector validate --json
python -m devpilot_core validate-artifact docs/03_security/mcp_connector_threat_model.md --json
python -m pytest -q
```

## Criterios PASS

- Registry distingue `disabled`, `planned`, `implemented`, `experimental`.
- Todos los conectores tienen policy_rule_ids.
- MCP queda deshabilitado por defecto.

## Criterios BLOCK

- No cerrar si permite conectores sin policy.
- No cerrar si ejecuta conectores reales.

## Prompt operativo sugerido

```text
Implementa FUNC-SPRINT-88. Crea Connector Registry, schema y threat model MCP. No implementes cliente/servidor MCP real todavía. Todo conector debe ser deny-by-default.
```

---

## Estado de implementación Sprint 88

`FUNC-SPRINT-88 — MCP threat model y Connector Registry` queda implementado como primera base de gobernanza MCP/conectores. El sprint crea schema, registry, threat model, CLI `connector validate`, auditoría, manifest y pruebas. No implementa cliente MCP, servidor MCP, adapter ni ejecución real de conectores.

Límites explícitos:

- MCP queda `enabled_by_default=false`.
- Todos los conectores quedan `default_effect=deny`.
- Todo conector requiere `policy_rule_ids`.
- No hay red, API externa, shell ni ejecución real.
- `FUNC-SPRINT-89` queda autorizado únicamente como MVP read-only gobernado.


## FUNC-SPRINT-89 — MCP MVP controlado y herramientas read-only

## Objetivo

Implementar un MVP MCP/conector controlado, limitado a herramientas locales read-only y sin ejecución remota ni red externa por defecto.

## Historias

| ID | Historia | Criterio de aceptación |
|---|---|---|
| US-FUNC-89-001 | Como agente, quiero consultar un conector read-only. | MCP client/adapter controlado. |
| US-FUNC-89-002 | Como security reviewer, quiero policy antes de tool call. | PolicyEngine obligatorio. |
| US-FUNC-89-003 | Como auditor, quiero trazas por conector. | Connector calls trazadas. |

## Tareas

| ID | Tarea | Entregable | PASS |
|---|---|---|---|
| FUNC-89-001 | Crear ConnectorAdapter | `src/devpilot_core/connectors/adapter.py` | Read-only. |
| FUNC-89-002 | CLI connector call dry-run | `connector call --dry-run` | No ejecución real por defecto. |
| FUNC-89-003 | Integrar policy/trace | PolicyEngine + TraceEngine | Evidencia. |
| FUNC-89-004 | Fixtures de conector local | tests fixtures | Seguro. |
| FUNC-89-005 | Tests | `tests/test_connector_adapter.py` | PASS. |

## Archivos previstos

```text
src/devpilot_core/connectors/adapter.py
tests/test_connector_adapter.py
docs/audits/func_sprint_89_mcp_mvp_audit.md
docs/functional_sprint_89_manifest.json
```

## Comandos objetivo

```powershell
python -m devpilot_core connector call --connector local-docs --operation list --dry-run --json
python -m pytest -q
```

## Criterios PASS

- Conector MVP es read-only.
- Todo call pasa por PolicyEngine.
- Todo call genera trace/event.
- No red externa por defecto.

## Criterios BLOCK

- No cerrar si ejecuta comandos arbitrarios.
- No cerrar si permite stdio/raw shell sin allowlist.
- No cerrar si no tiene tests de bloqueo.

## Prompt operativo sugerido

```text
Implementa FUNC-SPRINT-89. Crea ConnectorAdapter read-only y dry-run. Integra policy y trazas. No habilites conectores de red ni ejecución shell.
```

---

## FUNC-SPRINT-90 — MultiAgentCoordinator MVP y handoffs gobernados

## Objetivo

Implementar un coordinador multiagente inicial, con handoffs explícitos, sin autonomía abierta y sin ejecución destructiva.

## Historias

| ID | Historia | Criterio de aceptación |
|---|---|---|
| US-FUNC-90-001 | Como usuario, quiero coordinar varios agentes especializados. | Existe MultiAgentCoordinator MVP. |
| US-FUNC-90-002 | Como auditor, quiero ver handoffs. | Handoffs trazados. |
| US-FUNC-90-003 | Como security reviewer, quiero límites por agente. | MIASI/policy por agente. |

## Tareas

| ID | Tarea | Entregable | PASS |
|---|---|---|---|
| FUNC-90-001 | Crear MultiAgentCoordinator | `src/devpilot_core/multiagent/coordinator.py` | Secuencial/gobernado. |
| FUNC-90-002 | Handoff model | `handoff.py` | Explicito. |
| FUNC-90-003 | CLI workflow dry-run | `multiagent run --workflow` | JSON. |
| FUNC-90-004 | MIASI update | Registry/policy | `multiagent.coordinator` implemented-initial. |
| FUNC-90-005 | Tests | `tests/test_multiagent_coordinator.py` | PASS. |

## Archivos previstos

```text
src/devpilot_core/multiagent/__init__.py
src/devpilot_core/multiagent/coordinator.py
src/devpilot_core/multiagent/handoff.py
tests/test_multiagent_coordinator.py
docs/audits/func_sprint_90_multiagent_coordinator_audit.md
docs/functional_sprint_90_manifest.json
```

## Comandos objetivo

```powershell
python -m devpilot_core multiagent run --workflow repo-review --dry-run --json
python -m pytest -q
```

## Criterios PASS

- Handoffs son explícitos y trazados.
- Coordinador solo usa agentes `implemented`.
- Dry-run por defecto.
- No ejecuta acciones críticas.

## Criterios BLOCK

- No cerrar si permite agentes `planned/future`.
- No cerrar si hay handoff implícito sin trace.
- No cerrar si modifica archivos.

## Prompt operativo sugerido

```text
Implementa FUNC-SPRINT-90. Crea MultiAgentCoordinator MVP secuencial y dry-run, con handoffs explícitos, trazas y MIASI/policy enforcement. No habilites autonomía abierta.
```

---

## Estado de implementación Sprint 90

`FUNC-SPRINT-90 — MultiAgentCoordinator MVP y handoffs gobernados` queda implementado como coordinador secuencial local `implemented-initial`. Se agrega `MultiAgentCoordinator`, `HandoffRecord`, CLI `multiagent run --workflow repo-review --dry-run`, MIASI agent/tool/policy updates, auditoría, manifest y pruebas.

Límites explícitos:

- solo workflow allowlisted `repo-review`;
- dry-run/report-only obligatorio;
- handoffs explícitos y trazados mediante `multiagent.handoff.evaluated`;
- solo agentes con estado `implemented` o `implemented-initial`;
- sin autonomía abierta, graph planner, memoria compartida semántica, ejecución destructiva, shell, red externa, APIs externas ni ejecución remota.

El siguiente sprint autorizado es `FUNC-SPRINT-91 — Workflows multiagente SDLC dry-run`.

---


## FUNC-SPRINT-91 — Workflows multiagente SDLC dry-run

## Objetivo

Definir y ejecutar workflows multiagente predefinidos para SDLC, inicialmente en modo dry-run y report-only.

## Historias

| ID | Historia | Criterio de aceptación |
|---|---|---|
| US-FUNC-91-001 | Como owner, quiero un workflow de revisión SDLC. | Existe workflow `sdlc-review`. |
| US-FUNC-91-002 | Como arquitecto, quiero salida consolidada. | Reporte multiagente. |
| US-FUNC-91-003 | Como auditor, quiero trazabilidad de cada agente. | Cada paso tiene trace. |

## Tareas

| ID | Tarea | Entregable | PASS |
|---|---|---|---|
| FUNC-91-001 | Workflow definitions | `.devpilot/workflows/*.json` | Schemas. |
| FUNC-91-002 | Workflow runner | `multiagent workflow run` | Dry-run. |
| FUNC-91-003 | Workflow report | `outputs/reports/multiagent_workflow.*` | Consolidado. |
| FUNC-91-004 | Evals workflow | Fixtures | PASS. |
| FUNC-91-005 | Docs | Runbook/MIASI | Actualizados. |

## Archivos previstos

```text
.devpilot/workflows/sdlc_review.json
src/devpilot_core/multiagent/workflow.py
tests/test_multiagent_workflow.py
docs/audits/func_sprint_91_multiagent_workflows_audit.md
docs/functional_sprint_91_manifest.json
```

## Comandos objetivo

```powershell
python -m devpilot_core multiagent workflow run --workflow sdlc_review --dry-run --json
python -m pytest -q
```

## Criterios PASS

- Workflow usa solo agentes implementados.
- Cada paso genera output trazable.
- No hay acciones destructivas.
- Reporte consolida riesgos y recomendaciones.

## Criterios BLOCK

- No cerrar si workflows no tienen schema.
- No cerrar si ejecuta herramientas críticas sin approval.

## Prompt operativo sugerido

```text
Implementa FUNC-SPRINT-91. Crea workflows multiagente SDLC predefinidos en dry-run, con schema, runner, reportes y trazas. No ejecutes acciones destructivas.
```

---


## Estado de implementación Sprint 91

`FUNC-SPRINT-91 — Workflows multiagente SDLC dry-run` queda implementado como capacidad `implemented-initial` de workflows SDLC predefinidos y gobernados. Se agrega `.devpilot/workflows/sdlc_review.json`, `docs/schemas/multiagent_workflow.schema.json`, `MultiAgentWorkflowRunner`, CLI `multiagent workflow run --workflow sdlc_review --dry-run`, fixtures de evaluación, auditoría, manifest y pruebas.

Límites explícitos:

- workflow `sdlc-review` validado por schema local antes de ejecutar;
- `dry-run/report-only` obligatorio;
- reutiliza `MultiAgentCoordinator` y `HandoffRecord`;
- cada paso conserva handoff explícito, policy check y trace;
- solo agentes `implemented` o `implemented-initial`;
- sin autonomía abierta, planner dinámico, graph orchestration, shell, red externa, APIs externas, ejecución remota ni mutaciones;
- el reporte consolida riesgos/recomendaciones como evidencia, no como autorización para modificar repositorio.

El siguiente sprint autorizado es `FUNC-SPRINT-92 — Evaluación avanzada, red teaming y safety scoring`.

---

## FUNC-SPRINT-92 — Evaluación avanzada, red teaming y safety scoring

## Objetivo

Ampliar el Evaluation Harness para agentes avanzados, RAG, MCP y multiagentes con casos adversariales y métricas de seguridad.

## Historias

| ID | Historia | Criterio de aceptación |
|---|---|---|
| US-FUNC-92-001 | Como revisor de seguridad, quiero probar ataques agentic. | Existen red-team fixtures. |
| US-FUNC-92-002 | Como owner, quiero safety score por agente/workflow. | Métricas generadas. |
| US-FUNC-92-003 | Como arquitecto, quiero bloquear workflows inseguros. | Quality gate consume evals. |

## Tareas

| ID | Tarea | Entregable | PASS |
|---|---|---|---|
| FUNC-92-001 | Red-team fixtures | `evals/fixtures/red_team_*` | Casos. |
| FUNC-92-002 | Safety metrics | EvalRunner extension | Scores. |
| FUNC-92-003 | RAG evals | groundedness/source coverage | PASS. |
| FUNC-92-004 | MCP evals | connector misuse/prompt injection | PASS. |
| FUNC-92-005 | Tests | `tests/test_advanced_evals.py` | PASS. |

## Archivos previstos

```text
evals/fixtures/advanced_agentic_eval_cases.json
src/devpilot_core/evals/safety.py
tests/test_advanced_evals.py
docs/audits/func_sprint_92_advanced_evals_audit.md
docs/functional_sprint_92_manifest.json
```

## Comandos objetivo

```powershell
python -m devpilot_core eval run --suite advanced-agentic --json
python -m devpilot_core eval run --suite red-team --json
python -m pytest -q
```

## Criterios PASS

- Incluye casos de prompt injection, secret leakage, tool misuse y missing sources.
- Métricas son JSON parseables.
- Quality gate puede consumir resultados.

## Criterios BLOCK

- No cerrar si evals solo prueban casos felices.
- No cerrar si red-team fixtures contienen secretos reales.

## Prompt operativo sugerido

```text
Implementa FUNC-SPRINT-92. Amplía Evaluation Harness con suite advanced-agentic y red-team, métricas de seguridad, RAG/MCP/multiagent evals y tests. No uses datos sensibles reales.
```

---

## Estado de implementación Sprint 92

`FUNC-SPRINT-92 — Evaluación avanzada, red teaming y safety scoring` queda implementado como capacidad `implemented-initial` de evaluación avanzada local. El sprint agrega suites `advanced-agentic` y `red-team`, `SafetyEvalEngine`, safety scoring, fixtures sintéticos, consumo por `quality-gate run --profile ci`, MIASI/policies, auditoría, manifest y pruebas.

Límites explícitos: no usa LLM judge, no usa red, no llama APIs externas, no almacena secretos reales, no autoriza correcciones automáticas y no sustituye red teaming industrial. El siguiente sprint autorizado es `FUNC-SPRINT-93 — Plugin y connector ecosystem controlado`.

## FUNC-SPRINT-93 — Plugin y connector ecosystem controlado

## Objetivo

Crear una arquitectura inicial de extensibilidad mediante plugins/conectores internos, con manifest, permisos, policy, evaluación y observabilidad.

## Historias

| ID | Historia | Criterio de aceptación |
|---|---|---|
| US-FUNC-93-001 | Como desarrollador, quiero registrar plugins internos. | Existe Plugin Registry. |
| US-FUNC-93-002 | Como security reviewer, quiero permisos por plugin. | Manifest incluye permissions/policy. |
| US-FUNC-93-003 | Como auditor, quiero saber qué plugin ejecutó qué. | Traces por plugin. |

## Tareas

| ID | Tarea | Entregable | PASS |
|---|---|---|---|
| FUNC-93-001 | Plugin manifest schema | `plugin_manifest.schema.json` | Validable. |
| FUNC-93-002 | Plugin Registry | `.devpilot/plugins/plugin_registry.json` | Controlado. |
| FUNC-93-003 | Plugin loader dry-run | No carga código arbitrario por defecto | Seguro. |
| FUNC-93-004 | Policy binding | Plugin permissions → PolicyEngine | Aplicado. |
| FUNC-93-005 | Tests | `tests/test_plugin_registry.py` | PASS. |

## Archivos previstos

```text
src/devpilot_core/plugins/__init__.py
src/devpilot_core/plugins/registry.py
.devpilot/plugins/plugin_registry.json
docs/schemas/plugin_manifest.schema.json
tests/test_plugin_registry.py
docs/audits/func_sprint_93_plugin_ecosystem_audit.md
docs/functional_sprint_93_manifest.json
```

## Comandos objetivo

```powershell
python -m devpilot_core plugin validate --json
python -m devpilot_core plugin list --json
python -m pytest -q
```

## Criterios PASS

- Plugin loading ejecutable queda deshabilitado o dry-run.
- Manifest incluye permisos, policy, owner, versión y risk level.
- No carga código remoto.

## Criterios BLOCK

- No cerrar si permite ejecución dinámica arbitraria.
- No cerrar si plugins no pasan por policy.

## Prompt operativo sugerido

```text
Implementa FUNC-SPRINT-93. Crea Plugin Registry y manifests controlados. No ejecutes plugins arbitrarios todavía. Integra permisos, policy, tests y documentación.
```

---

## FUNC-SPRINT-94 — Multiworkspace Manager y portfolio local

## Objetivo

Permitir que DevPilot administre múltiples workspaces locales sin mezclar configuración, estado, trazas ni secretos.

## Historias

| ID | Historia | Criterio de aceptación |
|---|---|---|
| US-FUNC-94-001 | Como owner, quiero registrar varios proyectos. | Existe `workspace registry`. |
| US-FUNC-94-002 | Como operador, quiero ver estado de portfolio. | `portfolio status` funciona. |
| US-FUNC-94-003 | Como security reviewer, quiero aislamiento. | No mezcla states ni paths. |

## Tareas

| ID | Tarea | Entregable | PASS |
|---|---|---|---|
| FUNC-94-001 | Workspace Registry | `~/.devpilot/workspaces.json` o local equivalente | Decisión documentada. |
| FUNC-94-002 | CLI multiworkspace | `workspace register/list/select` | JSON. |
| FUNC-94-003 | Portfolio status | `portfolio status` | Consolida read-only. |
| FUNC-94-004 | Path isolation tests | Tests | PASS. |
| FUNC-94-005 | Docs | Runbook | Actualizado. |

## Archivos previstos

```text
src/devpilot_core/workspace/registry.py
src/devpilot_core/portfolio/status.py
tests/test_multiworkspace.py
docs/audits/func_sprint_94_multiworkspace_audit.md
docs/functional_sprint_94_manifest.json
```

## Comandos objetivo

```powershell
python -m devpilot_core workspace register --path . --json
python -m devpilot_core workspace list --json
python -m devpilot_core portfolio status --json
python -m pytest -q
```

## Criterios PASS

- No mezcla `.devpilot/devpilot.db` entre workspaces.
- No accede a rutas no registradas.
- Portfolio status es read-only.

## Criterios BLOCK

- No cerrar si paths externos no pasan por PathGuard.
- No cerrar si estado de un workspace se escribe en otro.

## Prompt operativo sugerido

```text
Implementa FUNC-SPRINT-94. Crea Multiworkspace Registry y Portfolio status local read-only. Asegura aislamiento de rutas, estados, reportes y secretos.
```

---

## FUNC-SPRINT-95 — RBAC local y modelo de identidad

## Objetivo

Agregar un modelo local de identidad/roles para proteger UI/API/acciones sensibles, sin implementar SaaS ni autenticación remota.

## Historias

| ID | Historia | Criterio de aceptación |
|---|---|---|
| US-FUNC-95-001 | Como owner, quiero diferenciar roles. | Existen roles locales. |
| US-FUNC-95-002 | Como reviewer, quiero permisos por acción. | PolicyEngine consulta RBAC. |
| US-FUNC-95-003 | Como auditor, quiero saber quién aprobó. | Approvals incluyen actor. |

## Tareas

| ID | Tarea | Entregable | PASS |
|---|---|---|---|
| FUNC-95-001 | Identity model | `identity/models.py` | Usuarios/roles. |
| FUNC-95-002 | RBAC policy | `identity/rbac.py` | Permisos. |
| FUNC-95-003 | CLI identity | `identity list`, `identity current` | JSON. |
| FUNC-95-004 | Approval actor binding | Approval Workflow update | Actor. |
| FUNC-95-005 | Tests | `tests/test_identity_rbac.py` | PASS. |

## Archivos previstos

```text
src/devpilot_core/identity/__init__.py
src/devpilot_core/identity/models.py
src/devpilot_core/identity/rbac.py
tests/test_identity_rbac.py
docs/audits/func_sprint_95_rbac_audit.md
docs/functional_sprint_95_manifest.json
```

## Comandos objetivo

```powershell
python -m devpilot_core identity current --json
python -m devpilot_core identity roles --json
python -m pytest -q
```

## Criterios PASS

- Roles mínimos: owner, architect, developer, reviewer, operator, agent-supervisor.
- RBAC se integra con PolicyEngine para acciones sensibles.
- No implementa auth remota.

## Criterios BLOCK

- No cerrar si roles son solo decorativos.
- No cerrar si permite aprobar acciones críticas sin actor.

## Prompt operativo sugerido

```text
Implementa FUNC-SPRINT-95. Crea identidad local y RBAC mínimo integrado con PolicyEngine y Approval Workflow. No implementes SaaS ni auth remota.
```

---

## FUNC-SPRINT-96 — Colaboración local y audit packs

## Objetivo

Crear capacidades de colaboración local/documental y paquetes de auditoría exportables sin plataforma cloud.

## Historias

| ID | Historia | Criterio de aceptación |
|---|---|---|
| US-FUNC-96-001 | Como equipo, quiero compartir evidencia. | Audit pack exportable. |
| US-FUNC-96-002 | Como reviewer, quiero revisar cambios offline. | Pack contiene reports/manifests/changelog. |
| US-FUNC-96-003 | Como auditor, quiero integridad del pack. | Checksums incluidos. |

## Tareas

| ID | Tarea | Entregable | PASS |
|---|---|---|---|
| FUNC-96-001 | Audit pack builder | `audit-pack build` | ZIP limpio. |
| FUNC-96-002 | Collaboration notes | Docs | Procedimiento. |
| FUNC-96-003 | Pack manifest/checksum | JSON + SHA256 | Verificable. |
| FUNC-96-004 | Pack verify | `audit-pack verify` | PASS/BLOCK. |
| FUNC-96-005 | Tests | `tests/test_audit_pack.py` | PASS. |

## Archivos previstos

```text
src/devpilot_core/auditpack/__init__.py
src/devpilot_core/auditpack/builder.py
tests/test_audit_pack.py
docs/05_operations/audit_pack_runbook.md
docs/audits/func_sprint_96_audit_pack_audit.md
docs/functional_sprint_96_manifest.json
```

## Comandos objetivo

```powershell
python -m devpilot_core audit-pack build --json
python -m devpilot_core audit-pack verify --path outputs/auditpacks/<pack>.zip --json
python -m pytest -q
```

## Criterios PASS

- Audit pack no incluye secretos ni runtime DB salvo opción explícita.
- Incluye manifest y checksums.
- Verificación local funciona.

## Criterios BLOCK

- No cerrar si exporta `.env`, providers local o DB sin advertencia.
- No cerrar si no verifica integridad.

## Prompt operativo sugerido

```text
Implementa FUNC-SPRINT-96. Crea AuditPack builder/verifier local para compartir evidencia de forma controlada, con manifest, checksums y SecretGuard.
```

---

## FUNC-SPRINT-97 — Compliance packs y policy packs

## Objetivo

Permitir que DevPilot agrupe reglas, checklists, schemas y reportes en packs de cumplimiento adaptables a distintos contextos.

## Historias

| ID | Historia | Criterio de aceptación |
|---|---|---|
| US-FUNC-97-001 | Como architect, quiero packs de cumplimiento. | Existe Compliance Pack Registry. |
| US-FUNC-97-002 | Como auditor, quiero ejecutar pack. | `compliance run` funciona. |
| US-FUNC-97-003 | Como owner, quiero saber brechas por pack. | Reporte PASS/BLOCK. |

## Tareas

| ID | Tarea | Entregable | PASS |
|---|---|---|---|
| FUNC-97-001 | Compliance pack schema | `compliance_pack.schema.json` | Validable. |
| FUNC-97-002 | Registry | `.devpilot/compliance/packs.json` | Declarativo. |
| FUNC-97-003 | Runner | `compliance run --pack baseline` | Report. |
| FUNC-97-004 | Baseline pack | MIPSoftware/MIASI baseline | PASS. |
| FUNC-97-005 | Tests | `tests/test_compliance_packs.py` | PASS. |

## Archivos previstos

```text
src/devpilot_core/compliance/__init__.py
src/devpilot_core/compliance/registry.py
src/devpilot_core/compliance/runner.py
.devpilot/compliance/packs.json
tests/test_compliance_packs.py
docs/audits/func_sprint_97_compliance_packs_audit.md
docs/functional_sprint_97_manifest.json
```

## Comandos objetivo

```powershell
python -m devpilot_core compliance list --json
python -m devpilot_core compliance run --pack baseline --json --write-report
python -m pytest -q
```

## Criterios PASS

- Packs son declarativos.
- Runner usa validadores/gates existentes.
- Reporte indica gaps por pack.

## Criterios BLOCK

- No cerrar si packs ejecutan acciones no declaradas.
- No cerrar si compliance reemplaza PolicyEngine en vez de usarlo.

## Prompt operativo sugerido

```text
Implementa FUNC-SPRINT-97. Crea Compliance Pack Registry y runner declarativo sobre gates existentes. Incluye baseline MIPSoftware/MIASI y reportes.
```

---

## FUNC-SPRINT-98 — Remote runners experimentales y enterprise reporting

## Objetivo

Diseñar y prototipar de forma experimental capacidades de remote runners y reportes enterprise sin habilitar ejecución remota por defecto.

## Historias

| ID | Historia | Criterio de aceptación |
|---|---|---|
| US-FUNC-98-001 | Como architect, quiero evaluar remote runners. | ADR/prototipo disabled. |
| US-FUNC-98-002 | Como enterprise reviewer, quiero reportes agregados. | Enterprise report local. |
| US-FUNC-98-003 | Como security reviewer, quiero remote disabled. | No ejecución remota default. |

## Tareas

| ID | Tarea | Entregable | PASS |
|---|---|---|---|
| FUNC-98-001 | ADR remote runners | ADR | Disabled by default. |
| FUNC-98-002 | Enterprise report model | `enterprise/report.py` | Agregado local. |
| FUNC-98-003 | CLI enterprise report | `enterprise report --json` | Read-only. |
| FUNC-98-004 | Remote runner stub | `remote/runner.py` | No execute. |
| FUNC-98-005 | Tests | `tests/test_enterprise_reporting.py` | PASS. |

## Archivos previstos

```text
src/devpilot_core/enterprise/__init__.py
src/devpilot_core/enterprise/report.py
src/devpilot_core/remote/runner.py
tests/test_enterprise_reporting.py
docs/02_architecture/adrs/ADR-XXXX-remote-runners-experimental.md
docs/audits/func_sprint_98_enterprise_reporting_audit.md
docs/functional_sprint_98_manifest.json
```

## Comandos objetivo

```powershell
python -m devpilot_core enterprise report --json --write-report
python -m devpilot_core remote runner status --json
python -m pytest -q
```

## Criterios PASS

- Remote runner está `disabled/experimental`.
- Enterprise report es local/read-only.
- No hay ejecución remota.

## Criterios BLOCK

- No cerrar si remote runner ejecuta comandos reales.
- No cerrar si requiere cloud.
- No cerrar si no tiene ADR.

## Prompt operativo sugerido

```text
Implementa FUNC-SPRINT-98. Crea enterprise report local y remote runner stub experimental deshabilitado. No ejecutes remoto ni uses cloud. Documenta ADR y riesgos.
```

---

## FUNC-SPRINT-99 — Industrial readiness gate y cierre Fase H

## Objetivo

Crear un gate de readiness industrial que consolide capacidades avanzadas y cierre la Fase H con evidencia de madurez.

## Historias

| ID | Historia | Criterio de aceptación |
|---|---|---|
| US-FUNC-99-001 | Como owner, quiero saber si DevPilot es industrial-ready. | Existe `industrial-readiness check`. |
| US-FUNC-99-002 | Como auditor, quiero cierre de Fase H. | Closure report completo. |
| US-FUNC-99-003 | Como architect, quiero backlog post-H. | Recomendaciones futuras. |

## Tareas

| ID | Tarea | Entregable | PASS |
|---|---|---|---|
| FUNC-99-001 | Industrial Readiness Gate | `industrial/readiness.py` | Score. |
| FUNC-99-002 | CLI | `industrial-readiness check --json` | Report. |
| FUNC-99-003 | Closure report | `docs/audits/phase_h_advanced_capabilities_closure.md` | Completo. |
| FUNC-99-004 | Post-H backlog seed | `docs/backlogs/post_phase_h_ideas.md` | Priorizado. |
| FUNC-99-005 | Tests | `tests/test_industrial_readiness.py` | PASS. |

## Archivos previstos

```text
src/devpilot_core/industrial/__init__.py
src/devpilot_core/industrial/readiness.py
tests/test_industrial_readiness.py
docs/audits/phase_h_advanced_capabilities_closure.md
docs/backlogs/post_phase_h_ideas.md
docs/functional_sprint_99_manifest.json
```

## Comandos objetivo

```powershell
python -m devpilot_core industrial-readiness check --json --write-report
python -m devpilot_core quality-gate run --profile industrial --json
python -m pytest -q
```

## Criterios PASS

- Gate resume contract, policy, security, evals, observability, release, UI/API, multiagent, RAG, connectors y enterprise.
- Identifica capacidades production-ready vs experimental.
- Cierre Fase H documentado.

## Criterios BLOCK

- No cerrar si todo se marca como production sin evidencia.
- No cerrar si no diferencia experimental/future.
- No cerrar si quality gate falla.

## Prompt operativo sugerido

```text
Implementa FUNC-SPRINT-99. Crea Industrial Readiness Gate y cierre Fase H. Debe distinguir production-ready, implemented-initial, experimental, planned y future. No ocultes brechas.
```

---

## Cierre esperado de Fase H

Al finalizar FUNC-SPRINT-99, DevPilot debería contar con:

```text
- arquitectura avanzada agentic/enterprise decidida;
- AgentSession y memoria operativa controlada;
- RAG documental local con fuentes;
- Connector Registry y MCP MVP controlado;
- MultiAgentCoordinator MVP;
- workflows multiagente dry-run;
- evals avanzadas/red-team;
- plugin/connector registry;
- multiworkspace/portfolio;
- RBAC local;
- audit packs;
- compliance packs;
- enterprise reporting local;
- remote runner stub experimental disabled;
- industrial readiness gate;
- closure report Fase H.
```

## Prompt global de Fase H

```text
Desarrolla la Fase H — Capacidades avanzadas, iniciando en FUNC-SPRINT-85. Respeta el modelo de backlog ejecutable de DevPilot. No habilites multiagente, RAG, MCP, plugins, remote runners o enterprise features sin PolicyEngine, MIASI, Approval, evaluación, trazas, reportes y documentación. Mantén todo local-first y deny-by-default.
```


## Estado de implementación Sprint 89

`FUNC-SPRINT-89` queda implementado como MVP local read-only con `ConnectorAdapter` y `connector call --dry-run`.


### Estado de implementación FUNC-SPRINT-93

`FUNC-SPRINT-93 — Plugin y connector ecosystem controlado` queda implementado como capacidad `implemented-initial`. El sprint agrega Plugin Registry, schema `SCHEMA-DEVPL-PLUGIN-MANIFEST-V1`, CLI `plugin validate/list/dry-run`, loader metadata-only, políticas MIASI, fixtures `plugin-ecosystem`, auditoría, manifest y pruebas.

Límites explícitos: no carga código arbitrario, no importa módulos de plugins, no ejecuta entrypoints, no instala dependencias, no usa red, no llama APIs externas, no ejecuta shell, no realiza acciones remotas y no escribe fuera de outputs/traces/reportes opcionales. El siguiente sprint autorizado es `FUNC-SPRINT-94 — Multiworkspace y portfolio local`.
