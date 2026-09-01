---
doc_id: "DEVPL-FRX-V2-2-A-DOCUMENTATION-CONSISTENCY-CONTRACT-EVOLUTION"
title: "FRX-v2.2-A — Documentation consistency governance contract evolution"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-08-31"
approval: "approved_by_owner"
---

# FRX-v2.2-A — Documentation consistency governance contract evolution

## 1. Objetivo

Materializar como contrato ejecutable la política documental ya vigente de DevPilot, sin introducir una nueva jerarquía de autoridad y, por tanto, sin requerir ADR nueva. La evolución mueve la detección de contradicciones documentales desde gates tardíos y full regression hacia una validación incremental, determinística y basada en autoridades explícitas.

## 2. Decisión arquitectónica

Se preserva la jerarquía existente:

1. Project State y adjudicaciones finales current-active son autoridades de estado de cierre.
2. Backlogs aprobados/cerrados son fuentes de verdad de alcance y lifecycle.
3. Source Registry describe clasificación, lifecycle, owners y required tests.
4. README y changelog son proyecciones derivadas y no deben contradecir autoridades P0/P1.
5. Proposals, snapshots `*_at_close` y evidencias selladas permanecen historical-freeze.
6. Summaries/counters current-active se derivan de colecciones vivas; no se congelan números históricos en objetos mutables.

No cambia la autoridad global; se convierte en contratos verificables mediante `DocumentationAuthorityGraph`, `ClosureStateConsistencyValidator`, `DocumentationDriftLedger`, `DerivedMetadataProjection` y `DocImpactPlanner`.

## 3. Separación historical-freeze / current-active

FRX-v2.2-A añade snapshots explícitos para contratos POST-H-033 que históricamente esperaban la versión `1.0.0` de catálogos mutables:

- `.devpilot/validation/frontmatter_catalog_post_h_033_b_at_close.json`;
- `.devpilot/docs_governance/rule_registry_post_h_033_f_at_close.json`.

Los tests históricos leen esos snapshots; los contratos actuales leen los catálogos vivos `1.1.0`. Un cambio futuro de catálogo no autoriza reescribir el hecho histórico.

## 4. Consistencia transversal

`ClosureStateConsistencyValidator` compara, para cada closure contract configurado:

- Project State;
- frontmatter del backlog;
- Source Registry;
- proposal histórica versus adjudicación final;
- README;
- changelog;
- siguiente hito autorizado;
- counters derivados del Source Registry;
- drift P0/P1 abierto.

Un hallazgo P0/P1 produce BLOCK antes de consumir testing costoso.

## 5. DocImpact incremental

`DocImpactPlanner` recibe `changed_paths` y proyecta:

- documentos impactados;
- registries que deben reconciliarse;
- tests focales requeridos;
- criticidades P0/P1;
- necesidad de `closure-consistency`;
- `full_regression_required`;
- `browser_required`.

Para FRX-v2.2-A el plan actual exige validación focal y establece explícitamente `full_regression_required=false` y `browser_required=false`.

## 6. Recuperación y evidencia

Los operadores Windows sucesores deben:

- usar Git content/tree, no hashes físicos CRLF/LF;
- tratar receipts PASS como terminales para el mismo commit/fingerprint;
- reanudar solo checks `INFRA_ABORT`;
- preservar cambios desconocidos y bloquear en lugar de limpiarlos;
- empaquetar desde `git archive` tras PASS;
- separar validación técnica de promoción Git/remoto.

## 7. PASS/BLOCK

### PASS

- P0/P1 open drift = 0;
- Source Registry derived summary = live collection;
- historical snapshots intactos;
- focal tests y Project State/Docs Governance/TCR PASS;
- full regression runs = 0;
- browser runs = 0.

### BLOCK

- current-active contradice una autoridad de mayor rango;
- historical proposal vuelve a actuar como current authority;
- counter mutable hard-coded;
- test histórico consulta catálogo vivo cuando existe snapshot at-close;
- full/browser ejecutado durante FRX-v2.2-A.

## 8. Riesgos y limitaciones

Esta es una primera versión industrializable del consistency layer. No intenta resolver semántica documental arbitraria ni sustituye revisión humana en decisiones ambiguas. Su objetivo es eliminar drift determinístico y verificable antes de que llegue a la full regression. FRX-v2.2-B/C/D ampliarán telemetría y scheduling, no esta jerarquía documental.
