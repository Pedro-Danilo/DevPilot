---
doc_id: "POST-H-EVAL-002-01-B-CLOSURE-AUDIT"
title: "POST-H-EVAL-002-01-B — Clean installation and baseline verification closure"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-07-16"
approval: "PASS-WITH-GAPS"
---

# POST-H-EVAL-002-01-B — Closure report

## Decision

`PASS-WITH-GAPS`, closed and authorizing `POST-H-EVAL-002-01-C`.

The Windows-authoritative execution installed the immutable baseline 318 in a new path, installed Python and frontend dependencies, built the Web UI, executed the POST-H-034 closure contract and all required governance validators, and preserved physical separation between platform, governance, evidence and the future workspace.

## Authoritative artifacts

| Artifact | SHA-256 |
|---|---|
| `DevPilot_E2E_Evaluation_POST-H-EVAL-002-01-B.zip` | `83174a229e93bff2590e19896ea0ba9c0848827e0d37e7b5243580888e6f173f` |
| `POST-H-EVAL-002-01-B_windows_authoritative_evidence.zip` | `ac41871b57ec681146fa501ef57083de955d9ffb1dda1ffb8fb7edd9893080dd` |
| `salida_log_powershell_POST-H-EVAL-002-01-B_03.txt` | `5452d9b091fa5a85711b8ba8af6fc40f9b8a05fe94218a42ab0bbf481465aa90` |

Baseline and governance identities:

- executable baseline: `repo_DevPilot_Local_318_POST_H_EVAL_002_PILOT_READY.zip` — `bf5c10df92a104a9c212c19db28d518eff0d5e5a671b4b35ec71bfd79c7df308`;
- incoming governance: `repo_DevPilot_Local_319_POST_H_EVAL_002_01_A.zip` — `0f96a24fd8040abc2c14bd5c4469bfca3e4aed5b164a03b89238d1ab5776c204`;
- outgoing governance target: `repo_DevPilot_Local_320_POST_H_EVAL_002_01_B.zip`.

## Executed verification

- 17/17 commands PASS;
- clean Python 3.12.3 venv and editable `.[dev]` install PASS;
- `devpilot-local 0.1.0` import/version PASS;
- `npm ci`, smoke, visual, operator flows, route enforcement and production build PASS;
- POST-H-034 closure contract: `6 passed, 0 failed, 0 errors, 0 skipped`;
- Project State: `6/6 PASS`;
- Documentation Governance: `551/551 PASS`, zero drift, zero warnings/blockers;
- TCR v1: `245` contracts PASS;
- TCR v2: `245` contracts PASS, zero network/API/mutation allowance;
- Evidence Freshness: PASS, `42/43 fresh`, zero critical stale/missing/invalid;
- install smoke: PASS;
- secret scan: PASS, zero findings;
- path separation: PASS, zero overlaps;
- final archive sidecar and CRC: PASS.

## Regression decision

No new full `pytest -q` was executed in 01-B. The exact baseline hash matches the previously validated 318 artifact whose authoritative full regression is `1919 passed`. The 01-B prompt requires the focal POST-H-034 closure contract and the governance validators. Since the platform source was not changed, repeating the full suite would add cost without increasing confidence. The runbook is clarified accordingly: exact-hash inheritance is valid unless source drift, S0/S1, dependency behavior drift or a release gate explicitly requires a rerun.

## Non-blocking gap

`EVAL-002-01-B-GAP-001` — the evidence ZIP includes five generated `src/devpilot_local.egg-info/*` files created by editable installation. They contain package metadata only, no executable behavior or secrets, are not committed to Git, and do not invalidate installation evidence. They are classified `S3 / packaging hygiene`; future operator archives must exclude `*.egg-info`.

## Safety posture

- provisioning network was explicitly approved only for dependency installation;
- runtime external network remains disabled;
- external APIs, connector write, plugin execution, remote execution, productive multiuser and enterprise/SaaS remain disabled;
- no workspace was created;
- no API token was generated in 01-B;
- platform baseline remains frozen.
