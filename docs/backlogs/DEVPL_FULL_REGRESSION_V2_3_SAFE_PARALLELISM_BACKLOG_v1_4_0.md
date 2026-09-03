---
doc_id: "DEVPL-FULL-REGRESSION-V2-3"
title: "Full Regression v2.3 — Cost de-duplication, isolation evidence, normalized serial baseline and safe bounded parallelism"
status: "approved"
version: "1.4.0"
owner: "Ordóñez"
updated: "2026-09-03"
approval: "approved_by_owner"
predecessor: "DEVPL-FULL-REGRESSION-V2-2/CLOSED-PASS"
source_repo: "repo_DevPilot_Local_391_FRX_V2_2_D_COMPOSITE_RECOVERY_WINDOWS_VALIDATED_CANDIDATE.zip"
source_commit: "94a457748d7a1e1a33a203421efff4f83f459807"
full_regression_budget: "1 logical full in v2.3-E only"
default_parallel_safe: false
initial_workers: 0
first_micro_sprint: "FRX-v2.3-A"
cost_deduplication_required_before_parallelism: true
---
# Full Regression v2.3 — Backlog

## 1. Objetivo

Reducir de manera material y atribuible el costo end-to-end de la full regression en dos pasos ordenados:

1. **eliminar primero trabajo redundante y normalizar la ejecución serial**;
2. introducir paralelismo únicamente para tests con aislamiento demostrado y solo si el costo residual lo justifica.

V2.3 no puede acelerar duplicación accidental. El paralelismo se considera una optimización posterior a la eliminación de repetición in-process, agregados solapados, procesos Git innecesarios y fragmentación serial artificial.

## 2. Autoridad de entrada

FRX-v2.2 queda cerrado `CLOSED/PASS` por composite recovery:

- full lógica original: `2795 PASS / 44 FAIL / 0 ERROR / 5 SKIP / 2844 accounted`, preservada;
- selective recovery: `31 + 13 = 44/44 PASS`;
- logical full runs: `1/1`;
- `second_full=false`;
- scheduler temporal: `PASS/AVAILABLE-NOT-DEFAULT`;
- commit Windows validado: `94a457748d7a1e1a33a203421efff4f83f459807`.

La evidencia RUN-06 mostró que 13 tests ejecutados en **una sola instancia pytest** tardaron `3162.37 s`; ocho tests de binding que ejecutaban perfiles completos `hardening/industrial` consumieron `2931.421 s`, equivalentes a `92.7352%` del tiempo de ese retest.

## 3. Gaps P0/P1 heredados que V2.3-A debe cerrar

### P0-01 — Binding tests ejecutan agregados completos

Tests cuyo objetivo es demostrar que un subgate está registrado/consumido ejecutan `QualityGate(...).run()` completo. Los ocho casos demostrados por RUN-06 consumieron 48m51s.

### P0-02 — Agregados anidados duplican componentes en una misma ejecución

`hardening` contiene 46 subgates. Algunos agregados vuelven a ejecutar checks ya presentes:

- `ui-api-local-hardening` ejecuta nuevamente seis checks UI/API que también aparecen como subgates directos;
- `local-release-candidate` vuelve a ejecutar Evidence Freshness, Production Ready Final, Docs Governance, TCR v1/v2, UI/API smoke e install smoke, varios solapados con la superficie hardening;
- el perfil `industrial` amplía una superficie hardening ya costosa.

No se admite cache global opaca. La reutilización, si aplica, debe ser explícita, determinística y **scoped a una única invocación top-level**.

### P0-03 — Repetición del Release Candidate aggregator en tests

RUN-06 evidencia cuatro tests RC que consumieron aproximadamente 44–45 s cada uno y un closure RC de ~50.6 s. Debe existir una sola prueba canónica de ejecución integral; schema, serialization, CLI registration y QualityGate binding deben verificarse sin volver a ejecutar todo el aggregator.

### P0-04 — Strong Git fingerprint aún conserva hash per-file

El hot path v2.2-D ya usa `git-semantic-clean-guard` y elimina la tormenta per-shard. Sin embargo `_git_semantic_source_descriptor()` conserva `git hash-object` por archivo para el source seal inicial y fallback. En Git limpio, la identidad debe sellarse con commit + clean semantic state o una operación Git batch; el fallback no puede reintroducir miles de procesos.

### P0-05 — Fragmentación serial sigue estructuralmente alta

