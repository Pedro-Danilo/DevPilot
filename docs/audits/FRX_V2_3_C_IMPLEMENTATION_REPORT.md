---
doc_id: "FRX-V2-3-C-IMPLEMENTATION-REPORT"
title: "FRX-v2.3-C — Conflict graph and parallel shadow scheduler — implementation report"
status: "implemented-initial"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-09-02"
approval: "pending-windows-validation"
---
# FRX-v2.3-C — Implementation report

## Objetivo
Construir un conflict graph determinístico y un shadow planner de dos slots sin ejecutar workers paralelos ni full regression.

## Implementación
- `ParallelShadowPlanner` consume exclusivamente contratos explícitos de B y duraciones normalizadas.
- `UNCLASSIFIED` y `SERIAL_REQUIRED` permanecen en serial lane.
- Los resource locks/isolation domains crean aristas entre candidatos `PROVEN_PARALLEL_SAFE`; son defensa adicional, no autorización.
- La identidad del plan sella collection SHA, isolation SHA, duration registry SHA y normalized serial baseline SHA.
- El preview usa dos slots; `workers_executed=0` y `execute()` está bloqueado por diseño.
- El Amdahl report compara el ahorro paralelo incremental contra la baseline serial normalizada. La full histórica v2.2 se conserva solo para reporting total.

## Resultado inicial
La colección vigente contiene 2883 nodeids: 2872 tienen entrada en el registry B y los 11 tests añadidos por C se incorporan como `UNCLASSIFIED` implícitos. Ningún nodeid está `PROVEN_PARALLEL_SAFE`; por tanto C produce una serial lane de 2883, cero waves paralelas y decisión `NO-GO` para el canary D. Esto no es un fallo de C: evita fabricar paralelismo sin revisión explícita.

## Riesgos y evolución
La versión es preliminar. D solo podrá autorizarse en un sucesor cuando exista cobertura runtime `PROVEN_PARALLEL_SAFE` suficiente y C vuelva a producir `GO`; C no realiza reviews ni modifica el registry B.
