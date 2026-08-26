---
doc_id: "DEVPL-GSDLC-05"
title: "DEVPL-GSDLC-05 — Executable MIPSoftware/MIASI workflows and Step Action Advisor"
status: "approved"
version: "1.2.0"
owner: "Ordóñez"
updated: "2026-08-24"
approval: "approved_by_owner"
approved_at: "2026-08-24"
approval_decision: "APPROVE"
program_id: "DEVPL-GSDLC"
design_origin_repo: "repo_DevPilot_Local_341_POST_H_EVAL_002_PILOT_TRANSITION_REBIND.zip"
design_origin_git_commit: "cff43e8d992ff6139bd13bb1809ce4d497ae0952"
design_origin_repo_sha256: "e28cd2bae08d099a2b62c4869c83b6e5a647f3f780ca1572727b7c80f6eeea3b"
design_origin_role: "historical-design-origin-only/not-execution-authority"
source_repo: "repo_DevPilot_Local_369_DEVPL_GSDLC_04_E_ARTIFACT_WORKBENCH_BROWSER_CLOSURE_WINDOWS_VALIDATED_CANDIDATE.zip"
source_git_commit: "13c2a59bbcb8adbb27f2a9be59a1e2925454fb29"
source_repo_sha256: "de62ae248dbdc9f587ef85a72c2194fc5db7f8d5758c0a1dda1f135ceb0b4be7"
source_repo_role: "execution-authority/owner-adjudicated-gsdlc-04-successor"
execution_source_policy: "fixed/owner-adjudicated-gsdlc-04-successor"
predecessor_backlog: "DEVPL-GSDLC-04"
predecessor_micro_sprint_closure: "DEVPL_GSDLC_04_E_FINAL_OWNER_ADJUDICATION_v1_0_0.md"
predecessor_backlog_closure: "DEVPL_GSDLC_04_BACKLOG_CLOSURE_ADJUDICATION_v1_0_0.md"
predecessor_closure_current: "DEVPL_GSDLC_04_FINAL_OWNER_CLOSURE_CURRENT.json"
activation_requires_owner_adjudication: false
activation_rebind_required_before_functional_source: true
local_first: true
ui_complete_normal_journey: true
dry_run_default: true
backlog_id: "DEVPL-GSDLC-05"
backlog_status: "approved/executable-design"
micro_sprints_total: 5
validation_policy: "A-D cumulative-selective; E exactly-one-full-regression; no rerun after failure; composite recovery"
documentation_contract_policy: "DEVPL_DOCUMENTATION_CONTRACT_RECONCILIATION_POLICY_v1_0_0_APPROVED"
runtime_ephemeral_fixture_policy: "exclude auth.db*, devpilot.db* and equivalent runtime stores"
model_execution_policy: "out-of-scope; no API key or paid model required for DEVPL-GSDLC-05"
---

# 0. Aprobación, rebind y autoridad de ejecución

**Decisión owner:** `APPROVED / EXECUTABLE-DESIGN`.

DEVPL-GSDLC-05 queda rebindeado al successor owner-adjudicated de GSDLC-04:

```text
repo
repo_DevPilot_Local_369_DEVPL_GSDLC_04_E_ARTIFACT_WORKBENCH_BROWSER_CLOSURE_WINDOWS_VALIDATED_CANDIDATE.zip

commit
13c2a59bbcb8adbb27f2a9be59a1e2925454fb29

SHA-256
de62ae248dbdc9f587ef85a72c2194fc5db7f8d5758c0a1dda1f135ceb0b4be7
```

Repo341 se conserva exclusivamente como origen histórico de diseño. No es autoridad mutable y no puede usarse para simplificar ni reconstruir 05.

Antes de cualquier cambio funcional de 05-A debe ejecutarse el **activation rebind checkpoint** que incorpore al repo las adjudicaciones externas de 04-E/backlog 04 y reconcilie Project State, Source Registry, README y roadmap a `GSDLC-04 CLOSED/PASS` + `GSDLC-05 authorized/active`. El candidate repo369 permanece sellado como predecessor y no se reescribe.

