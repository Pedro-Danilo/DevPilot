---
doc_id: "ADR-DEVPL-GSDLC-11-E-LOCAL-RELEASE-ADOPTION"
title: "Evidence-backed local release adoption for registered workspaces"
status: "accepted"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-09-12"
approval: "approved_by_owner/GSDLC-11-E"
---

# Decision

A registered `OPEN_EXISTING` workspace that has no durable `WorkspaceEngineeringState` may receive an initial `RELEASE/RELEASED` state **only** when GSDLC-11-E proves a complete, exact-commit local release graph: reproducible package/checksums/SBOM, install/rollback PASS, human approval, annotated exact tag, clean Git authority, no push/publish/deploy, and no open S0/S1.

If an engineering state already exists, normal optimistic-concurrency successor update is used instead.

# Why

The normal browser acceptance uses a real GSDLC-03 registered workspace. Requiring an external operator to seed historical phases would violate the product invariant `normal-user external script = 0`. Conversely, marking a workspace RELEASED without complete evidence would bypass Guided SDLC authority. Evidence-backed adoption is therefore bounded to the final local-release proof and platform-local state only.

# Safety / PASS-BLOCK

**PASS:** exact scope, registered binding, hash-bound release graph, owner/release-manager, local-only release, immutable annotated tag, no managed-source mutation.

**BLOCK:** missing evidence, dirty Git, stale package/tag/approval, unregistered workspace, scope mismatch, push/publish/deploy, or graph hash drift.

# Verification

`python -m pytest -p no:ddtrace --assert=plain -q tests/test_devpl_gsdlc_11_e_release_closure.py`
