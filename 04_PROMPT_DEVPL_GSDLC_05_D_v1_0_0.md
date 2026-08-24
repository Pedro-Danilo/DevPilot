---
doc_id: "DEVPL-PROMPT-GSDLC-05-D"
prompt_number: "04"
title: "Prompt operativo — DEVPL-GSDLC-05-D — StepActionCatalog and ExecutionModeAdvisor"
status: "ready_for_execution"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-08-24"
approval: "owner_approved_backlog_scope"
program_id: "DEVPL-GSDLC"
backlog_id: "DEVPL-GSDLC-05"
micro_sprint: "DEVPL-GSDLC-05-D"
execution_rule: "solo 05-D; successor bloqueado hasta owner adjudication CLOSED/PASS"
source_authority_mode: "predecessor-owner-adjudicated-successor/05-C"
local_first: true
dry_run_default: true
pilot_workspace_access_allowed: false
full_regression_allowed: "false"
---

# Prompt operativo — DEVPL-GSDLC-05-D

## 1. Mandato

Implementa **solo** `GSDLC-05-D — StepActionCatalog and ExecutionModeAdvisor` desde el successor owner-adjudicated de 05-C.

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


## 2. Resultado funcional

Para cada `current_step`, producir una lista determinística de rutas válidas y sus razones, sin otorgar capacidades nuevas.

Action kinds contractuales:

- `MANUAL`;
- `PASTE`;
- `UPLOAD_IMPORT`;
- `EXTERNAL_EDITOR`;
- `AGENT`;
- `RAG`;
- `TYPED_OPERATION`.

`AGENT` y `RAG` deben aparecer `unavailable` durante GSDLC-05 salvo capability real ya autorizada por un backlog posterior; no fingir provider/model execution.

Implementar/componer `StepActionCatalog`, `ExecutionModeAdvisor` y `StepActionCard` UI con:

- purpose;
- availability;
- disabled reason(s);
- prerequisites;
- required role;
- policy/risk;
- side effects;
- approval required;
- network/external API;
- cost/tokens estimados o `not applicable`;
- deterministic rank/recommended flag;
- navigation target/typed-operation ID.

El Advisor solo refleja server policy; jamás convierte una acción prohibited en allowed. UI no recalcula autoridad.

## 3. Reutilización obligatoria

Inspeccionar y preferir composición con:

- Project Status/NextAction de GSDLC-01;
- `ui/web/src/components/OperatorNextActions.ts`;
- Artifact Workbench 04;
- MIP/MIASI registries 05-A/C;
- Server RBAC + sensitive action catalog + API/UI capability registries;
- provider/model availability existente solo como input informativo; no realizar llamadas.

## 4. Browser acceptance acotado

Demostrar como mínimo:

1. current step con MANUAL recomendado y alternativas visibles;
2. PASTE/UPLOAD import disponibles solo cuando el artifact profile lo permite;
3. wrong-role typed operation disabled con razón;
4. policy-blocked action no ejecutable;
5. AGENT/RAG visibles pero unavailable con explicación/enlace de configuración solo si pertinente;
6. budget exhausted/provider unavailable determinísticos;
7. cost/risk/approval/side effects visibles;
8. keyboard/focus/labels básicos;
9. route/project context guard preservado.

Normal user PowerShell=0. No hidden CLI bridge.

## 5. Pruebas/evidencia

- full step×action availability matrix;
- 100% current steps con acción válida o BLOCK explícito;
- RBAC negatives;
- policy negatives;
- provider unavailable;
- budget exhausted;
- stable ranking;
- no UI/server authority divergence;
- API/OpenAPI/API mapping/UI route/capability parity;
- Test Impact + sweeps.

Evidence: `step_action_coverage.json`, `advisor_decision_samples.json`, browser matrix/screenshots.

PASS: recommendation explicable, prohibited action nunca offered como executable, cost/risk no omitidos para agentic routes, S0/S1=0, full=0.

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

Branch: `feat/devpl-gsdlc-05-d-step-action-advisor`

Commit: `feat(gsdlc-05-d): add policy-bound step action advisor`

Candidate lógico: `repo_DevPilot_Local_373_DEVPL_GSDLC_05_D_STEP_ACTION_ADVISOR_WINDOWS_VALIDATED_CANDIDATE.zip`.
