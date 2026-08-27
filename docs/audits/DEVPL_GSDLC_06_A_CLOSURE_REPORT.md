---
doc_id: "DEVPL-GSDLC-06-A-CLOSURE-REPORT"
title: "GSDLC-06-A — Model capability and access-route contracts closure report"
status: "pass-candidate/windows-validated/pending-owner-adjudication"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-08-26"
micro_sprint: "DEVPL-GSDLC-06-A"
---

# GSDLC-06-A closure report

## Current decision

`PASS-CANDIDATE / WINDOWS-VALIDATED / PENDING-OWNER-ADJUDICATION`.

06-A establishes `ModelCapabilityCatalog`, `ProviderAccessRoute`, `ModelRoutingRequest` and `ModelRouteDecision`, keeping provider/model/access-route/gateway-adapter/auth-adapter identities separate. Routing is capability/constraint based and cannot grant tool/skill execution authority.

R01 decisions are imported without promotion: mock is enabled/default-safe; local routes remain opt-in and not promoted by 06-A; external routes remain runtime-disabled. OpenAI-compatible protocol is not authorization.

## BLOCK-01 recovery

Windows v1.0.1 passed `40/40` focal tests and then correctly blocked on the historical UOC-003 synchronization invariant because `ui/web/package.json -> devpilot.currentSprint` still said `DEVPL-GSDLC-05-E` while Project State already said `DEVPL-GSDLC-06-A`. A second same-family drift was present in the Source Registry derived summary.

v1.0.2 preserves the historical test unchanged, advances the UI current-active pointer, reconciles the Source Registry summary, and adds a machine guard requiring parity among Project State, UI currentSprint, Source Registry top-level and Source Registry summary. Package version/description are treated as historical build identity, not current pointers.

The v1.0.1 distributed reference bytes reproduce the UOC-003 failure; the older local `38/38` claim is therefore superseded for those bytes. No unsupported provenance explanation is asserted.

## Windows validation

The corrected fingerprint must show `40/40` focal + `38/38` historical-sensitive = `78/78 PASS`, plus Documentation Governance, Project State, TCR v1 and TCR v2 PASS pre-finalize and post-finalize. The prior v1.0.1 PASS receipts are not reusable because source changed.

No functional UI behavior changed, so browser acceptance remains not required. Network/external API remain 0. `full_regression_runs=0`; the unique GSDLC-06 full remains reserved for 06-E.

## Remaining gate

Owner adjudication of the Windows evidence and clean repo375 successor candidate is still required. 06-B remains unauthorized until that independent adjudication.
