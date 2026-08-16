---
doc_id: "DEVPL-GSDLC-01-D-RECONCILIATION-CONTRACT"
title: "DEVPL-GSDLC-01-D — Filesystem/Git reconciliation and revalidation contract"
status: "implemented-initial"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-08-16"
approval: "candidate-pre-windows"
---

# DEVPL-GSDLC-01-D — Reconciliation contract

## 1. Purpose

Provide a deterministic, bounded and local-only reconciliation authority that detects external filesystem/Git drift for a **registered workspace** without destructively changing that workspace.

## 2. Boundary

```text
registered WorkspaceEngineeringState
+ Workspace Registry / PathGuard
+ read-only filesystem
+ read-only Git
        ↓
WorkspaceReconciler.inspect()
        ↓
ReconciliationReport + successor WorkspaceEngineeringState
        ↓
GuidedSDLCService.reconcile(execute=false|true)
```

`execute=false` is a pure preview. `execute=true` may perform **one atomic save to the platform-local WorkspaceEngineeringState store only**. It never writes the managed workspace source and never runs a mutating Git command.

## 3. Git allow-list

Only:

- `git rev-parse HEAD`;
- `git branch --show-current`;
- `git status --porcelain=v1 --untracked-files=normal`;
- `git diff --name-status -M`;
- `git diff --cached --name-status -M`;
- `git diff --name-status -M <prior>..<current>` when HEAD changed.

Explicitly forbidden: reset, checkout, restore, clean, rebase, merge, stash, add and commit.

Each Git process has a bounded timeout.

## 4. Governed files

The reconciler reads only `source_ref` values already present in `WorkspaceEngineeringState.artifacts` or `source_fingerprints`.

Requirements:

- relative path only;
- no `..`;
- no absolute path;
- no symlink component;
- path remains under the registered workspace root;
- bounded file count and file size.

The reconciler does not crawl arbitrary workspace directories.

## 5. Drift semantics

Detected reasons include:

- Git HEAD changed;
- branch changed;
- dirty working tree;
- governed artifact renamed;
- governed artifact missing;
- source fingerprint changed;
- APPROVED/FROZEN artifact hash changed;
- artifact fingerprint stale.

A changed `APPROVED` or `FROZEN` artifact is projected to `REVALIDATION_REQUIRED`. Existing approval history is not deleted.

## 6. Successor state

If revalidation is required:

- lifecycle becomes `REVALIDATION_REQUIRED`;
- revalidation status becomes `REQUIRED`;
- reason codes are stable/sorted;
- sequence increments exactly once;
- observed Git snapshot is stored;
- APPROVED/FROZEN affected artifacts become `REVALIDATION_REQUIRED`;
- previous source fingerprints remain preserved as the expected baseline.

Preserving prior source fingerprints is intentional: reconciliation identifies the mismatch but does not silently accept new content as the new governed baseline.

## 7. ProjectStatus / NextAction

The successor state is projected through the same `ProjectProgressEngine` introduced by 01-C. Therefore drift yields `NextAction.kind=REVALIDATE` without duplicating frontend logic.

## 8. Initial-version limitations

This is the first production-oriented reconciliation kernel.

It does **not**:

- auto-resolve revalidation;
- accept a rename as a new governed path automatically;
- rewrite approvals;
- repair Git;
- index arbitrary files;
- expose HTTP/UI.

01-E consumes this authority for Project Status. Later workflow/backlog increments may introduce governed recovery workflows and richer provenance.

## 9. Security

No network, external API, LLM authority, arbitrary shell, cross-workspace traversal or managed-source write is permitted.

## ApplicationService boundary

The initial application facade exposes exactly two non-HTTP capabilities:

- `guided_sdlc.reconcile.preview`: read-only observation and successor-state projection.
- `guided_sdlc.reconcile.execute`: explicit internal operation that may persist only the local durable `WorkspaceEngineeringState` via atomic repository save.

Neither capability mutates managed workspace source or Git. HTTP/UI publication is deferred to a later authorized surface.
