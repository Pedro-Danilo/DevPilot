---
doc_id: "FRX-V2-3-BR-IMPLEMENTATION-REPORT"
title: "FRX-v2.3-BR — Isolation evidence and runtime-safe promotion — implementation report"
status: "implemented-initial"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-09-02"
approval: "windows-validated"
---
# FRX-v2.3-BR — Implementation report

## Objetivo

Insertar una fase de evidencia entre C y D para convertir el `NO-GO` por cobertura segura 0% en una decisión basada en pruebas, sin forzar un canary ni consumir la full v2.3.

## Capacidades nuevas

- `IsolationContractCatalog`: contratos reutilizables de aislamiento.
- `LOCAL_CLONE_PER_WORKER_V1`: cada worker futuro usa un clon Git local separado del mismo commit; repo-relative outputs, SQLite, Git metadata, caches, cwd y subprocesses quedan namespaced por worker.
- `FunctionIsolationAuditor`: auditoría por función/nodeid que bloquea recursos externos no aislables.
- `RuntimeSafePromotion`: construye successor registry, conserva nodeids nuevos como `UNCLASSIFIED` y promueve únicamente con audit + contract probe PASS.
- Candidate manifest runtime-ranked: 112 nodeids cubren 80.039% del runtime conocido normalizado antes de ejecutar pruebas dinámicas.

## Política de seguridad

El candidate manifest no autoriza paralelismo. Static hints, nombres y duración tampoco. La promoción requiere review explícito y evidencia dinámica del contrato en Windows. Los probes focales pueden usar dos procesos concurrentes en clones locales separados; la suite general sigue con workers=0 y full=0.

## Resultado esperado Windows

BR puede terminar `PASS/GO-D` o `PASS/NO-GO-D`. Solo un successor Amdahl con `feasible_for_canary=true` autoriza D. Un NO-GO honesto no es un fallo del sprint.

## Riesgos y limitaciones

Esta es una primera versión de evidencia de aislamiento. El contrato por clone reduce colisiones repo-locales, pero no puede aislar puertos externos, network services, Windows named resources o paths absolutos externos; esos recursos se bloquean estructuralmente. D, si se autoriza, deberá usar el mismo contrato de clone-per-worker o uno más fuerte, nunca una arquitectura menos aislada.

## Validación local

- focal BR: `10/10 PASS`;
- candidate envelope: `112` nodeids, `80.039%` del runtime conocido;
- todos los candidatos permanecen `parallel_safe=false` antes de evidencia Windows;
- auditoría estructural: `112/112` elegibles para probes del contrato;
- Project State, Documentation Governance y TCR v1/v2: PASS;
- full regression: `0`;
- workers de suite general: `0`;
- browser/API externos: `0`.

La proyección local que asume que los tres contract probes Windows pasan es únicamente orientativa y **no autoriza D**. La autoridad de promoción y Amdahl será la evidencia Windows de BR.

## Resultado Windows

- successor safe total: `112`;
- runtime-safe coverage: `80.039%`;
- Amdahl successor: `GO`;
- FRX-v2.3-D authorized: `true`;
- full regression: `0`; general-suite workers: `0`.
