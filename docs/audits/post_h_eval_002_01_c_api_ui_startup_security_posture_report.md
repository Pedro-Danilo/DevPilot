---
doc_id: "POST-H-EVAL-002-01-C-CLOSURE-AUDIT"
title: "POST-H-EVAL-002-01-C — API/UI startup and security posture closure"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-07-16"
approval: "PASS-WITH-GAPS"
---

# POST-H-EVAL-002-01-C — Closure report

## Decision

`PASS-WITH-GAPS`, closed and authorizing `POST-H-EVAL-002-01-D`.

The Windows-authoritative execution started the frozen DevPilot 318 API and Web UI on localhost, exercised real socket-level authentication and CORS behavior, ran the focused API/UI/npm verification suite, confirmed token redaction and evidence hygiene, and stopped both process trees with their ports released.

## Authoritative artifacts

| Artifact | SHA-256 |
|---|---|
| `DevPilot_E2E_Evaluation_POST-H-EVAL-002-01-C.zip` | `c962739b1c9f9045ea872be9b576f6045aa41268261b1aab5bc3ae629824d8a5` |
| `POST-H-EVAL-002-01-C_windows_authoritative_evidence.zip` | `4c5596d09c4208ccd092f42f110e8b23609b1d4de98166140fc26ac9b95407c5` |
| `Log_consola_implementacion_POST-H-EVAL-002-01-C_R2.txt` | `3b1678386b9b3f3c6605674df401f36b6b078966d1f25e6360e80c4fe9f990cc` |

Runtime/governance identities:

- executable baseline: `repo_DevPilot_Local_318_POST_H_EVAL_002_PILOT_READY.zip`;
- incoming governance: `repo_DevPilot_Local_320_POST_H_EVAL_002_01_B.zip`;
- outgoing governance target: `repo_DevPilot_Local_321_POST_H_EVAL_002_01_C.zip`;
- run: `PILOT-E2E-001-RUN-01`;
- operator: `2.0.0`.

## Executed verification

- operator checks: `41/41 PASS`;
- commands: `12/12 PASS`;
- API dry-run on `127.0.0.1:8787`: PASS;
- non-local bind `0.0.0.0`: correctly blocked with exit code `2`;
- real API startup: HTTP `200`;
- protected route without token: `401`;
- protected route with invalid token: `401`;
- protected route with valid token: `200`;
- local CORS origin reflected exactly: `http://127.0.0.1:5173`;
- `Vary: Origin`: present;
- local `OPTIONS` preflight: `200`, with `GET` and `X-DevPilot-Token` allowed;
- untrusted-origin preflight: `400`, without `Access-Control-Allow-Origin`;
- CORS wildcard: absent;
- Web UI startup on `127.0.0.1:5173`: HTTP `200`;
- npm smoke, visual, operator-flow and route-enforcement: PASS;
- API contract drift, security hardening, visual smoke, operator-flow smoke, UI route enforcement and release-candidate UI/API smoke: PASS;
- raw token findings: `0`;
- `.env` or SQLite evidence files: `0`;
- API/UI process trees stopped and ports released: PASS;
- clean archive: CRC PASS, `4598` included files, `3853` runtime files excluded and `0` forbidden entries.

## Resolved operator incident

The first 01-C attempt produced a false BLOCK because operator R1 converted the HTTP header collection to a case-sensitive dictionary and then searched for `Access-Control-Allow-Origin` using title case. Uvicorn emitted the valid lower-case field name. Operator R2 normalized header names, added a real OPTIONS preflight, passed self-validation and produced the authoritative PASS evidence.

This incident changed no DevPilot source, no runtime policy and no governance source. It is closed as an operator-evidence defect.

## Non-blocking gap

`EVAL-002-01-C-GAP-001` — `api contract-drift` passed all five blocking checks but reported four inherited warnings because the static OpenAPI artifact omits four public transport routes (`/api/v1/docs`, `/api/v1/health`, `/api/v1/openapi.json`, `/api/v1/security/posture`). Runtime, canonical and registry route totals remain aligned at `39`; all `36` protected routes have policy/auth coverage; no response-contract or no-go violation exists.

Classification: `S3 / static API documentation completeness`. It does not block 01-C or 01-D. It must be carried into the pilot gap register and resolved only through a future controlled product patch if prioritized.

## Scope boundary

01-C verified technical startup and basic security posture. It did **not** execute formal browser acceptance of the five critical routes, the complete negative-state matrix, screenshots or CLI bridge classification. Those activities remain exclusively in `POST-H-EVAL-002-01-D`.

## Safety posture

- platform 318 remains frozen and hash-identical;
- workspace pilot was not created;
- token was generated in memory, transported through environment/header and not persisted;
- UI stores a token only in browser `sessionStorage`;
- external APIs, connector write, plugin execution, remote execution, productive multiuser and enterprise/SaaS remain disabled;
- no full regression was required because no DevPilot source code changed.
