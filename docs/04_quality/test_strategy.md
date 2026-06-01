---
title: "Test Strategy — DevPilot Local"
doc_id: "DEVPL-QUAL-001"
status: "draft"
version: "0.1.0"
owner: "Ordóñez"
standard: "MIPSoftware"
updated: "2026-06-01"
---

# Test Strategy

## Pruebas mínimas MVP

| Tipo | Objetivo | Evidencia |
|---|---|---|
| Unit | Validadores de artefactos | pytest |
| Integration | CLI mínimo | pytest/subprocess futuro |
| Security | No secretos reales | revisión `.env.example` |
| Regression | Bugs críticos | test por bug |

## Quality gate inicial

`pytest -q` debe pasar antes de cualquier commit estable.
