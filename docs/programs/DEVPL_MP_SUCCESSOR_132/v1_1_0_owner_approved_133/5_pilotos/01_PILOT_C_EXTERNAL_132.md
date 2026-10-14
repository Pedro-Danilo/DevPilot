---
doc_id: DEVPL-MP-SUCCESSOR-132-01_PILOT_C_EXTERNAL_132
title: "Pilot C — Ensayo aislado de modelos externos con seguridad y costo"
version: "1.1.0"
status: "OWNER_APPROVED_PROGRAM"
baseline_commit: "8db5b44694abcced3231183e05731e732f5b8f24"
owner: "Owner DevPilot"
supersedes_program: "DEVPL_MP_SUCCESSOR_131 v1.0.0"
execution_authority: false
approval_revision: 1
approval_date: "2026-10-13"
approved_by: "Owner Ordóñez (instrucción explícita en conversación)"
approval_scope: "PROGRAMMATIC_PLANNING_ONLY"
owner_decision_ref: "DEVPL-MP-132-OWNER-APPROVAL-133"
---

# Pilot C — Ensayo aislado de modelos externos con seguridad y costo

## Alcance condicional

Pilot C se realiza sólo si el Owner habilita expresamente E y ADR-MP-132-010 adquiere autoridad después del threat model. Usa datos sintéticos y un fixture separado de Pilot B, con proveedor/red/modelo conocidos y costo máximo autorizado. No es prerequisito de la clasificación `LOCAL_FIRST_PROFESSIONAL`, pero sí de `EXTERNAL_ENABLED`.

## Gates obligatorios

`NO_EGRESS` por defecto, secrets-by-reference, revocación/circuit breaker, privacy/PII classification, consent per task/provider, máximo gasto, rate limits, redacción de trazas, retries bounded, schema compatible, evals y negative suite. Denied request **antes** del HTTP. Prohibido inferir habilitación por presencia de `API_KEY`/endpoint.

## Verificación

Test sin credentials, sin presupuesto, rol sin permiso, datos no autorizados, fallback E no consentido y timeout: todos BLOCK sin costo. Prueba positiva con API real y dato sintético, coste real auditado, modelo/version, provenance e Owner decision. MCP/conectores constituyen otro trust boundary opcional, no parte automática de E.
