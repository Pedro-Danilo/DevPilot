---
doc_id: "DEVPL-FULL-REGRESSION-V2-2-V2-3-EXECUTION-ROADMAP"
title: "DevPilot — Full Regression v2.2/v2.3 execution roadmap"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-08-31"
approval: "approved_by_owner"
source_repo: "repo_DevPilot_Local_386_DEVPL_GSDLC_07_E_AGENTIC_PRECODE_MODEL_EVALS_WINDOWS_VALIDATED_CANDIDATE.zip"
source_commit: "17db6b219f5066f2df91d897a0e3ad62314a0176"
---
# Full Regression v2.2/v2.3 — Roadmap de ejecución

## 1. Problema

La full regression es actualmente un cuello de botella de ingeniería. La telemetría de GSDLC-07-E contiene 2.805 nodeids terminales, 12.952,888 s (~3,60 h) de duración acumulada, mediana ~0,022 s, p95 ~10,65 s y máximo ~774,74 s. La distribución es altamente sesgada.

Los bloqueos recientes además demostraron una segunda causa: drift documental/contractual detectado demasiado tarde. Optimizar únicamente el runner sin eliminar drift desplaza el costo, no lo resuelve.

## 2. Estrategia

### v2.2 — Distribución temporal inteligente
- sincronización documental incremental obligatoria;
- registry histórico de duración por nodeid/environment;
- estimación robusta y cold-start;
- shards balanceados por tiempo, todavía secuenciales (`workers=1`);
- una única full de cierre para medir mejora real.

### v2.3 — Paralelismo seguro
- clasificación explícita de aislamiento y recursos compartidos;
- `parallel_safe=false` por defecto;
- conflict graph + resource locks;
- workers subprocess tipados, sin shell y sin dependencia nueva obligatoria;
- canary antes de la única full de cierre;
- default paralelo solo con seguridad y mejora medible.

## 3. Regla global de testing

Cada backlog v2.2 y v2.3 puede consumir **exactamente una** logical full regression, exclusivamente en su micro-sprint de cierre. Los micro-sprints previos usan tests focales, simulación, shadow planning y canaries acotados.

## 4. Regla global de documentación

Ninguna full puede empezar si `DocumentationDriftGate != PASS`. El gate debe exigir drift P0/P1 current-active = 0 y separar `historical-freeze`, `current-active`, `derived`, `runtime-ephemeral` y `successor-needed`.

## 5. Métricas

- wall-clock total;
- CPU/process overhead estimado;
- máximo/p95 de shard;
- coeficiente de variación de shard durations;
- infra aborts/resumes;
- nodeids rerun indebidamente = 0;
- drift documental encontrado durante full = 0;
- flake delta = 0;
- v2.3: speedup y parallel-safe coverage.

## 6. Orden

`repo386 → v2.2-A..D → v2.2 CLOSED/PASS → v2.3-A..D → v2.3 CLOSED/PASS → DEVPL-GSDLC-08`.

## 7. Corrective rebase after FRX-v2.2-D one-full — 2026-09-02

La full v2.2-D demostró que el criterio de balance de shard era insuficiente como proxy del costo real. El benchmark debe separar `pytest_process_seconds`, `source_guard_seconds`, `inter_shard_gap_seconds` y `observed_end_to_end_wall_seconds`. La adopción v2.2 queda `AVAILABLE-NOT-DEFAULT` hasta cierre por composite recovery; no se consume otra full.

V2.3 mantiene el diseño de paralelismo seguro, pero agrega un **feasibility gate ponderado por duración** antes de su única full. Con 2 workers, el target de 30% requiere que al menos ~60% del runtime sea `PROVEN_PARALLEL_SAFE` en el límite ideal de Amdahl. Si el techo teórico no llega al target, v2.3-D no debe gastar su única full para demostrar un speedup matemáticamente inalcanzable.
