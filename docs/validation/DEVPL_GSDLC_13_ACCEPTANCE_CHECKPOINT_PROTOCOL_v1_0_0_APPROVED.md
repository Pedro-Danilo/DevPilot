---
doc_id: "DEVPL-GSDLC-13-ACCEPTANCE-CHECKPOINT-PROTOCOL"
title: "DEVPL-GSDLC-13 — Acceptance checkpoint protocol"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-09-21"
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

### 13-D

- `13-D-01`: first Story context + implementation route — pasos 18–19.
- `13-D-02`: Change Plan + Diff + Dry-run + Approval + Apply — pasos 20–24.
- `13-D-03`: Test Impact + targeted tests + remediation + Quality — pasos 25–27.
- `13-D-04`: Git review/stage/commit + return Project Status — pasos 28–30.
- `13-D-05`: repeat story cycle until MVP — paso 31.
- `13-D-06`: controlled recovery scenarios — paso 32.
- `13-D-07`: Release Readiness + package/checksum/SBOM/version/release notes — pasos 34–35.
- `13-D-08`: clean install + rollback + local release — pasos 36–38.

`Paso 33 / UX-P1` aplica a todos los checkpoints B-D.

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
