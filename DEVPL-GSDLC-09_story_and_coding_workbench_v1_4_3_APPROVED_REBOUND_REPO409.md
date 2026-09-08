---
doc_id: "DEVPL-GSDLC-09"
title: "DEVPL-GSDLC-09 — Story and Coding Workbench"
status: "approved"
version: "1.4.3"
owner: "Ordóñez"
updated: "2026-09-08"
approval: "approved_by_owner/rebound_repo409_post_09_b"
program_id: "DEVPL-GSDLC"
source_repo: "repo_DevPilot_Local_409_DEVPL_GSDLC_09_B_CODE_WORKBENCH_WINDOWS_VALIDATED_CANDIDATE.zip"
source_git_commit: "3c06d72445525e9b6d246726e5d6c6eb58fd20d4"
source_repo_sha256: "857084478f2661c471bc3421e23a68dfb027855e3321f52bd05ac21a7db64573"
source_repo_role: "current-approved-post-GSDLC-09-B-windows-validated-baseline"
design_origin_repo: "repo_DevPilot_Local_341_POST_H_EVAL_002_PILOT_TRANSITION_REBIND.zip"
design_origin_commit: "cff43e8d992ff6139bd13bb1809ce4d497ae0952"
design_origin_sha256: "e28cd2bae08d099a2b62c4869c83b6e5a647f3f780ca1572727b7c80f6eeea3b"
execution_source_policy: "repo409-post-GSDLC-09-B-authority; FRX-v2.4 current profile mandatory"
predecessor_backlog: "DEVPL-GSDLC-08/CLOSED-PASS/WINDOWS-VALIDATED"
activation_requires_owner_adjudication: false
activation_requires_frx_v2_4_closed_pass: true
local_first: true
ui_complete_normal_journey: true
dry_run_default: true
backlog_id: "DEVPL-GSDLC-09"
r01_research_binding: "CLOSED/PASS"
r01_research_authority_repo: "repo_DevPilot_Local_348_DEVPL_GSDLC_R01_E_RESEARCH_CLOSURE.zip"
r01_research_authority_commit: "3d7fda44d7ab5feefadd2eb4a7b9d20680eb1b5d"
r01_research_authority_sha256: "68487b2d210a0fd8fb6f2c46f2f70f205f925aeda7d556e13af205de4583515d"
r01_binding_scope: "architecture-and-security-input"
backlog_status: "APPROVED/ACTIVE-GSDLC-09-C"
micro_sprints_total: 5
validation_policy: "A-D cumulative-selective; E exactly-one-logical-full via mandatory current FRX profile; no operator low-level overrides; no rerun after functional failure; composite recovery"
frx_execution_profile_policy: "mandatory-current-active/profile-id-only"
documentation_contract_policy: "DEVPL_DOCUMENTATION_CONTRACT_RECONCILIATION_POLICY_v1_0_0_APPROVED"
runtime_ephemeral_fixture_policy: "exclude auth.db*, devpilot.db* and equivalent runtime stores"
---

# 0.0.5 Rebind GSDLC-09-C a repo409 — 2026-09-08

GSDLC-09-B está `CLOSED/PASS/WINDOWS-VALIDATED`. La autoridad current-active para GSDLC-09-C es:

```text
repo:    repo_DevPilot_Local_409_DEVPL_GSDLC_09_B_CODE_WORKBENCH_WINDOWS_VALIDATED_CANDIDATE.zip
commit:  3c06d72445525e9b6d246726e5d6c6eb58fd20d4
sha256:  857084478f2661c471bc3421e23a68dfb027855e3321f52bd05ac21a7db64573
profile: frx-v2.4-current
profile_sha256: 2339df5fd79134fa8a675092e71ed71c8c11300b46747f055e86628e72679219
```

09-C habilita únicamente source mutation tipada y approval-bound mediante `SourceChangePlan`; conserva `full=0`, browser real obligatorio, Historical Contract Authority y Contract Reconciliation. Los hechos UOC-005 permanecen congelados mediante snapshot dedicado; la autoridad current-active puede crecer por successor contracts sin volver falsos los cierres históricos.

# 0.0.4 Rebind GSDLC-09-B a repo408 — 2026-09-07

GSDLC-09-A está `CLOSED/PASS/WINDOWS-VALIDATED`. La autoridad current-active para GSDLC-09-B es:

