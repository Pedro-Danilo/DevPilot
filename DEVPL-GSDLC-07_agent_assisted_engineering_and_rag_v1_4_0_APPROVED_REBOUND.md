---
doc_id: "DEVPL-GSDLC-07"
title: "DEVPL-GSDLC-07 — Agent-assisted Engineering, contextual RAG and bounded handoffs"
status: "closed"
version: "1.4.0"
owner: "Ordóñez"
updated: "2026-08-31"
approval: "approved_by_owner"
approved_at: "2026-08-28"
approval_decision: "APPROVE"
program_id: "DEVPL-GSDLC"
design_origin_repo: "repo_DevPilot_Local_341_POST_H_EVAL_002_PILOT_TRANSITION_REBIND.zip"
design_origin_git_commit: "cff43e8d992ff6139bd13bb1809ce4d497ae0952"
design_origin_repo_sha256: "e28cd2bae08d099a2b62c4869c83b6e5a647f3f780ca1572727b7c80f6eeea3b"
design_origin_role: "historical-design-origin-only/not-execution-authority"
source_repo: "repo_DevPilot_Local_384_DEVPL_GSDLC_07_C_DRAFT_REWRITE_CRITIQUE_TRANSFORM_WINDOWS_VALIDATED_CANDIDATE.zip"
source_git_commit: "c70f878951d2bc3f39f34f74b8190ce7fff69ca2"
source_repo_sha256: "03c601399e27c2a110f502705043ea4bd9f3d719804fff0683acd9936e27e140"
source_repo_role: "execution-authority/owner-adjudicated-gsdlc-06-successor"
execution_source_policy: "rebound/repo384-windows-validated/07-d"
predecessor_backlog: "DEVPL-GSDLC-06"
predecessor_micro_sprint_closure: "DEVPL_GSDLC_06_E_FINAL_OWNER_ADJUDICATION_v1_0_0.md"
predecessor_backlog_closure: "DEVPL_GSDLC_06_BACKLOG_CLOSURE_ADJUDICATION_v1_0_0.md"
activation_requires_owner_adjudication: false
activation_rebind_required_before_functional_source: true
local_first: true
ui_complete_normal_journey: true
dry_run_default: true
backlog_id: "DEVPL-GSDLC-07"
r01_research_binding: "CLOSED/PASS"
r01_research_authority_repo: "repo_DevPilot_Local_348_DEVPL_GSDLC_R01_E_RESEARCH_CLOSURE.zip"
r01_research_authority_commit: "3d7fda44d7ab5feefadd2eb4a7b9d20680eb1b5d"
r01_research_authority_sha256: "68487b2d210a0fd8fb6f2c46f2f70f205f925aeda7d556e13af205de4583515d"
r01_binding_scope: "architecture-and-security-input; historical design origin remains unchanged"
backlog_status: "CLOSED/PASS"
micro_sprints_total: 5
validation_policy: "A-D impact/selective+completion-first/no-full; E one logical sharded/resumable full session; no second full; composite recovery"
full_regression_architecture: "DEVPL_TESTING_FULL_REGRESSION_EXECUTION_V2_ARCHITECTURE_v1_0_0.md"
documentation_contract_policy: "DEVPL_DOCUMENTATION_CONTRACT_RECONCILIATION_POLICY_v1_0_0_APPROVED"
runtime_ephemeral_fixture_policy: "exclude auth.db*, devpilot.db*, outputs/tmp runtime stores, .vite caches and equivalents"
closure_repo: "repo_DevPilot_Local_386_DEVPL_GSDLC_07_E_AGENTIC_PRECODE_MODEL_EVALS_WINDOWS_VALIDATED_CANDIDATE.zip"
closure_git_commit: "17db6b219f5066f2df91d897a0e3ad62314a0176"
closure_repo_sha256: "0998e901a1149d377c6793dc923e0c45ed7eec42395e7182ef495ce652e79d23"
closure_decision: "CLOSED/PASS"
---

# 0. Aprobación y binding de ejecución

## 0.0 Cierre owner-adjudicated — 2026-08-31

