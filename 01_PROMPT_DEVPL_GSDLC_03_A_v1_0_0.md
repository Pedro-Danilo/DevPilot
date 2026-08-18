---
doc_id: "DEVPL-PROMPT-GSDLC-03-A"
prompt_number: "01"
title: "Prompt operativo — DEVPL-GSDLC-03-A — Project Intake and technology catalog contracts"
status: "ready_for_execution"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-08-17"
approval: "owner_approved_backlog_scope"
program_id: "DEVPL-GSDLC"
backlog_id: "DEVPL-GSDLC-03"
micro_sprint: "DEVPL-GSDLC-03-A"
execution_rule: "solo 03-A; 03-B bloqueado hasta owner adjudication CLOSED/PASS"
source_authority_mode: "fixed-rebound-baseline"
source_repo: "repo_DevPilot_Local_359_DEVPL_GSDLC_02_E_COMPOSITE_WINDOWS_VALIDATED_CANDIDATE.zip"
source_git_commit: "98e4b2f3f033580bfdd5fc027bf5afcd632f8169"
source_repo_sha256: "bb155968cd10c35a320cdcee3af1f9db4cb64ebed4acbca773f24918c3d58995"
canonical_branch: "eval/post-h-eval-002-02-a-onboarding"
local_first: true
dry_run_default: true
pilot_workspace_access_allowed: false
---

# Prompt operativo — DEVPL-GSDLC-03-A

## 1. Mandato

Implementa **solo** `GSDLC-03-A — Project Intake and technology catalog contracts`.

Precondición administrativa: la rama canónica debe estar `ff-only` en `98e4b2f3f033580bfdd5fc027bf5afcd632f8169` antes de crear la feature branch. No ejecutar otra full regression para esa promoción.

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


## 2. Resultado funcional

Crear contratos determinísticos para describir completamente un proyecto antes de cualquier write:

- ProjectIntake;
- TechnologyCatalog;
- ProjectCreationPlan;
- entry mode `CREATE_NEW | OPEN_EXISTING | IMPORT_GIT`;
- supported stack fixture React+TS/FastAPI/SQLite;
- allowed-root/path/collision rules;
- network/cost/approval metadata.

El caso conceptual `inventory-sales-local` debe ser expresable por fixture **sin leer ni escribir el repo piloto real**.

## 3. Requisitos técnicos

- schemas versionados y catalogados;
- typed enums, no command strings;
- stack unknown/ambiguous = BLOCK;
- root overlap con DevPilot = BLOCK;
- traversal/symlink escape = BLOCK;
- no credentials en intake;
- plan fields preparados para `writes/network/approval/rollback`;
- ApplicationService boundary respetada.

## 4. Historical contracts

Ejecutar sweep y clasificar cualquier contrato de POST-H-024, 02-A, UOC, GSDLC-01/02 y filesystem-write legacy. Crear successor cuando el nuevo Project Bootstrap amplíe alcance; no reescribir freeze.

## 5. Tests mínimos

- schema positive/negative;
- unsafe path/traversal/symlink;
- unsupported/ambiguous stack;
- repo overlap;
- no-command-string assertion;
- fixture serialization/hash stability;
- Source Registry/schema catalog/TCR/Project State/Docs Governance;
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


Para 03-A: **full regression = NO** salvo hard trigger owner-approved previo.

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
- schemas/catalog válidos;
- fixture de referencia completo;
- unknown/ambiguous = BLOCK;
- no writes;
- no pilot access;
- S0/S1=0.

BLOCK:
- free-form shell;
- allowed-root bypass;
- secret field material;
- historical snapshot retroactivamente cambiado.

## 7. Git

Feature: `feat/devpl-gsdlc-03-a-project-intake-contracts`

Commit: `feat(gsdlc-03-a): define project intake and technology contracts`

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

