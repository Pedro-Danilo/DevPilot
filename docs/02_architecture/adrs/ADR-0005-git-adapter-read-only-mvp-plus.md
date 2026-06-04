---
title: "ADR-0005 — Git Adapter read-only en MVP+"
doc_id: "DEVPL-ADR-0005"
status: "proposed"
version: "0.1.0"
owner: "Ordóñez"
standard: "MIPSoftware"
phase: "SPRINT-PRECODE-03"
updated: "2026-06-02"
---
# ADR-0005 — Git Adapter read-only en MVP+

## Contexto

DevPilot debe operar sobre repos reales. Git es central para trazabilidad, cambios, ramas y commits. Sin embargo, modificar repos automáticamente introduce riesgo.

## Decisión

El primer Git Adapter será read-only. Debe consultar branch, commit, dirty state y diff summary sin modificar el repo. Cualquier acción posterior de commit, branch, patch o reset requerirá policy gate y human approval.

## Consecuencias

- Se obtiene valor de trazabilidad sin riesgo destructivo inicial.
- El futuro patch/refactor flow queda preparado.
- Se evita automatización peligrosa prematura.
