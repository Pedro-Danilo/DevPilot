---
title: Threat Model
doc_id: MIPS-TPL-SEC-001
doc_type: template
version: 0.1.0
status: draft
owner: AI_agents / MIPSoftware
scope: security-privacy-compliance
created: '2026-05-31'
updated: '2026-05-31'
---

# Threat Model

## Propósito

Identificar amenazas, superficies de ataque, controles, mitigaciones y riesgo residual antes de implementación o release.

## Cuándo usarla

- Sistema expuesto a usuarios externos.
- Sistema con datos personales o sensibles.
- Sistema con roles/permisos.
- Sistema con integraciones externas.
- Sistema con IA/agentes mediante MIASI.

## Campos obligatorios

| Campo | Descripción |
|---|---|
| Sistema | Nombre y versión. |
| Alcance | Módulos incluidos/excluidos. |
| Activos | Datos, servicios, credenciales, procesos críticos. |
| Actores | Usuarios legítimos, administradores, servicios y adversarios. |
| Límites de confianza | Frontend/backend/db/terceros/CI/agentes. |
| Flujos de datos | Entradas, salidas y persistencia. |
| Amenazas | Amenazas identificadas. |
| Mitigaciones | Controles propuestos. |
| Riesgo residual | Bajo/medio/alto/crítico. |
| Owner | Responsable de mitigación. |
| Estado | open/mitigated/accepted/closed. |

## Ejemplo completo

| Amenaza | Activo | Impacto | Probabilidad | Mitigación | Residual | Owner | Estado |
|---|---|---:|---:|---|---:|---|---|
| IDOR en consulta de órdenes | datos de clientes | alto | medio | verificar ownership server-side | bajo | backend lead | mitigated |
| API key expuesta en logs | secretos | crítico | bajo | redaction + secret scan CI | bajo | security lead | mitigated |
| Prompt injection contra agente de soporte | datos de clientes | alto | medio | MIASI policy + output filter + eval adversarial | medio | AI lead | open |

## Criterios de revisión

- Amenazas críticas tienen mitigación o bloqueo.
- Límites de confianza están claros.
- Datos sensibles están identificados.
- Riesgo residual está justificado.

## Criterios de rechazo

- No identifica activos.
- No incluye mitigaciones.
- No asigna owners.
- Ignora IA/agentes cuando existen.