`DEVPL-GSDLC-07 = CLOSED/PASS` sobre repo386 / commit `17db6b219f5066f2df91d897a0e3ad62314a0176`. La secuencia posterior autorizada es `FRX-v2.2-A → FRX-v2.2-D → FRX-v2.3-A → FRX-v2.3-D → DEVPL-GSDLC-08`. Las secciones de aprobación de diseño debajo se preservan como historia del backlog y no representan el estado current-active.


**Decisión owner:** `APPROVE / EXECUTABLE-DESIGN`.

DEVPL-GSDLC-07 queda rebindeado al successor owner-adjudicated de GSDLC-06:

```text
repo   repo_DevPilot_Local_379_DEVPL_GSDLC_06_E_PROVIDER_SETTINGS_CONTROLLED_EVAL_WINDOWS_VALIDATED_CANDIDATE.zip
commit 7deeb043840945165205c8c1493b4f7e44d2b2ca
sha256 859134adf86e3b58ef16434c4db7517be536a9caa08cf3fa493055c69a28d2e2
```

Repo341 se conserva exclusivamente como origen histórico de diseño.

GSDLC-06 se adjudica `CLOSED/PASS-WITH-GAPS` con dos gaps S2 no funcionales. Antes de cualquier mutación funcional de 07-A, el activation rebind debe incorporar las adjudicaciones finales, corregir el README stale de 06-E, registrar el erratum RBAC, corroborar enforcement con contratos focales y reconciliar Project State / Source Registry / README / roadmap.

## 0.0.1 Rebind vigente para GSDLC-07-C

Tras owner adjudication de `GSDLC-07-B = CLOSED/PASS`, la autoridad de ejecución vigente para 07-C es:

```text
repo   repo_DevPilot_Local_383_DEVPL_GSDLC_07_B_RAG_CONTEXT_PACKS_PROVENANCE_BUDGET_WINDOWS_VALIDATED_CANDIDATE.zip
commit 749d5f9ae039c961b506834de191b94bf65ff50b
sha256 d6535db2dd4e54414a38873379957619ed1e106258a625b268d08d89683a05aa
```

El binding repo379 descrito debajo se conserva como registro histórico de activación de la ola y no es autoridad de ejecución para 07-C.

## 0.1 Invariantes heredadas

1. navegación project-scoped solo con proyecto server-validado;
2. sesión/RBAC/approval server-side es autoridad;
3. runtime stores/caches nunca entran a candidate;
4. mutaciones mediante typed operations; no arbitrary shell;
5. históricos evolucionan mediante successor contracts, no reescritura;
6. Model Gateway decide modelo/ruta, no tools;
7. `ToolIntent` y `ToolExecutionDecision` permanecen separados;
8. mock/local obligatorio; APIs externas opcionales y gobernadas;
9. dry-run por defecto; loops con límites explícitos.

## 0.2 Gaps del predecessor que el activation rebind debe cerrar administrativamente

- `S2-EVIDENCE-06E-001`: screenshot RBAC no coincide con su nota;
- `S2-DOC-06E-002`: README afirma `full 1/1 PASS` en lugar de `FAIL/TIMEOUT/1-of-1/PRESERVED + composite PASS`.

Estos gaps no autorizan reabrir la full de 06.

## 0.3 Política de testing aplicable

Se adopta `DEVPL_TESTING_FULL_REGRESSION_EXECUTION_V2_ARCHITECTURE_v1_0_0.md`.

- A-D: completion-first focal/selective, sin full por rutina.
- E: una sola logical full session sharded/resumable.
- fallos ordinarios se agregan; no stop-on-first-failure.
- segunda full prohibida.
- browser se repite solo si runtime UI cambia.


## 0.4 Rebound 07-B (2026-08-29)

GSDLC-07-A quedó owner-adjudicated `CLOSED/PASS` sobre commit `807685993b9ef526d1274fd8d3440fb14f6e56cf`. La autoridad funcional para 07-B es repo382 Windows-validated (SHA-256 `dfde12877a1f9a96297aab42ad30a4f85a64216e42004042e43b7a51ded1e865`). La implementación de 07-B debe evolucionar los contratos RAG históricos mediante successor `ContextPack v2`; no se reescriben snapshots históricos POST-H-032.

## 0.4 Estado reconciliado para GSDLC-07-D — 2026-08-29

