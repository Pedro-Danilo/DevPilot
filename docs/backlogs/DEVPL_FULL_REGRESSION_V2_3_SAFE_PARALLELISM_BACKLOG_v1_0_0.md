---
doc_id: "DEVPL-FULL-REGRESSION-V2-3"
title: "Full Regression v2.3 — Safe bounded parallelism"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-08-31"
approval: "approved_by_owner"
predecessor: "DEVPL-FULL-REGRESSION-V2-2/CLOSED-PASS"
full_regression_budget: "1 logical full in v2.3-D only"
default_parallel_safe: false
initial_workers: 0
---
# Full Regression v2.3 — Backlog

## Objetivo

Reducir de manera material el wall-clock de la full regression mediante paralelismo **solo para tests con aislamiento demostrado**, preservando determinismo, coverage, evidencia, seguridad y resumibilidad.

## Principios

- `parallel_safe=false` por defecto;
- duración/nombre nunca autoriza paralelismo;
- clasificación requiere evidencia de recursos compartidos;
- ningún worker usa shell;
- cada worker usa subprocess pytest tipado, temp/output namespaces separados y receipts propios;
- conflict graph evita concurrencia incompatible;
- resource locks serializan recursos explícitamente compartidos;
- full coverage y accounting siguen siendo globales;
- fallback secuencial es seguro y automático ante clase no conocida;
- no dependencia xdist obligatoria.

## Resource classes mínimas

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

## Micro-sprints

### FRX-v2.3-A — Isolation contract registry
Crear `TestIsolationRegistry`, static hints, explicit review workflow y negative fixtures. Todo nodeid inicia UNCLASSIFIED/false.

### FRX-v2.3-B — Conflict graph and parallel shadow scheduler
Combinar temporal estimate v2.2 + isolation classes para construir waves. Sin ejecutar workers en paralelo todavía. Probar conflict graph, locks y deterministic plan.

### FRX-v2.3-C — Bounded parallel canary
Habilitar exclusivamente canary con `workers=2` sobre subset PROVEN_PARALLEL_SAFE. Comparar con ejecución secuencial del mismo canary como validación focal, no full. Exigir resultados idénticos y cero contaminación de recursos.

### FRX-v2.3-D — Windows one-full parallel closure
Ejecutar una sola full v2.3 con workers inicialmente limitados a 2 y fallback serial por conflicto. Medir speedup real contra la full v2.2 ya ejecutada. No ejecutar una segunda full de comparación.

## Criterios de adopción

### Safety PASS
- outcome parity sin nuevas flakes;
- 100% accounting;
- conflict violations=0;
- source drift=0;
- no secret/runtime leakage;
- resume no reejecuta terminales.

### Performance target
Para habilitar paralelismo por defecto se exige mejora wall-clock >= 30% frente a la full v2.2, o umbral owner explícitamente reajustado con evidencia. Si safety pasa pero speedup es insuficiente, la capacidad puede cerrar `PASS/AVAILABLE-NOT-DEFAULT`, sin fingir que el problema de rendimiento quedó resuelto.

## DocumentationDriftGate

Continúa siendo precondición dura antes de la full. v2.3 no debe gastar paralelismo en descubrir drift determinista que pudo detectarse focalmente.
