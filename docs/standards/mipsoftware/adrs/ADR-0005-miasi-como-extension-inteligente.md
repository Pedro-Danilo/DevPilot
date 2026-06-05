---
title: ADR-0005 — Integrar MIASI como extensión inteligente obligatoria
doc_id: ADR-0005
doc_type: adr
version: 0.1.0
status: accepted
owner: AI_agents / MIPSoftware
scope: software-engineering-model
created: '2026-05-31'
updated: '2026-05-31'
decision_status: accepted
---

# ADR-0005 — Integrar MIASI como extensión inteligente obligatoria

## Estado

Aceptado.

## Contexto

MIASI ya fue construido y aprobado como estándar especializado para sistemas agénticos inteligentes. MIPSoftware es un estándar general de ingeniería de software y no debe duplicar ni reemplazar MIASI.

## Decisión

Declarar MIASI como módulo especializado obligatorio de MIPSoftware cuando un proyecto use IA, agentes, LLMs, RAG, memoria, tool calling, automatización inteligente o sistemas adaptativos.

## Consecuencias positivas

- Evita duplicidad documental.
- Mantiene separación clara entre ingeniería general e ingeniería agéntica.
- Permite que proyectos sin IA usen MIPSoftware sin complejidad innecesaria.
- Permite que proyectos con IA cumplan ambos modelos.

## Consecuencias negativas o costos

- Requiere criterios claros de activación MIASI.
- Requiere trazabilidad entre quality gates generales y quality gates agénticos.

## Criterios de cumplimiento

- Todo proyecto debe indicar si activa MIASI.
- Si activa MIASI, debe cumplir sus Agent Cards, Tool Cards, Eval Cards, policy gates y readiness checks.
- La ausencia de MIASI en un sistema con IA bloquea avance a producción.

## Relación con MIASI

Este ADR formaliza la relación jerárquica: MIPSoftware gobierna el ciclo general; MIASI gobierna la capa inteligente/agéntica.

## Referencias

- MIASI v1.0.0.
- NIST AI RMF / GenAI Profile.
- OWASP LLM Top 10.
- OpenTelemetry GenAI.

## Changelog

| Versión | Fecha | Cambio |
|---|---|---|
| 0.1.0 | 2026-05-31 | ADR inicial. |
