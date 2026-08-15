---
doc_id: "DEVPL-GSDLC-R01-B-REGIONAL-JURISDICTION-MATRIX"
title: "DEVPL-GSDLC-R01-B — Regional availability and jurisdiction matrix"
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

# Regional availability and jurisdiction matrix

Primary target region: **CO / Colombia**.

## Jurisdiction policy

Origin/nationality is metadata, never a standalone allow/block rule. The controlling dimensions are provider legal entity/terms, target-region availability, processing/hosting region, transfer path, workload/data class and verified export/sanctions constraints where applicable.

## Route decisions for CO

| Route | R01-B decision | CO integration status | Required next evidence |
|---|---|---|---|
| Ollama localhost | allowed | local benchmark candidate only | local data path; exact model license and dataset classification still apply |
| LM Studio localhost | allowed | local benchmark candidate only | local data path; exact model license and dataset classification still apply |
| OpenAI API directa | conditional | not authorized | fresh terms/privacy/region + data classification + secret injection + owner budget approval |
| Anthropic API directa | conditional | not authorized | fresh terms/privacy/region + data classification + approved secret handling |
| Gemini API paid | conditional | not authorized | DPA/terms/privacy/region freeze + data classification + logging controls |
| Gemini API unpaid | blocked | not authorized | BLOCK for non-public/confidential/PII; no DevPilot external runtime enablement |
| Azure OpenAI | conditional | not authorized | exact Azure region, identity, DPA, retention/logging and dataset classification |
| AWS Bedrock | conditional | not authorized | provider+model+retention_mode+source_region+inference_profile must be frozen |
| Mistral API | unknown | not authorized | BLOCK from allow until CO contractual/processing/residency evidence is frozen |
| OpenRouter | conditional | not authorized | downstream provider/route, logging, ZDR/retention and data policy must be frozen |
| Remote OpenAI-compatible genérico | unknown | not authorized | provider identity + official terms/privacy/region required before any allow |
| Consumer web session piggyback | blocked | not authorized | BLOCK; no exception in R01-B |
| Consumer subscription como API | blocked | not authorized | BLOCK unless an official supported programmatic mechanism is separately reviewed |
| Long-tail R01-A no congelado contractualmente | unknown | not authorized | route-specific review required |

## Regulatory notes preserved from research

- **Colombia:** use of AI does not remove personal-data obligations; external PII remains blocked until the specific Privacy/Legal gate is satisfied.
- **United Kingdom:** technical availability does not imply lawful restricted transfer; appropriate safeguards/IDTA/Addendum and transfer-risk assessment may be required when applicable.
- **United States:** no single universal privacy rule is assumed; state/sector/workload review remains case-specific.
- **China:** no origin-based provider block is introduced. A covered public deployment may require jurisdiction-specific legal review; the report distinguishes scope from provider nationality.

Availability/residency values not frozen in the attached research remain `unknown` rather than inferred.
