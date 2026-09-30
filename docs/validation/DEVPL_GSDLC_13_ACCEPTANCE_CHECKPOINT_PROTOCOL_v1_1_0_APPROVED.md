---
doc_id: "DEVPL-GSDLC-13-ACCEPTANCE-CHECKPOINT-PROTOCOL"
title: "DEVPL-GSDLC-13 — Acceptance checkpoint protocol — 13-D audit-aligned successor"
status: "approved"
version: "1.1.0"
owner: "Ordóñez"
updated: "2026-09-30"
approval: "approved_by_owner_for_pre13d"
supersedes_on_approval: "03_DEVPL_GSDLC_13_ACCEPTANCE_CHECKPOINT_PROTOCOL_v1_0_0_APPROVED.md"
audit_input: "DEVPL_IMPLEMENTATION_RELEASE_CAPABILITY_AUDIT_PRE_13D_v1_0_0.md"
---

# Acceptance checkpoint protocol

## 1. Principio

13-B..13-D se ejecutan por **checkpoints semánticos**, no por un script de clics ni por una conversación distinta después de cada acción.

## 2. Ciclo de cada checkpoint

1. ChatGPT emite Run Card con `checkpoint_id`, objective, start state, mission, prohibited help, stop point y evidence minimum.
2. Owner opera DevPilot hasta stop point o BLOCK.
3. Owner registra first-attempt y métricas UX.
4. Owner adjunta Run Packet incremental.
5. ChatGPT adjudica `PASS`, `PASS+FINDING` o `BLOCK`.
6. Si PASS, emite la siguiente Run Card.
7. Si BLOCK de DevPilot, entra Corrective Mode; tras validación se retesta el mismo checkpoint, no el sprint completo.

## 3. Checkpoints oficiales

### 13-B

- `13-B-01`: launch/login/Home — pasos 1–2.
- `13-B-02`: Create Project → idea/constraints → plan/dry-run/approval → workspace/Git/environment — pasos 3–7.
- `13-B-03`: Project Status + controlled restart/recovery — paso 8 y primer caso controlado de resiliencia.

### 13-C

- `13-C-01`: Vision + Scope + Requirements — pasos 9–11.
- `13-C-02`: Architecture + Security + Test Strategy + ADRs + traceability — paso 12.
- `13-C-03`: MIASI/MIPSoftware + Pre-code readiness — paso 13.
- `13-C-04`: Roadmap + Backlog + Sprint + Stories/readiness — pasos 14–17.

### 13-D — audit-aligned

### D01 — first Story activation/context + implementation route

Start evidence:

- DevPilot repo/commit/SHA;
- active workspace/project context;
- Planning FROZEN/IMPLEMENTING_READY;
- current StoryExecution state before Owner action.

PASS evidence:

- selected READY story identity;
- DoR result/hash;
- StoryContextPack ID/hash;
- StoryExecution PLANNED/IN_PROGRESS transition;
- context/source/provenance reviewability;
- route mode/provider/model/provenance when applicable;
- operator project/runtime seed = 0.

BLOCK:

- authority ambiguity;
- no-active-story with no normal activation route;
- terminal/operator required to create StoryExecution;
- Owner forced to act blind on context.

### D02 — Change Plan/apply

Evidence:

- draft source mutation=false;
- plan ID/hash;
- exact path allowlist;
- diff;
- risk;
- Test Impact preview;
- dry-run/recheck;
- approval ID;
- apply manifest;
- source changed only after approved apply.

### D03 — Test/Quality

Evidence:

- Test Impact report/hash;
- StoryTestPlan ID/hash/status;
- required/recommended tests;
- typed jobs/results;
- Quality Report;
- remediation/retest if used;
- Full signal recorded as informational;
- **full_regression_runs=0**.

### D04 — Git

Evidence:

- Quality COMMIT_READY binding;
- CommitPlan ID/hash/path set;
- stage approval ID;
- exact stage receipt;
- staged recheck;
- commit approval ID;
- commit SHA/parent/files;
- GitCommitRecord/trace;
- Story DONE;
- Project Status next action;
- push=false.

### D05 — repeat cycle

PASS only if at least one subsequent story can be activated and executed through the normal story loop.
Navigation alone is insufficient.

### D06 — controlled recovery

Evidence per scenario:

- precondition;
- injected/observed condition;
- classification;
- next safe action;
- preserved drafts/evidence;
- Git before/after;
- destructive operations=false.

### D07 — release readiness/package/metadata

Evidence:

- readiness state/blockers;
- package plan/result;
- artifact checksum;
- SBOM;
- reproducibility;
- version decision;
- release notes hash;
- TagPlan ID/hash;
- release approval ID;
- local annotated tag;
- exact commit verification;
- push/publish/deploy=false.

### D08 — install/rollback/local release

Evidence:

- clean install plan/report;
- sandbox identity;
- install smoke;
- backup;
- upgrade;
- rollback;
- restore/hash parity;
- production data touched=false;
- release graph hash;
- READY_TO_FINALIZE;
- final local release receipt;
- Project Status RELEASED.

### 13-E

- `13-E-01`: independent adjudication — paso 39.

## 4. Evidence minimum por Run Packet

- checkpoint ID y timestamps;
- start/end DevPilot authority/project context;
- receipts/export/logs generados por DevPilot;
- screenshots solo de estados decisivos;
- first-attempt PASS/BLOCK;
- time-to-next-valid-action;
- confused moments y causa;
- normal-user terminal escapes;
- audit/operator terminal uses por separado;
- operator project writes;
- approvals/provenance IDs cuando correspondan;
- Git before/after cuando corresponda;
- tests/gates/result cuando corresponda;
- UX finding IDs/severity/disposition;
- Owner confidence 1–5.

## 4A. Invariantes adicionales para D01–D08

- `operator_project_writes=0`;
- normal-user terminal escapes=0;
- approvals server-authoritative;
- source mutations solo por rutas gobernadas;
- no destructive Git;
- **Full Regression=0**;
- S0/S1=0 para checkpoint PASS.

## 5. Stop conditions

Detener el checkpoint si:

- la UI no ofrece una ruta normal para una acción obligatoria;
- se requiere escribir/editar el proyecto externamente;
- una approval puede bypassarse;
- authority/project context es ambiguo;
- aparece UX-S0/S1;
- la recuperación propuesta es destructiva;
- provenance/evidence no permite atribuir el cambio.

No detener por un S3 puramente visual si la tarea sigue siendo inequívoca; registrarlo en UX-P1.

### Stop conditions adicionales derivadas de la auditoría PRE-13D

También detener si:

- start authority stores contradicen materialmente Git/finalize authority;
- D01/D05 requiere operador, terminal o API manual para sembrar `StoryExecution`;
- D04 omite stage approval o commit approval;
- D03 intenta ejecutar Full Regression;
- D07 intenta cerrar el release sin TagPlan, release approval y annotated local tag exact-commit;
- D08 trata push/publish/deploy/signing como requisito del local release.
