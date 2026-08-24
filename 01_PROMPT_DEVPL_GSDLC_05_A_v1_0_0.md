---
doc_id: "DEVPL-PROMPT-GSDLC-05-A"
prompt_number: "01"
title: "Prompt operativo — DEVPL-GSDLC-05-A — ExecutableStandardRegistry and source mapping"
status: "ready_for_execution"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-08-24"
approval: "owner_approved_backlog_scope"
program_id: "DEVPL-GSDLC"
backlog_id: "DEVPL-GSDLC-05"
micro_sprint: "DEVPL-GSDLC-05-A"
execution_rule: "solo 05-A; successor bloqueado hasta owner adjudication CLOSED/PASS"
source_authority_mode: "fixed-owner-adjudicated-gsdlc04-successor"
local_first: true
dry_run_default: true
pilot_workspace_access_allowed: false
full_regression_allowed: "false"
---

# Prompt operativo — DEVPL-GSDLC-05-A

## 1. Mandato

Implementa **solo** `GSDLC-05-A — ExecutableStandardRegistry and source mapping`.

### Checkpoint A0 — activation rebind obligatorio

Antes de cualquier source funcional:

1. verificar byte/SHA del candidate repo369 y comprobar la identidad commit registrada;
2. incorporar las adjudicaciones externas de 04-E y backlog 04 y `DEVPL_GSDLC_04_FINAL_OWNER_CLOSURE_CURRENT.json`;
3. incorporar backlog 05 APPROVED_REBOUND y prompts vigentes;
4. reconciliar Project State, Source Registry, README y roadmap a `GSDLC-04 CLOSED/PASS` + `GSDLC-05 authorized/active` + current `05-A`;
5. crear o seleccionar una rama específica `feat/devpl-gsdlc-05-executable-workflows` desde el commit autoritativo repo369, sin rebase automático ni mutar `.git` fuera de operaciones Git normales;
6. registrar los nuevos documentos en Source Registry sin mutar snapshots históricos;
7. ejecutar Project State/schema, Source Registry schema, Docs Governance, TCR impacted, historical transition sweep y `git diff --check`;
8. terminar **BLOCK antes de funcionalidad** si existe contradicción o path inesperado.

A0 es administrativo, no es un sexto micro-sprint y no ejecuta full ni browser.

## Autoridad y reglas transversales obligatorias

Autoridad de entrada de la ola:

- repo: `repo_DevPilot_Local_369_DEVPL_GSDLC_04_E_ARTIFACT_WORKBENCH_BROWSER_CLOSURE_WINDOWS_VALIDATED_CANDIDATE.zip`
- commit: `13c2a59bbcb8adbb27f2a9be59a1e2925454fb29`
- SHA-256: `de62ae248dbdc9f587ef85a72c2194fc5db7f8d5758c0a1dda1f135ceb0b4be7`
- backlog: `DEVPL-GSDLC-05_executable_mipsoftware_miasi_and_step_action_advisor_v1_2_0_APPROVED_REBOUND.md`
- predecessor closure: `DEVPL_GSDLC_04_E_FINAL_OWNER_ADJUDICATION_v1_0_0.md` + `DEVPL_GSDLC_04_BACKLOG_CLOSURE_ADJUDICATION_v1_0_0.md`.

Reglas permanentes:

1. local-first, deny-by-default y `dry-run` por defecto;
2. no API key, red ni modelo pago requerido; model execution real está fuera de alcance de GSDLC-05;
3. Human Session/RBAC/Policy/Approval server-side son autoridad; browser storage es UX-only;
4. mutaciones solo typed operations: `plan → dry-run → policy/RBAC → approval si aplica → execute → verify → evidence`;
5. no arbitrary shell; subprocess con argv nativo, `shell=False`, timeouts class-specific y resolución explícita `.cmd/.exe` en Windows;
6. no `reset --hard`, `git clean`, rebase automático, force push ni edición de `.git`;
7. Git status NUL-safe: `git status --porcelain=v1 -z`; Git blob es autoridad frente a diferencias físicas LF/CRLF;
8. excluir `auth.db*`, `devpilot.db*` y stores runtime de fixtures/sandboxes/evidence/release;
9. ZIP final excluye `.git`, `.venv`, `node_modules`, `outputs`, caches, runtime DBs y secretos;
10. no acceder al piloto `D:\Projects\DevPilot_Workspaces\inventory-sales-local`; topología externa limitada a DevPilot_Local, DevPilot_E2E_Evaluation y DevPilot_Artifacts/POST-H-EVAL-002;
11. cada fase/gate produce checkpoint JSON y toda instrucción de consola termina visualmente en **PASS verde o BLOCK rojo**;
12. PowerShell de guías: una sola línea física por comando, rutas completas listas para copiar/pegar bajo `C:\Users\Pedro\Downloads`;
13. historical contracts: clasificar `historical-freeze`, `current-active`, `successor-needed`, `deprecated-after-proof`, `derived`, `runtime-ephemeral`; no cambiar aserciones históricas solo para hacer verde pytest;
14. antes del cierre de cada micro-sprint ejecutar Historical Contract Sweep + Contract Reconciliation Sweep + Test Impact;
15. A→D: full regression = **NO por rutina**. Solo hard-trigger explícito owner-approved puede consumir anticipadamente la única full de la ola; si la consume, 05-E no ejecuta otra;
16. 05-E: después de cheap gates + predictive reconciliation + browser, consumir la única full exactamente una vez. Si FAIL: preservar marker/log/JUnit, **NO rerun**, exact failed-nodeid retest + bounded impacted retest + Historical Regression Guard + composite closure PASS;
17. browser no se repite por correctives que no modifiquen la UX ya acreditada.


