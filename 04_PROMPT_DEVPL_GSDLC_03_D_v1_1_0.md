---
doc_id: "DEVPL-PROMPT-GSDLC-03-D"
prompt_number: "04"
title: "Prompt operativo — DEVPL-GSDLC-03-D — Approval-bound bootstrap execution"
status: "ready_for_execution"
version: "1.1.0"
owner: "Ordóñez"
updated: "2026-08-17"
approval: "owner_approved_backlog_scope"
program_id: "DEVPL-GSDLC"
backlog_id: "DEVPL-GSDLC-03"
micro_sprint: "DEVPL-GSDLC-03-D"
execution_rule: "solo 03-D; requiere 03-C CLOSED/PASS"
source_authority_mode: "repo362-gsdlc03c-closed-pass"
local_first: true
dry_run_default: true
pilot_workspace_access_allowed: false
---

# Prompt operativo — DEVPL-GSDLC-03-D

## Rebind v1.1.0 — autoridad inmediata

```text
repo = repo_DevPilot_Local_362_DEVPL_GSDLC_03_C_DRY_RUN_CREATE_OPEN_IMPORT_WINDOWS_VALIDATED_CANDIDATE.zip
commit = ecbc9b38b3722f9fc360bdc0b6c7349371c14625
SHA-256 = cc7991196ff8553550604a146c8dc957f0f60311ab432aad04812063a88d1806
predecessor = DEVPL-GSDLC-03-C CLOSED/PASS
predecessor adjudication = DEVPL_GSDLC_03_C_FINAL_OWNER_ADJUDICATION_v1_0_0.md
```

El repo359 de GSDLC-02 permanece como autoridad histórica de la ola de auth/session, pero **no** es el baseline inmediato sobre el cual se muta 03-D. Toda implementación 03-D se proyecta sobre repo362.


## 1. Mandato

Implementa **solo** `GSDLC-03-D — Approval-bound bootstrap execution` sobre 03-C CLOSED/PASS. Rebind obligatorio al successor C.

## Fuentes obligatorias de autoridad

Antes de proyectar cambios, consultar literalmente como mínimo:

- `repo_DevPilot_Local_362_DEVPL_GSDLC_03_C_DRY_RUN_CREATE_OPEN_IMPORT_WINDOWS_VALIDATED_CANDIDATE.zip` como baseline técnico inmediato y autoridad source de ejecución (`commit=ecbc9b38b3722f9fc360bdc0b6c7349371c14625`, `SHA-256=cc7991196ff8553550604a146c8dc957f0f60311ab432aad04812063a88d1806`);
- `DEVPL_GSDLC_03_C_FINAL_OWNER_ADJUDICATION_v1_0_0.md` como autoridad inmediata de predecessor `CLOSED/PASS`;
- `DEVPL_GSDLC_02_E_FINAL_OWNER_ADJUDICATION_v1_0_0.md` como autoridad histórica de auth/session;
- `DEVPL_GSDLC_02_BACKLOG_CLOSURE_ADJUDICATION_v1_0_0.md`;
- `DEVPL-GSDLC-03_project_entry_creation_open_and_git_import_workbench_v1_2_0_APPROVED.md`;
- `.devpilot/gsdlc/transversal_validation_policy.json`;
- `.devpilot/project_state.json`;
- `.devpilot/docs_governance/source_registry.json`;
- `.devpilot/testing/test_contract_registry.json`;
- `.devpilot/testing/test_contract_registry_v2.json`;
- `docs/schemas/schema_catalog.json`;
- `docs/00_product/DEVPL_GSDLC_product_evolution_roadmap.md`;
- `docs/05_operations/DevPilot_POST_H_EVAL_002_Piloto_Real_End_to_End_UI_First_Runbook.md`;
- `docs/backlogs/POST-H-EVAL-002-02_sdlc_execution_traceability.md`;
- workspace/bootstrap/Git/job/ApplicationService/API/UI/security artifacts impactados.

Si una fuente obligatoria no está disponible, **BLOCK antes de implementar**. No completar documentación por suposición.


## 2. Execution contract

Solo un plan previamente revisado/aprobado puede ejecutar. Antes de cada side effect:
- revalidar plan hash/preimage;
- human-session vigente;
- RBAC;
- workspace/path scope;
- approval;
- policy/network state.

## 3. BootstrapExecutor

Implementar por stages transaccionales:
1. target root;
2. structure/templates;
3. Git init/import local;
4. `.venv`;
5. dependency typed jobs;
6. DevPilot metadata/standards;
7. workspace register;
8. verify;
9. success manifest.

Cada stage registra before/after, result y rollback action.

## 4. Dependency/network

- acceptance primaria offline/cache/local fixture;
- no package extra fuera del plan;
- cualquier red real = explicit plan + policy + approval + evidence;
- remote clone real no es requisito del backlog; local Git import sí;
- no credential material en logs.

## 5. Fault injection y rollback

