---
doc_id: "DEVPL-GSDLC-R01-E-MODEL-GATEWAY-V2-RECOMMENDATION"
title: "R01-E — Model Gateway v2 recommendation"
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

# Model Gateway v2 recommendation

## 1. Decision

R01-E recommends a **policy-aware Model Gateway v2 contract** for later implementation in GSDLC-06. This sprint does not modify runtime code and does not enable external providers.

The gateway owns only:

- model selection;
- provider selection;
- access-route selection;
- gateway-adapter selection;
- auth-adapter reference;
- capability, availability, cost and benchmark evidence used for routing;
- safe fallback selection;
- routing trace metadata.

It **does not** own planning, handoffs, tool execution, skills, connector execution, MCP server invocation or approvals.

## 2. Mandatory boundary

```text
ApplicationService / caller
  ├─ non-agentic model workload ──> Model Gateway v2
  └─ agentic workload ─────────────> Agent Runtime
                                      │
                                      ├─ ModelRoutingRequest ─> Model Gateway v2
                                      └─ ToolIntent ──────────> Deterministic Policy + Approval
                                                                  ├─ allow -> typed Skill/Tool/MCP
                                                                  └─ deny  -> BLOCK + trace
```

`ModelRouteDecision` MUST NEVER imply or grant `ToolExecutionDecision`.

## 3. Proposed contracts for GSDLC-06

### ModelRoutingRequest

- `workload_id`
- `required_capabilities[]`
- `privacy_class`
- `max_cost_usd`
- `offline_required`
- `target_region`
- `provider_constraints[]`
- `latency_preference`
- `fallback_policy`

### ModelRouteDecision

- `model_id`
- `provider_id`
- `access_route_id`
- `gateway_adapter_id`
- `auth_adapter_id`
- `evidence_refs[]`
- `estimated_cost`
- `route_status`
- `fallback`
- `blocked_reason`

## 4. Routing order

1. required capabilities;
2. privacy/offline gate;
3. explicit provider enablement gate;
4. region + terms + auth + data-handling gate for external candidates;
5. cost ceiling;
6. health/availability;
7. workload-specific benchmark evidence;
8. safe selection or safe fallback;
9. BLOCK when no safe candidate exists.

## 5. Current default and fallbacks

- `mock`: safe default for deterministic/no-cost baseline.
- Ollama localhost: local opt-in candidate based on R01-C/D evidence.
- LM Studio localhost: local fallback candidate subject to health/hardware and exact model license.
- external APIs/cloud/brokers: remain conditional or unknown and runtime-disabled.
- consumer subscription/session/browser piggyback: blocked.

No benchmark result creates an operational permission. The R01-D quality/cost ordering is workload evidence only.

## 6. Agentic safety constraint inherited from R01-D

Both tested local models selected `filesystem.delete` in `DVP-AGENTIC-REFUSAL-001`; DevPilot policy blocked the execution. Both scored 40.0 in the recovery fixture. Therefore:

- autonomous forbidden-tool handling: blocked;
- bounded ToolIntent proposal: conditional and guarded by deterministic policy/approval;
- autonomous recovery: not production-accredited;
- model ranking cannot override PolicyEngine, approval or tool permissions.

## 7. Auth adapter recommendation

Recommend interfaces only; do not configure credentials in R01-E:

- `LocalLoopbackNoSecretAdapter`: base local recommendation;
- `EnvApiKeyAdapter`: conditional future provider enablement; store env-var name only;
- `AzureEntraIdentityAdapter`: conditional future provider-specific route;
- `AwsIamRoleAdapter`: conditional future provider-specific route;
- `McpOAuthAdapter`: future Skills/Protocols layer;
- `ConsumerSessionAdapter`: blocked.

A generic adapter accepting arbitrary secrets is not recommended.

## 8. PASS/BLOCK

PASS for this recommendation when routing remains evidence-backed, mock/local remains default, all external enablement stays disabled, and tool execution remains outside Model Gateway.

BLOCK any future implementation that lets a provider/model route decision bypass deterministic tool policy, approval, cost, privacy, region or no-go gates.

## 9. Risks

This is a design recommendation, not a production Model Gateway implementation. It requires GSDLC-06 implementation, schemas, tests, observability, migrations and provider-specific ADRs before production use.

## 10. Verification

```powershell
python -m devpilot_core project-state validate --json
python -m devpilot_core docs-governance validate --json
python -m devpilot_core test-contracts validate --json
python -m devpilot_core test-contracts validate-v2 --json
```
