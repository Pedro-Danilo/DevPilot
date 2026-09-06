---
doc_id: "DEVPL-FRX-V2-4-B-MIGRATION-NOTES"
title: "FRX-v2.4-B — Execution Profile Migration Notes"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-09-06"
approval: "approved_by_owner/source-authorized-local-qualification"
---

# FRX-v2.4-B — Execution Profile Migration Notes

## Objective
Migrate the consolidated FRX-v2.3 execution policy into one versioned current-active consumer contract without changing historical evidence.

## Source baseline
- Repo: `repo_DevPilot_Local_405_FRX_V2_4_A_HISTORICAL_CONTRACT_AUTHORITY_WINDOWS_VALIDATED_CANDIDATE.zip`
- Commit: `10acf1864864f1954d07abb8c913a765795fcd9c`
- SHA-256: `1d9f6bd62e2369ac10b54e3516f0f6c8090fa7824f03c09ce7767bee9dc4d52b`
- FRX-v2.4-A: `CLOSED/PASS/WINDOWS-VALIDATED`.

## Migrated current policy
`frx-v2.4-current` preserves deterministic LPT temporal planning, 900-second target shards, max 200 nodeids, manifest transport, one default worker, <=2 workers only by explicit prior opt-in, unknown/unclassified serial handling, completion-first, exact accounting, one-full, same-session resume, composite recovery after functional FAIL and Git-semantic source guard.

## Consumer migration
- `tests full-session plan` is profile-ID based and no longer accepts legacy shard-size topology.
- `run` and `resume` require a governed profile-bound plan.
- `tests full-regression profile|preflight|topology-check` provide read-only governance surfaces.
- The UOC direct full worker is blocked; it cannot start pytest outside the FRX session path.
- Legacy `tests temporal-planner` remains preview-only for historical compatibility and is not an execution consumer.

## Compatibility fixtures
- Positive: v2.3 current topology reproduces the current profile and PASSes.
- Negative: GSDLC-08-E `count50/max50/command-line` topology BLOCKs before budget reservation.

## PASS / BLOCK
PASS requires deterministic profile hash/pointer integrity, profile-only consumer contract, representative preflight PASS, negative downgrade BLOCK before reservation, registry schema/coverage PASS, full=0, browser=0 and S0/S1=0. Any deviation is BLOCK.

## Risks
This migration locks current execution policy; it does not itself consume a full or prove future GSDLC-09 functionality. The first legitimate full remains owned by the corresponding backlog closing micro-sprint.

## Verification commands
Use the delivered Windows guide as the sole operational command source.