- `GSDLC-07-A = CLOSED/PASS`.
- `GSDLC-07-B = CLOSED/PASS`.
- `GSDLC-07-C = CLOSED/PASS`; successor repo384 / commit `c70f878951d2bc3f39f34f74b8190ce7fff69ca2` / SHA `03c601399e27c2a110f502705043ea4bd9f3d719804fff0683acd9936e27e140`.
- `GSDLC-07-D = IMPLEMENTED-INITIAL / LOCAL-VALIDATION-PENDING` durante construcción de este successor.
- Full regression consumida en GSDLC-07: `0`; la única logical full continúa reservada para 07-E.

# DEVPL-GSDLC-07 — Agent-assisted Engineering, contextual RAG and bounded handoffs

## 1. Objetivo

Integrar agentes contextuales en cada paso del Artifact Workbench y Guided SDLC, usando RAG, provenance, tools gobernadas y límites de costo/iteración.

## 2. Invariante de producto que esta ola debe demostrar

> El botón `Usar agente` del StepActionAdvisor produce un draft/propuesta revisable, nunca una aprobación automática; el usuario ve agente, modelo, fuentes, costo y acciones.

Esta invariante es parte del criterio de cierre. No basta con que existan clases, endpoints o archivos: debe demostrarse el comportamiento de producto descrito.

## 3. Dependencias y precondiciones de entrada

- GSDLC-06 owner-adjudicated `CLOSED/PASS` o `CLOSED/PASS-WITH-GAPS` exclusivamente con gaps S2/S3, owner/evidencia y sin invalidar la invariante de producto
- R01-E Agent Runtime / Skills boundary disponible desde `repo_DevPilot_Local_348_DEVPL_GSDLC_R01_E_RESEARCH_CLOSURE.zip` y owner-adjudicated CLOSED/PASS

Si alguna precondición no puede verificarse de forma reproducible, el backlog entra en `BLOCK` antes de mutar source.

Precondición transversal adicional: debe existir un proyecto activo/server-validado proveniente del journey GSDLC-03 para toda superficie project-scoped; Settings/Account globales no sustituyen project context.

## 4. Alcance funcional y técnico

### 4.1 Incluido

- agent role bindings
- RAG context packs
- draft/rewrite/critique
- tool calls bounded
- handoffs/supervisor
- human review
- explicit `ToolIntent` → deterministic `ToolExecutionDecision`
- agent-runtime experiment ADR and bounded runtime selection
- AI Control Center agent/runtime/skills administration surfaces

### 4.2 Fuera de alcance

- autonomous swarm
- silent file writes
- agent self-approval
- open-ended autonomous runtime
- real MCP write-capable execution before explicit experiment/ADR
- framework guardrails replacing DevPilot deterministic policy

## 5. Superficies y fuentes que probablemente serán afectadas

- agent capability inventory
- RAG
- memory
- tool calls
- multiagent
- Artifact Workbench

La lista es orientativa para Test Impact. Cada micro-sprint debe cerrar su manifest exacto antes de ejecutar cambios.

## 6. Micro-sprints secuenciales

### GSDLC-07-A — Contextual engineering agent roles and step bindings

**07-A execution gate semantics (2026-08-29):** 07-A está autorizado a nivel de programa. Su primera mutación se inicia únicamente después del owner adjudication `CLOSED/PASS` del activation enabler FRX2.1. Esa condición no constituye un micro-sprint adicional y se extingue con la adjudicación. Full Regression v2.2/v2.3 son optimizaciones posteriores y no bloquean 07-A..D.

**Objetivo.** Mapear agentes especializados a pasos concretos del Guided SDLC.

**Entradas obligatorias**
- GSDLC-06 CLOSED/PASS
- MIASI executable

**Actividades**
1. Definir Product, Requirements, Architecture, Security, Test, Planning, Coding y Review agent roles.
2. Vincular cada rol a steps/artifacts permitidos y tool allowlists.
3. Definir required model capabilities y fallback.
4. Exponer en StepActionAdvisor el agente recomendado y por qué.
5. Registrar roles sin otorgar aprobación humana.
6. Materializar la frontera R01-E: Agent Runtime posee session/planning/handoffs/ToolIntent lifecycle; Model Gateway solo resuelve modelos/rutas; Skills/Tools/MCP poseen capabilities tipadas.
7. Definir un ADR de experimento antes de adoptar cualquier framework externo. DevPilot governed runtime permanece baseline/reference; OpenAI Agents SDK, Microsoft Agent Framework y LangGraph son `candidate-for-experiment`, no dependencias implícitas.
8. Exponer en `AIControlCenterView` un `AgentRuntimeView` con agent role, enabled state, required capabilities, runtime binding, max steps/time/tokens/cost y policy status.

