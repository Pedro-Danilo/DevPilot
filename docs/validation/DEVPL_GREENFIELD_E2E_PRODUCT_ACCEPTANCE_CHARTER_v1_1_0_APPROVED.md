---
doc_id: "DEVPL-GREENFIELD-E2E-PRODUCT-ACCEPTANCE-CHARTER"
title: "DevPilot — Greenfield real-product end-to-end acceptance charter"
status: "approved"
version: "1.1.0"
owner: "Ordóñez"
updated: "2026-09-21"
approval: "approved_by_owner; aligned_to_user_journey_and_acceptance_operating_model"
supersedes: "03_DEVPL_GREENFIELD_E2E_PRODUCT_ACCEPTANCE_CHARTER_v1_0_0_APPROVED.md"
source_repo: "repo_DevPilot_Local_436_DEVPL_UX_P0_E_PRE_PILOT_PRODUCTIZATION_RC_WINDOWS_VALIDATED_CANDIDATE.zip"
source_git_commit: "423e99fa38df3114328b555aff8f859740a49a01"
source_repo_sha256: "d8e1b2ded46648dab7d463ab3d4f6973ba0122c8ad22bf6f6cf474791deb68cb"
pilot_type: "greenfield/full-product-acceptance"
execution_model: "owner-driven/devpilot-executed/chatgpt-adjudicated"
operator_project_writes_default: 0
local_first: true
---

# DevPilot — Greenfield E2E product acceptance charter

## 1. Hipótesis

Una persona puede iniciar DevPilot sin proyecto preexistente, describir una necesidad real, completar el Guided SDLC, implementar stories, ejecutar quality loops, producir commits gobernados y alcanzar un local release reproducible usando DevPilot como control plane.

## 2. Separación greenfield/legacy

`inventory-sales-local` histórico se preserva para futura Legacy Adoption Acceptance. El piloto actual usa `inventory-sales-local-greenfield` y no copia artifacts, DBs, code, Git history, configuration ni evidence histórica.

## 3. Operating model vinculante

13-B..13-D se ejecutan como `Owner-driven / DevPilot-executed / ChatGPT-adjudicated` según `01_DEVPL_GSDLC_13_OWNER_DEVPL_CHATGPT_OPERATING_MODEL_v1_0_0_APPROVED.md`.

- Owner opera la UI y toma decisiones humanas legítimas.
- DevPilot produce el trabajo normal del proyecto.
- ChatGPT prepara Run Cards y adjudica Run Packets.
- Un PASS normal no genera bundle.
- Solo un defecto de DevPilot activa Corrective Mode.

## 4. Journey vinculante

El journey completo es el de `02_DEVPL_GSDLC_13_GREENFIELD_USER_JOURNEY_RUNBOOK_v1_0_0_APPROVED.md`, pasos 1–39.

Macro-flow:

`IDEA → Create Project → Vision → Scope → Requirements → Architecture/Security/Tests/ADRs → Roadmap → Backlog → Sprint → Stories → Context/Plan/Diff/Dry-run/Approval/Apply → Tests/Quality/Remediation → Git Commit → Release Readiness → Package/Checksum/SBOM → Clean Install → Rollback → LOCAL RELEASE → Independent Adjudication`.

## 5. Modelo de IA

1. mock/no API baseline;
2. local model opcional cuando aporte valor;
3. external API solo si está aprobada y con provenance.

External API no es requisito de PASS. ChatGPT externo a DevPilot no actúa como autor del proyecto durante baseline acceptance.

## 6. Regla del operador

Permitido: instalar/iniciar/detener/auditar/capturar/adjudicar.

Prohibido: crear/editar contenido normal del proyecto para ayudar a pasar.

Objetivo: `operator_project_writes=0`; mandatory normal-user terminal escapes=0.

## 7. Evidence/checkpoints

Se usa `03_DEVPL_GSDLC_13_ACCEPTANCE_CHECKPOINT_PROTOCOL_v1_0_0_APPROVED.md`. Authority Pack estable + Run Packets incrementales. No se repite una corrida completa para esconder un FAIL.

## 8. PASS

- greenfield creado desde cero;
- normal journey alcanza local release;
- project content no preinyectado;
- operator project writes=0;
- mandatory terminal escapes=0;
- approvals/provenance reproducibles;
- recovery scenarios probados;
- S0=0/S1=0;
- clean install y rollback probados;
- no hidden model fallback.

## 9. BLOCK

- bootstrap externo requerido;
- raw terminal/editor externo necesario para tarea normal;
- ChatGPT externo suministra artifacts/code que se copian para superar el checkpoint;
- DevPilot no explica/recupera su estado;
- authority/approval/provenance bypass;
- artifacts históricos usados como oracle greenfield;
- release solo posible mediante bypass externo.

## 10. Legacy posterior

Solo después de Greenfield PASS se autoriza Legacy Adoption Acceptance sobre `inventory-sales-local`; ambos resultados se adjudican por separado.
