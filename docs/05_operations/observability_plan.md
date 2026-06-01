---
title: "Observability Plan — DevPilot Local"
doc_id: "DEVPL-OPS-001"
status: "draft"
version: "0.1.0"
owner: "Ordóñez"
standard: "MIPSoftware"
updated: "2026-06-01"
---

# Observability Plan

## Señales iniciales

| Señal | Formato | Ubicación |
|---|---|---|
| Readiness report | JSON | `outputs/reports/` |
| Logs futuros | JSONL | `outputs/logs/` |
| Quality gate | JSON/Markdown | `outputs/reports/` |

## Regla

Toda validación debe producir evidencia local auditable.