**Entregables verificables**
- AgentRoleBindingCatalog
- StepAgentBinding
- UI agent descriptors
- AgentRuntimeBoundary contract
- AgentRuntimeView

**Pruebas / validadores**
- binding coverage
- forbidden tool negative
- missing capability route
- framework/runtime cannot bypass PolicyEngine
- model route cannot grant tool permission

**Evidencia mínima**
- agent_binding_matrix.json

**Seguridad operacional específica**
- least privilege
- agent role nunca se convierte en human approval role

**PASS**
- cada step soportado tiene agente explícito o `none`
- no generic all-tools agent

**BLOCK**
- un agente recibe tools fuera de scope
- agent role puede approve

**Salida / autorización**
- autoriza GSDLC-07-B


### GSDLC-07-B — RAG context packs, provenance and budget

**Objetivo.** Construir contexto grounded mínimo y verificable por step.

**Entradas obligatorias**
- GSDLC-07-A PASS

**Actividades**
1. Seleccionar solo fuentes approved/relevant del workspace y standards.
2. Agregar citations, freshness, content hashes y insufficient-evidence semantics.
3. Aplicar ContextBudget/top-k/diff-first.
4. Excluir secrets, runtime DB y archivos fuera de policy.
5. Mostrar fuentes usadas en UI antes/después del run.

**Entregables verificables**
- ContextPack v2
- RAG provenance panel
- source selection policy

**Pruebas / validadores**
- groundedness
- stale/missing source
- secret exclusion
- budget trim

**Evidencia mínima**
- rag_grounding_samples.json
- context_budget_report.json

**Seguridad operacional específica**
- source allowlist
- no raw secrets
- untrusted external source tagged

**PASS**
- claims grounded/cited
- insufficient evidence blocks unsupported claims

**BLOCK**
- uncited authoritative claim
- secret in context

**Salida / autorización**
- autoriza GSDLC-07-C


### GSDLC-07-C — Draft, rewrite, critique and transform workflows

**Objetivo.** Añadir asistencia IA al Artifact Workbench sin saltarse lifecycle.

**Entradas obligatorias**
- GSDLC-07-B PASS

**Actividades**
1. Implementar generate draft, rewrite selection, critique, improve y transform imported source.
2. Mostrar model/provider/context/tokens/cost antes del run.
3. Validar structured output y convertir resultado a proposal/draft.
4. Mostrar diff antes de insertar/replace.
5. Registrar provenance agent-assisted y decisión humana accept/reject/modify.

**Entregables verificables**
- AgentAssistService
- Artifact AI panel
- AgentProvenance record

**Pruebas / validadores**
- mock deterministic
- local fake
- structured output invalid
- accept/reject flow

**Evidencia mínima**
- agent_assist_traces.json
- cost/provenance samples

**Seguridad operacional específica**
- output untrusted
- no direct APPROVED/FROZEN transition

**PASS**
- human review mandatory
- provenance retained
- manual route unchanged

**BLOCK**
- agent writes approved source directly
- hidden model/cost

**Salida / autorización**
- autoriza GSDLC-07-D


### GSDLC-07-D — Tools, approvals, limits and handoffs

**Objetivo.** Habilitar acciones agentic bounded con políticas y supervisor.

**Entradas obligatorias**
- GSDLC-07-C PASS

**Actividades**
1. Aplicar tool allowlists por agent/step.
1a. El modelo/agent solo puede producir `ToolIntent`; DevPilot Policy/RBAC/Approval produce `ToolExecutionDecision`. Un `ModelRouteDecision` nunca vuelve executable una tool.
2. Usar dry-run first para tools mutantes.
3. Solicitar approval role-bound cuando risk/side effect lo exige.
4. Enforzar max iterations, wall-time, tokens, cost y cancellation.
5. Implementar handoff supervisor con explicit transfer state y human checkpoints.
6. Incorporar como fixture obligatorio el hallazgo R01-D `filesystem.delete`: una selección de tool prohibida por el modelo debe quedar `executable=false` y `tool_executed=false`.
7. Mantener autonomous recovery como `BLOCK_PRODUCTION/CANDIDATE_EXPERIMENT` hasta evidencia sucesora; real MCP permanece `NOT_ENABLED/CANDIDATE_EXPERIMENT`.

