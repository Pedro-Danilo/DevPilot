---
doc_id: "ADR-GSDLC-006"
title: "ADR-GSDLC-006 — Preview-first external-source import as runtime DRAFT"
status: "accepted/pending-windows-proof"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-08-21"
approval: "accepted_for_gsdlc_04_c"
---

# ADR-GSDLC-006 — Preview-first external-source import as runtime DRAFT

## Context

Artifact Workbench needs PASTE/UPLOAD/IMPORT without bypassing lifecycle/provenance, UOC-005 apply governance or project-scoped security. Treating a browser upload as an immediate workspace write would create a second write engine and implicit authority escalation.

## Decision

External content is ingested through a two-step `preview → persist DRAFT` application boundary. Preview is read-only and computes canonical path, original/normalized hashes, deterministic encoding normalization and diff. Persist requires the exact preview hash and creates only runtime-ephemeral DRAFT state. URLs/references are metadata only; no network fetch exists in 04-C. Source promotion remains delegated to the existing governed write/apply boundary evolved in 04-D.

The runtime store is outside the approved workspace source tree but inside the governed local platform runtime boundary; `workspace_writes_performed=false` and `source_mutations_performed=false` remain explicit. This mirrors 04-B draft separation and avoids storing unapproved external material in Git.

## Consequences

Positive:
- no implicit authority escalation;
- deterministic provenance and two-hash auditability;
- no second source-write engine;
- safe restart/recent-import discovery;
- strict local-first/no-network posture.

Trade-offs:
- imported content is not a workspace file until the successor governed apply flow;
- current allowlist is intentionally narrow (`.md`/`.json`, 1 MiB);
- advanced MIME sniffing, archive import, cloud sync and binary document workflows remain out of scope.

## Rejected alternatives

1. Write upload directly to target path: rejected because it bypasses preview/approval/apply boundaries.
2. Fetch source URLs server-side: rejected because 04-C is local-first and reference metadata is not authorization for network access.
3. Store raw external content in browser storage: rejected because browser storage is UX-only and not authority/persistent audit state.
