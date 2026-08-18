---
doc_id: "DEVPL-PROMPT-GSDLC-03-B"
prompt_number: "02"
title: "Prompt operativo — DEVPL-GSDLC-03-B — Environment discovery and bootstrap planning"
status: "ready_for_execution"
version: "1.1.0"
owner: "Ordóñez"
updated: "2026-08-17"
approval: "owner_approved_backlog_scope"
program_id: "DEVPL-GSDLC"
backlog_id: "DEVPL-GSDLC-03"
micro_sprint: "DEVPL-GSDLC-03-B"
execution_rule: "solo 03-B; requiere 03-A CLOSED/PASS"
source_authority_mode: "fixed-rebound-to-03-a-closure"
source_repo: "repo_DevPilot_Local_360_DEVPL_GSDLC_03_A_PROJECT_INTAKE_CONTRACTS_WINDOWS_VALIDATED_CANDIDATE.zip"
source_git_commit: "2ebed62c243ea4034a5381023fb118de33c4aecd"
source_repo_sha256: "81212d518b21be447f136acf0357ef32a6f5e48c1975056dad7225d87a4b2d0b"
predecessor_adjudication: "DEVPL_GSDLC_03_A_FINAL_OWNER_ADJUDICATION_v1_0_0.md"
local_first: true
dry_run_default: true
pilot_workspace_access_allowed: false
---

# Prompt operativo — DEVPL-GSDLC-03-B

## 1. Mandato

Implementa **solo** `GSDLC-03-B — Environment discovery and bootstrap planning` sobre el successor adjudicado de 03-A: `repo_DevPilot_Local_360_DEVPL_GSDLC_03_A_PROJECT_INTAKE_CONTRACTS_WINDOWS_VALIDATED_CANDIDATE.zip`, commit `2ebed62c243ea4034a5381023fb118de33c4aecd`, SHA-256 `81212d518b21be447f136acf0357ef32a6f5e48c1975056dad7225d87a4b2d0b`. Si esta autoridad o `DEVPL_GSDLC_03_A_FINAL_OWNER_ADJUDICATION_v1_0_0.md` no puede verificarse, BLOCK antes de mutar.

## Fuentes obligatorias de autoridad

Antes de proyectar cambios, consultar literalmente como mínimo:

- `repo_DevPilot_Local_360_DEVPL_GSDLC_03_A_PROJECT_INTAKE_CONTRACTS_WINDOWS_VALIDATED_CANDIDATE.zip` como baseline técnico vigente y directo de 03-B;
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


Autoridad inmediata obligatoria: `DEVPL_GSDLC_03_A_FINAL_OWNER_ADJUDICATION_v1_0_0.md` y `repo_DevPilot_Local_360_DEVPL_GSDLC_03_A_PROJECT_INTAKE_CONTRACTS_WINDOWS_VALIDATED_CANDIDATE.zip` / `2ebed62c243ea4034a5381023fb118de33c4aecd` / `81212d518b21be447f136acf0357ef32a6f5e48c1975056dad7225d87a4b2d0b`.

## 2. Discovery read-only

Implementar discovery tipado de:
- Python;
- Node;
- npm capability/version sin depender de shell textual;
- Git;
- venv;
- espacio libre;
- permisos;
- path collisions;
- estado Git para OPEN/IMPORT cuando corresponda.

Discovery debe producir `writes=0`, bounded timeouts y **no volcar environment completo**.

## 3. BootstrapPlan

El plan debe enumerar exactamente:
- directorios;
- archivos;
- Git operations;
- venv;
- dependency jobs;
- workspace registration;
- network need;
- approval need;
- expected side effects;
- rollback steps;
- stable plan hash.

Missing tool no instala nada: devuelve BLOCK/alternatives.

## 4. UI projection

Exponer desde ApplicationService/API una proyección read-only del discovery/plan suficiente para el wizard posterior, sin habilitar execute.

## 5. Tests

- Windows path/version fixtures;
- executable missing/ambiguous;
- timeout;
- no-write assertion;
- no secret env dump;
- plan deterministic/stable hash;
- network metadata;
- A+B cumulative;
- Project State/Docs Governance/TCR;
- Test Impact.

## Política transversal de validación

Autoridad: `.devpilot/gsdlc/transversal_validation_policy.json`.

- A→D: `validation_mode=cumulative-selective`.
- Test Impact siempre se ejecuta en analyze/dry-run y sus P0/P1 son inputs de selección.
- `full_regression_required=true` en A→D es señal de escalamiento, **no orden automática**.
- Full intermedia solo con hard trigger sistémico y owner approval previo.
- 03-E ejecuta la **única full regression del backlog exactamente una vez**, después de browser acceptance.
- Si la full de E falla: preservar log/marker, no repetir, corregir raíces, exact failed-nodeid retest + bounded impacted retest + Historical Regression Guard.
- Nunca modificar snapshots históricos únicamente para hacer pasar pytest.


Para 03-B: **full regression = NO** salvo hard trigger owner-approved previo.

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


## 6. PASS/BLOCK

PASS-CANDIDATE:
- discovery writes=0;
- plan exacto/stable;
- cada side effect declarado;
- no pilot access;
- S0/S1=0.

BLOCK:
- discovery modifica disco;
- executable ambiguo;
- command no tipado;
- secreto/environment leak.

## 7. Git

Feature: `feat/devpl-gsdlc-03-b-bootstrap-planning`

Commit: `feat(gsdlc-03-b): add environment discovery and bootstrap plans`

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

