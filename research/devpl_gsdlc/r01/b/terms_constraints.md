---
doc_id: "DEVPL-GSDLC-R01-B-TERMS-CONSTRAINTS"
title: "DEVPL-GSDLC-R01-B — Terms, subscription and billing constraints"
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

# Terms, subscription and billing constraints

## Mandatory separation

`consumer subscription != API/programmatic entitlement != technical authentication != workload authorization`.

No price, rate-limit number or contractual term absent from the attached report is invented here. Values not frozen by the report remain `unknown` and must be refreshed before any external benchmark/enablement.

## Route constraints

| Route | Decision | Contract/billing constraint |
|---|---|---|
| Ollama localhost | allowed | The attached research report explicitly allows this local route for R01-C only; model license, hardware fit, loopback and owner approval before download remain mandatory. |
| LM Studio localhost | allowed | The attached report explicitly allows LM Studio localhost for R01-C only, with no external network/API requirement and approval before model download. |
| OpenAI API directa | conditional | Technical authentication does not establish contractual entitlement, data handling suitability or budget approval; external provider runtime remains disabled. |
| Anthropic API directa | conditional | External API route remains conditional pending provider-specific fresh terms/privacy/region freeze and controlled credentials/budget. |
| Gemini API paid | conditional | Attached research distinguishes paid services from unpaid services and states a different data-use regime; paid access still requires provider-specific contractual/privacy/region gates. |
| Gemini API unpaid | blocked | The attached report explicitly blocks unpaid Gemini for confidential code, PII and non-public DevPilot datasets due to the documented unpaid-service data-use regime. |
| Azure OpenAI | conditional | Cloud route requires exact subscription/region/data-processing configuration and contractual review; report does not authorize runtime enablement. |
| AWS Bedrock | conditional | Report identifies invocation logging, retention and cross-region behavior as configuration-sensitive; route must pin model, retention mode, source region and inference profile. |
| Mistral API | unknown | The attached report explicitly states that authentication is documented but evidence was insufficient to freeze all Colombia processing/residency/contract variables; unknown is retained rather than inferred. |
| OpenRouter | conditional | Broker route is conditional and must pin the downstream provider; dynamic fallback to unevaluated providers is not allowed. |
| Remote OpenAI-compatible genérico | unknown | Protocol compatibility does not inherit OpenAI terms, privacy, region or behavior. Provider identity and contract/data path are unresolved. |
| Consumer web session piggyback | blocked | Prompt and report explicitly prohibit browser/DOM/cookie piggyback and reuse of consumer sessions as provider integration. |
| Consumer subscription como API | blocked | Consumer subscription is not evidence of API/programmatic entitlement; the prompt explicitly forbids this equivalence. |
| Long-tail R01-A no congelado contractualmente | unknown | The report retains long-tail routes as unknown until provider-specific auth/terms/privacy/region evidence is frozen. Unknown is not a failure and does not authorize use. |

## Negative cases

- Browser/DOM/cookie/session piggyback: **blocked**.
- Consumer seat treated as API allowance: **blocked**.
- Generic OpenAI-compatible endpoint with unidentified provider/terms: **unknown**, therefore not usable.
- Broker fallback to an unreviewed downstream provider: **blocked by policy** until that downstream route passes the same analysis.
- External paid test without fresh `PRICE_FREEZE`, owner budget approval and bounded CostGuard: **blocked**.

## Future CostGuard minimum for R01-D

Before any paid API benchmark, freeze at least: `budget_usd`, `max_requests`, `max_input_tokens`, `max_output_tokens`, `route_id`, `model_id`, official price source, approver and timestamp. This document authorizes no paid call.
