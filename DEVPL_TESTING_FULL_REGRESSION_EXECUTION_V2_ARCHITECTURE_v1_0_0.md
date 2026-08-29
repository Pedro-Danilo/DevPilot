---
doc_id: "DEVPL-TESTING-FULL-REGRESSION-EXECUTION-V2-ARCHITECTURE"
title: "DevPilot — Full Regression Execution v2 architecture"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-08-28"
approval: "approved_by_owner"
architecture_scope: "logical full-regression session, resumable sequential sharding, terminal accounting"
---

# DevPilot — Full Regression Execution v2

## 1. Problema confirmado

Repo379 dispone de TCR v1/v2, Test Impact v2, perfiles `always-fast`, `p0-critical`, `security`, `impact`, `release`, `release-candidate-local` y `full`, además de HistoricalRegressionGuard. Sin embargo, la full física sigue siendo un único `pytest -q` con un timeout global. En 06-E el límite de cuatro horas terminó alrededor del 82.24 %: `2255/2742` resultados observados y `487` nodeids sin ejecutar.

El TCR tampoco es todavía un scheduler temporal: 298 contratos referencian 901 test files, pero corresponden a 386 archivos únicos. La suma de `expected_duration_seconds` duplica trabajo contractual y no equivale al tiempo real de ejecución.

## 2. Decisión arquitectónica

La full deja de modelarse como un proceso monolítico y pasa a ser una **sesión lógica**:

```text
collect -> immutable plan -> sequential shards -> per-shard receipts -> aggregate adjudication
```

La cobertura no se reduce. La primera versión prioriza **cero pérdida de progreso**, no paralelismo.

## 3. Contratos principales

### FullRegressionSession

Debe persistir fuera del source tree una identidad inmutable:

- `session_id`;
- `source_fingerprint` (commit + clean/delta fingerprint);
- `environment_fingerprint` (OS/Python/pytest/dependency lock/config);
- `collection_sha256`;
- `shard_plan_sha256`;
- timestamps;
- policy version;
- terminal accounting.

### CollectedNode

Cada nodeid se representa una sola vez en la collection sellada. No se deriva desde TCR para evitar duplicación contractual.

### ShardPlan

- inicialmente secuencial;
- objetivo 5-10 minutos por shard cuando haya telemetría;
- watchdog 15-20 minutos;
- no duplicar nodeids;
- orden determinista;
- plan sellado antes de ejecutar.

### ShardReceipt

Por shard:

- nodeids previstos;
- nodeids observados;
- start/end/duration;
- exit code;
- JUnit path/hash;
- log path/hash;
- terminal outcomes;
- infra abort metadata;
- source/environment/collection fingerprints repetidos.

## 4. Estados terminales de nodeid

Todo nodeid termina exactamente como uno de:

`PASS`, `FAIL`, `ERROR`, `SKIP_APPROVED`, `INFRA_ABORT`, `UNEXECUTED`.

`UNEXECUTED` solo es válido durante una sesión abierta. Una adjudicación final no puede declarar cobertura completa mientras exista un `UNEXECUTED` no justificado.

## 5. Completion-first

Un `FAIL` funcional ordinario **no detiene** los shards restantes. Se completa el plan y se entrega el inventario integral de fallos. Fail-fast queda reservado a una condición que invalide la seguridad o la identidad de la sesión (fingerprint drift, source mutation, policy breach, destructive precondition).

## 6. Resumibilidad

Una interrupción de Windows/pytest/shard no crea una segunda full si:

1. source fingerprint coincide;
2. environment fingerprint coincide;
3. collection SHA coincide;
4. shard-plan SHA coincide;
5. no hubo mutación source desde el receipt previo.

La reanudación ejecuta únicamente nodeids sin outcome terminal. Los receipts previos permanecen inmutables.

## 7. Separación de fallos funcionales e infraestructura

- `FAIL/ERROR`: outcome funcional que debe corregirse luego de completar la colección;
- `INFRA_ABORT`: el shard no pudo completar por infraestructura;
- `fingerprint mismatch`: BLOCK y nueva logical session; no se mezclan receipts.

## 8. NodeDurationRegistry — fase posterior

Después de v2.1 se incorpora duración real nodeid-level proveniente de receipts. El registry debe deduplicar nodeids, usar muestras robustas (mediana/p95) y separar cold-start de duración estable. TCR conserva criticidad/riesgo/costo semántico, pero no se usa como reloj físico.

## 9. Paralelización — explícitamente diferida

No introducir `pytest-xdist` en v2.1. Antes se requiere clasificar:

- `parallel_safe`;
- `serial_only`;
- `isolation_class`;
- `shared_resources` (filesystem, outputs, SQLite, Git, ports, global state).

Solo después se evalúan 2-4 workers sobre tests demostrablemente aislados.

## 10. CLI/API propuestas

Primera superficie CLI local-first:

```text
testing full-session collect
testing full-session plan
testing full-session run
testing full-session resume
testing full-session status
testing full-session adjudicate
```

No se expone ejecución browser ni una UI nueva en v2.1. Las salidas machine-readable son obligatorias.

## 11. Runtime state

La sesión/receipts/JUnit/logs viven en `outputs/testing/full_regression/<session_id>/` o ruta runtime equivalente. No se versionan y no entran al candidate ZIP. Solo los schemas, contratos, documentación y fixtures deterministas viven en source.

## 12. Seguridad

- no shell arbitrario: subprocess usa argv tipado/allowlisted;
- timeout por shard;
- no red requerida;
- secrets redacted;
- no modificación `.git`;
- source fingerprint antes/después de cada shard;
- cualquier mutación source inesperada = BLOCK;
- resume no puede mezclar source/env distintos.

## 13. Fases de madurez

| Fase | Objetivo |
|---|---|
| v2.1 | cero pérdida de progreso; collection/plan/receipts/resume/adjudication |
| v2.2 | NodeDurationRegistry + hotspots cuantificados; secuencial <4 h si la evidencia lo permite |
| v2.3 | paralelización segura clasificada; objetivo <2 h |
| objetivo maduro | <90 min solo si evidencia y aislamiento lo permiten |

## 14. Criterios PASS/BLOCK de v2.1

**PASS:** colección íntegra, zero duplicate/missing nodeids, plan inmutable, receipts verificables, resume preserva logical attempt, FAIL ordinario no aborta el resto y adjudication reporta 100 % de accounting.  
**BLOCK:** coverage reduction, receipt mutable, resume con fingerprint distinto, nodeids silenciosamente omitidos, segundo intento presentado como resume, o paralelismo sin clasificación de aislamiento.
