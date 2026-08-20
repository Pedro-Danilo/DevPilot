---
doc_id: "DEVPL-PROMPT-GSDLC-03-E"
prompt_number: "05"
title: "Prompt operativo — DEVPL-GSDLC-03-E — Post-login Home and browser acceptance"
status: "ready_for_execution"
version: "1.1.0"
owner: "Ordóñez"
updated: "2026-08-18"
approval: "owner_approved_backlog_scope"
program_id: "DEVPL-GSDLC"
backlog_id: "DEVPL-GSDLC-03"
micro_sprint: "DEVPL-GSDLC-03-E"
execution_rule: "cierre de backlog; GSDLC-04 bloqueado hasta owner adjudication CLOSED/PASS"
source_authority_mode: "dynamic-predecessor-rebind"
local_first: true
dry_run_default: true
pilot_workspace_access_allowed: false
source_repo: "repo_DevPilot_Local_363_DEVPL_GSDLC_03_D_APPROVAL_BOUND_BOOTSTRAP_EXECUTION_WINDOWS_VALIDATED_CANDIDATE.zip"
source_git_commit: "7eb5f6512da8644ff08651cec0bd464795cfda8e"
source_repo_sha256: "a660005465fa8ee566d0b9d1cdaa8bd978457cbbc59ca9ebb83891f8b1f53b4b"
predecessor_micro_sprint: "DEVPL-GSDLC-03-D"
predecessor_status: "CLOSED/PASS"
predecessor_closure_authority: "DEVPL_GSDLC_03_D_FINAL_OWNER_ADJUDICATION_v1_0_0.md"

---

# Prompt operativo — DEVPL-GSDLC-03-E

## 0. Rebind autoritativo v1.1.0

La autoridad mutable inmediata para implementar 03-E es el cierre Windows adjudicado de 03-D:

```text
repo
repo_DevPilot_Local_363_DEVPL_GSDLC_03_D_APPROVAL_BOUND_BOOTSTRAP_EXECUTION_WINDOWS_VALIDATED_CANDIDATE.zip

commit
7eb5f6512da8644ff08651cec0bd464795cfda8e

SHA-256
a660005465fa8ee566d0b9d1cdaa8bd978457cbbc59ca9ebb83891f8b1f53b4b

predecessor
DEVPL-GSDLC-03-D CLOSED/PASS
```

`repo359` y las autoridades GSDLC-02 permanecen como baseline histórico de la ola y deben consultarse literalmente, pero **no son el baseline mutable de implementación de 03-E**.

Antes de mutar source, la rama canónica debe poder promoverse `ff-only` al commit de repo363. No repetir pruebas de 03-D por esa promoción administrativa.

## 1. Mandato

Implementa **solo** `GSDLC-03-E — Post-login Home, entry options and browser acceptance` sobre 03-D `CLOSED/PASS`, usando repo363/commit `7eb5f651…` como baseline mutable inmediato, y ejecuta el cierre industrial A→E. El rebind al successor D es obligatorio.

## Fuentes obligatorias de autoridad

Antes de proyectar cambios, consultar literalmente como mínimo:

- `repo_DevPilot_Local_359_DEVPL_GSDLC_02_E_COMPOSITE_WINDOWS_VALIDATED_CANDIDATE.zip` como baseline técnico de la ola;
- `DEVPL_GSDLC_02_E_FINAL_OWNER_ADJUDICATION_v1_0_0.md`;
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


## 2. UX requerida

Después de login debe existir Home clara con:

```text
[ Crear nuevo proyecto ]
[ Abrir proyecto existente ]
[ Importar repositorio Git ]
```

Requisitos:
- progressive disclosure;
- defaults explicados;
- disabled reasons;
- plan summary;
- approval state;
- progress/retry/recovery;
- éxito → Project Status;
- rol/identidad persistente;
- no shell/CLI visible como requisito del normal journey.

## 3. Browser acceptance real

Usar fixtures controlados, nunca el piloto.

Escenarios mínimos:
1. Home post-login con tres opciones;
2. Create wizard intake;
3. Create dry-run plan;
4. Create approval;
5. Create execute + progress;
6. Create success → Project Status;
7. Open existing fixture dry-run/open;
8. Import local Git fixture dry-run/import;
9. unauthorized role denied;
10. stale plan/reapproval;
11. rollback/recovery observable;
12. path outside policy blocked;
13. API-down/recovery;
14. accessibility keyboard/focus/labels.

Capturas sanitizadas y machine evidence deben correlacionar UI/API/job/plan hash/approval.

**Normal journey acceptance:** el usuario realiza Create/Open/Import desde navegador. PowerShell/operator se usa solo para levantar harness, fixtures y recolectar/verificar evidencia; no escribe el proyecto en nombre del usuario.

## 4. Métricas obligatorias

- `normal_user_powershell_required = 0`;
- `external_operator_project_writes = 0`;
- create/open/import UI eligible coverage = 100%;
- S0=0;
- S1=0.

## 5. Tests previos a full

Orden:
1. schemas/domain/unit;
2. path/security negatives;
3. A→E cumulative;
4. ApplicationService/API;
5. Node/frontend;
6. Vite build;
7. Project State/Docs Governance/TCR;
8. Test Impact;
9. historical sweep;
10. browser acceptance real;
11. **full regression exactamente una vez**.

## Política transversal de validación

Autoridad: `.devpilot/gsdlc/transversal_validation_policy.json`.

- A→D: `validation_mode=cumulative-selective`.
- Test Impact siempre se ejecuta en analyze/dry-run y sus P0/P1 son inputs de selección.
- `full_regression_required=true` en A→D es señal de escalamiento, **no orden automática**.
- Full intermedia solo con hard trigger sistémico y owner approval previo.
- 03-E ejecuta la **única full regression del backlog exactamente una vez**, después de browser acceptance.
- Si la full de E falla: preservar log/marker, no repetir, corregir raíces, exact failed-nodeid retest + bounded impacted retest + Historical Regression Guard.
- Nunca modificar snapshots históricos únicamente para hacer pasar pytest.


## 6. Full regression

Crear marker durable antes de la ejecución.

Si PASS:
- continuar closure.

Si FAIL:
- preservar marker/log;
- no repetir full;
- clasificar residuals;
- corrective mínimo;
- exact failed-nodeid retest;
- bounded impacted retest;
- Historical Regression Guard;
- `validation_mode=composite-full-regression-selective-retest`.

Una segunda full regression es BLOCK.

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


## 7. PASS/BLOCK

CLOSED/PASS candidate:
- tres entry options visibles;
- Create E2E UI PASS;
- Open E2E UI PASS;
- Import local Git E2E UI PASS;
- approval/RBAC/path boundaries PASS;
- rollback/recovery PASS;
- normal user PowerShell=0;
- operator project writes=0;
- full/composite evidence válida;
- S0/S1=0.

BLOCK:
- usuario necesita ejecutar operador externo para crear/abrir/importar;
- UI bypass approval;
- arbitrary shell;
- write fuera de fixture/workspace;
- remote/network silenciosa;
- route/API mismatch;
- segunda full.

## 8. Cierre

Tras owner adjudication:
- generar successor repo limpio;
- backlog GSDLC-03 CLOSED/PASS;
- autorizar GSDLC-04.

Feature: `feat/devpl-gsdlc-03-e-project-entry-browser-closure`

Commit: `feat(gsdlc-03-e): close project entry wizard journey`

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
