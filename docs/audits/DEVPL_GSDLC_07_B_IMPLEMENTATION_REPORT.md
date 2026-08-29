---
doc_id: "DEVPL-GSDLC-07-B-IMPLEMENTATION-REPORT"
title: "DEVPL-GSDLC-07-B — ContextPack v2 implementation report"
status: "current"
version: "1.0.0"
owner: "DEVPL-GSDLC-07-B"
updated: "2026-08-29"
approval: "implementation-candidate"
---

# GSDLC-07-B implementation report

## Implementación

07-B añade `ContextPack v2` como successor del RAG local existente. La selección parte del índice lexical versionado, pero antes de sellar contexto aplica `Documentation Source Registry` + `context_pack_v2_policy.json`, filtra fuentes runtime/no registradas/stale, calcula SHA-256 de fuente y fragmento, clasifica freshness/trust, registra selection reason y citation mapping y aplica `ContextBudget` con top-k acotado y prioridad diff-first opcional.

`ContextPackV2Builder` no ejecuta modelos, agentes, tools ni mutaciones. La ruta obligatoria de costo cero continúa siendo lexical/local; embeddings/modelos locales quedan opt-in futuro y API externa no es requisito de PASS. Ante evidencia insuficiente devuelve explícitamente `insufficient-evidence` con cero citas, en lugar de fabricar contexto autoritativo.

## Superficies nuevas y modificadas

- `.devpilot/rag/context_pack_v2_policy.json`: política allowlist/freshness/trust/budget/exclusiones.
- `docs/schemas/context_pack_v2.schema.json`: contrato estricto del pack sellado.
- `src/devpilot_core/rag/context_pack_v2.py`: builder determinístico y provenance sealing.
- `SettingsApplicationService` / `ApplicationService`: preview read-only `settings.rag_context`.
- `GET /api/v1/settings/rag-context`: API autenticada read-only.
- `RagProvenanceView`: panel de administración/diagnóstico en AI Control Center; muestra candidatos antes del presupuesto, pack sellado, hashes/citas/freshness/trust y estrategia de budget.
- `rag_grounding_samples.json` y `context_budget_report.json`: evidencia determinística de grounding/budget.

## Validación local gobernada

El plan 07-B está congelado en `DEVPL_GSDLC_07_B_VALIDATION_PLAN.json`. Resultados finales locales:

- plan selectivo completo: **170/170 PASS**;
- static UI `RagProvenanceView`: **8/8 PASS**;
- Project State: **6/6 PASS**;
- Documentation Governance: **1290 documentos / 0 blocking / 0 warnings**;
- TCR v1/v2: **301/301 PASS**;
- Test Impact v2: `REVIEW_REQUIRED`, riesgo residual `high`, full recomendada por impacto transversal;
- Historical Regression Guard: **PASS** con waiver owner-policy válido;
- full regression ejecutada: **0**, reservada a GSDLC-07-E;
- external API/network/embeddings: **0/no requeridos**;
- high-confidence secrets: **0**.

El plan Windows se reduce a la evidencia estrictamente necesaria: materialización semántica, subset selectivo directo, validadores administrativos, Regression Guard, un único browser focal de `RagProvenanceView`, cleanup, staging allowlisted y promoción three-state.

## Riesgos y limitaciones

Esta es una versión **implemented-initial** de ContextPack v2, no el estado final industrial de RAG. Limitaciones deliberadas:

1. ranking principal sigue siendo lexical; no hay reranker semántico ni embeddings obligatorios;
2. freshness se deriva de metadata disponible y puede quedar `unknown` con warning controlado;
3. `diff-first` es una prioridad determinística, no un modelo de relevancia aprendido;
4. el panel es preview/diagnóstico; 07-C será el primer consumidor del pack dentro de workflows de draft/rewrite/critique;
5. la calidad completa del backlog se evaluará en 07-E mediante groundedness/model evals y la única logical full regression.

## Seguridad

- source allowlist y runtime-path denylist antes de selección;
- SecretGuard sobre query/fragmentos;
- hashes y citation parity obligatorios;
- external sources no se tratan como trusted por defecto;
- `ModelRouteDecision` continúa sin autoridad sobre tools;
- 07-B no habilita agent execution, approval ni filesystem mutation.
