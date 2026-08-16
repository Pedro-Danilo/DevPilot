---
doc_id: "DEVPL-GSDLC-R01-E-REEVALUATION-PROTOCOL"
title: "R01-E — Multi-model and agentic reevaluation protocol"
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

# Reevaluation protocol

## 1. Purpose

Keep R01 decisions updateable without silently changing historical evidence.

## 2. Freshness classes

- F0: same-day/high-volatility pricing, availability, outages or legal notices when directly gating an action.
- F1: <=30 days for provider/agent-runtime documentation used in active design decisions.
- F2: <=90 days for slower-moving architecture documentation.
- Historical: immutable R01-A→D benchmark and adjudication evidence.

## 3. Mandatory reevaluation triggers

Re-run targeted research before:

- enabling any external provider;
- changing auth method;
- changing target region/jurisdiction;
- changing model license/version/quantization;
- adopting a broker/downstream fallback;
- adopting an agent framework/runtime;
- enabling real MCP transport or write-capable tools;
- changing privacy/data classification;
- material provider terms/pricing/retention changes;
- benchmark hardware or workload profile changes.

## 4. Procedure

1. freeze current source register;
2. query official primary sources only for changing claims;
3. retain retrieval timestamp, target region and source URL;
4. compare against previous decision;
5. never rewrite historical R01 evidence;
6. create successor recommendation/ADR when decision changes;
7. run policy simulation and affected tests;
8. obtain owner approval before enablement.

## 5. Benchmark cadence

Local model benchmark should be repeated when hardware, runtime, model digest or DevPilot workload fixtures change materially. Agentic safety fixtures should expand adversarially before any claim of autonomous capability.

## 6. PASS/BLOCK

PASS when no critical claim used for an action is stale. BLOCK enablement when contractual/privacy/region/license evidence is stale, absent or ambiguous.

## 7. Risks

A fresh documentation page does not guarantee legal sufficiency; legal/contract review may remain an explicit gate.

## 8. Verification

```powershell
python -m devpilot_core docs-governance validate --json
```