**Entregables verificables**
- AgentExecutionPolicy
- HandoffSupervisor integration
- ToolIntent / ToolExecutionDecision contracts
- SkillToolPolicyView
- kill/cancel controls

**Pruebas / validadores**
- tool injection
- approval bypass
- budget exhaustion
- iteration cap
- cancel
- handoff scope
- forbidden-tool selection containment
- autonomous-recovery negative
- MCP real execution disabled

**Evidencia mínima**
- agent_security_eval.json
- handoff_traces.json

**Seguridad operacional específica**
- no shell
- no self-approval
- kill switch
- tool scope inheritance forbidden

**PASS**
- limits server-side
- handoffs traceable
- unauthorized tool blocked

**BLOCK**
- loop exceeds cap
- tool outside allowlist executes
- agent approves itself

**Salida / autorización**
- autoriza GSDLC-07-E


### GSDLC-07-E — Agentic pre-code browser acceptance and model evals

**Objetivo.** Demostrar pre-code asistido con calidad, costo y provenance visibles.

**Entradas obligatorias**
- GSDLC-07-D PASS

**Actividades**
1. Crear/revisar varios artifacts con agent route y comparar con manual.
2. Ejecutar subset DVP-MODEL workloads con mock/local y API opcional.
3. Revisar citations, cost ledger y human decisions.
4. Completar un path Product Vision→PRE_CODE_READY usando asistencia en algunos pasos.
5. Medir suggestions accepted/rejected/modified y fallback.
6. Validar `AIControlCenterView` con sub-vistas `AgentRuntimeView`, `SkillToolPolicyView` y `AgentEvalTraceView`; mostrar model route y tool-execution authority como decisiones separadas.
7. Mostrar agent/runtime/model/provider/access-route, sources, tokens/cost, ToolIntent, policy decision y approval state sin exponer secretos.

**Entregables verificables**
- agentic_precode_acceptance.md
- model_task_eval_matrix.json
- AgentEvalTraceView
- ai_control_center_acceptance.md

**Pruebas / validadores**
- browser
- groundedness
- MIASI/tool policy
- cost budget
- model routing

**Evidencia mínima**
- screenshots
- traces
- cost ledger
- approval records

**Seguridad operacional específica**
- API opcional
- mock/local mandatory
- no hidden autonomy

**Cierre de regresión obligatorio**
- ejecutar gates baratos + Contract Reconciliation Sweep + browser/capability acceptance;
- crear una única logical full-regression session con collection/fingerprint/shard-plan sellados;
- ejecutar todos los shards planificados aunque aparezcan fallos ordinarios y producir un reporte agregado;
- ante interrupción de infraestructura, reanudar únicamente nodeids no ejecutados bajo el mismo fingerprint;
- ante FAIL funcional no repetir la full: aplicar recuperación compuesta selectiva y Historical Regression Guard.

**PASS**
- agent-assisted route gobernada
- S0/S1=0
- cost/provenance completos

**BLOCK**
- unbounded action
- cost unknown no explicado
- approval bypass

**Salida / autorización**
- CLOSED/PASS
- autoriza GSDLC-08


## 7. Alcance transversal específico de esta ola

- La asistencia IA de trabajo sigue siendo contextual; no se fuerza al usuario a abandonar Artifact/Guided Workbench para usarla.
- `AIControlCenterView` es la superficie dedicada de **administración y diagnóstico**, no el lugar donde se ejecuta el trabajo cotidiano.
- Dentro del control center se mantienen separados: Models/Routes (Model Gateway), Agents/Runtime, Skills/Tools/Policy y Evals/Traces.
- MCP se ubica en Skills/Protocols; no pertenece a Model Gateway.
- Manual/import siguen first-class y no pueden degradarse.

## 8. Política de contratos históricos específica

- UOC-010 y POST-H-032 constraints se congelan históricamente; successor tests deben permitir bounded execution nueva sin reescribir el pasado.
- Reusar Tool/Memory/Handoff contracts.

