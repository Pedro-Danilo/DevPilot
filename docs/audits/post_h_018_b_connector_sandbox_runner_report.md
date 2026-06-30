---
doc_id: "POST-H-018-B-CONNECTOR-SANDBOX-RUNNER-REPORT"
title: "POST-H-018-B — Connector sandbox runner read-only/dry-run"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-06-30"
approval: "approved"
phase: "POST-FASE-H"
---

# POST-H-018-B — Connector sandbox runner read-only/dry-run

## Resultado

Estado: `implemented-initial`.

Se implementa `ConnectorSandboxRunner` como frontera local para validar, dry-run y replay simulado de conectores sin ejecutar llamadas reales. El runner valida `connector_sandbox_policy.json`, bloquea modos fuera de `validate/dry-run/replay`, invoca `PolicyEngine` para conectores gobernados y genera `ConnectorSandboxReport` cuando se solicita evidencia con `--write-report`.

## Artefactos principales

```text
src/devpilot_core/connectors/sandbox.py
src/devpilot_core/cli.py
src/devpilot_core/cli_registry/registry.py
tests/test_post_h_018_connector_sandbox_runner.py
docs/post_h_018_b_manifest.json
```

## PASS/BLOCK

PASS si `connector sandbox run --mode replay --json` retorna `ok=true`, `policy_engine_invoked=true`, `network_used=false`, `external_api_used=false`, `mutations_performed=false` y `connector_write_used=false`.

BLOCK si se solicita `write/execute`, si el modo no está permitido por policy, si el conector no está cubierto por policy o si alguna bandera habilita red/API/mutación/write.

## Límites

POST-H-018-B no ejecuta conectores reales ni fixtures. El replay determinístico con fixtures y redaction checks queda para POST-H-018-C. Approval/RBAC binding y quality gate quedan para POST-H-018-D/E.
