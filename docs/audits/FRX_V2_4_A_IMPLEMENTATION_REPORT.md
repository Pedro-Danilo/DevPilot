---
doc_id: "DEVPL-FRX-V2-4-A-IMPLEMENTATION-REPORT"
title: "FRX-v2.4-A — Historical Contract Authority Hardening — Implementation Report"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-09-06"
approval: "approved_by_owner/source-authorized-local-qualification"
---

# FRX-v2.4-A — Implementation Report

## Objective
Separate immutable historical facts from mutable `current-active` state so historical contracts cannot produce false FAIL after legitimate successor evolution.

## Source authority
- Baseline: `repo_DevPilot_Local_404_DEVPL_GSDLC_08_E_FINAL_CLOSURE_RECONCILIATION_WINDOWS_VALIDATED_CANDIDATE.zip`
- Commit: `c0347423b78c67ed93f9eb4a2af39e0411b1d22f`
- SHA-256: `c90fb00a4416bb62c50e161b1eb837efcf88f88d0d3c19d0c0bcbc9fd47cb767`
- Scope: only `FRX-v2.4-A`; FRX-v2.4-B and GSDLC-09 are not implemented.

## Implemented
- Machine-readable six-scope Historical Contract Authority Registry.
- Deterministic `HistoricalContractAuthorityGate`, integrated into Documentation Governance.
- FRX-v2.3-E historical planning contract migrated to an explicit immutable semantic pre-execution fixture.
- GSDLC-08-E lifecycle split into `required_at_detection` and `pending_now` while preserving the legacy historical fact.
- Complete JSON Schema checks for Isolation and Duration registries, plus existing isolation semantics and duration rejected-telemetry guard.
- Negative/positive authority tests and 46-FAIL authority audit.
- Owner-approved scoped Historical Regression Guard waiver because the sprint source explicitly requires `full=0`.

## Local qualification result
- Focal authority tests: `12/12 PASS`.
- Bounded impacted: `40/40 PASS`.
- Historical Contract Authority Gate: `PASS`; authority contracts=7; leakage=0; lifecycle ambiguities=0; registry schema errors=0.
- TestIsolationRegistry: `2980` entries; complete schema + semantics PASS.
- NodeDurationRegistry: complete schema PASS; rejected telemetry=0.
- TCR v1/v2: PASS; `319` contracts.
- Project State / Documentation Governance / Evidence Freshness / API contract drift: PASS.
- Historical Regression Guard: PASS with owner-approved scoped waiver; full/browser remain `0/0`.
- S0/S1: `0/0`.
- API/UI not started; network/external API not used.

## Local qualification target
PASS requires: focal 12/12, bounded impacted PASS, Historical Regression Guard PASS with valid waiver, Project State/TCR v1/v2/Docs Governance/Evidence Freshness/API contract drift PASS, authority leakage=0, registry schema errors=0, S0/S1=0, full=0, browser=0.

## Risks and limitations
- The pre-execution FRX-v2.3-E fixture is a documented semantic reconstruction; it is not represented as byte-identical archived evidence.
- Repo404 does not carry the original runtime manifest containing all 46 failed nodeids; the already-adjudicated authority category counts are preserved without inventing nodeids.
- Windows validation and Git three-state promotion remain pending until the supplied operator runs on the official Windows environment.

## PASS / BLOCK
PASS only when all local/Windows qualification gates above pass and no second full/browser run occurs. BLOCK on any historical→current leakage, missing historical snapshot, ambiguous lifecycle field, FRX registry schema/semantic error, S0/S1, unsafe Git ancestry, or forbidden artifact in packaging.

## Verification commands
Use the single Windows guide delivered with the validation bundle. It is the canonical operator procedure; commands are intentionally not duplicated here.

## Windows closure result
After the Windows operator `validate` step passes, `close` applies this technical closure overlay: `CLOSED/PASS/WINDOWS-VALIDATED`, FRX-v2.4-B authorized, full/browser remain `0/0`, and all deterministic post-close gates must remain PASS. Git/remote/package receipts remain external runtime evidence and are not fabricated into source.
