---
doc_id: "DEVPL-GSDLC-13-D-04-RUN-CARD"
title: "13-D-04 — Governed Git CommitPlan, exact stage, two Owner approvals and Story DONE"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-10-04"
approval: "projected-for-owner-windows-validation"
authority: "SPRINT_DEVPL_GSDLC_13_D_v1_2_0_APPROVED + runbook-v1.1.0 + acceptance-protocol-v1.1.0"
execution_mode: "OWNER-DRIVEN/DEVPL-EXECUTED/CHATGPT-ADJUDICATED"
full_regression_runs_allowed: 0
---

# RUN CARD 13-D-04 v1.0.0

## Objetivo

Aceptar sobre el Pilot A real la capability Git gobernada ya existente, con el corrective first-greenfield de baseline, empezando exactamente desde el cierre D03:

`story-rf-001 = COMMIT_READY`.

Secuencia obligatoria:

`COMMIT_READY → CommitPlan → stage approval → exact-path stage → staged recheck → commit approval → governed commit → GitCommitRecord → Story DONE → Project Status`.

STOP después de Project Status. No iniciar 13-D-05.

## Precondiciones

- DevPilot oficial contiene el corrective D04 validado y Git 3-state limpio.
- Pilot A sigue en `inventory-sales-local-greenfield`.
- `story-rf-001` es la Story actual y está `COMMIT_READY`.
- D03 Quality report exacto sigue PASS / `commit_ready=true`.
- Full Regression acumulada durante D04 = `0`.
- No hay staged paths preexistentes en el proyecto.
- No se corrige el project workspace desde terminal.

## Particularidad del primer commit greenfield

El Project Context/Pre-code/Planning/Story runtime se construyó antes del primer checkpoint Git. Por tanto el CommitPlan D04 puede contener dos grupos source:

### Story paths

Exactamente los cuatro paths del SourceChangePlan de `story-rf-001`:

- `src/inventory_sales_local_greenfield/application/create_product.py`;
- `src/inventory_sales_local_greenfield/domain/product.py`;
- `src/inventory_sales_local_greenfield/infrastructure/sqlite_product_repository.py`;
- `tests/test_create_product.py`.

### Baseline greenfield verificado

Únicamente documentos Pre-code/ADRs todavía untracked cuya autoridad FROZEN/approval/hash sea comprobada server-side. Para Pilot A se espera el baseline técnico/documental vigente bajo:

- `docs/00_product/**`;
- `docs/01_requirements/**`;
- `docs/02_architecture/architecture_document.md`;
- `docs/02_architecture/adrs/**` aprobados;
- `docs/03_security/security_threat_model.md`;
- `docs/04_quality/test_strategy.md`.

`outputs/**` **no** es source Git, no debe aparecer en `CommitPlan.exact_paths`, stage ni commit. Debe permanecer en disco como runtime/evidence.

Cualquier otro source path inesperado = BLOCK.

## Pasos UI Owner

1. Arrancar API/UI mediante el launcher normal indicado por la guía Windows del bundle y autenticar sesión Owner.
2. Abrir Story Code Workbench y comprobar `story-rf-001 · COMMIT_READY`.
3. Abrir la sección Git gobernado y pulsar `Recuperar contexto COMMIT_READY`.
4. Verificar Quality PASS, StoryTestPlan y SourceChangePlan actuales; capturar `01_d04_commit_ready_context.png`.
5. Revisar mensaje/autor/email de commit. No introducir argumentos Git ni comandos.
6. Pulsar `Construir CommitPlan exacto`.
7. Revisar el CommitPlan completo:
   - Story paths = cuatro;
   - baseline greenfield solo authority-verified;
   - runtime outputs excluidos;
   - HEAD/branch correctos;
   - `stage_and_commit_separate=true`;
   - push/force/rebase/reset-hard/full=false.
