---
title: "Use Cases — DevPilot Local"
doc_id: "DEVPL-REQ-003"
status: "draft"
version: "0.1.0"
owner: "Ordóñez"
standard: "MIPSoftware"
updated: "2026-06-01"
---

# Use Cases

## UC-001 — Ejecutar readiness pre-code

Actor: desarrollador.  
Precondición: proyecto con estructura inicial.  
Flujo principal:
1. El usuario ejecuta `python -m devpilot_core readiness-check`.
2. El sistema revisa artefactos mínimos.
3. El sistema emite JSON con PASS/FAIL.

Resultado esperado: reporte en `outputs/reports/readiness_check.json`.

## UC-002 — Determinar activación MIASI

Actor: desarrollador.  
Flujo principal:
1. El usuario ejecuta `python -m devpilot_core miasi-required`.
2. El sistema informa que MIASI aplica porque el proyecto es agent-assisted.
