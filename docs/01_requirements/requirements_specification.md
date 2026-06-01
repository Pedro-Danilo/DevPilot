---
title: "Requirements Specification — DevPilot Local"
doc_id: "DEVPL-REQ-001"
status: "draft"
version: "0.1.0"
owner: "Ordóñez"
standard: "MIPSoftware"
updated: "2026-06-01"
---

# Requirements Specification

## Requerimientos funcionales

| ID | Requerimiento | Prioridad | Criterio de aceptación |
|---|---|---:|---|
| FR-001 | El sistema debe inicializar la estructura base de un proyecto MIPSoftware. | Alta | Dada una carpeta vacía, genera estructura documental mínima. |
| FR-002 | El sistema debe validar artefactos pre-code obligatorios. | Alta | Reporta PASS si todos existen y tienen contenido mínimo. |
| FR-003 | El sistema debe indicar si MIASI aplica. | Alta | Para DevPilot Local retorna `miasi_required=true`. |
| FR-004 | El sistema debe generar reportes JSON. | Alta | Crea `outputs/reports/readiness_check.json`. |
| FR-005 | El sistema debe ejecutarse sin API keys. | Alta | Todas las pruebas pasan sin `.env` real. |

## Requerimientos no funcionales

| ID | Atributo | Requerimiento medible | Umbral |
|---|---|---|---|
| NFR-001 | Portabilidad | Debe ejecutarse en Windows con Python local. | Windows + Python 3.10+ |
| NFR-002 | Seguridad | No debe ejecutar acciones destructivas por defecto. | 100% dry-run en MVP |
| NFR-003 | Testabilidad | Debe tener pruebas herméticas. | `pytest -q` PASS |
| NFR-004 | Trazabilidad | Debe emitir reportes en outputs. | JSON generado |

## Restricciones

- No usar APIs externas en el MVP.
- No almacenar secretos reales.
- No escribir fuera del workspace del proyecto.
