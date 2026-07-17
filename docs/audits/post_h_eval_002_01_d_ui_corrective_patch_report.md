---
doc_id: "POST-H-EVAL-002-01-D-UI-CORRECTIVE"
title: "POST-H-EVAL-002-01-D — UI corrective patch after partial RUN-01"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-07-17"
approval: "IMPLEMENTED-PENDING-RUN-02-WINDOWS-BROWSER-EVIDENCE"
---

# POST-H-EVAL-002-01-D — UI corrective patch

## Decision

`IMPLEMENTED / OPEN / RETEST REQUIRED`. The partial RUN-01 archive is valid as
diagnostic input but not as closure evidence. It contains the four requested
logs and `session_state.json`; `process_lifecycle.json` is absent because the
archive was captured while `running=true`.

## Literal diagnostic evidence

- archive SHA-256: `5cd73ae64eb2abc85e0b1fbd4a20089d27974300c5c3e5ef01471dd39154f72e`;
- API requests logged: `115`;
- HTTP non-200 responses: `0`;
- API stderr: only normal Uvicorn startup;
- UI stderr: empty;
- session: API/UI on `127.0.0.1`, token not persisted and not present in URL;
- matrices remain `PENDING`: routes `0/5`, negative states `0/8`, UI eligible `0%`.

The request distribution shows eager duplication: reports `12 GET`, traces
`10 GET`, metrics `9 GET`, approvals `9 GET`, settings workspace/policy/security
`6/6/7 GET`, while the dashboard also launches its own five protected calls.
All API calls eventually return 200, so the browser timeout does not represent
an API crash. Source inspection establishes that Dashboard embedded the full
Reports/Traces, Approval and Settings surfaces and each embedded surface
started its own refresh. Protected requests also perform policy and local
observability work, so burst concurrency is an avoidable local contention
amplifier.

## Corrective design

1. Dashboard renders only operational summaries and route links.
2. Five dashboard loaders execute progressively with maximum concurrency 2.
3. Reports and Traces are distinct components and do not cross-fetch.
4. Settings uses mutually exclusive `idle/loading/ready/empty/error` phases and
   maximum concurrency 2.
5. Missing no-go snapshot is `UNKNOWN`, not `BLOCK`; disabled sensitive
   capabilities are `DISABLED BY POLICY`.
6. Timeout remains 8000 ms and now identifies endpoint, duration and retry.
7. No API, PolicyEngine, SQLite schema, RBAC, approval or sensitive capability
   is changed.

## Closure boundary

This patch does not close 01-D or backlog 01. Formal RUN-02 must produce five
routes, eight negative states, 100% UI-eligible coverage, lifecycle cleanup,
secret scan, browser-console evidence, CLI bridge register and clean evidence
packages. `POST-H-EVAL-002-02-A` remains unauthorized.
