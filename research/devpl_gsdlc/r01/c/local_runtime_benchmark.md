---
doc_id: "DEVPL-GSDLC-R01-C-LOCAL-RUNTIME-BENCHMARK"
title: "DEVPL-GSDLC-R01-C — Local runtime benchmark"
status: "pass-candidate/integration-pending"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-08-15"
backlog_id: "DEVPL-GSDLC-R01"
micro_sprint: "DEVPL-GSDLC-R01-C"
source_repo: "repo_DevPilot_Local_344_DEVPL_GSDLC_R01_B_AUTH_TERMS_DATA.zip"
source_git_commit: "e4c22c5e95fe856dec9fc3d1767aab3a4ebd3af0"
---

# Local runtime benchmark

## Decision

`PASS-CANDIDATE`.

The benchmark is local-only, zero external API and zero API cost. No raw prompts or model outputs are versioned; only hashes and metrics are retained.

## Measured results

| Candidate | Runtime | Model | License | Result | Median tok/s | Tested prompt tokens |
|---|---|---|---|---|---:|---:|
| ollama-mistral7b-v03-existing | ollama | mistral:7b | Apache-2.0 | VIABLE | None | 2051 |
| ollama-phi4-mini-q4 | ollama | phi4-mini:3.8b-q4_K_M | MIT | NOT-SELECTED | None | None |
| ollama-qwen3-4b-q4 | ollama | qwen3:4b-instruct-2507-q4_K_M | Apache-2.0 | NOT-SELECTED | None | None |
| ollama-gpt-oss-20b | ollama | gpt-oss:20b | Apache-2.0 | NOT-SELECTED | None | None |
| lmstudio-phi4-mini-q4 | lmstudio | microsoft/phi-4-mini | MIT | NOT-SELECTED | None | None |
| lmstudio-qwen3-4b-q4 | lmstudio | qwen/qwen3-4b-2507 | Apache-2.0 | NOT-SELECTED | None | None |
| lmstudio-gpt-oss-20b | lmstudio | openai/gpt-oss-20b | Apache-2.0 | NOT-SELECTED | None | None |

## Interpretation

Viable candidates: `ollama-mistral7b-v03-existing`. Vendor maximum context is not claimed as measured; `tested prompt tokens` is the actual local probe point returned by the runtime when available.

## Security

- localhost-only required;
- external provider calls: `0`;
- API budget: `0 USD`;
- real API keys: none;
- runtime/model installers are never automated;
- model download is possible only after explicit owner approval.
