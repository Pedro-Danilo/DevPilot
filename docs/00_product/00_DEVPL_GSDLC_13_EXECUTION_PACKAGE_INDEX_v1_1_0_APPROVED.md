---
doc_id: "DEVPL-GSDLC-13-EXECUTION-PACKAGE-INDEX"
title: "DEVPL-GSDLC-13 — Greenfield acceptance execution package index"
status: "approved"
version: "1.1.0"
owner: "Ordóñez"
updated: "2026-09-21"
approval: "approved_by_owner; aligned_to_greenfield_user_journey"
source_repo: "repo_DevPilot_Local_436_DEVPL_UX_P0_E_PRE_PILOT_PRODUCTIZATION_RC_WINDOWS_VALIDATED_CANDIDATE.zip"
source_git_commit: "423e99fa38df3114328b555aff8f859740a49a01"
source_repo_sha256: "d8e1b2ded46648dab7d463ab3d4f6973ba0122c8ad22bf6f6cf474791deb68cb"
git_remote_sync: "PASS"
git_remote_branch: "origin/official/devpilot-local"
milestone_tag: "devpilot-ux-p0-closed-repo436"
supersedes: "00_DEVPL_GSDLC_13_EXECUTION_PACKAGE_INDEX_v1_0_0_APPROVED.md"
---

# DEVPL-GSDLC-13 — Execution package index

## 1. Estado de entrada

UX-P0 está cerrado. Repo436 permanece baseline immutable. Git local y remoto están sincronizados en `423e99fa38df3114328b555aff8f859740a49a01` y el milestone tag `devpilot-ux-p0-closed-repo436` existe. GSDLC-13 está `READY-FOR-13-A`.

## 2. Cambio de metodología

### 13-A — Implementation mode

Se mantiene la metodología histórica:

`Owner aporta authorities → ChatGPT implementa/rebind → bundle Windows → Owner valida → evidencia → adjudicación/promoción`.

13-A **no crea contenido del proyecto greenfield**.

### 13-B..13-D — Acceptance mode

Se adopta formalmente:

`Owner-driven → DevPilot-executed → ChatGPT-adjudicated`.

El Owner opera DevPilot desde la UI. DevPilot crea/transforma el proyecto. ChatGPT prepara Run Cards, interpreta evidencia y adjudica checkpoints, pero no implementa externamente el proyecto bajo prueba.

### Corrective mode — solo ante defecto real de DevPilot

`BLOCK → congelar checkpoint → ChatGPT analiza → patch bounded de DevPilot → bundle Windows → Owner valida/promueve/sincroniza → selective retest → resume exact checkpoint`.

### 13-E — Independent audit mode

ChatGPT actúa como auditor/adjudicador independiente sobre evidencia consolidada. No completa tareas faltantes del proyecto para fabricar PASS.

## 3. Autoridades obligatorias

1. `01_DEVPL_GSDLC_13_OWNER_DEVPL_CHATGPT_OPERATING_MODEL_v1_0_0_APPROVED.md`.
2. `02_DEVPL_GSDLC_13_GREENFIELD_USER_JOURNEY_RUNBOOK_v1_0_0_APPROVED.md`.
3. `03_DEVPL_GSDLC_13_ACCEPTANCE_CHECKPOINT_PROTOCOL_v1_0_0_APPROVED.md`.
4. Charter v1.1.0.
5. Rebaseline v2.1.0.
6. Roadmap/backlog/sprints/prompts v1.1.0.
7. UX-P1 plan v1.1.0.

## 4. Orden operativo

1. Ejecutar/cerrar 13-A mediante implementación y bundle Windows.
2. Iniciar 13-B con Run Card `13-B-01`, no con un implementation bundle.
3. Avanzar checkpoint por checkpoint usando Run Packets incrementales.
4. Ante PASS: ChatGPT entrega adjudicación + siguiente Run Card, sin bundle.
5. Ante finding no bloqueante: registrar UX-P1 y continuar si el sprint lo permite.
6. Ante BLOCK de producto: activar Corrective Mode y retomar el checkpoint exacto tras validación.
7. Cerrar 13-B, luego 13-C, 13-D y finalmente 13-E.

## 5. Regla anti-oracle

El Owner puede pedir a ChatGPT explicación de una pantalla, concepto, riesgo o significado de una approval. ChatGPT no debe redactar el contenido normal del proyecto para pegarlo en DevPilot ni producir código del greenfield por fuera del workflow. Si DevPilot usa un modelo a través de su Model Gateway, esa ejecución sí pertenece al producto y debe quedar con provenance.
