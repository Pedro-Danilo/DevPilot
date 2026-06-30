---
doc_id: "POST-H-018-C-CONNECTOR-REPLAY-REDACTION-REPORT"
title: "POST-H-018-C — Connector replay fixtures y redacción"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-06-30"
approval: "approved"
phase: "POST-FASE-H"
---

# POST-H-018-C — Connector replay fixtures y redacción

## Resultado

Estado: `implemented-initial`.

Se implementa `ConnectorReplayRunner` para validar replay determinístico de conectores a partir de fixtures locales sanitizados. La ejecución de `connector sandbox run --mode replay` integra ahora `evals/fixtures/connector_replay_cases.json`, genera un redaction report y propaga al `ConnectorSandboxReport` métricas de `fixtures_total`, `fixtures_passed`, `redaction_passed` y `deterministic_replay`.

## Artefactos principales

```text
src/devpilot_core/connectors/replay.py
evals/fixtures/connector_replay_cases.json
src/devpilot_core/connectors/sandbox.py
src/devpilot_core/cli.py
tests/test_post_h_018_connector_replay.py
docs/post_h_018_c_manifest.json
```

## PASS/BLOCK

PASS si los fixtures locales pasan redaction checks, no contienen secretos ni URLs, replay es determinístico y los reportes declaran `network_used=false`, `external_api_used=false`, `mutations_performed=false`, `connector_write_used=false` y `secrets_included=false`.

BLOCK si un fixture contiene un token, campo secreto, referencia `.env`, bearer value, private key o URL; si no existe fixture para el conector/operación solicitado; o si replay intenta red, API externa, mutación, connector write, remote execution o plugin execution.

## Límites

POST-H-018-C no ejecuta conectores reales. Replay se satisface exclusivamente desde fixtures locales sanitizados. El binding Policy/Approval/RBAC queda para POST-H-018-D y el quality gate final `connector-sandbox` queda para POST-H-018-E.
