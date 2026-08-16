---
doc_id: "DEVPL-GSDLC-01-A-STATE-MIGRATION-CONTRACT"
title: "WorkspaceEngineeringState v1 — migration contract"
status: "implemented-initial"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-08-16"
approval: "pending_owner_01_a_adjudication"
program_id: "DEVPL-GSDLC"
micro_sprint: "DEVPL-GSDLC-01-A"
---
# WorkspaceEngineeringState v1 — migration contract

## Initial version

`schema_version=1.0` is the first durable version. There is no fabricated legacy migration.

The v1 migrator therefore performs an idempotent identity migration after typed validation. Missing, unknown or newer schema versions fail closed and require an explicit successor migration before the record can be loaded.

## Future rule

Future migrations must be sequential and explicit (`1.0 → 1.1 → ...`), preserve workspace/project/root binding, never infer PASS/APPROVED from missing data, and emit evidence before overwriting the prior durable record. Destructive implicit migration is prohibited.

## Recovery

A corrupt/partial JSON document is a BLOCK, not a blank NEW state. The source can be reconstructed in a later recovery flow from registry metadata, canonical artifacts and Git, but reconstruction must never silently overwrite evidence.
