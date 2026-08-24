---
doc_id: "DEVPL-PROMPT-GSDLC-05-B"
prompt_number: "02"
title: "Prompt operativo — DEVPL-GSDLC-05-B — MIPSoftware executable lifecycle and gates"
status: "ready_for_execution"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-08-24"
approval: "owner_approved_backlog_scope"
program_id: "DEVPL-GSDLC"
backlog_id: "DEVPL-GSDLC-05"
micro_sprint: "DEVPL-GSDLC-05-B"
execution_rule: "solo 05-B; successor bloqueado hasta owner adjudication CLOSED/PASS"
source_authority_mode: "predecessor-owner-adjudicated-successor/05-A"
local_first: true
dry_run_default: true
pilot_workspace_access_allowed: false
full_regression_allowed: "false"
---

# Prompt operativo — DEVPL-GSDLC-05-B

## 1. Mandato

Implementa **solo** `GSDLC-05-B — MIPSoftware executable lifecycle and gates`. Empieza únicamente desde el successor owner-adjudicated de 05-A; no vuelvas a repo369 si 05-A ya produjo successor.

## Autoridad y reglas transversales obligatorias

Baseline ancestral fijo de la ola (lineage; **no** sustituye al predecessor inmediato de este micro-sprint):

- repo: `repo_DevPilot_Local_369_DEVPL_GSDLC_04_E_ARTIFACT_WORKBENCH_BROWSER_CLOSURE_WINDOWS_VALIDATED_CANDIDATE.zip`
- commit: `13c2a59bbcb8adbb27f2a9be59a1e2925454fb29`
- SHA-256: `de62ae248dbdc9f587ef85a72c2194fc5db7f8d5758c0a1dda1f135ceb0b4be7`
- autoridad inmediata: **el successor owner-adjudicated del micro-sprint predecessor**; si no existe o no puede verificarse reproduciblemente, terminar `BLOCK` antes de mutar source.
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


## 2. Preflight predecessor

Exigir `05-A CLOSED/PASS`, candidate/commit/SHA, owner adjudication y Project State/Source Registry reconciliados. Si falta cualquiera, BLOCK antes de source.

## 3. Resultado funcional

Convertir el registry aprobado en un lifecycle MIPSoftware ejecutable desde intake hasta release, concentrando en este micro-sprint la semántica de prerequisites/exit gates/progress/blockers **sin LLM**.

Reutilizar `WorkspaceEngineeringState`, `workflow_transition_catalog` y el motor determinístico de GSDLC-01; no crear un segundo state engine.

Implementar:

- `MIPWorkflowRegistry`/binding equivalente;
- `MIPGateEvaluator`;
- phase/step prerequisite graph;
- artifact-profile/validator bindings;
- deterministic progress model;
- blocker explanations y remediation actions machine-readable;
- waiver contract gobernado para excepciones permitidas, sin owner bypass informal.

El owner no puede saltar un mandatory step salvo waiver typed, scoped, auditable y expresamente permitido por policy. Un LLM nunca decide PASS/BLOCK.

## 4. Semántica requerida

- transición solo si source state, prerequisites, required artifacts y exit gates coinciden;
- progress derivado del registry vivo, no hardcoded por UI;
- weights determinísticos/versionados;
- blocker IDs estables y explicación reproducible;
- current step proyectado desde server state;
- no source write por evaluar gates;
- legacy generic transition catalog se conserva como historical/current predecessor y evoluciona mediante successor, no se reescribe retroactivamente.

## 5. Pruebas/evidencia

- phase fixtures por camino nominal;
- skip-required negatives;
- gate missing/fail;
- artifact missing/not-ready;
- waiver valid/invalid/expired/wrong-scope;
- cycle detection;
- progress determinism y stable ordering;
- GSDLC-01 historical state/transition contracts;
- readiness/profile bindings;
- Test Impact + historical/contract reconciliation.

Evidence: `mip_workflow_coverage.json`, `transition_case_matrix.json`, progress determinism report.

PASS: required phases no skip, blockers explicables, progress reproducible, no LLM authority, S0/S1=0, full=0.

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


## 6. Git/successor

Branch sugerida: `feat/devpl-gsdlc-05-b-mip-executable-lifecycle`

Commit: `feat(gsdlc-05-b): enforce executable MIP lifecycle gates`

Candidate lógico: `repo_DevPilot_Local_371_DEVPL_GSDLC_05_B_MIP_EXECUTABLE_LIFECYCLE_WINDOWS_VALIDATED_CANDIDATE.zip` (validar secuencia real).
