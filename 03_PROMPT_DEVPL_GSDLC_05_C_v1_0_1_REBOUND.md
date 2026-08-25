---
doc_id: "DEVPL-PROMPT-GSDLC-05-C"
prompt_number: "03"
title: "Prompt operativo — DEVPL-GSDLC-05-C — MIASI applicability, roles and policy binding"
status: "ready_for_execution/rebound-repo371"
version: "1.0.1"
owner: "Ordóñez"
updated: "2026-08-24"
approval: "owner_approved_backlog_scope"
program_id: "DEVPL-GSDLC"
backlog_id: "DEVPL-GSDLC-05"
micro_sprint: "DEVPL-GSDLC-05-C"
execution_rule: "solo 05-C; successor bloqueado hasta owner adjudication CLOSED/PASS"
source_authority_mode: "predecessor-owner-adjudicated-successor/05-B"
local_first: true
dry_run_default: true
pilot_workspace_access_allowed: false
full_regression_allowed: "false"
---

# Prompt operativo — DEVPL-GSDLC-05-C

## 1. Mandato

Implementa **solo** `GSDLC-05-C — MIASI applicability, roles and policy binding` desde el successor owner-adjudicated de 05-B.

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



### Autoridad inmediata rebindeada para esta ejecución

- repo: `repo_DevPilot_Local_371_DEVPL_GSDLC_05_B_MIP_EXECUTABLE_LIFECYCLE_WINDOWS_VALIDATED_CANDIDATE.zip`
- commit: `176284f17cf34e916e8a9a6fd68b1311fa8f0773`
- SHA-256: `8f40c077174c8df3e1a4589898863b787ed7fc56f5d83f20c006259b55f81d12`
- predecessor adjudication: `DEVPL_GSDLC_05_B_FINAL_OWNER_ADJUDICATION_v1_0_0.md`
- predecessor closure current: `DEVPL_GSDLC_05_B_FINAL_OWNER_CLOSURE_CURRENT.json`

Esta autoridad inmediata reemplaza a repo369 para toda mutación de 05-C. Repo369 se conserva únicamente como baseline ancestral de lineage.

## 2. Resultado funcional

Hacer que MIASI se active de forma determinística a nivel proyecto y feature cuando existan capacidades AI/agentic, y proyectar esa decisión en Project Status/artifact readiness. No ejecutar modelos ni agentes.

Reutilizar y componer `.devpilot/miasi/agent_registry.json`, `tool_registry.json`, `policy_matrix.json`, `semantic_rules.json`, `src/devpilot_core/miasi/registry.py` y `semantic.py`; no crear una segunda MIASI policy engine.

Implementar `MIASIApplicabilityEvaluator`/successor equivalente con:

- `APPLICABLE`, `NOT_APPLICABLE`, `AMBIGUOUS/REVIEW_REQUIRED`;
- reasons/evidence refs;
- project-level + feature-level classification;
- required Agent/Tool/Policy/Eval/Human Approval/Observability/RAG/Memory artifacts;
- risk escalation y no-go gates;
- re-evaluation cuando una feature inicialmente no-AI incorpora IA;
- server projection consumible por Project Status.

High uncertainty/risk debe fallar cerrado. `AGENT`/`RAG` siguen no ejecutables en esta ola.

## 3. UX/capability acceptance

Como 05-C añade indicador MIASI en Project Status, requiere browser capability acceptance acotado, no full:

- non-AI project: MIASI not applicable con rationale;
- AI project/feature: MIASI applicable con required controls;
- ambiguous: BLOCK/review required, no auto-advance;
- missing card/control visible;
- risk escalation visible;
- direct route/project-context guard preservado;
- normal user PowerShell=0, external operator project writes=0.

No usar datos preinyectados por operador para fingir la decisión; el fixture puede preparar inputs declarativos, pero la evaluación debe ocurrir por API/service real.

## 4. Pruebas/evidencia

- AI/non-AI/ambiguous fixtures;
- feature changes non-AI→AI;
- missing cards;
- critical risk without control;
- policy/RBAC binding;
- no agent execution with MIASI incomplete;
- deterministic rationale;
- Project Status UI mapping + route registry/API mapping;
- existing MIASI semantic validation historical/current contracts;
- Test Impact + sweeps.

Evidence: `miasi_activation_matrix.json`, `miasi_gate_report.json`, screenshots de los estados requeridos.

PASS: MIASI status justificable, required controls enforced, no unsafe advance, browser capability PASS, S0/S1=0, full=0.

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


## 5. Git/successor

Branch: `feat/devpl-gsdlc-05-c-miasi-applicability`

Commit: `feat(gsdlc-05-c): bind MIASI applicability and policy gates`

Candidate lógico: `repo_DevPilot_Local_372_DEVPL_GSDLC_05_C_MIASI_APPLICABILITY_WINDOWS_VALIDATED_CANDIDATE.zip`.
