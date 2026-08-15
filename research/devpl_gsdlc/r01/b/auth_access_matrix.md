---
doc_id: "DEVPL-GSDLC-R01-B-AUTH-ACCESS-MATRIX"
title: "DEVPL-GSDLC-R01-B — Authentication and access-route matrix"
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

# Authentication and access-route matrix

## 1. Decision semantics

This artifact materializes the attached R01-B research; it does **not** re-run provider research and does not test credentials. Technical authentication, contractual entitlement and billing are separate dimensions. A consumer web subscription is never treated as API entitlement, and an OpenAI-compatible protocol never inherits OpenAI terms/privacy by protocol compatibility alone.

Decision values are exactly `allowed`, `conditional`, `blocked` or `unknown`. `allowed` in R01-B does not mean production enablement: the only allowed routes are local R01-C benchmark candidates and remain disabled by default.

## 2. Route decisions

| Route | Auth documented by research | Billing/access relation | Decision | Authorization after B research | Evidence |
|---|---|---|---|---|---|
| Ollama localhost | anonymous/local | hardware-local | **allowed** | R01-C controlled local benchmark only | SRC-OLLAMA-OPENAI-COMPAT, RPT-DECISION-TABLE, RPT-R01C-GATE |
| LM Studio localhost | anonymous/local, local token optional | hardware-local | **allowed** | R01-C controlled local benchmark only | SRC-LMSTUDIO-APP, RPT-DECISION-TABLE, RPT-R01C-GATE |
| OpenAI API directa | project/service-account API key | API usage/prepaid | **conditional** | none | SRC-OPENAI-ENTERPRISE-PRIVACY, RPT-DECISION-TABLE |
| Anthropic API directa | API key | API usage/credits | **conditional** | none | SRC-ANTHROPIC-MODELS, SRC-ANTHROPIC-DATA-LOCATION, RPT-DECISION-TABLE |
| Gemini API paid | API key, OAuth | Cloud Billing | **conditional** | none | SRC-GOOGLE-GEMINI-LATEST, SRC-GOOGLE-GEMINI-TERMS, RPT-WEB-turn19search1, RPT-WEB-turn19search2, RPT-DECISION-TABLE |
| Gemini API unpaid | API key | free quota | **blocked** | none | SRC-GOOGLE-GEMINI-TERMS, RPT-WEB-turn19search1, RPT-WEB-turn19search2, RPT-DECISION-TABLE |
| Azure OpenAI | Entra/managed identity preferred | Azure usage | **conditional** | none | RPT-DECISION-TABLE |
| AWS Bedrock | IAM, short-lived credentials preferred | AWS usage | **conditional** | none | RPT-WEB-turn19search5, RPT-WEB-turn19search10, RPT-WEB-turn19search6, RPT-WEB-turn19search14, RPT-DECISION-TABLE |
| Mistral API | Workspace API key | free/paid | **unknown** | none | SRC-MISTRAL-SMALL4, RPT-WEB-turn19search3, RPT-WEB-turn19search13, RPT-DECISION-TABLE |
| OpenRouter | broker API key, BYOK where supported | broker + downstream model | **conditional** | none | SRC-OPENROUTER-PRIVACY, SRC-OPENROUTER-PROVIDER-LOGGING, SRC-OPENROUTER-ZDR, RPT-DECISION-TABLE, RPT-BROKER-PINNING |
| Remote OpenAI-compatible genérico | provider-specific | provider-specific | **unknown** | none | SRC-VLLM-OPENAI-COMPAT, RPT-DECISION-TABLE |
| Consumer web session piggyback | cookies/session token | consumer subscription | **blocked** | prohibited | R01B-PROMPT, RPT-DECISION-TABLE |
| Consumer subscription como API | consumer login | seat/subscription | **blocked** | prohibited | R01B-PROMPT, RPT-DECISION-TABLE |
| Long-tail R01-A no congelado contractualmente | provider-specific, unsupported/unknown | provider-specific | **unknown** | none | R01A-SOURCE-REGISTER, R01A-LANDSCAPE, RPT-DECISION-TABLE |

## 3. Reproducible rules

1. `allowed`: official/local route evidence is sufficient for the next bounded activity and no prohibited data/credential condition is triggered.
2. `conditional`: route can only be evaluated after provider-specific terms/privacy/region/data/budget/secret gates are frozen.
3. `blocked`: the attached prompt/report contains an explicit prohibition or a data-use condition makes the requested DevPilot workload inadmissible.
4. `unknown`: evidence in the attached research is insufficient; absence of proof is not converted into allow.
5. No route decision uses model/provider nationality as an allow/block shortcut.
6. External provider runtime remains disabled regardless of this matrix.

## 4. R01-C gate

Only `Ollama localhost` and `LM Studio localhost` may move to the **controlled local benchmark proposal** for R01-C. Before any model download the proposal must state exact model ID, official source, exact license, size, estimated RAM/VRAM, disk, runtime and benchmark purpose; owner approval is required. No approval means no download.
