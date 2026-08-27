---
doc_id: "DEVPL-GSDLC-06"
title: "DEVPL-GSDLC-06 — Model Gateway v2, token/cost governance and provider settings"
status: "approved"
version: "1.4.0"
owner: "Ordóñez"
updated: "2026-08-26"
approval: "approved_by_owner"
approved_at: "2026-08-26"
approval_decision: "APPROVE"
program_id: "DEVPL-GSDLC"
design_origin_repo: "repo_DevPilot_Local_341_POST_H_EVAL_002_PILOT_TRANSITION_REBIND.zip"
design_origin_git_commit: "cff43e8d992ff6139bd13bb1809ce4d497ae0952"
design_origin_repo_sha256: "e28cd2bae08d099a2b62c4869c83b6e5a647f3f780ca1572727b7c80f6eeea3b"
design_origin_role: "historical-design-origin-only/not-execution-authority"
source_repo: "repo_DevPilot_Local_374_DEVPL_GSDLC_05_E_MANUAL_PRE_CODE_WINDOWS_VALIDATED_CANDIDATE.zip"
source_git_commit: "db04b6f158fc4dd366b3f61635fb2d66d63f7d40"
source_repo_sha256: "f87c2a1db339b1d0f2dcf1d694366672c8cc9d57c27bfcd33a460a3889706152"
source_repo_role: "execution-authority/owner-adjudicated-gsdlc-05-successor"
execution_source_policy: "fixed/owner-adjudicated-gsdlc-05-successor"
predecessor_backlog: "DEVPL-GSDLC-05"
predecessor_micro_sprint_closure: "DEVPL_GSDLC_05_E_FINAL_OWNER_ADJUDICATION_v1_0_0.md"
predecessor_backlog_closure: "DEVPL_GSDLC_05_BACKLOG_CLOSURE_ADJUDICATION_v1_0_0.md"
predecessor_closure_current: "DEVPL_GSDLC_05_FINAL_OWNER_CLOSURE_CURRENT.json"
activation_requires_owner_adjudication: false
activation_rebind_required_before_functional_source: true
local_first: true
ui_complete_normal_journey: true
dry_run_default: true
backlog_id: "DEVPL-GSDLC-06"
r01_research_binding: "CLOSED/PASS"
r01_research_authority_repo: "repo_DevPilot_Local_348_DEVPL_GSDLC_R01_E_RESEARCH_CLOSURE.zip"
r01_research_authority_commit: "3d7fda44d7ab5feefadd2eb4a7b9d20680eb1b5d"
r01_research_authority_sha256: "68487b2d210a0fd8fb6f2c46f2f70f205f925aeda7d556e13af205de4583515d"
r01_binding_scope: "architecture-and-security-input; historical design_origin remains unchanged"
backlog_status: "approved/executable-design"
micro_sprints_total: 5
validation_policy: "A-D cumulative-selective/no-full; E exactly-one-full-regression after cheap+predictive+browser gates; no rerun after failure; composite recovery"
documentation_contract_policy: "DEVPL_DOCUMENTATION_CONTRACT_RECONCILIATION_POLICY_v1_0_0_APPROVED"
runtime_ephemeral_fixture_policy: "exclude auth.db*, devpilot.db* and equivalent runtime stores"
model_provider_cost_policy: "mock-first/local-opt-in/external-disabled-until-ADR+freshness+RBAC+budget"
---

# 0. Aprobación y binding de ejecución

**Decisión owner:** `APPROVED / EXECUTABLE-DESIGN`.

DEVPL-GSDLC-06 queda rebindeado al successor owner-adjudicated de GSDLC-05:

```text
repo   repo_DevPilot_Local_374_DEVPL_GSDLC_05_E_MANUAL_PRE_CODE_WINDOWS_VALIDATED_CANDIDATE.zip
commit db04b6f158fc4dd366b3f61635fb2d66d63f7d40
sha256 f87c2a1db339b1d0f2dcf1d694366672c8cc9d57c27bfcd33a460a3889706152
```

Repo341 se conserva exclusivamente como origen histórico de diseño. No es autoridad mutable. La ejecución de 06-A debe partir de repo374 y realizar primero un **activation rebind administrativo** que incorpore `DEVPL_GSDLC_05_E_FINAL_OWNER_ADJUDICATION_v1_0_0.md`, `DEVPL_GSDLC_05_BACKLOG_CLOSURE_ADJUDICATION_v1_0_0.md`, sus closure-current, este backlog aprobado y los prompts 06-A→E. Después debe reconciliar Project State / Source Registry / README / roadmap a `GSDLC-05 CLOSED/PASS` + `GSDLC-06 APPROVED/ACTIVE`.

