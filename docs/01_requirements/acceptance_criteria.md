---
title: "Acceptance Criteria — DevPilot Local"
doc_id: "DEVPL-REQ-004"
status: "draft"
version: "0.1.0"
owner: "Ordóñez"
standard: "MIPSoftware"
updated: "2026-06-01"
---

# Acceptance Criteria

| ID | Criterio | Evidencia |
|---|---|---|
| AC-001 | El entorno se instala localmente. | `.venv` activo y `pytest -q` PASS. |
| AC-002 | Readiness report se genera. | `outputs/reports/readiness_check.json`. |
| AC-003 | No se requieren API keys. | `.env.example` no contiene secretos reales. |
| AC-004 | MIASI se activa formalmente. | `docs/06_miasi/*` presente. |