## 2. Fuentes literales obligatorias

Consultar antes de diseñar:

- `docs/standards/mipsoftware/**`;
- `docs/standards/miasi/**`, en especial `03_agentic_sdlc.md`, manifests, schemas, checklists y reference;
- `.devpilot/gsdlc/workflow_transition_catalog.json`, cuyo scope actual declara explícitamente que artifact-specific executable workflow se difiere a GSDLC-05;
- `.devpilot/readiness/readiness_requirements.json`;
- `.devpilot/miasi/agent_registry.json`, `tool_registry.json`, `policy_matrix.json`, `semantic_rules.json`;
- `src/devpilot_core/miasi/registry.py` y `semantic.py`;
- Guided SDLC state/transition services de GSDLC-01;
- Artifact Profiles/Workbench 04;
- schema catalog, Source Registry y TCR v1/v2.

No inventar una regla ejecutable si no puede vincularse a `doc_id/path/heading/source_hash` o a una decisión/ADR explícita.

## 3. Resultado funcional

Crear un `ExecutableStandardRegistry` versionado que represente de forma machine-readable:

- standard/version;
- phases/steps;
- artifacts y artifact profiles;
- prerequisites/dependencies;
- validators;
- approvals;
- exit gates;
- next actions;
- mandatory/optional semantics;
- source references con hash y heading;
- migration/version semantics.

La documentación normativa sigue siendo autoridad hasta owner approval del registry; el registry no puede “corregir” silenciosamente MIPSoftware/MIASI.

## 4. Diseño mínimo esperado

Preferir extender el paquete Guided SDLC existente. Como mínimo evaluar/crear, con nombres finales justificados por inspección:

- schema `executable_standard_registry`;
- `.devpilot/gsdlc/executable_standard_registry.json` o successor equivalente;
- loader/validator/service en `src/devpilot_core`;
- source mapping report;
- source drift detector.

Validator fail-closed ante duplicate IDs, orphan mandatory steps, missing source, source-hash drift crítico y cycles no permitidos. Las dependencias legítimamente cíclicas solo pueden representarse si el modelo distingue explícitamente graph edges no-transicionales; no relajar cycle detection genéricamente.

## 5. Pruebas y evidencia

Mínimo:

- schema positive/negative;
- 100% mandatory pre-code mapping;
- source-link/path/heading/hash verification;
- orphan critical step negative;
- duplicate ID negative;
- cycle negative;
- source drift negative;
- migration/version compatibility;
- current workflow catalog coexistence;
- Test Impact + focal/cumulative;
- historical + contract reconciliation sweeps.

Evidence: `standard_mapping_coverage.json`, `source_drift_report.json`, registry validation report.

PASS exige `mandatory_pre_code_mapping=100%`, `orphan_critical_steps=0`, no new rule without source y S0/S1=0. Full=0.

## Contrato de entregables y operador

Entregar como mínimo:

- implementation/validation package ZIP + SHA;
- source delta exacto + manifest pre/post SHA;
- operador Python state-aware/idempotente/reanudable;
- guía Windows única para operador no experto;
- `CURRENT`, Test Impact, Historical Contract Sweep, Contract Reconciliation Sweep, closure report y operation declaration;
- evidence package Windows cuando aplique;
- candidate successor desde Git HEAD limpio + SHA;
- propuesta de owner adjudication que **no** autoriza el siguiente micro-sprint hasta decisión owner.

El operador debe reconocer `pending/already_applied/conflict`, nunca exigir repetir un gate PASS si su autoridad no cambió y bloquear antes de mutaciones ante estado ambiguo.


## 6. Git/successor sugerido

Branch: `feat/devpl-gsdlc-05-a-executable-standard-registry`

Commit: `feat(gsdlc-05-a): add executable standards registry`

Nombre lógico candidate: `repo_DevPilot_Local_370_DEVPL_GSDLC_05_A_EXECUTABLE_STANDARD_REGISTRY_WINDOWS_VALIDATED_CANDIDATE.zip` (validar numeración real antes de empaquetar).

No autorizar 05-B dentro de este prompt; entregar evidencia para owner adjudication.
