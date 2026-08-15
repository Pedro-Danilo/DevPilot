---
doc_id: "DEVPL-GSDLC-R01-B-RESEARCH-REPORT"
title: "DEVPL-GSDLC-R01-B — Canonical research materialization"
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

# R01-B research materialization

## Authority

This artifact is a versioned materialization of `deep-research-report_GSDLC-R01-B.md` (SHA-256 `75180cea1d5755254b7b8db959eba16ff4e626869d41ab93aa4caff698a8a23e`), not a new research run.

Source authority used by the research and by this integration:

```text
repo:   repo_DevPilot_Local_343_DEVPL_GSDLC_R01_A_LANDSCAPE.zip
commit: 316f616263a74916e9a35ce1596f70e86952ebaa
sha256: fcb853ea37f02e2d820bd26b12a883157c01581966b429acb221e0ee73eafa01
parent historical repo342 commit: 90d4f4b76168aab1f2e74c86213cf7d4e4831186
```

R01-A is `CLOSED/PASS` by owner adjudication. The copy of R01-A CURRENT inside repo343 may remain the historical pre-owner snapshot and is not rewritten.

## Research verdict before integration

`PASS-CANDIDATE / INTEGRATION-PENDING`.

- real provider API calls: 0
- real credentials read/tested: 0
- paid tests: 0
- models downloaded: 0
- external provider runtime enabled: no
- S0/S1: 0/0
- R01-C authorized: not yet; owner adjudication after integration is required

## Decisions

| Route | Decision |
|---|---|
| Ollama localhost | **allowed** |
| LM Studio localhost | **allowed** |
| OpenAI API directa | **conditional** |
| Anthropic API directa | **conditional** |
| Gemini API paid | **conditional** |
| Gemini API unpaid | **blocked** |
| Azure OpenAI | **conditional** |
| AWS Bedrock | **conditional** |
| Mistral API | **unknown** |
| OpenRouter | **conditional** |
| Remote OpenAI-compatible genérico | **unknown** |
| Consumer web session piggyback | **blocked** |
| Consumer subscription como API | **blocked** |
| Long-tail R01-A no congelado contractualmente | **unknown** |

## Main conclusions

1. No external provider is enabled or authorized for production by this research.
2. Ollama localhost and LM Studio localhost are the only `allowed` routes for the next **controlled local** R01-C benchmark proposal, still disabled by default and requiring owner approval before model download.
3. External APIs are at best `conditional`; Gemini unpaid is explicitly blocked for confidential/non-public/PII workloads; Mistral and generic remote OpenAI-compatible routes retain `unknown` where evidence is insufficient.
4. PII/sensitive/regulated data to external providers defaults to BLOCK until Privacy/Legal controls are frozen.
5. Consumer web subscriptions/sessions are not API entitlement and browser-session piggyback is blocked.
6. Broker routes must pin downstream providers; no dynamic fallback to unevaluated routes.
7. Model Gateway, Agent Runtime and Skills/Tools/Protocols remain separate boundaries.

## Source-ledger integrity note

The attached report states that the original deep-research session produced **61 source records**. The attached `.md` does not embed the full original 61-record URL ledger. This integration therefore retains:
- all 27 exact R01-A source records inherited from repo343;
- every research citation handle that is actually present in the attached R01-B report;
- internal authority documents and hashes;
- an explicit flag that the original 61-row ledger was not byte-for-byte recoverable from the attachment.

No missing URL is fabricated. This is an audit/reproducibility limitation, not a hidden assertion. The owner may accept the report+citation references as closure evidence or require the original source-list artifact before adjudicating `CLOSED/PASS`.

## Effective research date

The attached report declares `2026-08-15 America/Bogota` as its effective retrieval date. That source-declared date is preserved; this materialization does not rewrite it.
