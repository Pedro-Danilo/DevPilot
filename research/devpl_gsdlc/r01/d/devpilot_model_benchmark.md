---
doc_id: "DEVPL-GSDLC-R01-D-MODEL-BENCHMARK"
title: "DEVPL-GSDLC-R01-D — DevPilot model benchmark"
status: "pass-candidate/integration-pending"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-08-15"
backlog_id: "DEVPL-GSDLC-R01"
micro_sprint: "DEVPL-GSDLC-R01-D"
source_repo: "repo_DevPilot_Local_346_DEVPL_GSDLC_R01_C_BENCHMARK_RECONCILIATION.zip"
source_git_commit: "1bd3468b8bcc8e13de62fbce6b4007981c1eaf52"
---

# DevPilot model benchmark

## Scope

Versioned DevPilot workloads executed locally through Ollama. External APIs were not executed.

## Models

- `mistral:7b` — Apache-2.0 — local-medium
- `qwen2.5:1.5b-instruct` — Apache-2.0 — local-small

## Results

- `mistral:7b` mean deterministic score `71.45`, median latency `33.327303 s`, cost `0 USD`.
- `qwen2.5:1.5b-instruct` mean deterministic score `64.8`, median latency `4.216636 s`, cost `0 USD`.

The scores are preliminary R01-D research evidence, not a production routing policy and not a universal winner declaration.
