---
doc_id: "DEVPL-GSDLC-07-D-AGENT-EXECUTION-RUNBOOK"
title: "GSDLC-07-D — Bounded agent execution runbook"
status: "current"
version: "1.0.0"
owner: "DEVPL-GSDLC-07-D"
updated: "2026-08-29"
---
# GSDLC-07-D bounded agent execution

`ToolIntent` is proposal-only. `AgentExecutionPolicy` joins exact role/step allowlists, MIASI Tool Registry and `PolicyEngine/RBAC/Approval` to produce `ToolExecutionDecision`.

Safety invariants: dry-run first; no shell; no self approval; `filesystem.delete` globally forbidden; real MCP write disabled; autonomous recovery blocked; max iterations/time/tokens/cost server-side; cancel/kill server-side; handoffs require human checkpoint and never inherit tool scope.

07-D remains an **implemented-initial** bounded runtime. Safe `policy.check` in fake-local mode is the only direct execution fixture; production-grade broad tool execution is not enabled.