```text
repo:    repo_DevPilot_Local_408_DEVPL_GSDLC_09_A_STORY_EXECUTION_CONTEXT_WINDOWS_VALIDATED_CANDIDATE.zip
commit:  fede10c963d7af571fc0fd062f76323d647877f7
sha256:  c077fcba424527a179773e9f2b155700c357fecd0e7d9af8e40533374d290e59
profile: frx-v2.4-current
profile_sha256: 2339df5fd79134fa8a675092e71ed71c8c11300b46747f055e86628e72679219
```

GSDLC-09-B conserva la política FRX-v2.4: Full Regression `0`; Test Impact + focal + acumulativa + Historical Contract Authority + Contract Reconciliation; browser obligatorio porque introduce UX; los knobs FRX de bajo nivel no pertenecen al operador. 09-B permite autoría manual **solo como SourceDraftBuffer runtime-only** y no habilita apply ni source mutation, que pertenecen exclusivamente a 09-C.

# 0.0.3 Rebind post-FRX-v2.4 — 2026-09-06

FRX-v2.4-A y FRX-v2.4-B están `CLOSED/PASS/WINDOWS-VALIDATED`. La autoridad de ejecución para activar DEVPL-GSDLC-09 es:

```text
repo:    repo_DevPilot_Local_406_FRX_V2_4_B_EXECUTION_PROFILE_LOCK_WINDOWS_VALIDATED_CANDIDATE.zip
commit:  6b8a9a5feef65860826904444f651421abad282a
sha256:  59c40713182b84655315773654e49adf95419ceb517ec9496929252fba33b191
profile: frx-v2.4-current
profile_sha256: 2339df5fd79134fa8a675092e71ed71c8c11300b46747f055e86628e72679219
```

La cadena Git Windows acreditada es `c0347423… -> 10acf186… -> 6b8a9a5f…`, toda por fast-forward/ancestry verificado. El profile FRX current-active es obligatorio para la única full futura de cierre GSDLC-09-E; A→D mantienen `full=0` por rutina y no exponen planner/max_nodeids/transport/workers al operador. Esta sección sustituye únicamente la autoridad current-active; no reescribe los hechos históricos de repo404 ni el origen de diseño repo341.

# 0.0 Owner APPROVE y rebind current-active — 2026-09-05

DEVPL-GSDLC-08 y DEVPL-GSDLC-08-E quedaron `CLOSED/PASS/WINDOWS-VALIDATED`.
La autoridad vigente de entrada es `repo_DevPilot_Local_404_DEVPL_GSDLC_08_E_FINAL_CLOSURE_RECONCILIATION_WINDOWS_VALIDATED_CANDIDATE.zip` / `c0347423b78c67ed93f9eb4a2af39e0411b1d22f` /
SHA-256 `c90fb00a4416bb62c50e161b1eb837efcf88f88d0d3c19d0c0bcbc9fd47cb767`.

El repo403 solicitado como baseline técnico permanece preservado como predecessor funcional Windows-validado,
pero repo404 es su successor de reconciliación final y por tanto prevalece como autoridad current-active.

Este backlog queda elevado a `APPROVED`. Sin embargo, la aprobación **no autoriza todavía el primer cambio funcional**.
Antes de GSDLC-09-A debe cerrar el enabler:

`DEVPL-FRX-v2.4 — Regression Contract and Execution Policy Hardening = CLOSED/PASS/WINDOWS-VALIDATED`.

Después de ese cierre, el prompt `00_PROMPT_DEVPL_GSDLC_09_ACTIVATION_REBIND...` resolverá el successor canónico real de FRX-v2.4
y materializará el execution binding final de 09. Nunca se debe volver a repo341 ni ejecutar 09-A directamente sobre repo404
si FRX-v2.4 ya produjo un successor.

## 0.0.1 Política FRX obligatoria para DEVPL-GSDLC-09

A→D:
- full regression = 0 por rutina;
- Test Impact + focal + acumulativa + Historical Contract Authority + Contract Reconciliation Sweep;
- browser solo si el micro-sprint introduce/cierra UX que deba demostrarse.

E:
- exactamente una logical full del backlog, salvo hard-trigger anterior owner-approved que ya haya consumido el budget;
- el operador **no puede configurar** planner, max_nodeids, nodeid transport ni workers por cuenta propia;
- debe invocar el `FullRegressionExecutionProfile` current-active resultante de FRX-v2.4;
- preflight obligatorio antes de reservar la full;
- ante FAIL funcional: no rerun, selective/composite recovery;
- resume solo para `UNEXECUTED` dentro de la misma logical session.

