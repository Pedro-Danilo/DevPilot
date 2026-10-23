---
doc_id: ADR-MP132-013-187
title: "Autoría semántica generativa y revisión Markdown"
status: "PROGRAMMATIC_AMENDMENT"
version: "1.0.0"
date: "2026-10-17"
planning_baseline: "b666c5641c1b8231c5b609216f64490a72ff1763"
execution_authority: false
---
# ADR MP132-013 — Generative Semantic Authoring

## Contexto

R02-06 cerró satisfactoriamente comparación D/L y revisión Owner, pero D preservó B0 sin transformarlo y L resumió/omitió detalles. Eso acredita una evaluación, no Product Vision/Scope/Requirements profesionales. Se adopta la premisa permanente: creatividad contextual en IA; estándares, seguridad, identidad y mutaciones en determinismo.

## Decisión

1. L local `ELIGIBLE_FOR_TASK` genera **un** candidato inicial semántico `.md` por etapa. E es alternativa explícita, opt-in, solo cuando su propia ADR/CostGuard/privacy/egress lo habiliten. D no genera una «opción equivalente» de contenido semántico a partir de templates extractivos.
2. Las alternativas/refinamiento/comparación son **acciones optativas del Owner**, no un flujo D→L→E obligatorio; cada candidata es inmutable, versionada y hash-bound con provenance/context manifest.
3. Owner revisa y edita el documento Markdown vía Guided, generando una nueva revisión; JSON técnico conserva los schemas y receipts. En Planning, autoridad canónica continúa en JSON y Markdown opera como proyección de revisión gobernada.
4. Quality Gate específico de etapa exige coherencia semántica, grounding y completitud antes de approval. El LLM no decide PASS final ni concede permisos. Un fallo de calidad da `REVIEW_REQUIRED/MODEL_REQUIRED/PARTIAL`, con explicación y recuperación; nunca FROZEN automático.
5. Reusar ArtifactCandidateEnvelope/GenerationRoutePolicy, Publication/Lifecycle, Approval Center, Source Registry y PESP vigentes. Comparación de modelos queda opcional en Expert/Settings, no obligatoria en el flujo SDLC.

## Alternativas consideradas

A) D como candidato semántico siempre: descartada, no transforma negocio. B) Siempre dos o más L/E: descartada, costo/latencia y fricción injustificados. C) L-first, alternativas optativas y D para gobernanza: **adoptada programáticamente**.

## Consecuencias y pruebas

Beneficios: autoridad nítida, menor latencia, calidad por contrato, confianza en revisión Markdown. Riesgos: modelo offline o incapaz, alucinaciones, idioma, tokens/latencia, dual-authority y datos sensibles. Tests: proveedor local no disponible, salida incorrecta, prompt injection, referencias no grounded, Markdown editado en UI y successor, E DENY sin egreso, no-double apply, restart/resume. Ejecución técnica en R02-07+ y futuras olas con aprobación individual, no autorizada por esta ADR.
