---
doc_id: "SPRINT-DEVPL-GSDLC-13-D"
title: "DEVPL-GSDLC-13-D — Coding, quality, Git, release and recovery acceptance"
status: "approved"
version: "1.1.0"
owner: "Ordóñez"
updated: "2026-09-21"
supersedes: "SPRINT_DEVPL_GSDLC_13_D_v1_0_0_APPROVED.md"
precondition: "DEVPL-GSDLC-13-C/PASS"
full_policy: "0"
execution_mode: "OWNER-DRIVEN/DEVPL-EXECUTED/CHATGPT-ADJUDICATED"
journey_steps: "18-38; UX-P1 step 33 cross-cutting"
---

# DEVPL-GSDLC-13-D — Coding/quality/Git/release/recovery

## Execution rules

- `Owner-driven / DevPilot-executed / ChatGPT-adjudicated`;
- Owner operates normal UI and makes legitimate product decisions;
- ChatGPT must not implement or author project content for copy/paste;
- operator may start/stop/audit/capture but `operator_project_writes=0`;
- distinguish audit terminal use from mandatory normal-user terminal escape;
- no destructive Git; dry-run/approval before relevant mutations;
- external API not required for PASS;
- UX-P1 findings are evidence-driven;
- PASS normal returns adjudication + next Run Card, not an implementation bundle;
- DevPilot corrective only on real product defect; selective retest resumes exact checkpoint.


## Checkpoints

- `13-D-01` pasos 18–19: Story context pack + implementation route/model policy/provenance.
- `13-D-02` pasos 20–24: Change Plan → Diff → Dry-run → Approval → Apply.
- `13-D-03` pasos 25–27: Test Impact → targeted tests → remediation loop → Quality Gate.
- `13-D-04` pasos 28–30: Git review/stage/verify/commit → volver a Project Status.
- `13-D-05` paso 31: repetir story loop hasta MVP; no bypass externo para acelerar.
- `13-D-06` paso 32: restart/interrupted safe work/external edit/dirty/branch-divergence-conflict/stale lock con recuperación no destructiva.
- `13-D-07` pasos 34–35: Release Readiness → package/checksum/SBOM cuando corresponda → version/release notes.
- `13-D-08` pasos 36–38: clean install → rollback → local release.

Paso 33 / UX-P1 se observa en todos los checkpoints.

## PASS

MVP local reproducible mediante flow gobernado, commits/release/recovery probados, operator writes=0, terminal escapes=0, S0/S1=0.
