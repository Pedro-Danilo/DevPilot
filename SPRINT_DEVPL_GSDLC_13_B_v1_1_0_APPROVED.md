---
doc_id: "SPRINT-DEVPL-GSDLC-13-B"
title: "DEVPL-GSDLC-13-B — Greenfield project bootstrap acceptance"
status: "approved"
version: "1.1.0"
owner: "Ordóñez"
updated: "2026-09-21"
supersedes: "SPRINT_DEVPL_GSDLC_13_B_v1_0_0_APPROVED.md"
precondition: "DEVPL-GSDLC-13-A/PASS + latest DevPilot authority remote-synced"
full_policy: "0"
execution_mode: "OWNER-DRIVEN/DEVPL-EXECUTED/CHATGPT-ADJUDICATED"
journey_steps: "1-8"
---

# DEVPL-GSDLC-13-B — Bootstrap acceptance

## Objective

Demostrar creación desde cero mediante DevPilot, no mediante scripts externos.

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

### 13-B-01 — pasos 1–2
Launch/arranque permitido por operador → login → Home. Medir si Home explica project state, opciones y acción principal.

### 13-B-02 — pasos 3–7
Create Project → expresar idea de negocio → definir workspace/constraints/model policy → revisar plan/dry-run/efectos → approval → DevPilot crea workspace/Git/environment/config/context.

BLOCK si el Owner necesita crear carpeta/Git/files manualmente o recibir artifacts de ChatGPT externo.

### 13-B-03 — paso 8 + restart controlado
Project Status debe responder proyecto/etapa/completado/pendiente/blocker/causa/next action. Cerrar/reabrir DevPilot una vez y comprobar recuperación sin project write externo.

## PASS

B-01..B-03 PASS, greenfield realmente nuevo, operator writes=0, mandatory terminal escapes=0, UX-S0/S1=0.