## 0.0.2 Política de mutación

GSDLC-09 introduce source writes reales approval-bound. Por ello toda operación mutante debe conservar:
`plan → dry-run → preimage revalidation → RBAC/policy → approval → atomic execute → verify → evidence → rollback`.

No se permite:
- shell arbitrario;
- generic patch apply sin plan;
- self-approval por agentes;
- provider/model route como fuente de autoridad;
- writes fuera del workspace/project policy;
- inclusión de runtime stores o secretos en context packs/evidence.


# 0. Política de binding de ejecución

Este backlog conserva como **origen de diseño** el baseline histórico desde el que fue redactado, pero **no puede ejecutarse contra ese baseline congelado**.

Antes de cualquier mutación de DEVPL-GSDLC-09 debe existir una adjudicación reproducible:

- `DEVPL-GSDLC-08 = CLOSED/PASS`;
- successor repo + Git commit + SHA-256 del backlog predecessor;
- owner adjudication del micro-sprint de cierre y del backlog;
- rebind de Project State / Source Registry / README / roadmap al successor predecessor.

El `source_repo` de frontmatter se conserva únicamente como `design-origin`; la autoridad efectiva se resuelve en la activación del backlog mediante `execution_source_policy = predecessor-owner-adjudicated-successor`.

No está permitido volver a repo341 o a otro parent histórico para “simplificar” implementación. La evolución es acumulativa.

## 0.1 Invariantes heredadas

1. La navegación project-scoped solo opera con proyecto activado por el journey GSDLC-03.
2. La sesión/RBAC/approval server-side sigue siendo autoridad; storage browser es UX-only.
3. Stores `runtime-ephemeral` (`auth.db*`, `devpilot.db*`, etc.) no se copian a fixtures/sandboxes.
4. Mutaciones son typed operations gobernadas; no arbitrary shell.
5. Los contratos históricos se preservan como hechos scoped y evolucionan mediante successors.
6. El backlog debe incorporar cualquier adjudicación externa del predecessor antes de cambios funcionales.


# DEVPL-GSDLC-09 — Story and Coding Workbench

## 1. Objetivo

Implementar el ciclo de una historia desde contexto hasta cambio de código revisable, con editor/diff, agent assistance y apply gobernado.

## 2. Invariante de producto que esta ola debe demostrar

> El usuario abre una story, DevPilot reúne requisitos/ADRs/tests/riesgos, permite escribir o proponer código, muestra diff y nunca aplica cambios sin policy/approval.

Esta invariante es parte del criterio de cierre. No basta con que existan clases, endpoints o archivos: debe demostrarse el comportamiento de producto descrito.

## 3. Dependencias y precondiciones de entrada

- GSDLC-08 CLOSED/PASS
- GSDLC-07 CLOSED/PASS con `ToolIntent` / `ToolExecutionDecision` y Agent Runtime boundaries activos

Si alguna precondición no puede verificarse de forma reproducible, el backlog entra en `BLOCK` antes de mutar source.

Precondición transversal adicional: debe existir un proyecto activo/server-validado proveniente del journey GSDLC-03 para toda superficie project-scoped; Settings/Account globales no sustituyen project context.

## 4. Alcance funcional y técnico

### 4.1 Incluido

- StoryExecutionState
- context pack
- code viewer/editor
- change plan/diff
- bounded source writes
- coding/test agents
- rollback

### 4.2 Fuera de alcance

- final Git commit/quality closure
- arbitrary shell

## 5. Superficies y fuentes que probablemente serán afectadas

- workspace source files
- Patch Review
- filesystem typed ops
- agents

La lista es orientativa para Test Impact. Cada micro-sprint debe cerrar su manifest exacto antes de ejecutar cambios.

## 6. Micro-sprints secuenciales

### GSDLC-09-A — StoryExecutionState and context pack
  
**Objetivo.** Crear una unidad de ejecución trazable por story.

**Entradas obligatorias**
- GSDLC-08 CLOSED/PASS
- approved sprint

