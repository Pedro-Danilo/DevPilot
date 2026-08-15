---
doc_id: "DEVPL-GSDLC-R01-B-AGENTIC-ACCESS-CONSTRAINTS"
title: "DEVPL-GSDLC-R01-B — Agentic access and hosted-surface constraints"
status: "implemented-controlled/pending-windows-validation"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-08-14"
backlog_id: "DEVPL-GSDLC-R01"
micro_sprint: "DEVPL-GSDLC-R01-B"
source_repo: "repo_DevPilot_Local_343_DEVPL_GSDLC_R01_A_LANDSCAPE.zip"
source_git_commit: "316f616263a74916e9a35ce1596f70e86952ebaa"
research_basis: "deep-research-report_GSDLC-R01-B.md"
---

# Agentic access constraints

## Architectural separation

```text
Model Gateway
  = model/provider/access-route routing + capabilities + cost/auth metadata

Agent Runtime
  = planning/orchestration/session/handoffs/tool-use lifecycle

Skills/Tools/Protocols
  = typed capabilities + permissions + MCP/function interfaces
```

A local SDK/framework is not classified as an external provider simply because it supports agents. A hosted agent, cloud execution environment, hosted vector/file store, OAuth app, remote tool, broker or provider-managed skill surface must inherit the same auth/terms/privacy/region gate as its actual access route.

## Constraints

- No hosted agentic surface is enabled by R01-B.
- No browser-session/cookie piggyback is permitted.
- No remote tool or hosted skill may bypass deterministic DevPilot Policy/RBAC/Approval.
- No agent self-approval.
- No unbounded tool loop/cost.
- No arbitrary connector/plugin write or remote execution enablement.
- Broker/hosted orchestration must pin downstream provider(s); no unreviewed dynamic fallback.
- Provider/model/access route and Agent Runtime/Skill layers remain independently observable and attributable.

## Current outcome

R01-B supplies evidence only. Production Agent Runtime, skill/plugin execution and external provider enablement remain out of scope and disabled.
