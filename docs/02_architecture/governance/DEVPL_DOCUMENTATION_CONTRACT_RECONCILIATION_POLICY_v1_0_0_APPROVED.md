---
doc_id: "DEVPL-DOCUMENTATION-CONTRACT-RECONCILIATION-POLICY"
title: "DevPilot — Documentation and historical contract reconciliation policy"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-08-20"
approval: "approved_by_owner"
program_id: "DEVPL"
scope: "All successor sprints/backlogs and historical contract evolution"
effective_from: "DEVPL-GSDLC-03-E-REG-001"
---

# DevPilot — Documentation and historical contract reconciliation policy

## 1. Objective

Prevent recurrent test failures caused by **documentary drift, mutable-current pointers being treated as frozen historical facts, stale derived counters, schema-incompatible sprint annotations, incomplete cross-registry propagation, and runtime-state contamination**.

This policy is cumulative. It applies to every DevPilot successor sprint unless explicitly superseded by an owner-approved governance decision.

## 2. Contract classes

Every governed engineering artifact must be treated as exactly one of these lifecycle classes:

1. **frozen-snapshot** — immutable close-time artifact (`*_at_close`, approved adjudication, frozen registry). Historical tests MUST target this artifact when asserting exact historical bytes/counts/statuses.
2. **current-active** — mutable successor authority. Tests MUST validate semantic invariants and current schema, not freeze predecessor totals or copy.
3. **successor-aware** — historical test/contract that preserves predecessor invariants while explicitly allowing approved successor growth.
4. **derived** — counters/mappings/reports generated from another current authority. They MUST be reconciled in the same change transaction as their source.
5. **runtime-ephemeral** — databases, cookies, runtime evidence, temp state. They MUST be excluded from source/evidence baselines where policy says so and isolated from test fixtures.
6. **deprecated-after-proof** — retained only with an explicit successor pointer and non-authoritative lifecycle.

## 3. Frozen-history rule

A historical contract MUST NOT compare an evolving current artifact to a predecessor-era exact count/hash/status when a frozen close-time snapshot exists.

Required pattern:

```text
historical exact fact -> *_at_close / adjudication / immutable snapshot
current successor fact -> current-active registry + semantic invariant
```

Forbidden pattern:

```text
historical test -> exact hash/count of mutable current registry
```

unless the test explicitly proves that the artifact is contractually frozen forever.

## 4. Current-active transaction rule

Any change to a current-active registry must reconcile, in the **same sprint transaction**, all impacted layers:

```text
runtime/API/UI implementation
→ active registry row(s)
→ schema validity
→ summary counters
→ policy/RBAC/approval binding
→ MIASI tool/rule links
→ derived capability mappings
→ source/document registry pointers
→ TCR/test-contract references
→ successor-aware historical tests
→ focused deterministic validators
```

A sprint must not add a route/action/tool and defer its cross-registry reconciliation to the closing full regression.

## 5. Schema discipline

Do not extend a frozen/global schema merely to carry sprint-specific prose or transient status.

Use existing long-lived enum values plus notes/metadata where the schema permits them. Sprint-specific fields that are not schema-defined must not be injected into strict-schema documents.

Example: use `implemented-initial` plus `notes` rather than inventing `implemented-initial-gsdlc-03-d` when the schema enum does not allow it.

## 6. Mutable pointer ownership

Generic mutable pointers and program-specific pointers have different ownership.

- `last_registered_sprint`: must remain synchronized with the canonical global project-state authority expected by POST-H/UOC governance.
- `gsdlc_last_registered_micro_sprint`: owns current DEVPL-GSDLC progression.
- historical close facts: live in frozen snapshots/adjudications, never in the mutable pointer.

A successor program must not repurpose a global pointer if a dedicated namespace exists.

## 7. Derived-counter rule

For every modified registry, recompute counts from the live collection instead of manually carrying predecessor totals.

Examples:

