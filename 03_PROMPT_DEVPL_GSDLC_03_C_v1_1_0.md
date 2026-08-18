---
doc_id: "DEVPL-PROMPT-GSDLC-03-C"
prompt_number: "03"
title: "Prompt operativo — DEVPL-GSDLC-03-C — Dry-run Create/Open/Import"
status: "ready_for_execution"
version: "1.1.0"
owner: "Ordóñez"
updated: "2026-08-18"
approval: "owner_approved_backlog_scope"
program_id: "DEVPL-GSDLC"
backlog_id: "DEVPL-GSDLC-03"
micro_sprint: "DEVPL-GSDLC-03-C"
execution_rule: "solo 03-C; requiere 03-B CLOSED/PASS"
source_authority_mode: "fixed-rebound-to-03-b-successor"
local_first: true
dry_run_default: true
pilot_workspace_access_allowed: false
---

# Prompt operativo — DEVPL-GSDLC-03-C

## 1. Mandato

Implementa **solo** `GSDLC-03-C — Dry-run for Create/Open/Import` sobre 03-B CLOSED/PASS.

Autoridad inmediata rebindeada:

```text
repo=repo_DevPilot_Local_361_DEVPL_GSDLC_03_B_ENVIRONMENT_DISCOVERY_PLANNING_WINDOWS_VALIDATED_CANDIDATE.zip
commit=1ba680caffd9b30ec2d3252b8006b1fd7f183e17
sha256=69097543a95589f1957808da5e2e22e5576cd12153e23775da9bb8c4c1ad114b
adjudication=DEVPL_GSDLC_03_B_FINAL_OWNER_ADJUDICATION_v1_0_0.md
```

La rama canónica se promueve `ff-only` a ese commit antes de cualquier mutación 03-C.

## Fuentes obligatorias de autoridad

Antes de proyectar cambios, consultar literalmente como mínimo:

- `repo_DevPilot_Local_361_DEVPL_GSDLC_03_B_ENVIRONMENT_DISCOVERY_PLANNING_WINDOWS_VALIDATED_CANDIDATE.zip` como baseline técnico inmediato;
- `DEVPL_GSDLC_03_B_FINAL_OWNER_ADJUDICATION_v1_0_0.md`;
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


## 2. CREATE_NEW dry-run

Desde UI/API:
- mostrar tree previsto;
- Git init plan;
- venv plan;
- dependencies/jobs;
- metadata/config;
- writes declarados;
- plan hash.

No crear archivos.

## 3. OPEN_EXISTING dry-run

Usar solo fixture controlado bajo E2E Evaluation:
- validar repo/workspace;
- detectar standards/conflicts;
- path/isolation;
- read-only inventory;
- 0 writes.

## 4. IMPORT_GIT dry-run

Acceptance obligatoria: **import local** de fixture Git local.

Remote clone:
- disabled-by-default;
- URL sanitizada;
- credential strategy sin values;
- network plan explícito;
- no conexión real en 03-C.

## 5. Approval preview

Approval request debe derivar de `plan_hash + typed operations + scope`, no de command strings. Revalidar preimage antes de execute futuro.

## 6. Tests

- create/open/import 0-write;
- plan hash reproducibility;
- path overlap;
- changed-preimage invalidates plan;
- remote network blocked by default;
- URL/credential redaction;
- UI/API parity;
- A+B+C cumulative;
- governance/TCR/Test Impact.

## Política transversal de validación

Autoridad: `.devpilot/gsdlc/transversal_validation_policy.json`.

- A→D: `validation_mode=cumulative-selective`.
- Test Impact siempre se ejecuta en analyze/dry-run y sus P0/P1 son inputs de selección.
- `full_regression_required=true` en A→D es señal de escalamiento, **no orden automática**.
- Full intermedia solo con hard trigger sistémico y owner approval previo.
- 03-E ejecuta la **única full regression del backlog exactamente una vez**, después de browser acceptance.
- Si la full de E falla: preservar log/marker, no repetir, corregir raíces, exact failed-nodeid retest + bounded impacted retest + Historical Regression Guard.
- Nunca modificar snapshots históricos únicamente para hacer pasar pytest.


Para 03-C: **full regression = NO** salvo hard trigger owner-approved previo.

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

PASS-CANDIDATE:
- tres dry-runs visibles/revisables en UI;
- writes=0;
- network=0;
- immutable plan hash;
- approval preview typed;
- S0/S1=0.

BLOCK:
- cualquier write;
- network silenciosa;
- plan drift no bloqueado;
- credentials en evidence.

## 8. Git

Feature: `feat/devpl-gsdlc-03-c-entry-dry-runs`

Commit: `feat(gsdlc-03-c): add create open import dry-run flows`

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




## Acceptance UI mínima 03-C

Antes de owner adjudication, demostrar visualmente en navegador autenticado los tres modos sobre fixtures exclusivos de `DevPilot_E2E_Evaluation`:

- CREATE_NEW dry-run;
- OPEN_EXISTING dry-run;
- IMPORT_GIT local dry-run.

Las tres vistas deben mostrar `plan_hash`, `preimage_hash`, efectos declarados, approval preview, `writes_performed=false`, `network_used=false` y ausencia de control execute. La evidencia visual se limita a este alcance; el E2E de creación/apertura/importación real pertenece a 03-D/03-E.

La validación frontend debe incluir static smoke, TypeScript `--noEmit` y Vite build con salida fuera del source tree. No instalar dependencias mediante red como efecto lateral del operador.

## Refinamiento operativo obligatorio v1.1.0

Aplicar `DEVPL_GSDLC_OPERATOR_MINIMAL_VALIDATION_POLICY_v1_0_0.md`: operador de superficie mínima, gates por impacto, evidencia PASS reutilizable en recoveries y ninguna revalidación general redundante. Para 03-C, la UI manual se verifica únicamente contra los tres dry-runs y no habilita ejecución.
