---
doc_id: "ADR-0010-AGENT-RUNTIME-FRAMEWORK-EXPERIMENT-BOUNDARY"
title: "ADR-0010 — Agent runtime framework experiment boundary"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-08-29"
approval: "approved_by_owner_design"
---

# Decision

DevPilot governed runtime remains the baseline/reference runtime for GSDLC-07-A. No external agent framework dependency is adopted in this sprint.

OpenAI Agents SDK, Microsoft Agent Framework and LangGraph remain `candidate-for-experiment`. MCP remains `candidate-for-experiment/Skills-Protocols`; it does not belong to Model Gateway. Any future experiment requires a bounded fixture, threat model, dependency decision, rollback, observability and explicit owner adjudication before production adoption.

# Authority boundary

- Model Gateway owns provider/model/access-route/auth-adapter routing only.
- Agent Runtime owns session, bounded planning, handoffs and ToolIntent lifecycle.
- Skills/Tools/MCP own typed capability contracts/adapters.
- PolicyEngine + RBAC + Approval own ToolExecutionDecision.
- A ModelRouteDecision never grants tool permission.
- An agent role never becomes a human approval role.

# Safety

No arbitrary shell, no self-approval, no silent file writes, no unbounded loops, no real MCP write-capable execution and no external API requirement are introduced by 07-A.

# Revisit trigger

Revisit only from a later micro-sprint/backlog with experiment evidence; editing this ADR merely to enable a framework is BLOCK.
