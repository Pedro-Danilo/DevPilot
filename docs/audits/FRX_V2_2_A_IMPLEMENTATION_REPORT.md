---
doc_id: "FRX-V2-2-A-IMPLEMENTATION-REPORT"
title: "FRX-v2.2-A — Documentation consistency foundation — implementation report"
status: "reviewed"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-08-31"
approval: "implementation_candidate"
---

# FRX-v2.2-A — Documentation consistency foundation — Implementation Report

## 1. Veredicto local

`PASS-CANDIDATE / PENDING-WINDOWS`.

La implementación local cumple el alcance governance-only del micro-sprint. No se ejecutó full regression, browser, API/UI ni red externa. El cierre formal `CLOSED/PASS` queda condicionado a la validación Windows sobre el successor de repo386 y a la reconciliación Git de tres estados posterior al PASS.

## 2. Baseline

- Parent archive: `repo_DevPilot_Local_386_DEVPL_GSDLC_07_E_AGENTIC_PRECODE_MODEL_EVALS_WINDOWS_VALIDATED_CANDIDATE.zip`.
- Parent Git authority: `17db6b219f5066f2df91d897a0e3ad62314a0176`.
- Parent SHA-256: `0998e901a1149d377c6793dc923e0c45ed7eec42395e7182ef495ce652e79d23`.
- Parent remains immutable.

## 3. Capacidades nuevas

### DocumentationAuthorityGraph

Representa `doc_id`, path, subject, authority rank, authority kind, lifecycle, classification y successor. Permite distinguir `current-active`, `derived` e `historical-freeze` sin inferir autoridad por nombre de archivo.

### ClosureStateConsistencyValidator

Cruza Project State, backlog, Source Registry, README, changelog y adjudicaciones. El fixture negativo de repo386 detecta el S2 post-cierre; el successor reconciliado obtiene `13/13 PASS`, `P0/P1 open drift=0`.

### DocumentationDriftLedger

Conserva el finding `S2-DOC-GSDLC07-POSTCLOSE-001` con owner, expected/current y resolución. El finding pasa de abierto a `resolved` sin reescribir la evidencia histórica.

### DerivedMetadataProjection

Calcula counters current-active desde la colección viva del Source Registry. Evita que un número histórico quede incrustado en un summary mutable.

### DocImpactPlanner

Para el delta FRX-v2.2-A proyecta documentación, registries y tests impactados y afirma explícitamente que no se requiere full regression ni browser.

## 4. Reconciliación documental

Se reconciliaron en el successor:

- DEVPL-GSDLC-07 backlog → `closed / CLOSED/PASS`;
- README → DEVPL-GSDLC-07 cerrado y FRX-v2.2-A activo;
- Source Registry → final adjudication current, proposal 07-E historical/superseded;
- Project State → FRX-v2.2-A activo, FRX-v2.2-B next, GSDLC-08 authorized/deferred;
- changelog → cierre GSDLC-07 y activación FRX-v2.2-A;
- roadmap/backlogs/prompts FRX registrados;
- TCR v1/v2 → contrato `frx-v2.2-a-documentation-consistency`.

## 5. Historical/current separation corregida

Se detectaron dos tests POST-H-033 que todavía consultaban catálogos `current-active` y congelaban `1.0.0`:

1. Frontmatter Catalog POST-H-033-B.
2. Documentation Governance Rule Registry POST-H-033-F.

Se añadieron snapshots `*_at_close` `1.0.0` y los catálogos vivos evolucionan a `1.1.0`. Los tests históricos validan el snapshot; los contratos current-active validan la versión viva.

## 6. Drifts encontrados durante implementación

- ocho prompts FRX tenían `doc_id` no normalizado al contrato current-active;
- TCR v1 usaba `scope=governance`, fuera del enum permitido;
- TCR v2 usaba `domain=governance.documentation`, fuera del enum permitido;
- Source Registry summary quedó temporalmente desfasado al incorporar el snapshot POST-H-033-F; `DerivedMetadataProjection` lo detectó y fue reconciliado.

Todos fueron corregidos antes de empaquetar.

## 7. Pruebas locales ejecutadas

Resultados terminales acreditados:

- DocImpact-selected test files: `74/74 PASS` en ejecución completion-first por grupos/archivos;
- FRX-v2.2-A dedicated: `8/8 PASS`;
- Source Registry schema: `5/5 PASS`;
- Documentation Governance Validator: `4/4 PASS` ejecutados por nodeid para evitar timeout monolítico;
- Frontmatter Validator: `7/7 PASS`;
- POST-H-009 Documentation Governance: `7/7 PASS`;
- POST-H-033 Rule Registry: `8/8 PASS`;
- POST-H-033 Frontmatter Catalog: `8/8 PASS`;
- Project Global State: `27/27 PASS`;
- Project State CLI: `PASS`;
- Documentation Governance CLI: `PASS`;
- TCR v1 CLI: `PASS`;
- TCR v2 CLI: `PASS`;
- Closure State Consistency: `13/13 PASS`;
- open P0/P1 drift: `0`;
- full regression runs FRX-v2.2: `0`;
- browser runs FRX-v2.2-A: `0`.

`tests/test_documentation_governance_validator.py` resultó lento cuando se ejecutó como archivo monolítico. Sus cuatro nodeids se ejecutaron individualmente y terminaron `4/4 PASS`; el operador Windows conserva ese patrón completion-first para evitar que un timeout externo borre resultados terminales.

## 8. Seguridad

- network_used=false;
- external_api_used=false;
- secrets_exposed=false;
- browser_runs=0;
- full_regression_runs=0;
- repo386/evidencia histórica no mutados;
- `.git` no se modifica manualmente;
- packaging final desde Git.

## 9. Riesgos y limitaciones

- La consistency layer v1 cubre contradicciones determinísticas configuradas; no interpreta semántica libre de todos los documentos.
- La cobertura crecerá a medida que se agreguen nuevos closure contracts al authority graph.
- v2.2-A no reduce por sí mismo el tiempo CPU de la full; evita que drift determinista llegue a ella.
- v2.2-B/C/D son necesarios para estimación y distribución temporal.

## 10. Criterio de cierre Windows

FRX-v2.2-A podrá declarar `CLOSED/PASS` cuando el successor Windows acredite:

- parent repo386 correcto;
- patch/delta exacto e idempotente;
- fixture negativo BLOCK y successor PASS;
- focal tests PASS;
- Project State, Documentation Governance, TCR v1/v2 PASS;
- P0/P1 drift=0;
- full/browser=0;
- candidate limpio SHA/CRC;
- promoción Git three-state gobernada.
