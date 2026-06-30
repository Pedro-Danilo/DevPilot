---
doc_id: "POST-H-018-D-CONNECTOR-POLICY-BINDING-REPORT"
title: "POST-H-018-D — Connector Policy/Approval/RBAC binding report"
status: "approved"
owner: "Ordóñez"
updated: "2026-06-30"
version: "1.0.0"
source_of_truth: true
preliminary: true
---

# POST-H-018-D — Connector Policy/Approval/RBAC binding report

## Propósito

POST-H-018-D conecta el sandbox de conectores con controles determinísticos de PolicyEngine, ApprovalPolicyChecker y RBAC local sin habilitar ejecución real de conectores, red, APIs externas ni `connector write`.

## Alcance implementado

- Reglas mínimas `connector.validate`, `connector.replay` y `connector.write_future`.
- `connector.write_future` se evalúa como acción sintética sensible y debe quedar deny/block.
- Conectores read-only conservan policy coverage.
- Conectores side-effecting (`simulation`, `network_cost`) requieren evaluación de ApprovalPolicyChecker y bloquean sin approval válido.
- Conectores `high` y `critical` evalúan RBAC.
- `connector sandbox exposure` genera un reporte local por riesgo, side effect y estado de binding.
- `connector sandbox run` integra el binding antes de aceptar replay/dry-run como evidencia.

## Comandos principales

```powershell
$env:PYTHONPATH="src"
python -m devpilot_core connector sandbox exposure --json --write-report
python -m devpilot_core connector sandbox run --mode replay --json --write-report
python -m devpilot_core schema validate --schema-id ConnectorPolicyExposureReport --instance outputs/reports/connector_policy_exposure_report.json --json
```

## PASS/BLOCK

PASS si todos los conectores tienen policy coverage, `connector.write_future` queda bloqueado, RBAC se evalúa para riesgo alto/crítico y los reportes conservan `network_used=false`, `external_api_used=false`, `mutations_performed=false` y `connector_write_used=false`.

BLOCK si un conector write futuro pasa, si un conector de riesgo alto no evalúa RBAC, si una clasificación side-effecting no exige ApprovalPolicyChecker, si falta policy coverage o si aparece red/API externa/mutación/write.

## Límites

Esta es una versión `implemented-initial`. No habilita conectores externos reales, OAuth, tokens, webhooks, background workers, mutación de sistemas externos, remote execution ni plugin execution. El quality gate final y el runbook operativo específico de conectores quedan para POST-H-018-E.