`scheduler_enabled=false` devuelve el plan normal a count-sharding de 50 nodeids. Para la colección sellada de 2844 tests esto implica ~57 procesos pytest. Incluso `target_shard_seconds=900` con `max_nodeids=50` proyecta 57 shards. El límite de `max_command_chars=7000` también restringe el coarsening.

Shadow analysis sobre la colección v2.2-D:

| Política | Shards proyectados |
|---|---:|
| count-based / 50 | ~57 |
| temporal 900s / max 50 / 7000 chars | 57 |
| temporal 900s / max 100 / 7000 chars | 44 |
| temporal 900s / max 200 / 14000 chars | 22 |
| temporal 900s / max 200 / 30000 chars | 15 |

V2.3-A debe eliminar el command-line-length coupling mediante nodeid manifest/args-file o mecanismo equivalente, manteniendo exact accounting y receipts por nodeid.

### P0-06 — Baseline contaminado para atribuir speedup paralelo

La full observada v2.2 incluye overhead que A corregirá. Comparar directamente una full paralela posterior contra las 10.27 h observadas atribuiría al paralelismo mejoras producidas por de-dup y serial coarsening.

V2.3 debe mantener dos baselines:

- **historical operational baseline**: wall-clock observado v2.2 para mostrar mejora total al usuario;
- **normalized serial baseline**: mismo código ya de-duplicado, source guard corregido y serial planner normalizado; este baseline es la autoridad para atribuir speedup al paralelismo.

### P1-01 — Riesgo de fallback fuerte silencioso

Todo fallback desde el cheap Git guard debe quedar contado. En el camino normal Git-clean se espera `strong_fingerprint_fallbacks=0` durante ejecución de shards. Un dirty guard debe BLOCK directamente; no debe disparar hashing masivo para “confirmar” el drift.

## 4. Principios v2.3

- de-dup antes de parallel;
- `parallel_safe=false` por defecto;
- duración/nombre nunca autoriza paralelismo;
- ningún worker usa shell;
- full coverage y accounting siguen siendo globales;
- receipts terminales son sticky;
- no hidden/global cache para maquillar costo;
- reutilización de resultados solo dentro de un execution context explícito y con component identity estable;
- fallback secuencial seguro para unknown/conflicting;
- no dependencia obligatoria de xdist;
- comparar wall-clock end-to-end, no solo suma de node durations;
- una única full v2.3, exclusivamente en E.
 
## 5. Micro-sprints

### FRX-v2.3-A — Cost de-duplication and normalized serial baseline

Eliminar los gaps P0 anteriores antes de estudiar aislamiento/paralelismo.

Entregables mínimos:

- `QualityGatePlan` / API pública read-only equivalente para inspeccionar composición sin ejecutar runners;
- refactor de binding-only tests para usar plan + ejecución directa del subgate solo cuando deba probarse su semántica;
- execution DAG/context scoped para impedir reejecución de componentes equivalentes dentro de un único aggregate run;
- de-dup del `LocalReleaseCandidateReporter` en tests, conservando una prueba canónica integral;
- `AggregateExecutionCostAudit` o mecanismo equivalente que reporte component execution multiplicity y prohíba duplicación accidental;
- source seal Git bounded/batch sin per-file subprocess en Git clean;
- source guard fallback accounting y dirty-fast-BLOCK;
- nodeid manifest/args-file para desacoplar cantidad de nodeids del límite de línea de comando;
- serial shadow plan coarsened y `NormalizedSerialBaselineReport`;
- actualización focal de duration estimates para tests cuyo costo cambió;
- ningún worker paralelo y ninguna full.

PASS mínimo:

- los ocho binding tests RUN-06 dejan de ejecutar perfiles completos y su wall-clock agregado cae >=80% en Windows respecto de `2931.421 s`, o cualquier desviación queda BLOCK hasta adjudicación owner;
- binding/registration tests no invocan aggregate `.run()` salvo allowlist explícita y justificada;
- dentro de un top-level hardening/industrial run no hay duplicate canonical component executions no justificadas;
- strong per-file Git subprocess count = 0 en Git-clean source seal/hot path;
- strong fallback count durante shard hot path = 0 en caso nominal;
- serial shadow plan reduce >=60% los procesos respecto del count50 baseline, sin perder nodeids y sin exceder timeout/command safety;
- normalized serial baseline separa ahorro de de-dup/coarsening del futuro ahorro paralelo;
- workers=0; full=0.

