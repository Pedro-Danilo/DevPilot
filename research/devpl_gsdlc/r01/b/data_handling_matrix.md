---
doc_id: "DEVPL-GSDLC-R01-B-DATA-HANDLING-MATRIX"
title: "DEVPL-GSDLC-R01-B — Data handling, retention and privacy matrix"
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

# Data handling, retention and privacy matrix

## Default rule

Data is classified **before** selecting a model/route. For PII, sensitive or regulated data sent to an external provider, the default is `BLOCK` until a Privacy/Legal gate documents lawful basis/authorization, controller/processor roles, DPA, transfer/transmission mechanism, processing region, subprocessors, retention, deletion, security controls and approval.

## Route-level data gates

| Route | Decision | Data handling gate |
|---|---|---|
| Ollama localhost | allowed | local data path; exact model license and dataset classification still apply |
| LM Studio localhost | allowed | local data path; exact model license and dataset classification still apply |
| OpenAI API directa | conditional | fresh terms/privacy/region + data classification + secret injection + owner budget approval |
| Anthropic API directa | conditional | fresh terms/privacy/region + data classification + approved secret handling |
| Gemini API paid | conditional | DPA/terms/privacy/region freeze + data classification + logging controls |
| Gemini API unpaid | blocked | BLOCK for non-public/confidential/PII; no DevPilot external runtime enablement |
| Azure OpenAI | conditional | exact Azure region, identity, DPA, retention/logging and dataset classification |
| AWS Bedrock | conditional | provider+model+retention_mode+source_region+inference_profile must be frozen |
| Mistral API | unknown | BLOCK from allow until CO contractual/processing/residency evidence is frozen |
| OpenRouter | conditional | downstream provider/route, logging, ZDR/retention and data policy must be frozen |
| Remote OpenAI-compatible genérico | unknown | provider identity + official terms/privacy/region required before any allow |
| Consumer web session piggyback | blocked | BLOCK; no exception in R01-B |
| Consumer subscription como API | blocked | BLOCK unless an official supported programmatic mechanism is separately reviewed |
| Long-tail R01-A no congelado contractualmente | unknown | route-specific review required |

## Research-specific findings preserved literally

- Gemini unpaid is blocked for confidential code, PII and non-public DevPilot datasets; Gemini paid remains conditional under a different service/data-use regime.
- AWS Bedrock is conditional because invocation logging, retention and cross-region behavior are configuration-sensitive; a future route must pin model, retention mode, source region and inference profile.
- Google benchmark logging/dataset sharing remains off unless explicitly approved.
- Mistral remains `unknown` for the Colombia gate because the attached research did not freeze all processing/residency/contract variables.
- Local runtime does not waive exact model license or dataset-classification requirements.

## No inference policy

If retention, training, abuse monitoring, residency or deletion is not officially documented in the attached research for a route, this materialization records `unknown`; it does not infer a favorable answer.