No se modifica ni reconstruye el ZIP repo374 para introducir metadata post-candidate. El rebind se materializa en el successor de trabajo de 06-A antes de cualquier cambio funcional.

## 0.1 Política de regresión reforzada

- GSDLC-06-A→D: **sin full regression por rutina**; únicamente Test Impact, focales, acumulativas, schemas, Historical Contract Sweep y validadores determinísticos.
- GSDLC-06-E: browser/capability acceptance + Contract Reconciliation Sweep + Predictive Pre-Full **antes** del marker; luego una sola full regression.
- Si la full falla: marker/log/JUnit/failed-nodeids quedan inmutables, **no rerun**, se corrige la causa y se usa `exact failed-nodeid retest + bounded impacted retest + Historical Regression Guard + composite-full-regression-selective-retest`.
- Los gates predictivos deben prevenir los defectos observados en 05-E: counters derivados desincronizados, tests históricos atados a punteros `current`, composición eager de capabilities posteriores sobre fixtures históricos, scans de secretos whole-tree no diferenciales y parsers que no reflejen el schema real.

# 0.2 Contrato de binding heredado

Este backlog conserva como **origen de diseño** el baseline histórico desde el que fue redactado, pero **no puede ejecutarse contra ese baseline congelado**.

Antes de cualquier mutación de DEVPL-GSDLC-06 debe existir una adjudicación reproducible:

- `DEVPL-GSDLC-05 = CLOSED/PASS`;
- successor repo + Git commit + SHA-256 del backlog predecessor;
- owner adjudication del micro-sprint de cierre y del backlog;
- rebind de Project State / Source Registry / README / roadmap al successor predecessor.

El `design_origin_repo` de frontmatter conserva el origen histórico. `source_repo` ya apunta a repo374 como autoridad efectiva fija; cualquier successor posterior se resuelve por adjudicación secuencial de micro-sprint, sin regresar al design origin.

No está permitido volver a repo341 o a otro parent histórico para “simplificar” implementación. La evolución es acumulativa.

## 0.3 Invariantes heredadas

1. La navegación project-scoped solo opera con proyecto activado por el journey GSDLC-03.
2. La sesión/RBAC/approval server-side sigue siendo autoridad; storage browser es UX-only.
3. Stores `runtime-ephemeral` (`auth.db*`, `devpilot.db*`, etc.) no se copian a fixtures/sandboxes.
4. Mutaciones son typed operations gobernadas; no arbitrary shell.
5. Los contratos históricos se preservan como hechos scoped y evolucionan mediante successors.
6. El backlog debe incorporar cualquier adjudicación externa del predecessor antes de cambios funcionales.


# DEVPL-GSDLC-06 — Model Gateway v2, token/cost governance and provider settings

## 1. Objetivo

Ampliar ModelAdapter/CostGuard para routing por capabilities, modelos locales/API oficialmente soportados, budgets y configuración segura desde UI.

## 2. Invariante de producto que esta ola debe demostrar

> El usuario puede elegir Mock/Local/API desde Settings; DevPilot recomienda/rutea modelos por tarea y muestra tokens/costo estimado antes de ejecutar, con hard stops y fallback.

Esta invariante es parte del criterio de cierre. No basta con que existan clases, endpoints o archivos: debe demostrarse el comportamiento de producto descrito.

## 3. Dependencias y precondiciones de entrada

- GSDLC-05 CLOSED/PASS
- GSDLC-R01 CLOSED/PASS
- autoridad de investigación R01 disponible y verificada:
  - repo `repo_DevPilot_Local_348_DEVPL_GSDLC_R01_E_RESEARCH_CLOSURE.zip`
  - commit `3d7fda44d7ab5feefadd2eb4a7b9d20680eb1b5d`
  - SHA-256 `68487b2d210a0fd8fb6f2c46f2f70f205f925aeda7d556e13af205de4583515d`
  - `DEVPL_GSDLC_R01_E_FINAL_OWNER_ADJUDICATION_v1_0_0.md/.json`
  - `DEVPL_GSDLC_R01_FINAL_BACKLOG_CLOSURE_ADJUDICATION_v1_0_0.md/.json`

La evidencia R01 se consume como **input arquitectónico y de policy**, no como habilitación automática de providers. Antes de activar cualquier ruta externa se debe refrescar la evidencia cambiante conforme a `reevaluation_protocol.md`.

Si alguna precondición no puede verificarse de forma reproducible, el backlog entra en `BLOCK` antes de mutar source.

