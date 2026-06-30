---
doc_id: "POST-H-018-CONNECTOR-SANDBOX-THREAT-MODEL"
title: "POST-H-018 — Connector sandbox threat model"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-06-30"
approval: "approved_by_owner"
phase: "POST-FASE-H"
source_of_truth: true
preliminary: true
---

# POST-H-018 — Connector sandbox threat model

## Alcance

Este threat model cubre el sandbox local de conectores implementado hasta POST-H-018-E. El sistema valida policy, fixtures de replay, redaction, exposure report y binding Policy/Approval/RBAC. No cubre conectores write reales, OAuth, APIs externas, webhooks, background workers remotos, plugin execution ni remote execution porque siguen fuera de alcance.

## Activos protegidos

```text
- Código fuente y documentación del workspace.
- Metadatos de conectores y policies locales.
- Fixtures de replay y reportes de evidencia.
- Secretos potenciales que no deben entrar en fixtures ni reportes.
- Frontera PolicyEngine / Approval / RBAC.
```

## Amenazas principales

| Amenaza | Riesgo | Control actual |
|---|---:|---|
| Interpretar registry como autorización de ejecución | Alto | Runbook y reports separan declared/validated/replayed/executable. |
| Habilitar connector write accidentalmente | Crítico | `connector_write_enabled=false`, `connector.write_future` sintético bloqueado y subgate `connector-sandbox`. |
| Usar red/API externa durante replay | Alto | Fixtures locales, safety flags y no-go gates. |
| Filtrar secretos en fixtures | Alto | `ConnectorReplayRunner` bloquea patrones de tokens, `.env`, private keys, bearer values y URLs. |
| Omitir Approval/RBAC en conectores de riesgo | Alto | Exposure report exige ApprovalPolicyChecker para side-effecting y RBAC para high/critical. |
| Sobredeclarar madurez productiva | Medio-alto | Estado `implemented-initial` y disclaimers en README/runbook/backlog. |

## Controles PASS/BLOCK

```text
PASS si policy_coverage_complete=true.
PASS si write_future_blocked_total == connectors_total.
PASS si all_high_risk_rbac_evaluated=true.
PASS si all_side_effecting_future_write_blocked=true.
PASS si network_used=false, external_api_used=false, mutations_performed=false y connector_write_used=false.

BLOCK si connector write pasa, si red/API externa aparece como usada, si hay secretos en fixtures, si falta RBAC para high/critical o si se declara integración externa productiva.
```

## Decisión de seguridad vigente

El sandbox de conectores es una base local de evaluación y evidencia. No es una autorización de ejecución externa. Habilitar cualquier capacidad de write, red, OAuth, webhook, remote execution o plugin execution requiere ADR nueva, threat model ampliado, tests de regresión, runbook, observabilidad y aprobación explícita del owner.
