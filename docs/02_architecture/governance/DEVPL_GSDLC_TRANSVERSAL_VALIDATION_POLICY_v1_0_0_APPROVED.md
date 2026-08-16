---
doc_id: "DEVPL-GSDLC-TRANSVERSAL-VALIDATION-POLICY"
title: "DEVPL-GSDLC — Transversal risk-based validation and full-regression policy"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-08-16"
approval: "approved_by_owner"
program_id: "DEVPL-GSDLC"
scope: "DEVPL-GSDLC-01..13 and successor micro-sprints unless explicitly superseded"
effective_from: "DEVPL-GSDLC-01-A"
---

# DEVPL-GSDLC — Transversal validation policy

## 1. Decision

The program adopts **risk-based, change-surface-based and cumulative validation**. A complete repository regression is no longer an automatic consequence of an intermediate micro-sprint or of `Test Impact full_regression_required=true`.

The default cadence is:

```text
intermediate micro-sprint
  → structural gates
  → focal tests
  → cumulative backlog tests
  → Test Impact
  → governance/security/acceptance gates
  → NO full regression by default

closing micro-sprint of each backlog
  → all cheaper gates first
  → one full regression
  → if residuals: fix + selective retest only
```

## 2. Rationale

The observed full-suite cost on the authoritative Windows workstation is greater than three hours. Executing the same broad suite at every micro-sprint creates disproportionate cost while adding little information when the change surface is bounded and already covered by cumulative focal/impact-selected contracts.

The policy reduces redundant execution without reducing contractual rigor: each micro-sprint remains blocked on its own tests, prior micro-sprint tests in the same backlog, Test Impact-selected contracts, governance validators, security negatives and specific acceptance tests.

## 3. Validation levels

### L0 — Structural/integrity

Always required: source authority, Git cleanliness/identity, package/manifest SHA, compile/schema syntax, forbidden paths, `git diff --check`.

### L1 — Current focal suite

Always required for code/schema/docs/contracts introduced or modified in the current micro-sprint, including security/negative cases.

### L2 — Cumulative backlog suite

Always required. Micro-sprint `N` executes the focal suites of all previously closed micro-sprints within the same backlog plus the current focal suite.

Example A→E:

```text
A: A
B: A+B
C: A+B+C
D: A+B+C+D
E: A+B+C+D+E
```

Equivalent tests may be consolidated, but coverage cannot be silently dropped.

### L3 — Test Impact

Always dry-run/analyze. Its P0/P1 recommendations are inputs to selective validation.

`full_regression_required=true` is interpreted as **full-regression recommendation / escalation signal**, not as an automatic execution command in an intermediate micro-sprint.

### L4 — Transversal deterministic validators

Run when impacted: Project State, Documentation Governance, schema catalog, Source Registry, TCR v1/v2, policy/no-go gates, evidence freshness and related deterministic validators.

### L5 — Capability-specific acceptance

Run only where relevant: API contract, browser acceptance, Git/filesystem reconciliation, RBAC/security, provider/model benchmark, RAG eval, release packaging, etc.

### L6 — Full regression

Default: exactly once in the **closing micro-sprint of each backlog**, after L0–L5 pass.

## 4. Intermediate micro-sprint rule

For a non-closing micro-sprint:

```text
full_regression_enforced = false
validation_mode = cumulative-selective
```

A Test Impact recommendation must still be preserved in machine-readable evidence, including selected P0/P1 and unmatched paths.

## 5. Hard-trigger exception

An intermediate full regression is allowed only if selective/cumulative validation is demonstrably insufficient because at least one hard trigger is present:

1. incompatible persistence/data migration across multiple bounded contexts;
2. transversal auth/RBAC/PolicyEngine/approval-authority change;
3. incompatible global ApplicationService/API contract with broad fan-out;
4. cross-domain plugin/connector/tool-execution infrastructure change;
5. major runtime/dependency-platform upgrade (Python/Node/framework/database/build chain);
6. packaging/startup/runtime topology change with broad blast radius;
7. selective tests fail in apparently unrelated domains, invalidating impact bounds;
8. material mid-backlog source baseline/rebase drift;
9. another explicitly documented systemic change where selective validation is insufficient.

Before executing such a suite, create an owner/technical decision artifact containing at least:

```text
policy_version
micro_sprint
hard_trigger_id
observed evidence
why cumulative/selective is insufficient
estimated full-regression cost
approved_by
approved_at
run_exactly_once=true
```

Absence of this approved artifact means the intermediate full regression is blocked.

## 6. Closing micro-sprint rule

The closing micro-sprint executes the full regression **exactly once** after L0–L5.

If it passes, backlog closure may proceed subject to remaining gates.

If it fails:

```text
preserve immutable full-regression evidence
→ classify residuals
→ correct root causes
→ selective retest of failures + impacted contracts
→ do not run the full regression again
```

The final validation mode is:

```text
composite-full-regression-selective-retest
```

and must record `full_pytest_repeated=false`.

## 7. Test Impact semantics

Test Impact remains conservative and may recommend full regression. The execution controller must distinguish:

```text
test_impact_full_regression_recommended
full_regression_enforced
full_regression_deferred_to
hard_trigger_present
```

For intermediate micro-sprints, `recommended=true` may coexist with `enforced=false`.

## 7.1 Compatibility with the current Historical Regression Guard

The current guard can classify sensitive/unmatched paths as `full_regression_required` even in a micro-sprint. The guard is **not disabled or bypassed**.

When L0–L5/cumulative tests are PASS and the owner-approved policy defers full regression, the operator may use the guard's native `waiver` decision with a short-lived evidence artifact generated in the external control directory. That artifact must:

- reference this policy/version;
- list the executed cumulative/selective tests;
- state that no test/security failure is being waived;
- expire within seven days;
- attach focal/Test Impact evidence;
- be preserved in the Windows evidence package.

This is a compatibility bridge for **validation cadence**, not permission to ignore failing tests, S0/S1, security findings or governance gates.

## 8. Evidence and audit

Every micro-sprint records:

- validation mode;
- focal/cumulative test sets and results;
- Test Impact summary;
- governance/acceptance results;
- full-regression recommendation;
- enforcement/defer decision;
- exception artifact if applicable;
- S0/S1;
- source/baseline identity.

## 9. Precedence

This owner-approved policy supersedes earlier DEVPL-GSDLC text that treated Test Impact `full_regression_required=true` as an automatic requirement for an **intermediate** micro-sprint.

It does not supersede a backlog-closing full regression, nor an explicitly owner-approved hard-trigger exception.

## 10. Immediate application to DEVPL-GSDLC-01

```text
01-A  cumulative-selective; full regression deferred
01-B  A+B cumulative-selective; full regression deferred
01-C  A+B+C cumulative-selective; full regression deferred
01-D  A+B+C+D cumulative-selective; full regression deferred
01-E  A+B+C+D+E + browser/API/etc + one full regression
```

For 01-A specifically, the existing Test Impact recommendation is retained as evidence but does not execute the >3h full suite.
