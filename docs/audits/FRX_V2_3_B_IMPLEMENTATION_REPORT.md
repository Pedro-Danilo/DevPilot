---
doc_id: "FRX-V2-3-B-IMPLEMENTATION-REPORT"
title: "FRX-v2.3-B — Isolation contract registry — implementation report"
status: "implemented-initial"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-09-02"
approval: "windows-validated"
---
# FRX-v2.3-B — Implementation report

## Resultado
Se implementó una primera versión industrial conservadora del `TestIsolationRegistry`. La autoridad de entrada es repo392 Windows-validado (`e5b0d53...`). Ningún test se declara parallel-safe por inferencia, nombre o duración.

## Nuevas capacidades
- Registry schema-backed con estados `UNCLASSIFIED`, `SERIAL_REQUIRED` y `PROVEN_PARALLEL_SAFE`.
- Default obligatorio `UNCLASSIFIED`, `parallel_safe=false`, `explicit_review_required=true`.
- Once resource classes estables y `suggested_hints` estáticos no autoritativos.
- Workflow explícito de review positivo/negativo con reviewer, reason, timestamp y evidence IDs.
- Isolation domains y resource lock keys listos para el conflict graph de C.
- Runtime estimate por nodeid usando la evidencia más reciente disponible; las ocho mediciones successor de A prevalecen sobre muestras históricas cuando coinciden.
- Coverage report ponderado por runtime.

## Estado inicial deliberado
La colección post-B contiene 2872 nodeids y todos inician `UNCLASSIFIED`. `proven_parallel_safe_total=0`. Esto no es una carencia de seguridad: evita que B fabrique safe coverage antes del review explícito. C debe mantener todo unknown en serial lane.

## Riesgos y limitaciones
- El analizador es intencionalmente conservador y opera a nivel de archivo de test; puede producir false-positive hints, pero nunca autoriza paralelismo.
- 68 nodeids no tienen duration estimate conocido; permanecen cubiertos funcionalmente y seriales por default.
- Esta versión es preliminar/primera versión del contrato de aislamiento. La clasificación real de capacidad paralela debe crecer mediante reviews/evidence posteriores, no por heurística automática.
- B no implementa conflict graph, waves ni workers; pertenecen a C/D.

## Pruebas
La aceptación focal cubre las 11 resource classes, default unsafe, prohibición de inference-to-safe, review positivo/negativo, schema/semantics, coverage ponderada y workers/full en cero.
