---
doc_id: "DEVPL-GSDLC-13-REBASELINE"
title: "DEVPL-GSDLC-13 — Real product acceptance and pilot rebaseline"
status: "approved/active"
version: "2.1.0"
owner: "Ordóñez"
updated: "2026-09-21"
supersedes: "04_DEVPL_GSDLC_13_REAL_PRODUCT_ACCEPTANCE_REBASELINE_v2_0_0_APPROVED.md"
source_repo: "repo_DevPilot_Local_436_DEVPL_UX_P0_E_PRE_PILOT_PRODUCTIZATION_RC_WINDOWS_VALIDATED_CANDIDATE.zip"
source_git_commit: "423e99fa38df3114328b555aff8f859740a49a01"
source_repo_sha256: "d8e1b2ded46648dab7d463ab3d4f6973ba0122c8ad22bf6f6cf474791deb68cb"
predecessor_backlog: "DEVPL-UX-P0/CLOSED-PASS-WINDOWS-VALIDATED"
git_remote_sync: "PASS"
execution_model_after_13_a: "owner-driven/devpilot-executed/chatgpt-adjudicated"
---

# DEVPL-GSDLC-13 — Real product acceptance rebaseline

## 1. Activation state

Repo436 frozen; local/remote synchronized at `423e99fa38df3114328b555aff8f859740a49a01` with tag `devpilot-ux-p0-closed-repo436`. Precondition de remote sync satisfecha.

## 2. Objective

Demostrar DevPilot como producto integrado desde project creation hasta local release y posteriormente autorizar, por separado, Legacy Adoption Acceptance.

## 3. Micro-sprints y journey

### 13-A — Transition/rebind and authority hygiene

Último sprint en Implementation Mode. Materializa estas autoridades, rebind current-active y prepara roots/instrumentation. No crea project content. Full=0.

### 13-B — Greenfield bootstrap acceptance — pasos 1–8

Launch/login/Home → Create Project → idea/constraints/model policy → plan/dry-run/approval → workspace/Git/environment → Project Status → restart/recover. Se ejecuta desde UI por el Owner.

### 13-C — Guided engineering + planning — pasos 9–17

Vision → Scope → Requirements → Architecture/Security/Test Strategy/ADRs/traceability → MIASI/MIPSoftware → readiness → Roadmap/Backlog/Sprint/Stories.

### 13-D — Coding/quality/Git/release/recovery — pasos 18–38

Story context → implementation route → Change Plan/Diff/Dry-run/Approval/Apply → tests/remediation/Quality → Git commit → repeat to MVP → recovery scenarios → Release Readiness → package/checksum/SBOM → clean install → rollback → local release. UX-P1 paso 33 transversal.

### 13-E — Independent adjudication — paso 39

Audita evidence; aplica Full condicional solo si hubo DevPilot source delta según policy; segunda Full=0; autoriza legacy solo después de greenfield closure.

## 4. Interaction policy

Los prompts B/C/D no son implementation specifications. Son **acceptance protocols**. ChatGPT no implementa el greenfield; entrega Run Cards y adjudica Run Packets. Corrective bundle reaparece únicamente si un defecto de DevPilot requiere source mutation.

## 5. DoD

Greenfield local release; operator writes=0; mandatory terminal escapes=0; provenance complete; recovery/conflict paths probados; Guided critical path usable; S0/S1=0; Full policy respected; legacy preserved.
