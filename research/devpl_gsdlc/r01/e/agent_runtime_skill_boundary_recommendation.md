---
doc_id: "DEVPL-GSDLC-R01-E-AGENT-RUNTIME-SKILL-BOUNDARY"
title: "R01-E — Agent Runtime / Skills boundary recommendation"
status: "pass-candidate"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-08-15"
approval: "pending_owner_adjudication"
backlog_id: "DEVPL-GSDLC-R01"
micro_sprint: "DEVPL-GSDLC-R01-E"
source_repo: "repo_DevPilot_Local_347_DEVPL_GSDLC_R01_D_MODEL_AGENTIC_BENCHMARK.zip"
source_git_commit: "3027baffc9ffe7c96850783cb2adc61d531fd8e1"
source_repo_sha256: "b88a962952b3a80abbdcc6aa18ced89e608816589fb51583f68a497983079751"
---

# Agent Runtime / Skills boundary recommendation

## 1. Architectural decision input

Keep three independent authority planes:

| Plane | Owns | Must not own |
|---|---|---|
| Model Gateway | model/provider/access-route/auth-adapter routing | tool permission, planning, handoff execution |
| Agent Runtime | session, bounded planning, handoffs, ToolIntent lifecycle | provider terms authority, direct destructive execution |
| Skills/Tools/MCP | typed capability contracts and invocation adapters | model routing policy, self-approval |

## 2. ToolIntent vs ToolExecutionDecision

A model/agent may emit `ToolIntent`. DevPilot deterministic policy and approval controls produce `ToolExecutionDecision`. Only the latter may make a tool executable.

Required fields for later implementation:

```text
ToolIntent
  tool_id
  arguments
  originating_model
  originating_route
  agent_session
  trace_id

ToolExecutionDecision
  deterministic_policy_result
  approval_required
  approval_id
  permission_scope
  executable
  reason
```

## 3. R01-D constraint

The tested models did not reliably refuse the forbidden tool and did not demonstrate reliable autonomous recovery. This is a direct reason to keep the runtime bounded and policy-dominant.

## 4. MCP placement

MCP is treated as a Skills/Protocols interoperability mechanism. MCP authorization and transport do not belong to Model Gateway. Real MCP remains candidate-for-experiment only; the current fake/in-process MCP remains the safe contract baseline.

## 5. Agent runtime candidates for later experiments

- DevPilot governed runtime: baseline/reference.
- OpenAI Agents SDK: candidate-for-experiment.
- Microsoft Agent Framework: candidate-for-experiment.
- LangGraph: candidate-for-experiment.
- MCP protocol: candidate-for-experiment in Skills/Protocols.
- Anthropic hosted MCP Connector: observe/conditional because it is remote/provider-bound.
- open-ended autonomous frameworks: not recommended/blocked under current evidence.

R01-E does not add any dependency or framework.

## 6. Security

- no agent self-approval;
- no unbounded loops;
- no direct shell/filesystem mutation from model output;
- no secret harvesting;
- no connector write/plugin execution/remote execution;
- deterministic policy remains final authority.

## 7. PASS/BLOCK

PASS if the three planes remain distinct and later experiments are explicitly bounded. BLOCK if Model Gateway silently becomes an orchestrator or if Agent Runtime/skills bypass policy/approval.

## 8. Risks and limitations

This is architecture input only. Actual runtime experiments require a later backlog, threat model, dependency decision, sandboxing, evals, rollback and observability.

## 9. Verification

```powershell
python -m devpilot_core docs-governance validate --json
python -m devpilot_core project-state validate --json
```
