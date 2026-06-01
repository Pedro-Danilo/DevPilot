---
title: "ADR-0001 — Adoptar MIPSoftware y MIASI"
doc_id: "DEVPL-ADR-0001"
status: "accepted"
version: "0.1.0"
owner: "Ordóñez"
standard: "MIPSoftware"
updated: "2026-06-01"
---

# ADR-0001 — Adoptar MIPSoftware y MIASI

## Contexto

DevPilot Local será la primera plataforma aplicada construida después de MIPSoftware y MIASI.

## Decisión

Adoptar MIPSoftware como estándar general y MIASI como extensión obligatoria por tratarse de una plataforma agent-assisted SDLC.

## Consecuencias

- Ningún avance importante debe omitir artefactos mínimos.
- Las funciones agentic deben pasar por MIASI.
- El MVP inicia local-first y sin APIs externas.
