---
title: "Traceability Matrix — DevPilot Local"
doc_id: "DEVPL-REQ-005"
status: "draft"
version: "0.1.0"
owner: "Ordóñez"
standard: "MIPSoftware"
updated: "2026-06-01"
---

# Traceability Matrix

| Business Goal | Requirement | Test | Artifact |
|---|---|---|---|
| Profesionalizar SDLC personal | FR-002 | `test_required_pre_code_artifacts_exist` | `readiness_check.json` |
| Activar MIASI cuando aplica | FR-003 | CLI `miasi-required` | `docs/06_miasi/` |
| Costo externo cero | FR-005 | `pytest -q` sin API keys | `.env.example` |