El activation rebind es administrativo, no crea un sexto micro-sprint y **no ejecuta full regression**. Si existe drift, el operador debe terminar BLOCK antes de funcionalidad.

## 0.1 Invariantes heredadas

1. La navegación project-scoped solo opera con proyecto activado por el journey GSDLC-03.
2. La sesión/RBAC/approval server-side sigue siendo autoridad; storage browser es UX-only.
3. Stores `runtime-ephemeral` (`auth.db*`, `devpilot.db*`, etc.) no se copian a fixtures/sandboxes.
4. Mutaciones son typed operations gobernadas; no arbitrary shell.
5. Los contratos históricos se preservan como hechos scoped y evolucionan mediante successors.
6. El backlog debe incorporar cualquier adjudicación externa del predecessor antes de cambios funcionales.


# DEVPL-GSDLC-05 — Executable MIPSoftware/MIASI workflows and Step Action Advisor

## 1. Objetivo

Convertir MIPSoftware y MIASI en workflows machine-readable y, para cada paso actual, ofrecer opciones de ejecución aplicables con requisitos, riesgo, costo y permisos.

## 2. Invariante de producto que esta ola debe demostrar

> DevPilot guía secuencialmente: no deja saltar gates obligatorios y en cada paso muestra `qué puedes hacer ahora` —Manual, Paste, Upload/Import, Agent, RAG o typed operation— sin exigir conocimiento de comandos.

Esta invariante es parte del criterio de cierre. No basta con que existan clases, endpoints o archivos: debe demostrarse el comportamiento de producto descrito.

## 3. Dependencias y precondiciones de entrada

- GSDLC-04 CLOSED/PASS

Si alguna precondición no puede verificarse de forma reproducible, el backlog entra en `BLOCK` antes de mutar source.

Precondición transversal adicional: debe existir un proyecto activo/server-validado proveniente del journey GSDLC-03 para toda superficie project-scoped; Settings/Account globales no sustituyen project context.

## 4. Alcance funcional y técnico

### 4.1 Incluido

- ExecutableStandardRegistry
- MIP phase/artifact/gate graph
- MIASI applicability/policy graph
- NextAction binding
- StepActionCatalog
- ExecutionModeAdvisor
- manual/import pre-code vertical slice

### 4.2 Fuera de alcance

- model execution real
- coding
- roadmap generation

## 5. Superficies y fuentes que probablemente serán afectadas

- MIPSoftware
- MIASI
- readiness
- Guided SDLC engine
- Artifact Workbench

La lista es orientativa para Test Impact. Cada micro-sprint debe cerrar su manifest exacto antes de ejecutar cambios.

## 6. Micro-sprints secuenciales

### GSDLC-05-A — ExecutableStandardRegistry and source mapping

**Objetivo.** Crear una representación machine-readable trazable de MIPSoftware/MIASI sin inventar ni diluir sus reglas.

**Entradas obligatorias**
- GSDLC-04 CLOSED/PASS
- docs/standards/mipsoftware
- docs/standards/miasi

**Actividades**
1. Definir schema de phases, steps, artifacts, prerequisites, validators, approvals, exit gates y next actions.
2. Mapear cada requirement ejecutable a doc_id/heading/source hash del estándar.
3. Definir version/migration semantics del registry.
4. Implementar validator de orphan steps, duplicate IDs, cycles y source drift.
5. Definir governance: estándar documental sigue normativo hasta que el owner apruebe registry version.

**Entregables verificables**
- ExecutableStandardRegistry schema
- initial source mapping
- registry validator

**Pruebas / validadores**
- schema positive/negative
- source-link verification
- cycle/orphan detection

**Evidencia mínima**
- standard_mapping_coverage.json
- source_drift_report.json

**Seguridad operacional específica**
- registry no puede desactivar controles críticos sin ADR
- fail closed ante source drift crítico

**PASS**
- 100% requisitos mandatory pre-code mapeados
- 0 orphan critical steps

**BLOCK**
- regla nueva sin source/decision
- critical control no mapeado
- cycle

**Salida / autorización**
- autoriza GSDLC-05-B


### GSDLC-05-B — MIPSoftware executable lifecycle and gates

