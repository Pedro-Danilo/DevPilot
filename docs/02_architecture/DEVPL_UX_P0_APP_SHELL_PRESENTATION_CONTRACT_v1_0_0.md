---
doc_id: "DEVPL-UX-P0-A-SHELL-CONTRACT"
title: "DevPilot UX-P0 — App Shell presentation contract"
status: "current"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-09-15"
approval: "derived_from_approved_DEVPL-UX-P0-A"
source_repo: "repo_DevPilot_Local_430_DEVPL_GSDLC_12_E_LOCAL_RC_WINDOWS_VALIDATED_CANDIDATE.zip"
source_git_commit: "a415504bbf021566243ef4000b1a27d4c8846fee"
architecture_decision: "no-ADR-required/no-shell-extraction-in-UX-P0-A"
---

# App Shell presentation contract

## Scope

UX-P0-A establishes the presentation contract only. UX-P0-B implements the structural shell/navigation refactor.

## Invariants

1. Existing route IDs and paths remain unchanged.
2. Server-side session, RBAC, approval, model and tool authority remain unchanged.
3. Guided and Expert are presentation modes only.
4. Project context and authoritative next action in UX-P0-B must be server-derived; browser state is UX-only.
5. Evidence remains available through progressive disclosure; blockers are never hidden.
6. No new runtime framework or external dependency is introduced.

## Target shell slots

`Global Navigation → Project Context → Location/Breadcrumb → Current Stage/State → Authoritative Next Action → Workbench → Evidence/Diagnostics → Recovery/Notifications`.

## PASS/BLOCK

**PASS:** UX-P0-A only prepares tokens/IA/contracts and does not change route behavior.

**BLOCK:** route/API/RBAC authority changes, browser-only execution authority, or UI simplification that hides a critical blocker.

## Risks and limitations

- The contract is presentation-only in UX-P0-A; structural shell extraction is deferred to UX-P0-B.
- Premature shell refactoring could regress auth/project guards or directed approval handoffs.

## PASS/BLOCK

**PASS:** route paths, route IDs, server authority and Guided/Expert permission parity remain unchanged.

**BLOCK:** a presentation change grants authority, changes a guard, or makes directed handoff navigation unsafe.

## Verification commands

```text
cd ui/web && npm run test:route-enforcement
cd ui/web && npm run test:state-matrix
python -m pytest tests/test_devpl_gsdlc_12_c_guided_expert_accessibility.py -q
```

