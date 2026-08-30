---
doc_id: "DEVPL-GSDLC-07-E-AGENTIC-PRECODE-RUNBOOK"
title: "GSDLC-07-E — Agentic pre-code acceptance runbook"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-08-30"
approval: "approved_for_windows_validation"
---
# GSDLC-07-E — Agentic pre-code acceptance runbook

## Purpose
Demonstrate Product Vision → PRE_CODE_READY with selected agent-assisted steps while preserving manual authoring and deterministic policy authority.

## Safety
Mock and fake-local are mandatory. External API is optional and not required. ToolIntent is never executable until Policy/RBAC/Approval produce ToolExecutionDecision. No auto-approval, source write, real MCP, autonomous recovery or arbitrary shell.

## Browser PASS
Agent/runtime, model/provider/access-route, sources, tokens/cost, ToolIntent, deterministic decision, human ACCEPT/MODIFY/REJECT and handoff state must be visible. `filesystem.delete` must visibly remain `executable=false` and `tool_executed=false`.

## Full regression
Exactly one logical session; complete all shards; resume only UNEXECUTED/INFRA_ABORT with identical fingerprints. A second full is BLOCK.

## Verification
`python -m pytest -p no:ddtrace --assert=plain -q tests/test_devpl_gsdlc_07_e_agentic_precode.py`

## PASS/BLOCK
PASS only with S0/S1=0, browser PASS and full logical coverage 100%. BLOCK on hidden cost/source/model, approval bypass, unbounded action, second full or runtime store inside candidate.