**Objetivo.** Operacionalizar el ciclo tradicional desde intake hasta release con prerequisites y exit gates.

**Entradas obligatorias**
- GSDLC-05-A PASS

**Actividades**
1. Codificar fases MIPSoftware relevantes y orden obligatorio.
2. Vincular artifact profiles y validators existentes.
3. Definir prerequisite graph, progress weights y exit gates.
4. Conectar transición con WorkspaceEngineeringState.
5. Generar blocker explanations y remediation actions sin LLM.

**Entregables verificables**
- MIP workflow registry
- MIPGateEvaluator bindings
- MIP progress model

**Pruebas / validadores**
- phase fixtures
- skip-required negative
- cycle detection
- progress determinism

**Evidencia mínima**
- mip_workflow_coverage.json
- transition_case_matrix.json

**Seguridad operacional específica**
- LLM no decide gates
- owner tampoco puede saltar mandatory step sin waiver gobernado

**PASS**
- required phases no skip
- progress reproducible
- blockers explicables

**BLOCK**
- phase mandatory puede omitirse
- gate depende de prompt/model

**Salida / autorización**
- autoriza GSDLC-05-C


### GSDLC-05-C — MIASI applicability, roles and policy binding

**Objetivo.** Hacer que MIASI se active de forma determinística cuando el proyecto/feature contiene capacidades inteligentes/agénticas.

**Entradas obligatorias**
- GSDLC-05-B PASS
- MIASI agentic SDLC

**Actividades**
1. Definir decisión de applicability a nivel proyecto y feature.
2. Vincular Agent/Tool/Policy/Eval/Human Approval/Observability/RAG/Memory artifacts requeridos.
3. Integrar classification de riesgo y no-go gates.
4. Mostrar indicador MIASI en Project Status y artifact readiness.
5. Permitir re-evaluación cuando una feature inicialmente no-AI incorpora IA.

**Entregables verificables**
- MIASI executable registry
- MIASIApplicabilityEvaluator
- MIASI project status projection

**Pruebas / validadores**
- AI/non-AI fixtures
- ambiguous applicability
- missing cards
- risk escalation

**Evidencia mínima**
- miasi_activation_matrix.json
- miasi_gate_report.json

**Seguridad operacional específica**
- fail closed en alta incertidumbre/riesgo
- no agent execution si MIASI gate incompleto

**PASS**
- MIASI status justificable
- required cards/gates enforced

**BLOCK**
- AI project avanza sin MIASI
- risk critical without control

**Salida / autorización**
- autoriza GSDLC-05-D


### GSDLC-05-D — StepActionCatalog and ExecutionModeAdvisor

**Objetivo.** Sugerir en cada `current_step` las herramientas/rutas válidas y explicar cuándo están bloqueadas.

**Entradas obligatorias**
- GSDLC-05-C PASS
- Artifact Workbench
- RBAC

**Actividades**
1. Definir action kinds MANUAL, PASTE, UPLOAD_IMPORT, EXTERNAL_EDITOR, AGENT, RAG, TYPED_OPERATION.
2. Calcular availability por step, artifact state, role, policy, provider/model availability y budget.
3. Mostrar para cada acción: propósito, side effects, approval requerido, costo/tokens estimados o `not applicable`, y prerequisites.
4. Ordenar recomendación default de manera determinística sin esconder alternativas.
5. Explicar disabled reasons y enlace a configuración cuando falta provider/rol.

**Entregables verificables**
- StepActionCatalog
- ExecutionModeAdvisor
- StepActionCard UI contract

**Pruebas / validadores**
- step×action availability matrix
- RBAC negatives
- policy blocked action
- provider unavailable
- budget exhausted

**Evidencia mínima**
- step_action_coverage.json
- advisor_decision_samples.json

**Seguridad operacional específica**
- Advisor no otorga capability; solo refleja server policy
- AGENT/RAG disabled sin route válida

**PASS**
- 100% current steps tienen acción válida o BLOCK explícito
- recomendación explicable

**BLOCK**
- advisor ofrece acción prohibida
- cost/risk omitido para agent route

**Salida / autorización**
- autoriza GSDLC-05-E


