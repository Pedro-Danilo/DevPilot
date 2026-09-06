---
doc_id: "ADR-FRX-005"
title: "Current Full Regression Execution Profile Lock"
status: "accepted"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-09-06"
approval: "approved_by_owner/FRX-v2.4-B"
---

# ADR-FRX-005 — Current Full Regression Execution Profile Lock

## Context
FRX-v2.1–v2.3 established completion-first resumable execution, temporal LPT planning, manifest nodeid transport and a bounded two-worker opt-in only for proven-safe work. GSDLC-08-E demonstrated that a consumer could still reconstruct low-level topology (`count50/max50`) instead of consuming the consolidated current policy.

## Decision
Full Regression consumers MUST select a versioned `FullRegressionExecutionProfile` by `profile_id`. The current pointer resolves to exactly one `current-active` profile. Planner, target shard seconds, max nodeids, nodeid transport, default workers, parallel ceiling, unknown/isolation policy, completion-first, exact accounting, one-full semantics, resume semantics and source guard are owned by that profile.

The public GSDLC-facing `tests full-session plan` surface accepts `profile-id` and full-budget state, not low-level topology knobs. `run`/`resume` validate that the persisted plan was produced by the current governed profile. The legacy temporal-planner command remains preview-only and cannot reserve or execute the full.

Every full must pass the read-only machine-readable preflight before budget reservation. The preflight validates collection seal, registry schema/coverage, duration coverage/cold-start policy, conflict/isolation consistency, topology, ETA, worker policy and budget state. It never executes tests and never reserves the full.

The historical UOC direct `pytest -q` full worker is BLOCKED. Quality UI/operations may point operators to the governed session path but cannot bypass the profile lock.

## Consequences
- Silent `manifest/max200 -> command-line/count50/max50` downgrade becomes deterministic BLOCK.
- Low-level overrides require an explicit owner-approved waiver scoped to named fields; default is BLOCK.
- The current profile can evolve only by source-controlled registry/pointer change plus tests/evidence.
- Safe parallelism remains opt-in; the default lane is one worker.
- Full budget remains 0/1 and is reserved only after a PASS preflight by a later legitimate closing backlog.

## Risks
- Existing internal/historical programmatic tests may still call lower-level planner functions. They are not consumer authority and must not be exposed as a GSDLC execution bypass.
- Duration telemetry is environment-specific; unknown nodeids are deliberately serialized and included in ETA through deterministic cold-start fallback.
- This is policy-lock v1.0; it does not claim future distributed/remote execution support.

## PASS / BLOCK
PASS when exactly one current profile is hash-valid, consumer low-level overrides are blocked, the representative v2.3 profile passes preflight, the 08-E regression fixture blocks before budget reservation, Isolation/Duration schema+coverage rules pass, and full/browser remain 0/0.

BLOCK on pointer/hash drift, unsealed collection, registry schema/coverage failure, worker/topology downgrade, budget state other than available 0, direct full worker invocation, or S0/S1.

## Verification commands
Use the FRX-v2.4-B Windows validation guide delivered with the implementation bundle. The guide is the single operator authority and avoids duplicate command instructions.
