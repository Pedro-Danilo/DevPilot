---
doc_id: DEVPL-GSDLC-02-B-CREDENTIAL-KDF-DECISION
title: Credential KDF decision
status: approved-initial
version: 1.0.0
owner: Ordóñez
updated: 2026-08-16
---
# Credential KDF decision

## Decision
Use Python stdlib `hashlib.scrypt` in GSDLC-02-B to avoid silently introducing a new dependency in the Windows/local distribution.

Parameters v1: `N=16384`, `r=8`, `p=1`, `dklen=32`, random salt 16 bytes. Parameters and KDF version are stored with each credential to support future migration. Verification uses constant-time comparison.

## Rejected
Plaintext, reversible encryption, SHA-2/SHA-3 alone, unsalted hashes, fixed salts.

## Future evolution
Argon2id remains preferred for a later hardening revision if dependency/licensing/platform/package impact is explicitly approved and migration/rollback is tested. This implementation is therefore an **initial local credential KDF**, not the final enterprise password subsystem.
