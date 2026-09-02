---
doc_id: "03A_PROMPT_FRX_V2_3_BR_ISOLATION_EVIDENCE_RUNTIME_SAFE_PROMOTION_V1_0_0"
title: "FRX-v2.3-BR — Isolation evidence and runtime-safe promotion — implementation and Windows validation prompt"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-09-02"
approval: "approved_by_owner"
source_repo: "repo_DevPilot_Local_394_FRX_V2_3_C_CONFLICT_GRAPH_SHADOW_SCHEDULER_WINDOWS_VALIDATED_CANDIDATE.zip"
source_commit: "95b7805744bc3878d7d60792e0647076f5517afc"
predecessor: "FRX-v2.3-C/CLOSED-PASS-WINDOWS-VALIDATED/AMDHAL-NO-GO"
full_regression_policy: "no full regression"
general_suite_parallel_workers: 0
probe_max_concurrency: 2
---
# FRX-v2.3-BR — Isolation evidence and runtime-safe promotion

## 1. Misión

Obtener evidencia suficiente y auditable para promover un subset runtime-representative desde `UNCLASSIFIED` a `PROVEN_PARALLEL_SAFE` sin ejecutar una full regression ni iniciar todavía el canary D.

BR es un successor de B/C: no reimplementa `TestIsolationRegistry` ni `ParallelShadowPlanner`. Añade la evidencia explícita que B exigía y que C demostró ausente.

## 2. Autoridad de entrada

- repo394 Windows-validado, commit `95b7805744bc3878d7d60792e0647076f5517afc`;
- A/B/C `CLOSED/PASS/WINDOWS-VALIDATED`;
- registry B con 2872 entradas iniciales `UNCLASSIFIED`;
- colección C de 2883 nodeids y 11 implícitos `UNCLASSIFIED`;
- runtime conocido normalizado `9740.888787 s`;
- C Amdahl `NO-GO`, safe coverage `0%`, D no autorizado;
- full v2.3 consumidas `0/1`.

## 3. Principio de seguridad

Un test no es seguro por nombre, duración, static hint o por estar en un candidate list. `PROVEN_PARALLEL_SAFE` requiere simultáneamente:

1. contrato de aislamiento explícito;
2. auditoría estructural por nodeid;
3. evidencia focal dinámica del contrato;
4. reviewer/reason/timestamp/evidence IDs persistidos en el registry.

## 4. Contrato de worker

BR introduce `LOCAL_CLONE_PER_WORKER_V1`: cada worker futuro opera sobre un clon Git local separado del mismo commit. Eso namespacia repo-relative outputs, SQLite, Git metadata, caches, cwd y subprocesses repo-locales. Continúan prohibidos recursos externos no namespaciables: puertos/servidores compartidos, network/external services reales, Windows named resources, paths absolutos externos y dependencias de sleep/clock no acotadas.

Los probes BR pueden usar máximo dos procesos concurrentes únicamente para demostrar aislamiento del contrato. Esto es validación focal, no ejecución paralela de la suite ni canary D.

## 5. Candidate envelope

Priorizar por runtime normalizado. El manifest de implementación debe apuntar a >=80% del runtime conocido cuando los candidatos pasen la auditoría estructural, dejando margen sobre el ~60% ideal de Amdahl para una reducción objetivo de 30% con dos workers.

La pertenencia al envelope no concede `parallel_safe=true`.

## 6. Implementación

- `IsolationContractCatalog` reusable;
- `FunctionIsolationAuditor` por nodeid;
- successor registry que incorpora nodeids nuevos como `UNCLASSIFIED`;
- `RuntimeSafePromotion` que solo promueve con audit + contract probe PASS;
- candidate manifest runtime-ranked;
- coverage report successor;
- re-evaluación del planner C con el nuevo registry, sin reimplementar C;
- resultado machine-readable `GO/NO-GO` para D.

## 7. Validación focal Windows

1. focal de contratos/auditor/promoción;
2. collection-only estructurada de la suite vigente;
3. re-audit de todos los candidates del manifest;
4. probes representativos de los tres contratos en clones locales separados;
5. comprobar que el checkout fuente permanece Git-clean;
6. aplicar promociones únicamente si el contract probe correspondiente pasa;
7. coverage runtime-weighted;
8. re-run read-only del shadow/Amdahl con workers ejecutados=0;
9. Project State + Docs Governance + TCR v1/v2;
10. full=0.

## 8. PASS/NO-GO permitido

BR PASS técnico exige integridad de registry/reviews/evidence y cero promoción accidental. Puede terminar:

- `PASS/GO-D`: safe runtime suficiente y C successor produce `feasible_for_canary=true`;
- `PASS/NO-GO-D`: evidencia honesta insuficiente; D permanece bloqueado y se requiere aislamiento adicional o adjudicación owner.

## 9. BLOCK

- un test safe solo por inferencia;
- candidate manifest usado como autorización;
- un contract probe falla y aun así se promueve su familia;
- recurso externo no aislable pasa como safe;
- source checkout mutado por probe;
- full ejecutada;
- worker general de suite >0;
- falsificar GO para continuar D.

## 10. Evidencia y salida

Entregar candidate manifest, contract catalog, structural audit, probe receipts, successor registry, coverage report, C successor shadow/Amdahl, focal JUnit/log, full_runs=0 y decisión D explícita.

Commit sugerido: `perf(frx-v2.3): prove runtime-safe isolation candidates before canary`.