### FRX-v2.3-B — Isolation contract registry

Crear `TestIsolationRegistry`, static hints, explicit review workflow y negative fixtures. Todo nodeid inicia `UNCLASSIFIED/parallel_safe=false`. Las estimaciones de duración consumidas deben ser las normalizadas por A cuando exista evidencia nueva.

### FRX-v2.3-C — Conflict graph and parallel shadow scheduler

Combinar temporal estimate normalizado + isolation classes para construir waves. Sin ejecutar workers en paralelo. Calcular safe coverage ponderada por runtime, serial fraction, predicted makespan, lock contention y Amdahl feasibility.

### FRX-v2.3-BR — Isolation evidence and runtime-safe promotion

Micro-sprint successor insertado entre C y D después del `NO-GO` Windows de C. No repite B ni C: usa el `TestIsolationRegistry` ya implementado y el shadow planner ya implementado para obtener evidencia explícita de aislamiento sobre candidatos de alto costo.

Objetivos mínimos:

- priorizar nodeids por runtime normalizado, no por cantidad;
- definir contratos reutilizables de aislamiento, incluido `LOCAL_CLONE_PER_WORKER_V1`;
- auditar estructuralmente cada candidato y bloquear recursos externos no aislables;
- ejecutar únicamente probes focales representativos de los contratos, nunca una full;
- promover a `PROVEN_PARALLEL_SAFE` solo mediante review explícito + evidencia;
- conservar `SERIAL_REQUIRED` o `UNCLASSIFIED` cuando la evidencia no alcance;
- regenerar el coverage report y re-evaluar el shadow/Amdahl de C sin reimplementar C;
- `workers` de la suite general permanecen 0; los únicos procesos concurrentes admitidos son probes focales de aislamiento en clones locales separados;
- `full=0`.

El envelope de candidatos debe cubrir por diseño al menos 70% del runtime normalizado conocido cuando sea estructuralmente posible, para dejar margen sobre el ~60% ideal requerido por una reducción objetivo de 30% con dos workers. Que un candidato esté en el envelope **no** lo autoriza; el resultado Windows decide la cobertura realmente promovida.

BR cierra PASS aunque el resultado siga siendo `NO-GO`, siempre que la decisión sea honesta, reproducible y preserve safety. D solo queda autorizado si la re-evaluación posterior produce `feasible_for_canary=true`.

### FRX-v2.3-D — Bounded parallel canary

Ejecutar un subset `PROVEN_PARALLEL_SAFE` con workers=2 y comparar **el mismo canary** secuencial vs paralelo, sobre código ya de-duplicado. Medir proceso + coordinator + locks + source guard. Outcome parity obligatoria.

### FRX-v2.3-E — Windows one-full safe-parallel closure

Única full v2.3. Workers inicialmente <=2; unsafe/unknown/conflicting permanecen seriales. No ejecutar una segunda full secuencial. Reportar por separado:

1. mejora total vs historical v2.2 observed;
2. mejora atribuible a A (de-dup/serial normalization);
3. mejora incremental atribuible a paralelismo vs normalized serial baseline.

## 6. Resource classes mínimas B–E

- fixed filesystem paths / shared outputs;
- SQLite/DB files;
- Git/worktree/repo mutation;
- localhost ports/server lifecycle;
- process-global env/cwd;
- singleton/global module state;
- subprocess/process trees;
- network/external service;
- clock/time-sensitive state;
- shared caches;
- Windows named resources/locks.

## 7. Go/no-go del paralelismo

Después de A, si el normalized serial baseline ya satisface el presupuesto owner, el paralelismo debe seguir siendo una capacidad evaluada, no una obligación de default enablement. Después del `NO-GO` de C, BR es la única vía autorizada para obtener evidencia de aislamiento antes de D.

Antes de D/E:

- BR debe estar `CLOSED/PASS` y su successor registry debe contener un subset runtime-representative realmente `PROVEN_PARALLEL_SAFE`;

- runtime-weighted safe coverage debe ser suficiente;
- con workers=2, una reducción ideal de 30% requiere aproximadamente 60% de runtime realmente paralelizable antes de overhead;
- si el objetivo es matemáticamente inviable, no gastar la única full E solo para confirmarlo;
- el owner puede mantener la capacidad `AVAILABLE-NOT-DEFAULT`.

## 8. Criterios de adopción final

### Safety PASS