Antes del cierre de **cada** micro-sprint se debe generar un `historical_contract_sweep` que clasifique los tests/contratos impactados como:

1. `historical-freeze`: valida únicamente el hecho histórico;
2. `current-active`: debe evolucionar con la capacidad vigente;
3. `successor-needed`: requiere nuevo contrato sin reescribir el anterior;
4. `deprecated-after-proof`: solo puede retirarse después de demostrar reemplazo equivalente.

No se permite modificar una aserción histórica únicamente para “hacer pasar pytest”; la modificación debe quedar justificada por esta clasificación.

### Contract Reconciliation Sweep obligatorio

La política `docs/02_architecture/governance/DEVPL_DOCUMENTATION_CONTRACT_RECONCILIATION_POLICY_v1_0_0_APPROVED.md`, materializada durante GSDLC-03-E, es transversal para esta ola.

Además del `historical_contract_sweep` de cada micro-sprint, antes de la full regression de cierre debe ejecutarse un `contract_reconciliation_sweep` que bloquee si detecta cualquiera de estas condiciones:

1. schema estricto inválido o metadata `current-active` contradictoria;
2. summary/counter/registry derivado desincronizado de su colección viva;
3. sensitive action sin RBAC/approval/MIASI/tool binding cuando aplique;
4. UI route/capability sin mapping current correspondiente;
5. `source_registry`, Project State, README, roadmap o CURRENT en estados incompatibles;
6. test histórico consultando un `current-active` mutable cuando existe snapshot `*_at_close`;
7. reutilización de un puntero histórico por otra ola;
8. fixture/sandbox que copie stores `runtime-ephemeral`, incluidos `auth.db*`, `devpilot.db*` o equivalentes;
9. evidencia sellada reescrita después de calcular su hash;
10. contrato successor agregado sin actualizar el historial/registry que deba reconocerlo.

La clasificación mínima continúa siendo `historical-freeze`, `current-active`, `successor-needed` y `deprecated-after-proof`; se añade la distinción explícita `derived` y `runtime-ephemeral`.

**Regla:** corregir drift determinista antes de consumir la única full regression del backlog.

## 9. Seguridad operacional específica

- Prompt/tool injection, excessive agency, RAG poisoning, unsafe output, data egress y cost abuse.
- Hallazgo R01-D vinculante: los dos modelos evaluados seleccionaron `filesystem.delete`; el sistema debe asumir que el modelo puede proponer acciones prohibidas y depender de policy determinista, no de obediencia del modelo.

Toda acción mutante debe seguir `plan → dry-run → policy/RBAC → approval cuando aplique → execute → verify → evidence`. Cualquier excepción requiere ADR o backlog correctivo separado.

## 10. Estrategia de pruebas de la ola

- agent bindings
- RAG groundedness
- tool policy
- limits
- handoff
- model eval
- browser

Regla de regresión:

- A→D usan Test Impact, pruebas focales, acumulativas y validadores determinísticos; **full regression = NO por rutina**.
- Todos los conjuntos focales siguen `complete-all-planned-checks → aggregate findings → adjudicate`; un fallo ordinario no debe abortar el resto del plan. Solo precondiciones de seguridad/mutación insegura hacen fail-fast.
- El micro-sprint E ejecuta una sola **logical full-regression session**, conforme a `DEVPL_TESTING_FULL_REGRESSION_EXECUTION_V2_ARCHITECTURE_v1_0_0.md`: collection fija, source/environment fingerprint, shards, JUnit/log/receipt por shard y terminal accounting de todos los nodeids.
- Un fallo de test no detiene shards restantes. Una interrupción de infraestructura puede reanudar únicamente nodeids sin resultado terminal si el fingerprint permanece idéntico; esto sigue perteneciendo al mismo intento lógico.
- Una full intermedia solo puede ocurrir por hard trigger owner-approved; consume la única logical full session disponible.
- Después de completar la full, si existen fallos, se preserva la evidencia y se corrige mediante failed-nodeids + bounded impacted + uncovered tail si aplica + Historical Regression Guard. **No existe segunda full**.
- Browser acceptance se ejecuta solo cuando una mutación cambia comportamiento browser; correctives byte-equivalent de runtime UI reutilizan evidencia previa con receipt de equivalencia.

