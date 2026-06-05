---
title: ADR-0003 — Usar C4 y arc42 como base arquitectónica
doc_id: ADR-0003
doc_type: adr
version: 0.1.0
status: accepted
owner: AI_agents / MIPSoftware
scope: software-engineering-model
created: '2026-05-31'
updated: '2026-05-31'
decision_status: accepted
---

# ADR-0003 — Usar C4 y arc42 como base arquitectónica

## Estado

Aceptado.

## Contexto

El emprendimiento necesita una forma consistente de documentar arquitectura para sistemas web, APIs, CLIs, automatizaciones, plataformas internas y sistemas con IA.

## Decisión

Adoptar C4 como modelo principal de visualización arquitectónica y arc42 como inspiración estructural para documentos de arquitectura.

## Consecuencias positivas

- C4 permite explicar arquitectura por niveles: contexto, contenedores, componentes y código.
- arc42 aporta una estructura práctica para comunicar arquitectura.
- Ambos son tecnológicos agnósticos.

## Consecuencias negativas o costos

- No sustituyen el análisis arquitectónico.
- Requieren criterio para no sobrediagramar.
- La vista de código solo se usará cuando aporte valor.

## Criterios de cumplimiento

- Todo sistema real debe tener al menos C4 contexto y contenedores.
- Componentes se documentan para módulos críticos.
- Decisiones relevantes deben registrarse como ADRs.

## Relación con MIASI

MIASI usa arquitectura de referencia para sistemas agénticos. MIPSoftware define la base arquitectónica general y activa MIASI para componentes inteligentes.

## Referencias

- C4 Model.
- arc42.
- ISO/IEC 25010.
- SEBoK.

## Changelog

| Versión | Fecha | Cambio |
|---|---|---|
| 0.1.0 | 2026-05-31 | ADR inicial. |