**Actividades**
1. Definir StoryExecutionState PLANNED→IN_PROGRESS→CHANGES_READY→VALIDATING→COMMIT_READY→DONE.
2. Construir context pack de requirement, acceptance, ADRs, risks, test intent y archivos relevantes.
3. Registrar provenance y context hash.
4. Definir DoR gate antes de iniciar.
5. Integrar Project Status current story.

**Entregables verificables**
- StoryExecutionState schema
- StoryContextPack
- DoR evaluator

**Pruebas / validadores**
- state matrix
- missing DoR negative
- context trace link

**Evidencia mínima**
- story_context_fixture.json
- DoR report

**Seguridad operacional específica**
- minimize context
- exclude secrets/runtime files

**PASS**
- story no inicia sin DoR
- context complete and traceable

**BLOCK**
- story starts blocked
- secret in context

**Salida / autorización**
- autoriza GSDLC-09-B


### GSDLC-09-B — Code/file workspace viewer-editor

**Objetivo.** Permitir creación/edición manual de código desde UI dentro del workspace.

**Entradas obligatorias**
- GSDLC-09-A PASS

**Actividades**
1. Implementar bounded source tree y text editor.
2. Permitir create/edit/rename de archivos allowlisted por project policy.
3. Separar draft/change buffer de source hasta apply.
4. Mostrar external edit/revalidation/conflict.
5. Aplicar syntax/language hints sin convertir editor en IDE completo.

**Entregables verificables**
- CodeWorkbench
- SourceDraftBuffer
- bounded file API

**Pruebas / validadores**
- path traversal
- binary/oversize
- concurrent edit
- outside root

**Evidencia mínima**
- code_workbench_security_report.json

**Seguridad operacional específica**
- workspace root enforcement
- hidden/secret files excluded
- no arbitrary executable upload

**PASS**
- manual source authoring UI
- no direct uncontrolled write

**BLOCK**
- path escape
- draft modifies source before approval

**Salida / autorización**
- autoriza GSDLC-09-C


### GSDLC-09-C — Change plan, diff, dry-run, approval and atomic apply

**Objetivo.** Aplicar cambios de código como operación tipada y reversible.

**Entradas obligatorias**
- GSDLC-09-B PASS

**Actividades**
1. Construir immutable SourceChangePlan.
2. Mostrar full diff y Test Impact preview.
3. Calcular risk y required approval role.
4. Revalidar preimage hashes antes de apply.
5. Aplicar multi-file atomically o rollback completo.

**Entregables verificables**
- SourceChangePlan schema/service
- source apply/rollback service

**Pruebas / validadores**
- stale preimage
- fault injection
- partial apply
- wrong role
- unexpected path

**Evidencia mínima**
- change_plan.json
- apply_manifest.json
- rollback_evidence.json

**Seguridad operacional específica**
- backup preimages
- no generic shell/patch arbitrary
- exact path allowlist

**PASS**
- all writes match approved plan
- rollback clean

**BLOCK**
- partial residue
- stale diff applied
- unapproved path

**Salida / autorización**
- autoriza GSDLC-09-D


### GSDLC-09-D — Coding and Test agents

**Objetivo.** Añadir asistencia agentic a plan/código/tests sin self-apply.

**Entradas obligatorias**
- GSDLC-09-C PASS
- GSDLC-07 agent framework

**Actividades**
1. Integrar CodingAgent para implementation plan/patch proposal.
2. Integrar TestAgent para test proposal/generation.
3. Usar StoryContextPack+RAG.
4. Mostrar model, cost, diff y provenance.
5. Requerir decisión humana antes de insertar/aplicar.
6. Resolver modelos exclusivamente vía Model Gateway; el Coding/Test agent no depende directamente de SDK/provider.
7. Registrar por propuesta `model_id`, `provider_id`, `access_route_id`, `agent_session`, `trace_id` y `ToolIntent`.
8. Toda mutación de archivos debe terminar en `ToolExecutionDecision`/`SourceChangePlan` determinista y approval-bound; nunca heredar permiso desde la ruta/modelo.

**Entregables verificables**
- CodingAgent binding
- TestAgent binding
- code assist UI
- agent_tool_execution_decision trace binding

**Pruebas / validadores**
- mock/local proposal
- tool scope
- unsafe output
- budget
- accept/reject

**Evidencia mínima**
- coding_agent_traces.json
- test_agent_traces.json

**Seguridad operacional específica**
- agent cannot apply/commit/approve itself
- bounded tokens/tools

**PASS**
- proposal only
- human-reviewed diff
- cost/provenance complete