8. Capturar `02_d04_commit_plan.png`. Si aparece cualquier path no explicado, STOP/BLOCK.
9. Pulsar `Solicitar approval de stage`.
10. Aprobar como Owner. Capturar `03_d04_stage_approval.png` con approval ID y estado APPROVED.
11. Pulsar `Ejecutar stage exacto`.
12. Verificar `STAGE PASS`, mismo exact path set, index fingerprint, `git add .=false`, `shell=false`. Capturar `04_d04_stage_pass.png`.
13. Pulsar `Solicitar approval de commit`. Debe crearse **otro approval ID**.
14. Aprobar como Owner. Capturar `05_d04_commit_approval.png`; debe ser distinto al stage approval ID.
15. Pulsar `Crear commit gobernado`.
16. Verificar `COMMIT PASS · TRACEABILITY COMPLETE`, commit SHA, parent, committed paths, evidence IDs y `push/force/rebase/reset-hard=false`. Capturar `06_d04_commit_pass.png`.
17. Volver/revisar Story Code. Debe mostrar `story-rf-001 · DONE`; capturar `07_d04_story_done.png`.
18. Abrir Project Status. Debe proyectar la siguiente acción válida sin iniciar D05; capturar `08_d04_project_status_next.png`.
19. STOP. No ejecutar siguiente Story, D05 ni Full Regression.

## Evidencia requerida

El RUN_01 de D04 debe preservar como mínimo:

- pre-audit/read-only receipt de estado inicial;
- screenshots 01..08 anteriores;
- CommitPlan JSON ID/hash/path set;
- stage approval record;
- stage execution/staging manifest/index fingerprint;
- staged recheck evidence;
- commit approval record separado;
- GitCommitRecord y traceability JSON;
- StoryExecution final `DONE`;
- Project Status final;
- HEAD before/after + parent + committed paths mediante lectura Git;
- `push_performed=false`;
- `operator_project_writes=0`;
- `normal_user_terminal_escapes=0`;
- `full_regression_runs=0`;
- observaciones Owner/UX.

## PASS

PASS si todo lo siguiente es verdadero:

- Quality binding exacto y actual;
- CommitPlan immutable y path set explicable;
- no `outputs/**` en el commit;
- stage approval y commit approval APPROVED y con IDs distintos;
- exact stage PASS + staged recheck PASS;
- commit parent/files coinciden exactamente con CommitPlan;
- GitCommitRecord/trace completos;
- Story `DONE`;
- Project Status tiene next action válida;
- no push/force/rebase/reset-hard/shell;
- Full Regression `0`;
- S0/S1 nuevos `0`.

## BLOCK

BLOCK ante cualquiera de estos casos:

- Story ya no `COMMIT_READY` al entrar;
- Quality/TestPlan/SourcePlan stale o no enlazados;
- dirty source desconocido;
- baseline Pre-code no FROZEN o hash drift;
- ADR receipt/approval no válido;
- baseline adicional ya trackeado y modificado;
- staged paths previos;
- mismo approval usado para stage y commit;
- staged content drift;
- commit parent/files no exactos;
- `outputs/**` stageado/committeado;
- terminal/operator muta project Git;
- push, force-push, automatic rebase, reset-hard o shell;
- Full Regression > 0.

## Riesgos

- `outputs/**` puede seguir apareciendo físicamente en el Pilot A histórico aunque Story Git lo clasifique runtime-only; no borrarlo.
- El primer commit será más amplio que los cuatro Story paths porque incorpora el baseline project-source ya aprobado antes de que existiera el primer Git checkpoint. Esto es una excepción gobernada first-greenfield, no precedente para absorber dirty paths arbitrarios.
- La capability sigue siendo local-first y preliminary para el piloto; no implementa remote push/release promotion.

## Verificación focal de source DevPilot

```text
python -m pytest -q -p no:cacheprovider tests/test_devpl_gsdlc_10_d_story_git_commit.py tests/test_workspace_git_operations_service.py tests/test_api_workspace_git_operations.py tests/test_devpl_gsdlc_10_e_story_cycle_lifecycle.py
python -m devpilot_core docs-governance validate --json
```

Full Regression: prohibida en este checkpoint.
