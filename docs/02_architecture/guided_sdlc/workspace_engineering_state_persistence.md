---
doc_id: "DEVPL-GSDLC-01-A-STATE-PERSISTENCE"
title: "WorkspaceEngineeringState v1 — local persistence decision"
status: "implemented-initial"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-08-16"
approval: "pending_owner_01_a_adjudication"
program_id: "DEVPL-GSDLC"
micro_sprint: "DEVPL-GSDLC-01-A"
---
# WorkspaceEngineeringState v1 — local persistence decision

## Decision

Default store:

```text
<DevPilot platform root>/outputs/workspaces/<workspace_id>/engineering_state.json
```

The store root is injectable for installation/tests.

## Why this location

- `outputs/` is already excluded by the product `.gitignore`, preventing accidental source-control of managed-project progress.
- state remains local-first and durable across process restarts;
- the managed workspace receives no hidden DevPilot state file;
- it is not `.devpilot/project_state.json` and not `.devpilot/devpilot.db`;
- state is reconstructible from registry metadata + canonical artifacts + Git if local cache is lost.

## Alternatives rejected

1. **Managed workspace `.devpilot/engineering_state.json`** — rejected for 01-A because it silently injects DevPilot metadata into arbitrary user repositories.
2. **`.devpilot/project_state.json`** — rejected because it is PlatformState.
3. **`.devpilot/devpilot.db`** — rejected because existing contracts classify it as runtime/operational state and it also contains unrelated concerns.
4. **memory only** — rejected because restart/resume would lose progress.

## Write safety

Writes use temp file in the destination directory, LF UTF-8 JSON, `flush + fsync`, then `os.replace`. Existing records require exact optimistic-concurrency `expected_sequence`; successor sequence increments by one.

Workspace binding is deny-by-default: registry v1/v2, explicit external-root allowlist, PathGuard, workspace status, project_id and root fingerprint must agree. Workspace and store symlink pivots are rejected.
