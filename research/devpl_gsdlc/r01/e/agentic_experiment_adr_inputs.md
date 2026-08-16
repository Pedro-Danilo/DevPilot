---
doc_id: "DEVPL-GSDLC-R01-E-AGENTIC-EXPERIMENT-ADR-INPUTS"
title: "R01-E — Agentic experiment ADR inputs"
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

# Agentic experiment ADR inputs

## Purpose

Define a safe later experiment program without adopting a framework during R01-E.

## Candidate matrix

| Candidate | R01-E disposition | Experiment focus |
|---|---|---|
| DevPilot governed runtime | baseline/reference | policy/approval/trace contract |
| OpenAI Agents SDK | candidate-for-experiment | tools, handoffs, tracing, HITL integration boundary |
| Microsoft Agent Framework | candidate-for-experiment | typed workflows, checkpoints, handoffs/HITL |
| LangGraph | candidate-for-experiment | durable execution, persistence, deterministic+LLM graph steps, HITL |
| MCP 2026-07-28 protocol | candidate-for-experiment | typed skills/resources/tools + auth/transport isolation |
| Anthropic hosted MCP Connector | observe/conditional | provider-bound remote MCP behavior only |
| open-ended autonomous runtimes | not-recommended/blocked | outside current safety evidence |

## Experiment constraints

- no production dependency adoption in R01-E;
- one isolated fixture repository or sandbox;
- read-only/non-destructive tools first;
- max steps and timeout;
- explicit allowlist;
- deterministic PolicyEngine remains final authority;
- human approval for sensitive tool intents;
- trace every model/tool/handoff event;
- zero hidden fallback to provider routes;
- no external provider use without separate approval/budget;
- no connector write/plugin execution/remote execution.

## Evaluation axes

- tool schema adherence;
- forbidden-tool refusal and policy containment;
- recovery behavior;
- handoff correctness;
- state/checkpoint semantics;
- observability;
- cancellation/timeouts;
- deterministic replay where possible;
- dependency footprint;
- security surface;
- local model compatibility;
- operator UX.

## Exit criteria

An experiment may recommend implementation only if it demonstrates bounded execution, policy compatibility, traceability, failure containment and no regression of local-first/no-go gates.

## PASS/BLOCK

PASS as ADR input; implementation remains NOT STARTED. BLOCK any experiment that treats framework guardrails as a replacement for DevPilot deterministic policy.

## Verification

```powershell
python -m devpilot_core docs-governance validate --json
```