**BLOCK**
- self-apply
- self-commit
- unknown tool
- model-route-to-file-write escalation
- forbidden filesystem.delete intent remains blocked

**Salida / autorización**
- autoriza GSDLC-09-E


### GSDLC-09-E — Story-level browser acceptance and rollback

**Objetivo.** Demostrar una story real hasta CHANGES_READY desde UI.

**Entradas obligatorias**
- GSDLC-09-D PASS

**Actividades**
1. Ejecutar fixture story por ruta manual y agent-assisted.
2. Aplicar change plan.
3. Probar rollback y conflict por external edit.
4. Verificar Project Status/Story state.
5. Ejecutar focal no-regression previa a quality integration.

**Entregables verificables**
- story_workbench_browser_acceptance
- story change evidence

**Pruebas / validadores**
- real browser
- rollback
- source hash parity
- focal tests

**Evidencia mínima**
- screenshots
- diff/apply/rollback manifests

**Seguridad operacional específica**
- unexpected writes scan
- no commit aún salvo fixture isolated

**Cierre de regresión obligatorio**
- ejecutar gates baratos + Contract Reconciliation Sweep + browser/capability acceptance;
- consumir la única full regression del backlog exactamente una vez, salvo que un hard-trigger anterior ya haya consumido esa corrida;
- ante FAIL no repetir full: aplicar recuperación compuesta selectiva y Historical Regression Guard.

**PASS**
- story reaches CHANGES_READY
- UI-complete
- S0/S1=0

**BLOCK**
- operator writes source
- untracked unexplained files

**Salida / autorización**
- CLOSED/PASS
- autoriza GSDLC-10


## 7. Alcance transversal específico de esta ola

- Filesystem writes se expresan como capability project-scoped typed, no como `filesystem_write_allowed=true` global.
- La selección de modelo/provider no confiere autoridad de escritura: `ModelRouteDecision != ToolExecutionDecision`.
- External IDE continúa soportado y reconciliado.

## 8. Política de contratos históricos específica

- Campos históricos globales que declaraban source mutation false pertenecen a hitos anteriores; successor tests deben scopear nueva capacidad approval-bound, no reescribir el pasado.
- Reutilizar patrones UOC-005 para atomic apply con risk policy distinta.

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

- Source mutation, path escape, stale diff, malicious generated code, concurrency y rollback son críticos.

Toda acción mutante debe seguir `plan → dry-run → policy/RBAC → approval cuando aplique → execute → verify → evidence`. Cualquier excepción requiere ADR o backlog correctivo separado.

## 10. Estrategia de pruebas de la ola

- story state
- path security
- change plan
- atomic apply
- agent eval
- browser

Regla de regresión:

- A→D usan Test Impact, pruebas focales, acumulativas y validadores determinísticos; **full regression = NO por rutina**.
- El micro-sprint E ejecuta la **única full regression del backlog exactamente una vez**, después de gates baratos, Contract Reconciliation Sweep y browser/capability acceptance pertinente.
- Una full intermedia solo puede ocurrir por hard trigger de riesgo explícito, owner-approved y documentado; si ocurre, **consume la única corrida full permitida** y E debe cerrar mediante evidencia compuesta sin lanzar otra.
- Si la full falla: preservar log/JUnit/marker inmutables, prohibir rerun, diagnosticar causa, ejecutar exact failed-nodeid retest + bounded impacted retest + Historical Regression Guard y cerrar solo con `composite-full-regression-selective-retest = PASS`.
- Browser acceptance se ejecuta únicamente cuando el micro-sprint introduce/cierra UX; no se repite por correctives que no cambian comportamiento browser demostrado.

## 11. Evidencia autoritativa esperada

- context pack
- agent route/tool-decision trace
- diff plan
- approval/apply manifest
- rollback evidence
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

- manual+agent code proposal
- governed apply
- rollback
- S0/S1=0

El backlog solo puede adjudicarse `CLOSED/PASS` si todos los micro-sprints A→E han cerrado en secuencia y no quedan S0/S1 abiertos.

## 13. Criterio de autorización del siguiente backlog

- GSDLC-10 solo si source changes están bounded y reproducibles.

Un `PASS-WITH-GAPS` solo puede autorizar el siguiente backlog cuando los gaps estén clasificados S2/S3, tengan owner, evidencia y no invaliden la invariante de producto de esta ola.

