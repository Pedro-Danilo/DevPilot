---
doc_id: "DEVPL-GSDLC-04-C-ARTIFACT-IMPORT-CONTRACT"
title: "DEVPL-GSDLC-04-C — Governed external-source import contract"
status: "implemented/ready-for-windows"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-08-21"
approval: "pending_windows_validation"
---

# DEVPL-GSDLC-04-C — Governed external-source import contract

## 1. Purpose

GSDLC-04-C adds project-scoped `PASTE`, `UPLOAD` and `IMPORT` ingestion to Artifact Workbench without turning external content into implicit authority. The capability is preview-first and creates only a governed runtime `DRAFT`; approved workspace files remain unchanged until the existing UOC-005/04-D apply boundary is used by a successor sprint.

## 2. Authority boundaries

- Human session + server RBAC own actor/role authority. Browser payloads cannot nominate the authoritative actor.
- `DEVPILOT_UI_ACTIVE_WORKSPACE_ROOT` / governed project context owns workspace scope.
- Destination is a relative workspace path only. Absolute paths, traversal, UNC, ADS/device-name syntax and symlink/reparse traversal fail closed.
- URLs/references are provenance metadata only. 04-C performs no URL fetch, network request or external API call.
- The browser preview is not evidence, approval or source authority.
- The import runtime store is ephemeral local state under `outputs/imports/gsdlc_04_c`; it is excluded from source packages and never replaces the approved artifact.

## 3. Input contract

Supported artifact extensions are `.md` and `.json`. Server-side size maximum is 1 MiB; the UI mirrors the limit as an early UX guard, but server validation is authoritative.

`PASTE` accepts text only. `UPLOAD` and `IMPORT` accept base64-transported file bytes with a basename-only original filename. A non-empty declared MIME, when available, must be compatible with the allowlisted extension. Executable/binary inputs and unsupported extensions are rejected.

Encoding is normalized deterministically:

- UTF-8;
- UTF-8 with BOM;
- BOM-qualified UTF-16 LE/BE.

Unqualified malformed/unknown encodings fail closed. CRLF/CR is normalized to LF before computing the normalized hash. Both `original_sha256` (raw bytes) and `normalized_sha256` (UTF-8 normalized content) are retained.

## 4. Preview and persistence state machine

`INPUT → PREVIEW → DRAFT`

1. Preview canonicalizes the destination, validates type/size/encoding/MIME, calculates both hashes and computes a bounded unified diff against the current workspace destination if it exists.
2. Preview performs zero workspace/source writes and zero network/API activity.
3. SecretGuard scans normalized content. If secret-like material is detected, preview remains available only in redacted form and DRAFT persistence is blocked.
4. Preview emits an immutable `preview_sha256` over source type, workspace, destination, original filename/MIME, source metadata and content/preimage hashes.
5. Persist recomputes the same preparation and requires exact `preview_sha256`. Drift forces a new preview.
6. Persist creates a lifecycle `DRAFT` with PASTE/UPLOAD/IMPORT provenance and writes only a schema-validated runtime import record.
7. No source destination is created or overwritten by 04-C.

## 5. Provenance and visibility

The UI displays:

- source type;
- source label/reference;
- original filename and MIME when applicable;
- original SHA-256;
- normalized SHA-256;
- encoding;
- destination and existing-source preimage when applicable;
- lifecycle `DRAFT`;
- explicit `workspace writes=false` and `network=false` posture.

The runtime record links to the GSDLC-04-A ArtifactLifecycle record instead of creating a second lifecycle engine.

## 6. Security properties

- deny-by-default project context and RBAC;
- no arbitrary shell;
- no executable upload;
- no path escape;
- no symlink/reparse traversal;
- no implicit URL fetch;
- no secret-bearing DRAFT persistence;
- no approval/freeze escalation in 04-C;
- no source write and no hidden apply;
- runtime stores excluded from Git/source ZIPs.

## 7. Successor boundary

GSDLC-04-D owns validation/findings, immutable change plan, approval, atomic apply/rollback and freeze. 04-C deliberately stops at `DRAFT` and therefore is an industrially bounded first import surface rather than the final Artifact Workbench lifecycle.
