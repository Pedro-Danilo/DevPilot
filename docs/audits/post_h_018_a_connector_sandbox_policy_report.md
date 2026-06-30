---
doc_id: "POST-H-018-A-CONNECTOR-SANDBOX-POLICY-REPORT"
title: "POST-H-018-A — Connector sandbox policy y schemas"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-06-30"
approval: "approved_by_owner"
phase: "POST-FASE-H"
---

# POST-H-018-A — Connector sandbox policy y schemas

## Estado

`implemented-initial`. Este micro-sprint aprueba el backlog POST-H-018 y crea la base contractual del sandbox de conectores.

## Implementado

- Schemas `ConnectorSandboxPolicy`, `ConnectorReplayFixture` y `ConnectorSandboxReport`.
- Policy local `.devpilot/connectors/connector_sandbox_policy.json`.
- Clasificación de conectores actuales por `side_effect`, `risk_level`, `data_sensitivity`, `allowed_modes`, `approval_required`, `rbac_required` y `policy_rules`.
- `ConnectorSandboxPolicyValidator` read-only para validar cobertura de registry y deny-write defaults.
- Pruebas focales de schema, policy coverage y no-go semantics.

## No implementado en POST-H-018-A

- Runner `connector sandbox run`.
- Replay runner determinístico.
- Binding runtime con PolicyEngine/Approval/RBAC.
- Quality gate `connector-sandbox`.
- Connector write real, OAuth, APIs externas, webhooks, background workers o mutaciones externas.

## Criterios PASS

```text
PASS si todos los conectores actuales tienen entrada de sandbox policy.
PASS si network_allowed=false, external_api_allowed=false, mutations_allowed=false y write_allowed=false.
PASS si schemas están registrados en schema_catalog.json.
PASS si high/critical risk declara RBAC y side-effecting connectors requieren approval.
```

## Criterios BLOCK

```text
BLOCK si se habilita connector write.
BLOCK si se habilita red o APIs externas por defecto.
BLOCK si un conector carece de side_effect, risk_level, data_sensitivity o policy_rules.
BLOCK si se declara capacidad productiva de integración externa.
```

## Comandos de verificación

```powershell
$env:PYTHONPATH="src"
python -m pytest -p no:ddtrace tests/test_post_h_018_connector_sandbox_policy.py tests/test_schema_registry.py tests/test_project_global_state.py -q
python -m devpilot_core schema validate --schema-id ConnectorSandboxPolicy --instance .devpilot/connectors/connector_sandbox_policy.json --json
python -m devpilot_core test-contracts validate --json
python -m devpilot_core docs-governance validate --json
```

## Riesgos

- Riesgo de sobreinterpretar el registry como autorización de ejecución. Mitigación: notas y no-go gates explícitos.
- Riesgo de habilitar write accidental en fases futuras. Mitigación: deny-write by default y tests BLOCK.
- Riesgo de fixtures con secretos en POST-H-018-C. Mitigación futura: redaction checks obligatorios.
