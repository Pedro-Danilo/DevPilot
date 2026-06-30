---
doc_id: "POST-H-018-CONNECTOR-SANDBOX-RUNBOOK"
title: "POST-H-018 — Connector sandbox operational runbook"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-06-30"
approval: "approved_by_owner"
phase: "POST-FASE-H"
source_of_truth: true
preliminary: true
---

# POST-H-018 — Connector sandbox operational runbook

## Propósito

Este runbook define cómo operar el sandbox de conectores de DevPilot Local después de POST-H-018-E. La capacidad es `implemented-initial`: permite validar policy, ejecutar replay determinístico con fixtures locales, revisar redaction checks, verificar binding Policy/Approval/RBAC y ejecutar el subgate `connector-sandbox` dentro de `quality-gate`. No autoriza ejecución real de conectores externos ni `connector write`.

## Comandos operativos

```powershell
$env:PYTHONPATH="src"

python -m devpilot_core connector sandbox exposure --json --write-report
python -m devpilot_core connector sandbox run --mode replay --json --write-report
python -m devpilot_core quality-gate run --profile hardening --json --write-report
```

Validaciones complementarias:

```powershell
python -m devpilot_core schema validate --schema-id ConnectorSandboxPolicy --instance .devpilot/connectors/connector_sandbox_policy.json --json
python -m devpilot_core schema validate --schema-id ConnectorSandboxReport --instance outputs/reports/connector_sandbox_report.json --json
python -m devpilot_core schema validate --schema-id ConnectorPolicyExposureReport --instance outputs/reports/connector_policy_exposure_report.json --json
python -m devpilot_core test-contracts validate --json
python -m devpilot_core test-contracts validate-v2 --json
```

## Evidencia esperada

```text
outputs/reports/connector_policy_exposure_report.json
outputs/reports/connector_policy_exposure_report.md
outputs/reports/connector_sandbox_report.json
outputs/reports/connector_sandbox_report.md
outputs/reports/connector_replay_redaction_report.json
outputs/reports/connector_replay_redaction_report.md
outputs/reports/quality_gate.json
outputs/reports/quality_gate.md
```

Los archivos bajo `outputs/` son evidencia runtime regenerable y no deben versionarse en ZIPs de entrega limpia.

## Criterios PASS

```text
PASS si quality-gate hardening incluye connector-sandbox y el subgate pasa.
PASS si network_used=false y external_api_used=false.
PASS si connector_write_used=false y connector.write_future permanece bloqueado.
PASS si fixtures_total > 0, fixtures_passed == fixtures_total, redaction_passed=true y deterministic_replay=true.
PASS si PolicyEngine se invoca y connector_binding_checked=true antes de aceptar evidencia de replay.
PASS si high/critical connectors evalúan RBAC y side-effecting connectors pasan por ApprovalPolicyChecker.
```

## No-go gates

```text
NO-GO si connector write queda habilitado.
NO-GO si una operación usa red real.
NO-GO si external_api_used=true.
NO-GO si se almacenan secretos reales, tokens, private keys o URLs sensibles en fixtures.
NO-GO si se omite PolicyEngine en conectores gobernados.
NO-GO si se declara que la integración externa productiva está lista.
NO-GO si remote execution o plugin execution se habilitan desde el flujo de conectores.
```

## Procedimiento ante BLOCK

1. Revisar el finding bloqueante en el reporte JSON.
2. Confirmar si el bloqueo viene de policy coverage, replay, redaction, Approval/RBAC o safety flags.
3. No relajar `connector_write_enabled=false`, `network_allowed=false`, `external_api_allowed=false` ni `mutations_allowed=false` para hacer pasar el gate.
4. Corregir fixtures/policy/docs/tests y repetir la validación focal.
5. Si se requiere habilitar write, red, API externa, OAuth, webhooks o ejecución real, crear ADR y backlog específico antes de tocar runtime.

## Límites explícitos

POST-H-018-E cierra el backlog como base local de sandbox de conectores. No implementa OAuth, tokens reales, conectores write, webhooks productivos, APIs externas, background workers remotos, remote execution, plugin execution ni integración productiva externa. Cualquier evolución hacia esas capacidades exige ADR, threat model, approvals, RBAC reforzado, observabilidad y quality gates adicionales.