Precondición transversal adicional: debe existir un proyecto activo/server-validado proveniente del journey GSDLC-03 para toda superficie project-scoped; Settings/Account globales no sustituyen project context.

## 4. Alcance funcional y técnico

### 4.1 Incluido

- ModelCapabilityCatalog
- ProviderAccessRoute
- local endpoints
- vendor APIs
- credential refs
- TokenBudgetPolicy
- ContextBudget
- routing/fallback
- Settings UI
- `ModelRoutingRequest` / `ModelRouteDecision`
- `AIControlCenterView` shell para separar administración de modelos de administración agentic posterior
- auth-adapter metadata y evidence/freshness metadata
- provider-specific enablement ADR gates

### 4.2 Fuera de alcance

- browser scraping consumer LLM apps
- unbounded auto-spend
- credentials in repo
- planning, handoffs o tool execution dentro de Model Gateway
- convertir `ModelRouteDecision` en `ToolExecutionDecision`
- ConsumerSessionAdapter/browser-session reuse

## 5. Superficies y fuentes que probablemente serán afectadas

- src/devpilot_core/modeling/*
- CostGuard
- ProviderRegistry
- Settings UI
- Secret store

La lista es orientativa para Test Impact. Cada micro-sprint debe cerrar su manifest exacto antes de ejecutar cambios.

## 6. Micro-sprints secuenciales

### GSDLC-06-A — Model capability and access-route contracts

**Objetivo.** Separar claramente modelo, proveedor, endpoint/ruta de acceso y capacidades.

**Entradas obligatorias**
- GSDLC-05 CLOSED/PASS
- GSDLC-R01 CLOSED/PASS

**Actividades**
1. Implementar ModelCapabilityCatalog y ProviderAccessRoute a partir de R01.
2. Registrar context window, structured output, tools, vision, coding, embeddings y cost metadata.
3. Representar enabled/disabled/conditional y reason.
4. Implementar capability matching sin vendor-specific branches en workflows.
5. Garantizar Mock route siempre disponible.
6. Implementar contratos explícitos `ModelRoutingRequest` y `ModelRouteDecision` con `workload_id`, capabilities, privacy, cost ceiling, offline/region constraints, route/evidence refs y blocked reason.
7. Importar la disposición inicial de R01-E sin promover estados: `mock=default-safe`; Ollama/LM Studio local=`allowed` solo como rutas local opt-in; rutas externas=`conditional/unknown/blocked` y runtime-disabled.
8. Registrar `provider_id`, `model_id`, `access_route_id`, `gateway_adapter_id` y `auth_adapter_id` como identidades separadas.

**Entregables verificables**
- catalog schemas/services
- routing capability query
- catalog migration

**Pruebas / validadores**
- schema
- capability matching
- unknown route deny
- mock availability
- route/model/provider identity separation
- `ModelRouteDecision` cannot grant tool execution

**Evidencia mínima**
- model_catalog_snapshot.json
- capability_match_cases.json

**Seguridad operacional específica**
- route unknown=deny
- no secrets dentro del catalog

**PASS**
- workflow pide capabilities, no vendor
- mock route valid

**BLOCK**
- hardcoded model name dentro de Guided workflow
- unknown route allowed
- una decisión de routing concede permiso de tool/skill
- una ruta externa cambia a enabled solo por compatibilidad OpenAI

**Salida / autorización**
- autoriza GSDLC-06-B


### GSDLC-06-B — Local provider discovery and OpenAI-compatible hardening

**Objetivo.** Habilitar rutas locales opt-in, reproducibles y protegidas contra SSRF.

**Entradas obligatorias**
- GSDLC-06-A PASS

**Actividades**
1. Endurecer Ollama y LM Studio adapters existentes.
2. Añadir generic local OpenAI-compatible endpoint allowlisted.
3. Implementar provider health/model discovery bounded.
4. Agregar hardware-fit hints desde R01 y fallback a mock.
5. Diferenciar claramente `localhost local` de remote API.

**Entregables verificables**
- LocalProviderAdapter v2
- local endpoint policy
- provider health UI data

**Pruebas / validadores**
- fake Ollama/LM Studio/OpenAI-compatible
- non-local endpoint negative
- timeout
- malformed model list

**Evidencia mínima**
- local_provider_health_report.json

**Seguridad operacional específica**
- localhost default
- SSRF/path URL validation
- no API key required for local routes unless explicitly configured

**PASS**
- mock + local fake route PASS
- remote endpoint no se clasifica local

**BLOCK**
- SSRF
- non-local accepted as local
- unbounded health call

**Salida / autorización**
- autoriza GSDLC-06-C


### GSDLC-06-C — External API credential and enablement flow

**Objetivo.** Permitir APIs externas solo mediante rutas oficialmente soportadas, configuración explícita y secretos seguros.

**Entradas obligatorias**
- GSDLC-06-B PASS
- R01 access decision matrix
- provider-specific ADR aprobado que resuelva los 12 gates de R01-E antes de ejecutar una ruta externa real
- evidencia contractual/privacy/region dentro de TTL de freshness

**Actividades**
1. Implementar credential references vía env/OS secret store, no valores persistidos en repo.
2. Agregar enable toggle por provider y workspace/policy.
3. Mostrar privacy/terms/cost notice antes de habilitar.
4. Implementar connectivity test redacted y disable/revoke.
5. Bloquear browser scraping/cookie/session piggyback no soportado.
6. Implementar auth adapters tipados: `LocalLoopbackNoSecretAdapter`, `EnvApiKeyAdapter`, provider-native identity adapters cuando aplique; `ConsumerSessionAdapter` permanece bloqueado.
7. Exigir que cada enablement ADR resuelva provider/model/route, region, auth, terms/billing/privacy, data classes, budget, health/fallback, logging/redaction, kill switch/rollback, eval threshold, RBAC y freshness TTL.
8. Revalidar evidencia F0/F1 inmediatamente antes de enablement real; evidencia R01 histórica no es autorización perpetua.

**Entregables verificables**
- ProviderCredentialReference
- external provider settings
- enablement audit

**Pruebas / validadores**
- fake vendor providers
- missing/invalid key
- secret scan
- network disabled
- unsupported web-session route

**Evidencia mínima**
- provider_enablement_audit.json
- secret_leak_scan.json

**Seguridad operacional específica**
- raw key never logged/exported
- network disabled by default
- no consumer-web automation

**PASS**
- external route disabled hasta config completa
- enable/disable auditado

**BLOCK**
- secret en log/DB source
- API called before consent/budget
- browser session used

**Salida / autorización**
- autoriza GSDLC-06-D


### GSDLC-06-D — TokenBudgetPolicy, ContextBudget and routing

**Objetivo.** Controlar costo y tamaño de contexto antes, durante y después de cada run.

**Entradas obligatorias**
- GSDLC-06-C PASS

**Actividades**
1. Definir budgets por request, artifact, story, session, day y workspace.
2. Estimar input/output tokens y costo antes de ejecución.
3. Implementar ContextBudget con RAG/summary/diff-first y hard trim.
4. Implementar quality/cost/locality routing y fallback explícito siguiendo el orden R01-E: capabilities → privacy/offline → provider enablement → region/terms/auth/data → cost ceiling → health → benchmark workload-specific → safe fallback/BLOCK.
5. Registrar planned vs actual tokens/cost y detener al exceder hard budget.

**Entregables verificables**
- TokenBudgetPolicy
- ContextBudget
- ModelRouter
- cost ledger v2

**Pruebas / validadores**
- budget exceed negatives
- routing determinism
- ledger accuracy
- context truncation
- fallback

**Evidencia mínima**
- budget_test_matrix.json
- cost_ledger_samples.json

**Seguridad operacional específica**
- hard stop server-side
- agent no puede ampliar su budget
- external high-cost route puede requerir approval

**PASS**
- no run supera hard budget
- cost/tokens explicables

**BLOCK**
- loop overspends
- actual cost unknown sin `unknown` explícito
- fallback silencioso

**Salida / autorización**
- autoriza GSDLC-06-E


### GSDLC-06-E — Provider Settings UX and controlled model evaluation

**Objetivo.** Cerrar configuración usable y visible desde UI.

**Entradas obligatorias**
- GSDLC-06-D PASS

**Actividades**
1. Construir `AIControlCenterView` como shell de administración IA y `ModelSettingsView` como sub-vista de Model Gateway, con provider/model/access-route, enabled state y health.
2. Mostrar capabilities, route disposition, privacy/data class, target region, auth-adapter type, estimated cost, budget, evidence freshness y fallback.
3. Permitir selección manual o routing policy sin permitir que una selección de modelo/provider cambie permisos de tools.
3a. Mostrar claramente `mock`, local opt-in y external-disabled/conditional; no ocultar `blocked/unknown`.
4. Ejecutar eval controlada mock/local y fake API; real API opcional con approval.
5. Probar disable/revoke/fallback desde navegador.

**Entregables verificables**
- AIControlCenterView shell
- ModelSettingsView
- provider eval report
- routing preference UI

**Pruebas / validadores**
- browser settings
- mock/local/fake API
- cost UI parity
- RBAC provider config

**Evidencia mínima**
- settings screenshots
- provider_model_eval.json
- cost parity report

**Seguridad operacional específica**
- credentials masked
- solo roles autorizados configuran providers

**Cierre de regresión obligatorio**
- ejecutar gates baratos + Contract Reconciliation Sweep + browser/capability acceptance;
- consumir la única full regression del backlog exactamente una vez, salvo que un hard-trigger anterior ya haya consumido esa corrida;
- ante FAIL no repetir full: aplicar recuperación compuesta selectiva y Historical Regression Guard.

**PASS**
- usuario entiende model/provider/access-route/costo/freshness
- `ModelRouteDecision` nunca concede `ToolExecutionDecision`
- mock/local mandatory PASS
- S0/S1=0

**BLOCK**
- credential visible
- cost absent
- route cambia sin audit

**Salida / autorización**
- CLOSED/PASS
- autoriza GSDLC-07


## 7. Alcance transversal específico de esta ola

- Model Gateway sirve a toda funcionalidad agentic; ningún workflow debe depender directamente de un SDK de vendor.
- Model Gateway posee routing de modelo/provider/access-route/auth-adapter, pero **no** planificación, handoffs, tools, approvals ni MCP execution.
- `ModelRouteDecision` y `ToolExecutionDecision` son contratos diferentes y no existe conversión implícita entre ambos.
- `AIControlCenterView` puede agrupar UX de IA, pero sus sub-vistas deben conservar las fronteras de autoridad de Model Gateway, Agent Runtime y Skills/Tools.
- Cost/token governance es capability de producto, no solo telemetry.

## 8. Política de contratos históricos específica

- POST-H-032-B/C providers disabled-by-default son hechos históricos; cualquier enablement se expresa en nuevos campos/ADRs, no cambiando retroactivamente esos contratos.
- No extender `external_api_used=false` histórico a futuro runtime habilitado con policy.

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

- SSRF, secret leakage, runaway spend, data egress, provider retention y fallback confusion.

Toda acción mutante debe seguir `plan → dry-run → policy/RBAC → approval cuando aplique → execute → verify → evidence`. Cualquier excepción requiere ADR o backlog correctivo separado.

## 10. Estrategia de pruebas de la ola

- adapter contract
- fake providers
- budget/cost tests
- secret scans
- browser provider settings
- negative route→tool-permission escalation
- provider evidence freshness/enablement ADR gates

Regla de regresión:

- A→D usan Test Impact, pruebas focales, acumulativas y validadores determinísticos; **full regression = NO por rutina**.
- El micro-sprint E ejecuta la **única full regression del backlog exactamente una vez**, después de gates baratos, Contract Reconciliation Sweep y browser/capability acceptance pertinente.
- Una full intermedia solo puede ocurrir por hard trigger de riesgo explícito, owner-approved y documentado; si ocurre, **consume la única corrida full permitida** y E debe cerrar mediante evidencia compuesta sin lanzar otra.
- Si la full falla: preservar log/JUnit/marker inmutables, prohibir rerun, diagnosticar causa, ejecutar exact failed-nodeid retest + bounded impacted retest + Historical Regression Guard y cerrar solo con `composite-full-regression-selective-retest = PASS`.
- Browser acceptance se ejecuta únicamente cuando el micro-sprint introduce/cierra UX; no se repite por correctives que no cambian comportamiento browser demostrado.

## 11. Evidencia autoritativa esperada

- provider catalog
- enablement audit
- cost ledger
- browser screenshots

Además, cada micro-sprint debe conservar:

- manifest de source delta;
- identidad Git pre/post;
- resultados PASS/BLOCK machine-readable;
- lista de S0/S1;
- browser screenshots cuando corresponda;
- hashes de artefactos empaquetados;
- declaración explícita `network_used`, `external_api_used`, `secrets_exposed`, `mutations_performed`.

## 12. Definition of Done del backlog

- mock/local route
- external gated route
- budget hard stop
- Settings UI
- R01 route dispositions preservadas hasta ADR/evidencia sucesora
- `ModelRouteDecision` separado de tool execution
- external provider enablement exige ADR + freshness + RBAC + budget

El backlog solo puede adjudicarse `CLOSED/PASS` si todos los micro-sprints A→E han cerrado en secuencia y no quedan S0/S1 abiertos.

## 13. Criterio de autorización del siguiente backlog

- GSDLC-07 solo si mock y al menos una ruta local/fake-local pasan; API real no es requisito.

Un `PASS-WITH-GAPS` solo puede autorizar el siguiente backlog cuando los gaps estén clasificados S2/S3, tengan owner, evidencia y no invaliden la invariante de producto de esta ola.

