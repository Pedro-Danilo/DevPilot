---
doc_id: "DEVPL-GSDLC-13-D-STORY-CODE-WORKBENCH-OPERATIONAL-CONTRACT"
title: "DEVPL-GSDLC-13-D — Story Code Workbench operational contract"
status: "approved"
version: "1.0.4"
owner: "Ordóñez"
updated: "2026-10-02"
approval: "projected_for_owner_windows_validation"
---

# Scope

This revision supersedes v1.0.3 for the D02 continuation. Proposal quality remains bounded to the accepted v2 design, with a v2.1 type-contract hardening absorbed because this corrective is already required. The corrective addresses live human-session preflight, action-local feedback and Source-tree progressive disclosure without relaxing server authentication, CSRF, RBAC or approval policy.


# Proposal review model

The proposal review model remains:

```text
StoryContextPack + Architecture FROZEN
→ ImplementationProposal v2.1 (proposal-only)
→ filename-only virtual PROPOSAL rows in Source tree
→ click file → Draft editor read-only review
→ Owner ACCEPT
→ SourceDraftBuffer Set runtime-only
→ Source tree DRAFT nodes
→ edit/recheck
→ one multi-file SourceChangePlan
→ diff/Test Impact/dry-run
→ Owner approval
→ atomic apply
```

# Manual CREATE/EDIT/RENAME

Manual CREATE/EDIT/RENAME remains a first-class explicit Owner/developer override. It never bypasses live human-session checks, proposal/Draft provenance, SourceChangePlan or approval-gated source apply.

# Human-session boundary

Story Code mutations remain fail-closed and require a server-authenticated human session. The UI must verify a live session immediately before proposal decisions and the remaining D02 mutation gates.

If the session is no longer valid:

- no proposal decision, Draft mutation, SourceChangePlan mutation or source apply is attempted;
- server-side Proposal/Draft/Plan state remains authority;
- the BLOCK is rendered next to the action surface that triggered it;
- the UI provides an explicit reauthentication route back to `/story/code`;
- legacy API token fallback must not be used to bypass human-session requirements.

The default local session idle timeout remains a security control and is not extended by this corrective.

# Action-feedback locality

Critical action feedback must be colocated with the current action group. Page-level status may remain as secondary telemetry, but it cannot be the only place where a BLOCK/PASS is visible after an action.

For D02:

- proposal create/ACCEPT/REJECT and Draft actions use feedback inside `Source tree`;
- SourceChangePlan/recheck/dry-run/approval/apply use feedback inside `Governed source change`.

# Source tree information architecture

The tree is the primary navigation surface for SOURCE/PROPOSAL/DRAFT/CONFLICT artifacts.

- leaf visible text is only the file name;
- state/path/detail remain available through dataset, accessible label/title and Editor metadata;
- leaf controls remain keyboard/focus accessible but are visually styled as tree rows, not button chrome;
- help, extension policy, proposal status, provider/model/profile/quality and technical provenance live under a single collapsed-by-default `Información y provenance` disclosure;
- `PROPOSAL` opens read-only in the existing Editor;
- Draft action toolbar is hidden while a PROPOSAL file is being reviewed and reappears for SOURCE/manual/DRAFT states.

# Proposal v2.1 contract

The proposal quality contract from v1.0.3 remains authoritative, with the JSON-compatible opaque attribute type hardening added in v2.1:

- provider/model: `devpilot-local / deterministic-story-implementation-template-v2.1`;
- RF-001 slice covers ARC-C02/C03/C04 and TEST-001;
- reusable Product semantics; no Story-ID persistence;
- no invented Product business fields;
- module docstrings include Purpose/Responsibilities/Boundaries/Traceability;
- `ACCEPT` creates runtime-only Draft Set; source remains unchanged.

# Source mutation safety

The source-write path remains unchanged:

```text
Proposal v2.1
→ Owner ACCEPT
→ Draft Set runtime-only
→ preimage rechecks
→ one multi-file SourceChangePlan
→ full diff / Test Impact / dry-run
→ exact Owner approval
→ final recheck
→ atomic apply
```

Full Regression remains `0` in D02.
