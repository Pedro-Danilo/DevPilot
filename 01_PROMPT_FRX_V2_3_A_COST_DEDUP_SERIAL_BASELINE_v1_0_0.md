---
doc_id: "01_PROMPT_FRX_V2_3_A_COST_DEDUP_SERIAL_BASELINE_V1_0_0"
title: "FRX-v2.3-A — Cost de-duplication and normalized serial baseline — implementation and Windows validation prompt"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-09-02"
approval: "approved_by_owner"
source_repo: "repo_DevPilot_Local_391_FRX_V2_2_D_COMPOSITE_RECOVERY_WINDOWS_VALIDATED_CANDIDATE.zip"
source_commit: "94a457748d7a1e1a33a203421efff4f83f459807"
full_regression_policy: "no full regression; focal/impact only"
parallel_workers: 0
---
# FRX-v2.3-A — Cost de-duplication and normalized serial baseline — Prompt

## 1. Misión

Eliminar trabajo redundante demostrado por FRX-v2.2-D y establecer una baseline serial normalizada antes de implementar cualquier aislamiento o paralelismo.

Este micro-sprint es P0. No debe iniciarse TestIsolationRegistry ni workers hasta cerrarlo.

## 2. Fuente y evidencia obligatoria de entrada

Entrada autoritativa:

- repo391 Windows validated candidate;
- commit `94a457748d7a1e1a33a203421efff4f83f459807`;
- composite recovery `44/44 PASS`, full `1/1`, `second_full=false`;
- RUN-06 residual JUnit con `13 passed in 3162.37s`;
- ocho binding tests = `2931.421 s / 92.7352%`;
- scheduler v2.2 `PASS/AVAILABLE-NOT-DEFAULT`;
- `performance_gap_status=OPEN/P0/QUALITY-GATE-BINDING-DEDUP`.

## 3. Problemas que deben resolverse

### 3.1 Binding vs execution

Los tests que solo verifican composición/registro de QualityGate no pueden ejecutar todo el aggregate profile.

Implementar una API pública determinística read-only, por ejemplo `QualityGate.describe_plan()` / `QualityGatePlan`, que exponga como mínimo:

- profile;
- ordered subgate ids;
- criticality;
- canonical component key;
- aggregate relationships;
- execution mode;
- duplicate-component projection.

La API de plan no ejecuta ningún runner.

Refactorizar los binding-only tests identificados y auditar todos los tests que invoquen `QualityGate.run()`. Los tests semánticos deben ejecutar únicamente el subgate que validan, salvo una pequeña allowlist de pruebas canónicas de aggregate execution.

### 3.2 Aggregate DAG de una sola invocación

Un top-level `hardening`/`industrial` no debe reejecutar el mismo componente por aparecer directo y dentro de otro aggregate.

Introducir un execution context explícito scoped a una sola llamada top-level. Puede reutilizar un resultado únicamente si:

- canonical component key coincide;
- inputs/options relevantes coinciden;
- source identity coincide;
- la reutilización queda registrada en el receipt/trace.

No cache global persistente. No reusar resultados entre commits o procesos por defecto.

Corregir al menos:

- duplicación de seis componentes UI/API por `ui-api-local-hardening`;
- solapamientos de `local-release-candidate` con Docs Governance, TCR, Production Ready y UI/install cuando la invocación superior ya disponga de esos resultados.

Los aggregate gates standalone deben seguir funcionando cuando no reciben context previo.

### 3.3 Release Candidate test de-duplication

Conservar una prueba canónica de `LocalReleaseCandidateReporter.run()` end-to-end. Separar:

- schema/serialization;
- CLI registration/dispatch;
- TCR/impact binding;
- QualityGate membership;

de la ejecución integral para que no vuelvan a correr todo el RC aggregator.

### 3.4 Source seal Git bounded

El hot path v2.2 ya usa cheap guard, pero el source seal/fallback conserva per-file `git hash-object`.

Para un Git worktree clean:

