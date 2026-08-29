---
doc_id: "DEVPL-GSDLC-07-E-PROMPT"
title: "DEVPL-GSDLC-07-E — Agentic pre-code browser acceptance and model evals — closing prompt"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-08-28"
approval: "approved_by_owner"
source_policy: "owner-adjudicated-07-D-successor"
validation_policy: "one-logical-full-session-v2/completion-first/no-second-full"
full_regression_architecture: "DEVPL_TESTING_FULL_REGRESSION_EXECUTION_V2_ARCHITECTURE_v1_0_0.md"
---

# 1. Misión

Cerrar **GSDLC-07-E — Agentic pre-code browser acceptance and model evals** y, si procede, el backlog DEVPL-GSDLC-07.

# 2. Entrada

Resolver predecessor exclusivamente desde la adjudicación final 07-D. Verificar A→D `CLOSED/PASS` o owner-adjudicated `PASS-WITH-GAPS` admisible, sin S0/S1.

# 3. Producto a demostrar

Completar un journey Product Vision → PRE_CODE_READY con asistencia agentic en pasos seleccionados y manual route preservada.

La UI debe mostrar:
- agent role/runtime;
- model/provider/access-route;
- sources/citations;
- tokens/cost/budget;
- ToolIntent;
- Policy/RBAC/Approval decision;
- handoffs;
- human accept/reject/modify;
- fallback y límites.

`Usar agente` produce draft/proposal revisable; nunca auto-approval.

Mock/local mandatory. API externa real opcional, cost-controlled y no requisito de PASS.

# 4. Pre-Full gates

Antes de crear marker:
- Test Impact final;
- Historical Contract Sweep;
- Contract Reconciliation Sweep;
- Documentation Governance;
- Project State;
- TCR v1/v2;
- API/UI capability/route parity;
- Secret differential scan;
- runtime-ephemeral cleanup;
- browser acceptance;
- groundedness;
- MIASI/tool policy;
- cost/provenance parity;
- S0/S1=0.

Si un gate barato falla, **no crear full marker**.

# 5. Browser acceptance

Ejecutar únicamente casos que cierren UX de 07-E más los invariantes de A-D que hayan cambiado. Reutilizar screenshots previos solo con byte/runtime-equivalence receipt.

Usar exactamente tres consolas:
1. operador/control;
2. API foreground;
3. UI foreground.

No background/detached.

Cada caso sensible debe tener:
- screenshot;
- machine receipt del resultado relevante;
- nota manual consistente con la imagen.

No aceptar el patrón observado en 06-E donde una nota declara 403 y la captura muestra API-down.

# 6. Logical Full Regression Session v2

## 6.1 Plan

1. congelar source commit/fingerprint;
2. registrar environment fingerprint;
3. `pytest --collect-only` una vez;
4. materializar `collection_nodeids.txt` + SHA;
5. construir shard plan estable usando historial de duración;
6. crear marker `attempt=1`, `max_attempts=1`, `rerun_allowed=false`.

## 6.2 Ejecución

- ejecutar todos los shards planificados;
- ordinary FAIL/ERROR se registra, pero no detiene los shards restantes;
- JUnit + log + JSON receipt por shard;
- guardar terminal outcome por nodeid;
- watchdog por shard, no timeout monolítico de varias horas;
- no patch de source hasta terminar el plan.

## 6.3 Resume

Ante interrupción de infraestructura:
- comprobar source/environment fingerprint idénticos;
- reanudar solo `UNEXECUTED/INFRA_ABORT`;
- no reejecutar PASS/FAIL/ERROR/SKIP terminales;
- sigue siendo la misma logical session.

Si el source cambió, congelar la sesión y pasar a composite; no iniciar una nueva full.

## 6.4 Adjudicación

Si todos los nodeids terminales son PASS o skip aprobado: full PASS.

Si existen FAIL/ERROR:
- preservar full original;
- diagnosticar todas las causas juntas;
- aplicar corrective;
- ejecutar exact failed-nodeids + bounded impacted + cualquier uncovered tail + Historical Regression Guard;
- `composite-full-regression-selective-retest` debe cubrir 100%;
- segunda full prohibida.

# 7. Evals obligatorios

- mock;
- fake/local;
- optional external fake;
- groundedness;
- tool injection;
- forbidden tool containment;
- cost budget/hard-stop;
- handoff trace;
- acceptance/rejection/modification rates;
- fallback.

# 8. Evidencia

- agentic_precode_acceptance.md
- model_task_eval_matrix.json
- ai_control_center_acceptance.md
- screenshots + machine receipts
- traces
- citations
- cost ledger
- approval records
- full session manifest/shard plan/ledger
- JUnit/log/receipt por shard
- aggregate full report
- composite report si aplica
- candidate/evidence SHA+CRC
- official 3-state review

# 9. PASS

- governed agent-assisted route;
- manual route intacta;
- citations/cost/provenance visibles;
- ToolIntent separado de execution authority;
- limits server-side;
- S0/S1=0;
- browser PASS;
- full logical coverage 100% o composite recovery 100%;
- no second full.

# 10. BLOCK

- auto-approval;
- tool executes without deterministic decision;
- hidden model/cost/source;
- unbounded loop;
- source changes mid-session without freezing evidence;
- stop-on-first-test-failure que deje coverage desconocida;
- second full;
- secret/runtime store in candidate.
