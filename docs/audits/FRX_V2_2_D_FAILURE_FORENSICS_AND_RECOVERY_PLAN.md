---
doc_id: "FRX-V2-2-D-FAILURE-FORENSICS-RECOVERY"
title: "FRX-v2.2-D — Failure forensics, performance corrective and selective recovery plan"
status: "approved-corrective"
version: "1.0.1"
owner: "Ordóñez"
updated: "2026-09-02"
approval: "residual-corrective-v1.0.5"
---
# FRX-v2.2-D — Failure forensics and recovery

## 1. Estado autoritativo del intento
La única logical full `FRX-V2-2-D-FULL-01` quedó consumida `1/1`: collection 2.844, accounting 2.844/2.844, PASS 2.795, FAIL 44, ERROR 0, SKIP_APPROVED 5, UNEXECUTED 0, INFRA_ABORT 0, workers=1, second_full=false. El resultado no autoriza otra full.

## 2. Forense temporal
- primer shard: `2026-09-01T12:16:56Z`;
- último shard: `2026-09-01T22:33:28Z`;
- wall-clock observado: 36.992 s = 10,276 h;
- suma `duration_seconds` de receipts: 16.546,17 s = 4,596 h;
- tiempo no contabilizado por receipts: 20.445,83 s = 5,679 h = 55,27% del wall-clock;
- gap inter-shard mediano: 282 s; máximo: 486 s.

El benchmark original contabilizó ~582,29 s de overhead dentro de los procesos pytest, pero omitió los ~20.446 s entre receipts. Por ello su `performance_threshold_pass=true` no era suficiente para una decisión de adopción.

## 3. Causa raíz de rendimiento
`_execute_shard()` ejecutaba `_source_descriptor()` antes y después de cada shard. En worktrees Git, `_git_semantic_source_descriptor()` enumeraba todos los archivos y `_git_semantic_blob_hash()` lanzaba `git hash-object` por archivo. Con 72 shards y ~3.530 archivos, el orden de magnitud es 72 × 2 × 3.530 = 508.320 procesos Git. Los dos fingerprints estaban fuera del cronómetro del receipt.

La fragmentación de pytest existe —72 startups, plugin loading, imports, JUnit y fixtures—, pero su costo medido es secundario frente al rehash Git per-file. La hipótesis de “mucha fragmentación” se confirma parcialmente: la fragmentación amplifica el defecto, pero el factor dominante fue el guard de integridad O(shards × files).

## 4. Causas raíz funcionales de los 44 FAIL
Los 44 FAIL se agrupan en contratos acumulativos comunes, no en 44 defectos independientes:
1. `Project State` y Documentation Registry mezclaron punteros globales FRX con punteros GSDLC congelados.
2. `local_release_candidate_criteria.json` conservó repo386 mientras `current_repo` ya era repo389.
3. `command_ownership_matrix.json` quedó en 199 comandos mientras el registry vivo llegó a 206.
4. El helper de ranking histórico no aceptaba `FRX-v2.2-D`.
5. Tests históricos todavía asumían que el puntero global mutable debía seguir exactamente en `DEVPL-GSDLC-07-E` o que todo successor repo debía pertenecer al namespace `DEVPL_GSDLC`.
6. Metadatos de seguridad de cinco comandos FRX declarativos no marcaban `writes_files=true` pese a su side-effect contract histórico.
7. El contador de full FRX seguía en 0 aunque la única full ya estaba consumida.

## 5. Corrective aplicado
- separación explícita de `gsdlc_*` y `frx_*`;
- freshness del release candidate enlazado al current repo vivo;
- ranking FRX monotónico;
- ownership matrix regenerada desde registry vivo (206);
- metadatos CLI conservadores;
- source guard Git-semántico acotado;
- instrumentación de lifecycle y wall-clock end-to-end;
- `target_shard_seconds=900` y scheduler `AVAILABLE-NOT-DEFAULT`;
- evolución de contratos históricos solo donde leían autoridad mutable equivocada.

## 6. Selective/composite recovery
La recuperación autorizada reutiliza la evidencia terminal original 2.795 PASS + 5 SKIP_APPROVED y vuelve a ejecutar únicamente:
- los 44 nodeids FAIL originales;
- tests focales del corrective de full runner/benchmark;
- contratos de Project State, Docs Governance, TCR v1/v2, CLI registry y Historical Regression Guard acotado.

No se ejecuta `pytest -q` global. La evidencia original permanece inmutable y la adjudicación final debe declarar explícitamente `original_full=FAIL`, `second_full=false`, `composite_recovery=PASS|BLOCK`.

## 7. Adopción v2.2
V2.2 no se desmonta. A/B conservan valor directo; C queda disponible en shadow/opt-in. D no habilita el scheduler como default con la evidencia actual. El cierre seguro, si la recovery pasa, es `PASS/AVAILABLE-NOT-DEFAULT`.

## 8. PASS/BLOCK
PASS de recovery: 44/44, bounded corrective PASS, Project State PASS, Documentation Governance PASS, TCR v1/v2 PASS, CLI ownership PASS, source clean, full runs=1, second_full=false.  
BLOCK: cualquier segundo full, nuevo FAIL fuera del bounded impact sin adjudicación, source drift, o claim `PASS/ENABLED` basado en el benchmark incompleto anterior.

## RUN-04 residual selective-recovery findings (v1.0.4)

Windows recovery v1.0.4 executed the exact 44 original failed nodeids in one pytest process. Accounting was `31 PASS / 13 FAIL / 0 ERROR / 0 SKIP`; no second full was executed. The 13 residual failures collapse to three causal groups:

1. **Environment readiness gap:** seven UI/API hardening subgates raised `ModuleNotFoundError: fastapi` because the Python interpreter selected by the operator lacked the already-declared optional API/dev dependencies. This is an environment-selection/provisioning defect in the recovery operator, not a product regression.
2. **Historical schema namespace gap:** `LocalReleaseCandidateCriteria` accepted POST-H, GSDLC and FULL-REGRESSION identifiers but not the live `FRX-v2.2-D` namespace used by `expected_next_micro_sprint`.
3. **CLI compatibility drift:** the five new FRX-v2.2 duration/scheduler commands are high-risk in the live ownership matrix and therefore require explicit `cli-compat:*` contracts; v1.0.4 regenerated ownership but did not extend compatibility fixtures.

Recovery v1.0.5 must preserve the 31 PASS receipts from RUN-04 and retest only the 13 still-failed nodeids. Composite terminal accounting is valid only when the union of RUN-04 PASS nodeids and RUN-05 PASS nodeids equals the exact original 44-nodeid failure set. The operator must select a Python interpreter with `pytest`, `jsonschema`, `fastapi`, `starlette`, `pydantic` and `httpx` before executing any residual test.

