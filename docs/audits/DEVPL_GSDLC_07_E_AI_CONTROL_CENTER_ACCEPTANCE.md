---
doc_id: "DEVPL-GSDLC-07-E-AI-CONTROL-CENTER-ACCEPTANCE"
title: "GSDLC-07-E — AI Control Center acceptance"
status: "PASS/PRE-WINDOWS"
version: "1.0.0"
owner: "DEVPL-GSDLC-07-E"
updated: "2026-08-30"
approval: "pending_browser_evidence"
---
# GSDLC-07-E — AI Control Center acceptance

`AgentEvalTraceView` is added to the existing AI Control Center administration surface. It is a read-only projection of sealed local evidence and does not invoke a model or tool.

The view exposes agent/runtime, model/provider/access-route, sources, tokens/cost, ACCEPT/MODIFY/REJECT, ToolIntent → PolicyEngine/RBAC/Approval → ToolExecutionDecision, forbidden-tool containment, hard-stop, bounded handoff and v2.2/v2.3 posture. Manual Artifact Workbench operation remains first-class.

Final PASS requires real Windows browser screenshots and machine receipts.
