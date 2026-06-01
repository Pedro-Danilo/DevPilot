---
title: "Runbook — DevPilot Local"
doc_id: "DEVPL-OPS-002"
status: "draft"
version: "0.1.0"
owner: "Ordóñez"
standard: "MIPSoftware"
updated: "2026-06-01"
---

# Runbook

## Instalación

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .[dev]
```

## Validación

```powershell
pytest -q
python -m devpilot_core readiness-check
python -m devpilot_core miasi-required
```

## Recuperación básica

Si el entorno falla, eliminar `.venv`, recrearlo y reinstalar dependencias.