Probar fallos controlados por stages representativos:
- file creation;
- Git;
- venv;
- dependency job;
- registration.

Rollback debe dejar cero residue fuera del target autorizado y un estado explicable dentro del target.

## 6. Workspace fixtures

Mutaciones únicamente bajo fixture identificado en `D:\Projects\DevPilot_E2E_Evaluation\worktrees\DEVPL-GSDLC-03-*`.

No leer/escribir `inventory-sales-local`.

## 7. Tests

- idempotency;
- approval/RBAC negative;
- stale plan;
- fault injection;
- rollback;
- workspace isolation;
- Git clean;
- typed dependency job contract;
- writes-outside-workspace=0;
- A→D cumulative;
- governance/TCR/Test Impact;
- Node/build focal si UI/API cambian.

## Política transversal de validación

Autoridad: `.devpilot/gsdlc/transversal_validation_policy.json`.

- A→D: `validation_mode=cumulative-selective`.
- Test Impact siempre se ejecuta en analyze/dry-run y sus P0/P1 son inputs de selección.
- `full_regression_required=true` en A→D es señal de escalamiento, **no orden automática**.
- Full intermedia solo con hard trigger sistémico y owner approval previo.
- 03-E ejecuta la **única full regression del backlog exactamente una vez**, después de browser acceptance.
- Si la full de E falla: preservar log/marker, no repetir, corregir raíces, exact failed-nodeid retest + bounded impacted retest + Historical Regression Guard.
- Nunca modificar snapshots históricos únicamente para hacer pasar pytest.


Para 03-D: **full regression = NO** salvo hard trigger owner-approved previo.

## Seguridad y límites

- local-first;
- deny-by-default;
- human-session/RBAC de GSDLC-02 permanece autoridad;
- no arbitrary shell;
- no texto del usuario interpolado como comando;
- PathGuard/canonical path/symlink checks;
- no network silenciosa;
- external APIs no requeridas;
- remote Git clone disabled-by-default salvo plan + policy + approval;
- secrets/credentials nunca en source/logs/screenshots;
- no pilot workspace access;
- toda mutación: `plan → dry-run → policy/RBAC → approval → execute → verify → evidence`.


## 8. PASS/BLOCK

PASS-CANDIDATE:
- workspace fixture usable;
- Git clean;
- venv/deps conforme plan;
- registration PASS;
- rollback PASS;
- external writes=0;
- S0/S1=0.

BLOCK:
- unexplained partial writes;
- command deviates plan;
- approval bypass;
- rollback residue;
- network no autorizada.

## 9. Git

Feature: `feat/devpl-gsdlc-03-d-bootstrap-execution`

Commit: `feat(gsdlc-03-d): execute approved project bootstrap plans`

## Contrato obligatorio del operador/harness

El operador entregado debe:

1. ser Python state-aware e idempotente;
2. usar dry-run por defecto;
3. no ejecutar `reset --hard`, `git clean`, rebase automático ni force push;
4. usar subprocess nativo con `argv`, `shell=False`, paths resueltos y timeouts;
5. evitar `cmd.exe`/quoting accidental cuando exista ejecutable nativo;
6. usar `git status --porcelain=v1 -z` para parsing de Git;
7. distinguir gross touched surface de net diff final;
8. validar baseline tracked Git-clean mediante Git blob cuando LF/CRLF material pueda diferir;
9. escribir checkpoints/reportes incrementalmente, incluso si un check posterior falla;
10. mostrar BLOCK/ERROR claramente y conservar evidencia causal;
11. reanudar desde estado válido sin reaplicar trabajo ya correcto;
12. no acceder ni mutar `D:\Projects\DevPilot_Workspaces\inventory-sales-local`;
13. usar fixtures de aceptación únicamente bajo `D:\Projects\DevPilot_E2E_Evaluation`;
14. excluir de ZIP final `.git`, `.venv`, `node_modules`, `outputs`, caches, runtime DBs y secretos.


## Topología y entregables Windows

Usar únicamente:

```text
D:\Projects\DevPilot_E2E_Evaluation
D:\Projects\DevPilot_Artifacts\POST-H-EVAL-002
D:\Projects\DevPilot_Local
```

El piloto real `D:\Projects\DevPilot_Workspaces\inventory-sales-local` no es input ni fixture de esta ola.

Entregar:
1. package ZIP con operador Python, payload, authority inputs y manifest;
2. delta candidate exacto;
3. repo PRE-WINDOWS limpio, no canónico;
4. guía única `.md` para personal no experto;
5. sidecars SHA-256;
6. SOURCE_DELTA_MANIFEST;
7. ARTIFACT_HASHES;
8. OPERATION_DECLARATION;
9. CURRENT;
10. closure report;
11. historical_contract_sweep;
12. definición exacta de evidence Windows;
13. feature branch/commit;
14. recuperación focal/reanudable ante BLOCK.

La guía usa comandos PowerShell en una sola línea física por bloque, puede agrupar operaciones afines y debe autoauditar rutas/comandos.
