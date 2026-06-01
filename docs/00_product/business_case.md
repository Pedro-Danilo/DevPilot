---
title: "Business Case — DevPilot Local"
doc_id: "DEVPL-PROD-002"
status: "draft"
version: "0.1.0"
owner: "Ordóñez"
standard: "MIPSoftware"
updated: "2026-06-01"
---

# Business Case — DevPilot Local

## Justificación

DevPilot Local reduce improvisación técnica, mejora trazabilidad, acelera preparación de proyectos y permite aplicar MIPSoftware/MIASI de forma repetible antes de escribir código productivo.

## Beneficios esperados

- Mejor calidad de requerimientos.
- Arquitectura mínima antes de implementación.
- Evidencia de seguridad y pruebas.
- Activación controlada de MIASI en sistemas inteligentes.
- Menor deuda documental.

## Costos del MVP

| Rubro | Costo externo |
|---|---:|
| Python local | 0 |
| Git local | 0 |
| pytest | 0 |
| LLM/API | 0 |

## Riesgos de negocio

| Riesgo | Mitigación |
|---|---|
| Sobredocumentar antes de validar utilidad | MVP enfocado en artefactos mínimos y CLI simple |
| Convertirlo en plataforma demasiado grande | Roadmap por sprints pequeños |
| Dependencia de proveedores IA | Mock/local-first por defecto |

## Decisión

Procede a fase de requerimientos si el MVP se mantiene local-first, sin costo externo y con foco en validadores antes que agentes autónomos.
