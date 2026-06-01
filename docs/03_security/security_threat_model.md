---
title: "Threat Model — DevPilot Local"
doc_id: "DEVPL-SEC-001"
status: "draft"
version: "0.1.0"
owner: "Ordóñez"
standard: "MIPSoftware"
updated: "2026-06-01"
---

# Threat Model

## Activos

- Repositorios locales.
- Documentos de proyectos.
- Configuración `.env`.
- Reportes de calidad.
- Futuras trazas de agentes.

## Amenazas iniciales

| ID | Amenaza | Riesgo | Mitigación |
|---|---|---:|---|
| T-001 | Escritura fuera del workspace | Alto | Validar rutas y usar dry-run. |
| T-002 | Exposición de secretos | Alto | `.env` ignorado y redacción en reportes. |
| T-003 | Acciones destructivas por agente | Alto | Human approval y policy-as-code. |
| T-004 | Reportes incorrectos | Medio | Tests y validadores. |

## Controles mínimos

- No ejecutar comandos destructivos.
- No requerir credenciales reales.
- No registrar secretos.
- Mantener trazas y reportes auditables.