### GSDLC-05-E — Manual/import pre-code wizard vertical slice

**Objetivo.** Demostrar que DevPilot conduce el pre-code completo sin IA, PowerShell ni inyección externa.

**Entradas obligatorias**
- GSDLC-05-D PASS

**Actividades**
1. Iniciar en Product Vision desde Project Status.
2. Completar secuencialmente scope, requirements, architecture, security, test strategy y traceability usando MANUAL/IMPORT.
3. Validar, corregir, aprobar y freeze cada artefacto.
4. Mostrar StepActionAdvisor en cada paso y bloquear intentos de skip.
5. Alcanzar PRE_CODE_READY y readiness strict PASS.

**Entregables verificables**
- pre_code_manual_browser_acceptance
- workflow transition trace
- readiness closure

**Pruebas / validadores**
- real browser full pre-code
- readiness strict
- MIASI applicability
- skip negative
- role approval

**Evidencia mínima**
- screenshots por etapa
- transition_trace.jsonl
- artifact provenance summary
- readiness report

**Seguridad operacional específica**
- PowerShell normal user=0
- external operator writes=0
- no hidden CLI bridge required

**Cierre de regresión obligatorio**
- ejecutar gates baratos + Contract Reconciliation Sweep + browser/capability acceptance;
- consumir la única full regression del backlog exactamente una vez, salvo que un hard-trigger anterior ya haya consumido esa corrida;
- ante FAIL no repetir full: aplicar recuperación compuesta selectiva y Historical Regression Guard.

**PASS**
- PRE_CODE_READY desde UI
- readiness strict PASS
- S0=0
- S1=0

**BLOCK**
- artefactos preinyectados por harness
- mandatory CLI bridge
- stage skip

**Salida / autorización**
- CLOSED/PASS
- Milestone Guided Pre-code Manual alcanzado
- autoriza GSDLC-06


## 7. Alcance transversal específico de esta ola

- Esta ola es la garantía contractual de que DevPilot es workflow wizard y no document explorer.
- StepActionAdvisor queda como componente obligatorio de cada `current_step` posterior.

## 8. Política de contratos históricos específica

- MIPSoftware/MIASI históricos permanecen fuentes normativas; el registry no los reescribe automáticamente.
- Readiness historical tests se migran a mappings versionados, no se relajan.

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


### Predictive Pre-Full Reconciliation Gate obligatorio

Como hardening derivado de GSDLC-04-E, antes de consumir la única full regression de esta ola el operador debe ejecutar y sellar un gate predictivo que, además del Contract Reconciliation Sweep, verifique al menos:

1. `Source Registry.status_required` frente a los valores `status` reales de todos los documentos current-active tocados;
2. `ApplicationService route contract ↔ OpenAPI ↔ api_service_mapping ↔ API route registry ↔ RBAC policy` sin conteos o rutas huérfanas;
3. UI package/version lineage actual frente a snapshots históricos sin aplicar invariantes históricas a successors;
4. budgets históricos congelados frente a budgets current-active, sin relajar retrospectivamente el histórico;
5. SecretGuard/redaction scan sobre el **árbol/ZIP de source que realmente será empaquetado**, no solo sobre fixtures sintéticos;
6. parsers de operadores probados contra el schema real de la evidencia que consumen y al menos una variante compatible documentada;
7. resolución explícita en Windows de wrappers `.cmd`/`.exe` usados con `shell=False`;
8. counters/registries derivados recalculados desde la colección viva y no hardcodeados;
9. `Project State / Source Registry / README / roadmap / CURRENT / TCR` coherentes entre sí;
10. runtime-ephemeral stores ausentes de fixtures, evidencia y release archives.

**Regla:** cualquier drift determinista se corrige antes del marker de full. El gate no puede degradarse a warnings para “ganar tiempo”.

## 9. Seguridad operacional específica

- AGENT/RAG aparecen `unavailable` hasta GSDLC-06/07; no se finge capability.
- No bypass de gates por owner o agente.

Toda acción mutante debe seguir `plan → dry-run → policy/RBAC → approval cuando aplique → execute → verify → evidence`. Cualquier excepción requiere ADR o backlog correctivo separado.

