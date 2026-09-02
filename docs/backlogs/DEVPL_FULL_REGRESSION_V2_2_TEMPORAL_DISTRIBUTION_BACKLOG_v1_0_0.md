---
doc_id: "DEVPL-FULL-REGRESSION-V2-2"
title: "Full Regression v2.2 — Intelligent temporal distribution and incremental documentation consistency"
status: "closed"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-09-02"
approval: "approved_by_owner"
source_repo: "repo_DevPilot_Local_386_DEVPL_GSDLC_07_E_AGENTIC_PRECODE_MODEL_EVALS_WINDOWS_VALIDATED_CANDIDATE.zip"
source_commit: "17db6b219f5066f2df91d897a0e3ad62314a0176"
full_regression_budget: "1 logical full in v2.2-D only"
parallel_workers: 1
---
# Full Regression v2.2 — Backlog

## Objetivo

Reducir la imprevisibilidad, el tail de shards y el costo de recuperación de la full regression mediante distribución temporal basada en telemetría real, **sin introducir paralelismo todavía**. Simultáneamente mover la reconciliación documental desde un gate tardío a un mecanismo incremental que impida consumir una full con drift determinista abierto.
 
## Invariantes

- coverage no se reduce;
- collection/fingerprint permanecen sellados;
- worker count = 1;
- no xdist requerido;
- no network/API externa;
- no segunda full;
- historical contracts no se reescriben;
- P0/P1 documentation drift = 0 antes de full-start.

## Micro-sprints

### FRX-v2.2-A — Documentation consistency foundation

**Objetivo:** reconciliar el S2 post-cierre de GSDLC-07 y crear validación incremental.

**Entregables:**
- `ClosureStateConsistencyValidator`;
- `DocumentationAuthorityGraph`;
- `DocImpactPlanner`;
- `DocumentationDriftLedger`;
- `DerivedMetadataProjection`;
- reconciliación successor de backlog/README/Source Registry/adjudicación final.

**Reglas:**
- proposal histórico no se reescribe;
- current-active y historical-freeze quedan separados;
- counters/summaries derivados desde registries vivos;
- todo changed-path produce doc-impact y contract-impact antes de tests.

**PASS:** drift P0/P1=0; focal governance PASS; no full.

### FRX-v2.2-B — NodeDurationRegistry and estimator

**Objetivo:** convertir las 2.805 muestras existentes en estimaciones reproducibles.

**Entregables:**
- `NodeDurationRegistry` con nodeid + environment fingerprint;
- median, p95, EWMA/robust estimate, sample_count, last_seen;
- cold/warm classification cuando sea demostrable;
- ingestion idempotente de telemetry handoff;
- schema + CLI preview.

**PASS:** 100% de muestras válidas o explícitamente rejected; no scheduler enabled; no full.

### FRX-v2.2-C — Duration-balanced sequential scheduler

**Objetivo:** reemplazar count-sharding por planificación temporal determinística en shadow/canary.

**Diseño:**
- LPT/bin-packing determinístico;
- slow singleton cuando estimate exceda target;
- límites `max_nodeids` y `max_command_chars` preservados;
- cold-start: stable nodeid order + bounded count/chars;
- target shard seconds configurable, default inicial 300 s;
- mismo collection SHA y accounting.

**Validación:** comparar plan count-based histórico vs temporal sin ejecutar dos fulls; ejecutar canary focal representativo.

**PASS:** predicted max shard y dispersion mejoran; 0 duplicados/omisiones; workers=1.

### FRX-v2.2-D — Windows adoption and one-full benchmark

**Objetivo:** ejecutar la única full v2.2 con scheduler temporal secuencial y decidir adopción.

**PASS funcional:** 100% terminal accounting, no source drift, resume solo UNEXECUTED, no second full.

**PASS performance:** respecto a baseline 07-E, reducir significativamente max shard/p95 shard y overhead de recuperación; toda desviación debe quedar cuantificada. La adopción puede ser `PASS/ENABLED` o `PASS/AVAILABLE-NOT-DEFAULT` si la seguridad/correctitud pasa pero la mejora no alcanza el umbral owner definido.

## Documentation Drift Gate

Debe ejecutarse antes de collection y nuevamente antes de adjudication. Full-start queda BLOCK si:
- backlog status, Project State, README, Source Registry, changelog y closure adjudication discrepan;
- derived counters no coinciden con live registries;
- historical test lee current-active cuando existe snapshot;
- runtime-ephemeral entra a fixture/candidate.

## Riesgos

v2.2 no puede reducir a la mitad el costo computacional total porque sigue siendo secuencial. Su valor es balance, predictibilidad, menos timeouts/restarts y la base estadística para v2.3.

## Corrective adjudication — FRX-v2.2-D Windows attempt 1/1

La única full D fue consumida y terminó `2795 PASS / 44 FAIL / 0 ERROR / 5 SKIP`, 100% accounted. No se autoriza segunda full. El scheduler temporal mejoró max/p95 de shard, pero el runner introdujo un overhead oculto crítico por fingerprint Git per-file antes/después de cada shard. D debe cerrarse únicamente mediante composite/selective recovery después del corrective de source guard y métricas end-to-end. La adopción default queda deshabilitada; resultado objetivo seguro: `PASS/AVAILABLE-NOT-DEFAULT`.

## Windows composite recovery closure

FRX-v2.2-D closed `PASS` by preserving the single full 1/1 and resolving its exact 44 failed nodeids through a bounded chain: v1.0.4 = 31 PASS/13 FAIL, v1.0.6 = residual 13/13 PASS. `second_full=false`. Temporal scheduling remains `PASS/AVAILABLE-NOT-DEFAULT`. The Git hot-path corrective is retained and sequential shards are coarsened to 900 s, but RUN-06 exposed a remaining P0 test-suite duplication gap: eight binding tests rerun the same hardening/industrial QualityGate and consumed 92.7% of the 13-test residual wall time. FRX-v2.3-A is authorized only with that deduplication as its first entry prerequisite before any parallel canary.
