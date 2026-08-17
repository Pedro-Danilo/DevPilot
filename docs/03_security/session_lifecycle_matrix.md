---
doc_id: DEVPL-GSDLC-02-B-SESSION-LIFECYCLE-MATRIX
title: Session lifecycle matrix
status: implemented-initial
version: 1.0.0
owner: Ordóñez
updated: 2026-08-16
---
# Session lifecycle matrix

The machine-readable authority is `docs/03_security/session_lifecycle_matrix.json`.

| State | Event | Result |
|---|---|---|
| NO_OWNER | bootstrap owner | ACTIVE_SESSION once only |
| NO_SESSION | valid login | ACTIVE_SESSION |
| NO_SESSION | invalid login | BLOCK |
| ACTIVE_SESSION | rotate + CSRF | old REVOKED, replacement ACTIVE |
| ACTIVE_SESSION | logout/revoke + CSRF | REVOKED immediately |
| ACTIVE_SESSION | idle/absolute expiry | REVOKED/BLOCK |
| ACTIVE_SESSION | restart | remains valid only if not expired/revoked |
| ANY | corrupt/incompatible store | FAIL_CLOSED |