## 10. Estrategia de pruebas de la ola

- registry validation
- workflow graph
- skip negatives
- Advisor matrix
- readiness strict
- browser vertical slice

Regla de regresión:

- A→D usan Test Impact, pruebas focales, acumulativas y validadores determinísticos; **full regression = NO por rutina**.
- El micro-sprint E ejecuta la **única full regression del backlog exactamente una vez**, después de gates baratos, Contract Reconciliation Sweep y browser/capability acceptance pertinente.
- Una full intermedia solo puede ocurrir por hard trigger de riesgo explícito, owner-approved y documentado; si ocurre, **consume la única corrida full permitida** y E debe cerrar mediante evidencia compuesta sin lanzar otra.
- Si la full falla: preservar log/JUnit/marker inmutables, prohibir rerun, diagnosticar causa, ejecutar exact failed-nodeid retest + bounded impacted retest + Historical Regression Guard y cerrar solo con `composite-full-regression-selective-retest = PASS`.
- Browser acceptance se ejecuta únicamente cuando el micro-sprint introduce/cierra UX; no se repite por correctives que no cambian comportamiento browser demostrado.

## 11. Evidencia autoritativa esperada

- workflow trace
- artifact lifecycle evidence
- advisor screenshots
- readiness/MIASI reports

Además, cada micro-sprint debe conservar:

- manifest de source delta;
- identidad Git pre/post;
- resultados PASS/BLOCK machine-readable;
- lista de S0/S1;
- browser screenshots cuando corresponda;
- hashes de artefactos empaquetados;
- declaración explícita `network_used`, `external_api_used`, `secrets_exposed`, `mutations_performed`.

## 12. Definition of Done del backlog

- MIP+MIASI ejecutables
- StepActionAdvisor
- manual/import PRE_CODE_READY
- UI-complete

El backlog solo puede adjudicarse `CLOSED/PASS` si todos los micro-sprints A→E han cerrado en secuencia y no quedan S0/S1 abiertos.

## 13. Criterio de autorización del siguiente backlog

- GSDLC-06 solo tras Milestone Manual PASS; GSDLC-06 además requiere R01-E.

Un `PASS-WITH-GAPS` solo puede autorizar el siguiente backlog cuando los gaps estén clasificados S2/S3, tengan owner, evidencia y no invaliden la invariante de producto de esta ola.



## 14. Execution progress — 2026-08-25

- GSDLC-05-A: `CLOSED/PASS` — repo370.
- GSDLC-05-B: `CLOSED/PASS` — repo371.
- GSDLC-05-C: `CLOSED/PASS` — repo372 / browser 6/6 / full=0.
- GSDLC-05-D: `IMPLEMENTED / PENDING-WINDOWS-BROWSER-VALIDATION`; 19 current steps, 136 action definitions, server-authoritative StepActionAdvisor, AGENT/RAG unavailable, full=0.
- GSDLC-05-E: **not authorized** until owner adjudication of 05-D.

This progress appendix does not alter the approved design contract or the A→D/no-full, E/exactly-one-full regression policy.

## 14. Estado de implementación — GSDLC-05-E

- GSDLC-05-D: `CLOSED/PASS` — repo373 / commit `a5b01a6ffb7f7808ccbaae54847bf2117b95b9f8` / browser 7/7 / full=0.
- GSDLC-05-E: `PASS-CANDIDATE / WINDOWS-COMPOSITE-CLOSURE / PENDING-OWNER-ADJUDICATION`; browser Windows y readiness strict PASS; `PRE_CODE_READY` alcanzado sin hidden CLI bridge.
- Full regression DEVPL-GSDLC-05 consumida exactamente una vez: `1/1 FAIL` (`2611 PASS / 38 FAIL / 0 ERROR / 5 SKIP`), preservada sin rerun; composite selective recovery `PASS` (exact failed-nodeid `38/38`, bounded impact `18/18`, Historical Regression Guard PASS). Segunda full prohibida.
- GSDLC-06 permanece bloqueado hasta owner adjudication de 05-E + cierre formal del backlog 05.
