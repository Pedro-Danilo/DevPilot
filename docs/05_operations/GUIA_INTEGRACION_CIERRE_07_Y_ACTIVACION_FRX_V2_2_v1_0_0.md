---
doc_id: "DEVPL-GSDLC-07-CLOSURE-FRX-V2-2-INTEGRATION-GUIDE"
title: "Guía única — Integración administrativa del cierre 07 y activación FRX v2.2"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-08-31"
approval: "approved_by_owner"
---
# Guía única — Integración cierre 07 y activación FRX v2.2

## 1. Objetivo

Crear un successor governance-only desde repo386 que:
1. preserve repo386 inmutable;
2. registre adjudicación final 07-E y cierre backlog 07;
3. corrija el S2 documental post-cierre;
4. incorpore roadmap/backlog/prompts FRX v2.2/v2.3;
5. autorice exclusivamente FRX-v2.2-A como siguiente implementación.

No modifica runtime UI/API ni comportamiento agentic. No requiere browser ni full regression.

## 2. Fuente obligatoria

- repo: `repo_DevPilot_Local_386_DEVPL_GSDLC_07_E_AGENTIC_PRECODE_MODEL_EVALS_WINDOWS_VALIDATED_CANDIDATE.zip`
- SHA-256: `0998e901a1149d377c6793dc923e0c45ed7eec42395e7182ef495ce652e79d23`
- commit: `17db6b219f5066f2df91d897a0e3ad62314a0176`

## 3. Artefactos a integrar

### Root/governance
- `DEVPL_GSDLC_07_E_FINAL_OWNER_ADJUDICATION_v1_0_0.md`
- `DEVPL_GSDLC_07_BACKLOG_CLOSURE_ADJUDICATION_v1_0_0.md`

### Audits/governance
- `DEVPL_GSDLC_07_POST_CLOSURE_DOCUMENTATION_ERRATUM_v1_0_0.md`

### Planning
- `DEVPL_FULL_REGRESSION_V2_2_V2_3_EXECUTION_ROADMAP_v1_0_0.md`
- backlog v2.2 + cuatro prompts;
- backlog v2.3 + cuatro prompts.

## 4. Reconciliación documental requerida

En el successor, no en repo386 histórico:
- backlog 07 frontmatter → `status: closed`, `backlog_status: CLOSED/PASS`, fecha de cierre y referencias repo386/evidence;
- README superior → backlog 07 CLOSED/PASS; siguiente acción FRX-v2.2-A;
- Source Registry → backlog 07 requiere estado closed; registrar adjudicación final y backlog closure; proposal 07-E pasa a lifecycle histórico/superseded, sin reescribir su contenido;
- Project State → conservar `gsdlc_07_status=CLOSED/PASS`; declarar FRX-v2.2-A como next engineering action y GSDLC-08 `authorized/deferred-by-owner`;
- changelog → registrar cierre administrativo y activación v2.2.

## 5. Nuevo contrato obligatorio

Añadir test focal `ClosureStateConsistencyValidator` que genere BLOCK cuando P0/P1 current-active discrepe entre:
- Project State;
- backlog frontmatter;
- Source Registry;
- README current/next;
- changelog;
- adjudicación final.

Debe tener fixture negativo que reproduzca exactamente repo386: Project State closed + backlog frontmatter approved + README implementation.

## 6. Validación estrictamente necesaria

Ejecutar únicamente:
- test nuevo de ClosureStateConsistencyValidator;
- tests impactados de Documentation Governance/Source Registry/Project State;
- `project-state validate`;
- `docs-governance validate`;
- TCR v1/v2 si sus registries fueron modificados.

**No ejecutar full regression. No ejecutar browser.**

## 7. Windows

Mantener tres consolas únicamente cuando exista runtime browser; esta integración no levanta API/UI, por lo que se usa solo Consola 1.

Todo comando PowerShell que se incorpore al operador successor debe ser de una sola línea y terminar visualmente en PASS verde o BLOCK rojo. Preferir un operador Python idempotente y transaccional; Git objects son autoridad, no hashes físicos LF/CRLF.

## 8. PASS/BLOCK

### PASS
- repo386 verificado e inmutable;
- successor Git clean al inicio;
- drift P0/P1=0 al final;
- focal validators PASS;
- ningún runtime byte cambiado;
- full/browser runs=0;
- successor empaquetado con `git archive`, SHA/CRC y forbidden paths=0.

### BLOCK
- cualquier cambio funcional/runtime;
- reescritura de evidencia histórica;
- full/browser ejecutado;
- estados current-active contradictorios;
- intento de force push o manipulación manual de `.git`.

## 9. Commit sugerido

`chore(gsdlc-07): reconcile final closure and activate full-regression v2.2 planning`

## 10. Resultado esperado

El successor administrativo se convierte en fuente de ejecución de FRX-v2.2-A. Repo386 permanece la evidencia histórica Windows del cierre de GSDLC-07-E/07.
