---
doc_id: "DEVPL-GSDLC-R01-E-SELECTIVE-REGRESSION-RECONCILIATION"
title: "DEVPL-GSDLC-R01-E — Selective regression reconciliation after one full regression"
status: "implemented-initial"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-08-15"
approval: "pending_owner_final_adjudication"
---

# DEVPL-GSDLC-R01-E — Selective regression reconciliation

## 1. Decision

`PASS-COMPOSITE/PENDING-OWNER-ADJUDICATION`.

The R01-E full regression was executed exactly once. It produced `2263 passed / 6 failed / 0 errors / 0 skipped`. The same six failures are reproducible on the immutable repo347 input before applying the R01-E delta; therefore they are inherited historical-contract drift rather than runtime/research regressions introduced by R01-E.

## 2. Corrective scope

- `.devpilot/release/local_release_candidate_criteria.json`: synchronize the mutable top-level `expected_current_repo` with `project_state.current_repo=repo342`; the critical evidence item was already repo342.
- `tests/test_devpl_gsdlc_00_e_baseline_closure.py`: freeze 00-E against its historical project-state snapshot, not the mutable top-level Source Registry last-registered pointer.
- `tests/test_post_h_eval_002_01_b_clean_install_baseline_verification.py`: replace obsolete POST-H-EVAL-002 filename-family coupling with monotonic successor semantics.
- `tests/test_post_h_eval_002_01_c_api_ui_startup_security_posture.py`: same successor correction for 01-C.
- No runtime, UI, TCR, provider policy, no-go gate, historical evidence hash or R01-E research result was weakened.

## 3. Validation actually executed

- original full regression: 2263 PASS / 6 FAIL; **not repeated**; SHA-256 `266a34088455aa2f3420b9424caf6c5eb87b50a3bfb60cb13bfdb9bff68d9a6f`.
- exact residual failures: `6/6 PASS`.
- complete files containing the three rewritten historical assertions: `16/16 PASS`.
- evidence freshness contract: `6/6 PASS`.
- Project State: PASS.
- Documentation Governance: PASS.
- TCR v1/v2: PASS.
- Test Impact v2: PASS/dry-run; no tests executed by analyzer.

## 4. PASS/BLOCK

PASS only if the exact final stage contains 25 paths, the six residual tests pass, all bounded selective validations above pass, `git diff --cached --check` passes, S0/S1 remain `0/0`, and `full_pytest_repeated=false`. Any new failure outside this bounded recovery is BLOCK and must be adjudicated before publish.

## 5. Risks and limitations

The composite decision relies on the already completed full regression for the 2263 unaffected tests and on selective retesting for the corrected surfaces. This is intentional and follows the GSDLC-00-E precedent (`composite-full-regression-selective-retest`). No claim is made that a second full regression was executed.

## 6. Verification commands

The authoritative commands are executed by `devpl_gsdlc_r01_e_selective_recovery_operator_v1_0_3.py validate-selective`; operators must not execute `pytest -q` over the whole repository again for this recovery.