- API `routes_total`, protected/public/mutating/application-service/policy-bound/source-write totals;
- UI route totals;
- UI capability route mappings/totals;
- RBAC route/action policy totals;
- sensitive-action totals and MIASI link totals.

A derived counter mismatch is a **BLOCK before full regression**.

## 8. Cross-registry closure rule

A new sensitive mutation is incomplete until all required relationships exist and validate:

```text
API route
↔ sensitive action
↔ RBAC policy
↔ MIASI policy rule
↔ MIASI tool
↔ UI capability/route (when exposed)
↔ test contract
```

No orphan ID is allowed.

## 9. Runtime-state isolation rule

Test fixtures that copy `.devpilot` or another platform tree MUST explicitly exclude runtime-ephemeral stores (`auth.db*`, `devpilot.db*`, caches and equivalent runtime DBs).

Source-exclusion means “not tracked/not packaged as canonical source”; it does **not** mean “the runtime file can never exist while DevPilot is running.” Historical tests must assert the correct invariant.

## 10. Successor-aware UI contract rule

Historical UI tests must preserve route IDs, safety/no-go contracts and frozen snapshots, but must not freeze obsolete labels, route totals, navigation hierarchy or troubleshooting copy after an approved successor UX changes them.

Static reporters should accept semantic successor equivalents (for example human-session authentication messaging replacing legacy token copy) while continuing to fail closed on missing security/error states.

## 11. Pre-full Contract Reconciliation Sweep

Before the one authorized closing full regression, run a deterministic **Contract Reconciliation Sweep**. It must fail if any of these exist:

- strict-schema validation error;
- current registry summary != live collection;
- active API route absent from RBAC/policy where required;
- sensitive action missing MIASI rule/tool/RBAC binding;
- current UI route absent from derived UI-capability mapping;
- mutable global pointer inconsistent with its owner authority;
- historical test freezes a mutable current artifact despite an available frozen snapshot;
- runtime-ephemeral state is copied into isolated test platform fixtures;
- TCR/docs governance has blocking drift.

The sweep is mandatory before expensive full regression. The full regression must not be used as the first detector of deterministic registry drift.

## 12. Exactly-once full regression recovery

The DEVPL-GSDLC transversal validation policy remains authoritative: one closing full regression per backlog.

If that full fails:

1. preserve its durable marker/log/JUnit/failed-nodeid list;
2. classify failures by common root cause;
3. patch causal source/contracts only;
4. run causal tests;
5. run the **exact failed-nodeid selective retest**;
6. run impact-selected deterministic/historical guards;
7. write a machine-readable composite recovery attestation;
8. **do not run a second full regression**.

## 13. Sprint checklist

Every successor sprint must answer before close:

- What current-active contracts changed?
- What frozen snapshots are relevant?
- Which derived registries/counters were recalculated?
- Which historical tests were made successor-aware, and why is that not test weakening?
- Which runtime-ephemeral stores were isolated?
- Did API ↔ sensitive action ↔ RBAC ↔ MIASI ↔ UI mappings remain total?
- Did Documentation Governance, TCR and contract sweep pass before the full?
- Was any historical frozen artifact overwritten? Expected answer: **no**.

## 14. PASS/BLOCK

PASS requires zero unclassified deterministic drift and all impacted frozen/current/successor relationships explicitly reconciled.

BLOCK if a change is made only to silence a test without identifying the artifact lifecycle and owning source of truth, or if a frozen historical artifact must be rewritten to make the successor pass.

## 15. Current application — GSDLC-03-E-REG-001

The first application of this policy classifies the 67 failures from the exactly-once GSDLC-03-E full regression into shared causes rather than 67 independent product bugs: runtime auth-state isolation, API registry drift, sensitive-action/RBAC/MIASI drift, derived UI-capability drift, mutable source-registry pointer contamination, historical frozen-vs-current assertions, and obsolete static UI-copy/reporting oracles.

The recovery preserves the failed full as immutable evidence and uses selective/composite recovery only.