- sellar identidad por commit + semantic clean state, o primitive Git batch equivalente;
- cero subprocess Git por archivo;
- dirty `git-semantic-clean-guard` debe producir BLOCK inmediato, no full-tree rehash;
- fallback fuerte solo cuando el cheap guard no está disponible y debe ser batch/bounded;
- instrumentar `git_processes_total`, `strong_fingerprint_fallbacks`, `source_guard_seconds`.

### 3.5 Serial shard coarsening sin command-line coupling

El estado actual default-disabled vuelve a count50 (~57 procesos para 2844 nodeids). El temporal 900s sigue limitado por `max_nodeids=50`; `max_command_chars=7000` también fuerza fragmentación.

Implementar nodeid manifest / pytest args-file / mecanismo equivalente para que los nodeids no deban materializarse todos en la línea de comando.

Mantener:

- live append/flush de per-node outcomes;
- resume solo UNEXECUTED;
- timeout con progreso preservado;
- exact collection identity.

Construir shadow serial plans contra la colección v2.2 y una colección current recalculada focalmente. No ejecutar full.

### 3.6 Normalized serial baseline

Crear `NormalizedSerialBaselineReport` que separe:

- node runtime histórico;
- duplicate aggregate cost eliminado/estimado;
- process startup/pytest overhead;
- source guard overhead;
- projected coarse serial orchestration;
- uncertainty/confidence;
- historical observed wall-clock v2.2 como referencia separada.

No atribuir futuros ahorros de A al paralelismo.

## 4. Validación focal obligatoria

1. Replay únicamente de los ocho binding tests RUN-06 después del refactor.
2. Una prueba canónica hardening y, si es necesario, una industrial para demostrar semántica real y execution-context de-dup.
3. Tests directos de cada subgate refactorizado cuando su semántica deba preservarse.
4. RC canonical execution una vez + pruebas estructurales baratas.
5. Source seal fixtures clean/dirty/fallback/no-git.
6. Shadow serial planner sobre collection v2.2; no tests ejecutados por ese shadow.
7. Contract que impida `binding-only -> aggregate .run()` fuera de allowlist.
8. DocumentationDriftGate/Docs Governance/Project State/TCR solo si realmente impactados.

## 5. PASS

- 8 binding tests RUN-06 reducen wall-clock agregado >=80% en Windows respecto de `2931.421 s`, salvo adjudicación owner explícita;
- 0 binding-only aggregate executions fuera de allowlist;
- 0 duplicate canonical component executions no justificadas en una invocación hardening/industrial;
- RC final conserva una ejecución integral canónica; pruebas de schema/CLI/binding no vuelven a ejecutar todo el RC;
- per-file Git subprocesses = 0 en Git-clean source seal y hot path;
- strong fallback hot-path = 0 en caso nominal;
- shadow serial process/shard count reduce >=60% vs count50 y conserva collection exactamente una vez;
- normalized serial baseline emitida con dual-baseline policy;
- workers=0;
- full=0;
- network/external APIs/browser=0 salvo cambio explícito de alcance, que este micro-sprint debe evitar.

## 6. BLOCK

- introducir cache global para “acelerar” sin identidad de inputs;
- eliminar la única prueba canónica de aggregate semantics;
- cualquier pérdida de cobertura/binding;
- dirty source dispara rehash masivo en vez de BLOCK;
- nodeid manifest pierde/duplica items;
- workers>0;
- full ejecutada;
- speedup claim basado solo en tiempo de testcases o receipts parciales.

## 7. Ingeniería del operador Windows

Un único operador Python resumible. Debe evitar cadenas largas de PowerShell; PowerShell solo invoca fases de alto nivel. No repetir gates terminales ya acreditados. No browser. Packaging desde Git limpio y promoción three-state solo tras PASS.

## 8. Evidencia

- binding cost before/after;
- aggregate execution graph/trace;
- duplicate component report;
- RC execution multiplicity report;
- Git process/source seal metrics;
- serial shadow plan comparison;
- normalized serial baseline report;
- focal JUnit/logs/receipts;
- full_runs_consumed=0.

## 9. Salida

Autoriza FRX-v2.3-B — Isolation contract registry.

Commit sugerido: `perf(frx-v2.3): deduplicate regression gates and normalize serial baseline`.
