---
title: Security Exception
doc_id: MIPS-TPL-SEC-006
doc_type: template
version: 0.1.0
status: draft
owner: AI_agents / MIPSoftware
scope: security-privacy-compliance
created: '2026-05-31'
updated: '2026-05-31'
---

# Security Exception

## Propósito

Registrar una excepción temporal, explícita y aprobada a un control de seguridad.

## Regla

Una excepción no elimina el riesgo. Lo acepta temporalmente bajo owner, expiración, justificación y plan de remediación.

## Campos obligatorios

| Campo | Descripción |
|---|---|
| ID | Identificador de excepción. |
| Control afectado | Gate o requisito incumplido. |
| Riesgo | Descripción del riesgo. |
| Severidad | critical/high/medium/low. |
| Justificación | Motivo de la excepción. |
| Compensating controls | Controles temporales. |
| Owner | Responsable. |
| Aprobador | Responsable autorizado. |
| Expiración | Fecha máxima. |
| Plan de remediación | Qué se hará. |
| Estado | requested/approved/rejected/expired/closed. |

## Ejemplo completo

| Campo | Valor |
|---|---|
| ID | SEC-EX-001 |
| Control afectado | dependency gate |
| Riesgo | dependencia con CVE alta sin fix disponible |
| Justificación | proveedor no ha liberado versión corregida |
| Compensating controls | endpoint no expuesto + WAF rule + monitoring |
| Expiración | 2026-06-30 |
| Aprobador | tech lead/security owner |

## Criterios de rechazo

- Excepción sin fecha de expiración.
- Crítico aceptado sin aprobador.
- No hay compensating controls.
- Se usa para ocultar deuda permanente.

