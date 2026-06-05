---
title: "ADR-0002 — Core local-first con CLI inicial y UI futura"
doc_id: "DEVPL-ADR-0002"
status: "accepted"
version: "1.0.0"
owner: "Ordóñez"
standard: "MIPSoftware"
phase: "SPRINT-PRECODE-03"
updated: "2026-06-04"
accepted_by: "Ordóñez"
accepted_at: "2026-06-04"
acceptance_scope: "SPRINT-PRECODE-03 architecture baseline"
---
# ADR-0002 — Core local-first con CLI inicial y UI futura

## Contexto

DevPilot debe iniciar rápido, ser testeable, local-first y útil antes de construir interfaces visuales. Sin embargo, la evolución hacia desktop y web es un compromiso del producto.

## Decisión

Construir primero un **DevPilot Core** reutilizable y exponerlo inicialmente por CLI. Desktop y Web deberán consumir el mismo core, no duplicar lógica.

## Consecuencias

- La CLI permite validar reglas, reportes y gates con bajo costo.
- El core se mantiene como activo principal.
- Desktop/Web llegan después con menor riesgo.
- Se evita crear una UI bonita sobre reglas inmaduras.
