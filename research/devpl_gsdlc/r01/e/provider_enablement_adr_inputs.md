---
doc_id: "DEVPL-GSDLC-R01-E-PROVIDER-ENABLEMENT-ADR-INPUTS"
title: "R01-E — Provider enablement ADR inputs"
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

# Provider enablement ADR inputs

## Decision context

R01-E does not enable providers. These inputs define what GSDLC-06/provider-specific ADRs must decide before any external route can move from `conditional/unknown/blocked` to an executable state.

## Required ADR questions

1. exact provider, model, access route and gateway adapter identity;
2. target region/jurisdiction and service availability;
3. exact auth mechanism and secret-injection method;
4. terms, billing, privacy, data retention/training and processing location;
5. data classifications allowed/blocked;
6. explicit budget and cost accounting;
7. availability/health/fallback behavior;
8. logging/redaction/trace requirements;
9. kill switch and rollback;
10. test/eval threshold per DevPilot workload;
11. approval/RBAC requirements;
12. source freshness TTL and revalidation trigger.

## Route dispositions inherited from R01-B/E

External direct APIs, cloud catalogs and brokers remain conditional; generic remote OpenAI-compatible is unknown/conditional; consumer subscription/session piggyback is blocked. No ADR may infer entitlement from protocol compatibility or consumer subscription.

## Auth adapter constraints

Prefer runtime injection and short-lived/provider-native identity. Repository stores metadata or environment variable names only, never raw secrets.

## PASS/BLOCK

PASS ADR input only if all fields above are resolved from official primary sources and no no-go gate is relaxed implicitly. BLOCK provider enablement on stale/unknown contractual evidence, missing budget, missing data-classification approval or missing rollback.

## Risks

Provider facts are time-sensitive. R01-B/E evidence is research evidence, not perpetual authorization. Refresh immediately before enablement.

## Verification

```powershell
python -m devpilot_core project-state validate --json
python -m devpilot_core docs-governance validate --json
```