## 11. Evidencia autoritativa esperada

- agent traces
- source citations
- cost ledgers
- approval records
- screenshots

Además, cada micro-sprint debe conservar:

- manifest de source delta;
- identidad Git pre/post;
- resultados PASS/BLOCK machine-readable;
- lista de S0/S1;
- browser screenshots cuando corresponda;
- hashes de artefactos empaquetados;
- declaración explícita `network_used`, `external_api_used`, `secrets_exposed`, `mutations_performed`.

## 12. Definition of Done del backlog

- contextual agents
- RAG
- human review
- bounded tools/handoffs
- `ToolIntent` separado de `ToolExecutionDecision`
- AI Control Center de administración agentic
- framework/runtime adoption solo tras experimento ADR
- manual route preserved

El backlog solo puede adjudicarse `CLOSED/PASS` si todos los micro-sprints A→E han cerrado en secuencia y no quedan S0/S1 abiertos.

## 13. Criterio de autorización del siguiente backlog

- GSDLC-08 solo después de cerrar pre-code agent-assisted sin bypass de gates.

Un `PASS-WITH-GAPS` solo puede autorizar el siguiente backlog cuando los gaps estén clasificados S2/S3, tengan owner, evidencia y no invaliden la invariante de producto de esta ola.

## 14. Execution reconciliation — GSDLC-07-E candidate (2026-08-30)

Execution authority for 07-E is the Windows-validated 07-D successor:

```text
repo    repo_DevPilot_Local_385_DEVPL_GSDLC_07_D_TOOLS_APPROVALS_LIMITS_HANDOFFS_WINDOWS_VALIDATED_CANDIDATE.zip
commit  a7a2af0660242633fb8e4a721fba3629304a60c6
sha256  45a394cb1c3e4e235eae5a6c354ab492b9e3229822f9269bdf144c5c66b1bb30
```

07-D is owner-adjudicated `CLOSED/PASS-WITH-S2-EVIDENCE-GAP`; `S2-EVIDENCE-07D-001` is evidence-only and does not reopen product behavior.

07-E candidate implements AgenticPrecodeAcceptanceEvaluator, AgentEvalTraceView and FullRegressionTelemetryExporter. The candidate remains `PASS/PRE-WINDOWS`: browser evidence and the unique logical full-regression session are intentionally not consumed locally. On final 07-E closure, the next engineering action is Full Regression v2.2 temporal distribution; v2.3 remains prepared/not-enabled with workers=0.


## 15. E09 validation reconciliation — 2026-08-31

The v1.0.9 Windows continuation completed E08 residual/selective recovery (`126/126 PASS`) and then blocked at Historical Regression Guard on one UOC-011 test that treated the live UI Capability Registry as if it were the immutable 193-capability UOC-011 snapshot. The live registry now contains 199 entries because GSDLC-07 added six Full Regression v2.1 CLI capabilities. Forward audit also found the same stale assumption in the UOC-011 release evaluator and a 193/199 coverage gap in the current Governed Job Capability Registry.

E09 classification: UOC-007/UOC-011 `193` is `historical-freeze`; the UI and governed-job registries are `current-active/derived` and must remain exact over all 199 live capabilities. The six successor capabilities remain CLI bridges with governed planning only; no UI/API runtime adapter is enabled. Sensitive full-session `run`/`resume` remain approval-bound in governed metadata. Browser evidence is reusable by runtime-byte equivalence. The single full session remains consumed; second full remains prohibited.

07-E remains open until E09 Historical Regression Guard, deterministic closure gates, Git three-state convergence and Windows packaging all PASS.


## 16. Windows E09 closure

GSDLC-07-E and DEVPL-GSDLC-07 are `CLOSED/PASS` only after the v1.0.10 E09 Historical Regression Guard, closure gates, post-finalize validation, candidate packaging and Git three-state reconciliation all pass. The original FULL-01 remains the unique logical full-regression session; no second full is authorized or executed. Browser evidence remains valid by runtime-byte equivalence. Current UI/governed-job registries cover 199/199 capabilities; UOC-007/UOC-011 historical closure remains frozen at 193 via explicit at-close metadata/manifests. GSDLC-08 is authorized.
