---
doc_id: "DEVPL-GSDLC-08-B-IMPLEMENTATION-REPORT"
title: "DEVPL-GSDLC-08-B — Roadmap Workbench implementation report"
status: "closed/windows-validated"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-09-03"
approval: "windows-browser-pass"
---
# DEVPL-GSDLC-08-B — Implementation report

## Scope

Implements the first governed Roadmap Workbench on top of A: shared MANUAL/IMPORT/AGENT structured authoring, server-side role-aware review/approval/freeze, explicit requirement/risk coverage, provenance and a project-scoped Web UI route.

## Safety

- DRAFT/review/frozen artifacts are runtime planning state below `outputs/planning/gsdlc_08_b`; managed source code is never edited by the product path.
- AGENT mode ingests structured output only in this first version; no external API/model call is required and no tool capability is granted.
- Agent self-approval is impossible. Approval/freeze authority is limited to authenticated `owner`/`product-owner` server roles.
- `full_regression_runs=0`; browser is required only for the focal Roadmap Workbench acceptance.

## Preliminary limits

This is the first Roadmap Workbench version. It does not yet derive epics/stories (08-C), schedule sprints (08-D), or transition the complete planning journey to `IMPLEMENTING_READY` (08-E). Agent generation remains structured-proposal ingestion rather than autonomous model invocation; later evolution may bind a controlled local/model route without changing approval authority.

## Local qualification

- A+B focal: 21/21 PASS.
- Bounded cumulative impact suite: 24/24 PASS.
- Roadmap Workbench static UI/browser contract smoke: PASS.
- Project State / Documentation Governance / TCR v1 / TCR v2 / Evidence Freshness: PASS.
- Current pytest collection: 2934 nodeids; all 9 new B nodeids registered UNCLASSIFIED/parallel_safe=false.
- Full regression runs: 0.
- Real browser acceptance remains Windows-authoritative and PENDING.

## R05 — Browser API authorization binding correction

Windows browser evidence showed the Roadmap Workbench route itself was reachable and Project Status was recovered, while `GET /api/v1/planning/roadmap` returned HTTP 403. The cause was a split authorization authority in the pre-close validation runtime: the API transport security map did not contain the five GSDLC-08-B roadmap operations, and the validation API was rooted at repo399 while the server-RBAC catalog containing those operations lived in the B worktree.

The correction adds the five explicit `ApiRoutePolicy` bindings and requires the Windows API runtime to instantiate the application against the B worktree while retaining only the authentication service/store in the official checkout. This preserves server-authoritative RBAC, source/runtime separation, local-only operation and `full=0`.

## Windows closure

Browser acceptance PASS using exactly three foreground consoles. MANUAL/IMPORT/AGENT routes were demonstrated, requirement coverage BLOCK remained visible, AGENT output remained DRAFT, and owner/product-owner approval/freeze produced an immutable revision. Full regression runs remained 0. GSDLC-08-C is authorized.
