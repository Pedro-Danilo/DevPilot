---
doc_id: "ADR-FRX-003"
title: "Bounded two-worker canary with atomic pytest jobs"
status: "accepted"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-09-03"
approval: "approved_by_owner_prompt"
---
# ADR-FRX-003 — Bounded two-worker canary with atomic pytest jobs

## Contexto

FRX-v2.3-BR cerró `CLOSED/PASS/WINDOWS-VALIDATED/GO-D` con 112 nodeids `PROVEN_PARALLEL_SAFE` y 80.038813% del runtime normalizado cubierto. FRX-v2.3-D debe probar paralelismo real sin convertir el canary en un scheduler general ni consumir la única full v2.3 reservada para E.

## Decisión

FRX-v2.3-D usa exactamente dos nodeids atómicos, ambos con evidencia BR y contratos distintos (`LOCAL_CLONE_PER_WORKER_V1` y `READ_ONLY_REPO_V1`). El mismo subset se ejecuta primero serialmente y después con máximo dos procesos concurrentes.

Cada job se ejecuta desde un clon Git local fresco del mismo commit y usa namespace temporal propio. El coordinador usa `subprocess.Popen` directamente: no usa shell, xdist, `ThreadPoolExecutor`, generic scheduler, red, API/UI ni full regression. Los resource locks siguen activos aunque los dos jobs seleccionados no compartan lock keys.

La decisión de PASS exige: outcome parity exacta, ambos outcomes `PASS`, artefactos runtime equivalentes, source guard limpio antes/después, cero conflictos, cero leakage, `max_workers_observed<=2`, `full_regression_runs=0` y speedup incremental estrictamente positivo contra el mismo canary serial.

## Consecuencias

- La evidencia de D autoriza E, pero **no activa paralelismo por defecto**.
- Cualquier nodeid no `PROVEN_PARALLEL_SAFE` permanece fuera del canary.
- Un hang o timeout de worker produce BLOCK; el operador Windows dispone además de un watchdog de proceso-tree para evitar estados supervivientes.
- Los receipts terminales y los mode receipts son evidencia sticky; una reanudación no sobrescribe evidencia no terminal.
- La única full v2.3 continúa reservada exclusivamente para FRX-v2.3-E.

## PASS/BLOCK

**PASS:** safety PASS + speedup incremental > 0 + workers<=2 + full=0.

**BLOCK:** flake/mismatch, collision, source/runtime contamination, leakage, worker desconocido/no seguro, timeout o beneficio paralelo no positivo.

## Verificación

`python -m pytest -p no:ddtrace --assert=plain -q tests/test_frx_v2_3_d_parallel_canary.py`

`python -m devpilot_core tests parallel-canary --json`
