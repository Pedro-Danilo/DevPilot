---
title: "Política de privacidad y gobierno de datos MIASI"
version: "1.0.0"
status: "approved"
owner: "AI_agents"
scope: "engineering-model/reference"
updated: "2026-05-31"
doc_type: "reference"
related_controls:
  - "MIASI-DATA-001"
  - "MIASI-DATA-002"
---
# Política de privacidad y gobierno de datos MIASI

## 1. Propósito

Definir reglas mínimas de clasificación, minimización, retención, uso, redacción y eliminación de datos para sistemas agénticos aplicados a DevPilot Local, FreelanceOps Agent y MicroVenta Agent.

## 2. Principios

| Principio | Regla |
|---|---|
| Minimización | El agente solo debe recibir datos necesarios para la tarea. |
| Propósito explícito | Todo dato debe tener finalidad documentada. |
| Retención limitada | Todo dato persistente debe declarar plazo de retención. |
| Redacción por defecto | Secretos, tokens, datos personales y datos sensibles se redactan en logs. |
| Separación de ambientes | Datos reales no se mezclan con fixtures, demos o tests. |
| Revisión humana | Datos sensibles usados para acciones externas requieren revisión. |
| Derecho a eliminación | Todo sistema debe prever eliminación o anonimización. |

## 3. Clasificación de datos

| Clase | Descripción | Ejemplos | Control mínimo |
|---|---|---|---|
| `public` | Datos destinados a difusión pública. | README, docs públicas. | Validar licencia/fuente. |
| `internal` | Datos internos no sensibles. | Backlogs, tareas, decisiones. | Control de acceso básico. |
| `confidential` | Datos de proyecto, cliente o negocio. | Propuestas freelance, precios, reportes. | Redacción, backups, permisos. |
| `personal` | Datos que identifican personas. | Cliente, email, teléfono. | Minimización, retención, eliminación. |
| `sensitive` | Datos de alto impacto. | Credenciales, pagos, documentos privados. | No exponer en LLM externo sin aprobación. |
| `secret` | Credenciales técnicas. | API keys, tokens. | Secret management obligatorio. |

## 4. Reglas por proyecto aplicado

| Proyecto | Datos probables | Riesgo | Regla mínima |
|---|---|---|---|
| DevPilot Local | Repos, issues, código, secretos accidentales. | Medio/alto | Secret scan, sandbox, no subir código sensible a API externa sin aprobación. |
| FreelanceOps Agent | Clientes, propuestas, mensajes, plataformas. | Medio/alto | No automatizar envíos masivos; datos de clientes con retención definida. |
| MicroVenta Agent | Clientes, ventas, productos, pagos manuales. | Alto | No almacenar tarjetas; pagos por proveedor; separar contabilidad operativa de formal. |

## 5. Campos obligatorios en Data Handling Sheet

- `data_category`
- `source`
- `purpose`
- `storage_location`
- `retention_period`
- `deletion_process`
- `redaction_rules`
- `external_model_allowed`
- `human_approval_required`
- `owner`

## 6. Criterios de cumplimiento

- Todo agente que procese datos de cliente completa `data_handling_sheet.md`.
- Todo dato sensible queda excluido de logs, prompts y trazas sin redacción.
- Todo uso de API externa con datos confidenciales debe pasar por policy gate.
- Todo dataset de evaluación debe usar fixtures sintéticos salvo excepción.

## 7. Criterios de bloqueo

- Datos personales sin clasificación bloquean operación.
- Secretos en logs o reportes bloquean release.
- Datos de pago almacenados sin proveedor autorizado bloquean producción.
- Información de cliente usada en LLM externo sin aprobación bloquea ejecución.