- outcome parity sin nuevas flakes;
- 100% accounting;
- conflict violations=0;
- source drift=0;
- no secret/runtime leakage;
- resume no reejecuta terminales;
- workers<=2 en primera adopción.

### Performance PASS

No se permite adjudicar speedup paralelo contra un baseline contaminado. El reporte final debe separar los tres componentes de mejora definidos en E.

Default parallel enablement requiere threshold owner predeclarado sobre **incremental parallel speedup vs normalized serial baseline**, además del safety PASS. Si no lo alcanza, `PASS/AVAILABLE-NOT-DEFAULT`.

## 9. DocumentationDriftGate

Continúa siendo precondición dura antes de la única full E. Ningún micro-sprint debe trasladar drift P0/P1 determinista a la full.

## 10. Riesgos

- ocultar duplicación mediante cache global puede crear falsos PASS;
- cambiar tests históricos sin distinguir binding vs semantic execution puede reducir cobertura real;
- shards demasiado grandes sin live per-node receipts pueden degradar recovery; por eso el coarsening solo es válido manteniendo el plugin de outcome append/flush;
- una baseline histórica contaminada puede exagerar el valor del paralelismo;
- paralelizar resource-unsafe tests puede generar flakes y corrupción local.

## 11. Definition of Done

V2.3 solo cierra cuando A–E están cerrados o existe una adjudicación owner explícita que detenga E por inviabilidad/ROI, sin false speedup claim. La full budget permanece `1` y solo E puede consumirla.
## 12. Estado de implementación incremental — FRX-v2.3-B

FRX-v2.3-B se encuentra `CLOSED/PASS/WINDOWS-VALIDATED` sobre repo393, con repo392 como parent Windows-validado. El registry inicial conserva todos los nodeids `UNCLASSIFIED/parallel_safe=false`; static hints no autorizan ejecución paralela. `workers=0`, `full=0`. FRX-v2.3-C permanece bloqueado hasta cierre Windows PASS de B.

## Estado operativo FRX-v2.3-C

FRX-v2.3-C se encuentra `CLOSED/PASS/WINDOWS-VALIDATED`. Su shadow es `NO-GO`: no existe runtime `PROVEN_PARALLEL_SAFE`; por lo tanto D permanece no autorizado hasta una revisión explícita successor.

## 13. Replan owner-approved tras C NO-GO

FRX-v2.3-C cerró `CLOSED/PASS/WINDOWS-VALIDATED` sobre repo394 con `Amdahl NO-GO`, 0 nodeids `PROVEN_PARALLEL_SAFE` y D no autorizado. El owner autoriza insertar FRX-v2.3-BR antes de D para obtener evidencia focal de aislamiento y promover candidatos de alto impacto sin consumir la full.

FRX-v2.3-BR cerró `CLOSED/PASS/WINDOWS-VALIDATED` sobre repo395 con `112` nodeids `PROVEN_PARALLEL_SAFE`, cobertura runtime `80.039%` y Amdahl successor `GO`. FRX-v2.3-D authorized=`true`; full consumida=0.

## 14. Estado de implementación — FRX-v2.3-D

FRX-v2.3-BR está `CLOSED/PASS/WINDOWS-VALIDATED/GO-D` sobre repo395. FRX-v2.3-D queda `IMPLEMENTED/WINDOWS-PENDING`: el bounded canary usa exactamente dos jobs atómicos `PROVEN_PARALLEL_SAFE`, dos contratos de aislamiento, clones/namespaces separados, `max_workers=2`, full=0 y el mismo subset serial/paralelo. El cierre y la autorización de E dependen exclusivamente de la evidencia Windows del bundle FRX-v2.3-D.

## 15. Cierre Windows — FRX-v2.3-D

FRX-v2.3-D cerró `CLOSED/PASS/WINDOWS-VALIDATED` sobre repo396. El mismo canary de dos nodeids `PROVEN_PARALLEL_SAFE` obtuvo parity exacta, conflictos=0, leakage=false, workers<=2 y full=0. Wall-clock serial=`70.000000s`; paralelo=`41.031000s`; speedup incremental=`41.384286%`. FRX-v2.3-E authorized=`true`. La decisión no habilita paralelismo por defecto y E mantiene la única full del backlog.


## 12. FRX-v2.3-E implementation binding

E is implemented against repo396 and remains `IMPLEMENTED/PENDING-WINDOWS-ONE-FULL`. The Windows operator is the only authority allowed to consume the single logical full. No comparison full is permitted.
