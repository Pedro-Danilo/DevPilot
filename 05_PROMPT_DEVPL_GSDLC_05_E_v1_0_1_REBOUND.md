---
doc_id: "DEVPL-PROMPT-GSDLC-05-E"
prompt_number: "05"
title: "Prompt operativo — DEVPL-GSDLC-05-E — Manual/import pre-code wizard vertical slice (repo373 rebound)"
status: "ready_for_execution"
version: "1.0.1"
owner: "Ordóñez"
updated: "2026-08-24"
approval: "owner_approved_backlog_scope"
program_id: "DEVPL-GSDLC"
backlog_id: "DEVPL-GSDLC-05"
micro_sprint: "DEVPL-GSDLC-05-E"
execution_rule: "solo 05-E; successor bloqueado hasta owner adjudication CLOSED/PASS"
source_authority_mode: "predecessor-owner-adjudicated-successor/05-D"
local_first: true
dry_run_default: true
pilot_workspace_access_allowed: false
full_regression_allowed: "true/exactly-once-at-closure"
---

# Prompt operativo — DEVPL-GSDLC-05-E — repo373 rebound

## 1. Mandato

Implementa y cierra **solo** `GSDLC-05-E — Manual/import pre-code wizard vertical slice`. Es el cierre industrial de la ola y el único punto normal autorizado para consumir la full regression de DEVPL-GSDLC-05.

Empieza únicamente desde el successor owner-adjudicated de 05-D.

## Autoridad y reglas transversales obligatorias

Baseline ancestral fijo de la ola (lineage; **no** sustituye al predecessor inmediato de este micro-sprint):

- repo: `repo_DevPilot_Local_369_DEVPL_GSDLC_04_E_ARTIFACT_WORKBENCH_BROWSER_CLOSURE_WINDOWS_VALIDATED_CANDIDATE.zip`
- commit: `13c2a59bbcb8adbb27f2a9be59a1e2925454fb29`
- SHA-256: `de62ae248dbdc9f587ef85a72c2194fc5db7f8d5758c0a1dda1f135ceb0b4be7`
- autoridad inmediata: `repo_DevPilot_Local_373_DEVPL_GSDLC_05_D_STEP_ACTION_ADVISOR_WINDOWS_VALIDATED_CANDIDATE.zip`;
- autoridad inmediata commit: `a5b01a6ffb7f7808ccbaae54847bf2117b95b9f8`;
- autoridad inmediata SHA-256: `56166db2626faf505fe4ebc93a9119abcffd6fbc0d21f5a5be364472d14c60c7`;
- predecessor owner adjudication: `DEVPL_GSDLC_05_D_FINAL_OWNER_ADJUDICATION_v1_0_0.md` + `DEVPL_GSDLC_05_D_FINAL_OWNER_CLOSURE_CURRENT.json`;
- si esta autoridad no puede verificarse reproduciblemente, terminar `BLOCK` antes de mutar source.
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


## 2. Invariante de producto a demostrar

Desde Project Status, una persona normal puede completar el pre-code secuencialmente por UI, sin IA, sin PowerShell y sin escrituras del operador al proyecto:

`Product Vision → Scope → Requirements → Architecture → Security → Test Strategy → Traceability → PRE_CODE_READY`.

Cada etapa debe:

- exponer StepActionAdvisor;
- permitir MANUAL y/o IMPORT según policy/profile;
- crear DRAFT real desde UI;
- validar/findings/corregir;
- plan/diff cuando haya promoción;
- approval server-side cuando aplique;
- apply/freeze;
- actualizar workflow state;
- bloquear skip mandatory;
- mostrar blocker/remediation determinísticos.

No está permitido preinyectar artefactos terminados desde el harness para obtener PRE_CODE_READY. Fixtures solo pueden preparar identidad/workspace/inputs externos inocuos necesarios para la prueba.

## 3. Browser acceptance de cierre

Diseñar una matriz reproducible que cubra como mínimo:

1. entrada desde Project Status con proyecto activo;
2. Product Vision manual;
3. Scope manual/import;
4. Requirements manual/import;
5. Architecture;
6. Security;
7. Test Strategy;
8. Traceability;
9. cada artefacto pasa DRAFT→validate→review/approval→apply/freeze según su policy;
10. intento de saltar stage mandatory = BLOCK visible;
11. wrong-role approval denied;
12. MIASI applicable/not-applicable/ambiguous según fixture y sin bypass;
13. StepActionAdvisor en cada current_step, AGENT/RAG unavailable;
14. restart/resume sin perder server-authoritative state;
15. API-down/error recoverable fail-closed;
16. keyboard/focus/labels;
17. final `PRE_CODE_READY`;
18. `readiness strict = PASS`;
19. transition trace consistente;
20. state/file/Git/provenance parity.

Capturas deben ser focales y legibles, sin secretos. La evidencia machine-readable no requiere screenshot sustituta cuando el dato no sea visual, pero cada escenario manual debe tener observación real no vacía.

## 4. Predictive Pre-Full Reconciliation Gate — obligatorio antes del marker

No consumir la full hasta que un operador separado o fase sellada entregue PASS para:

- schemas estrictos y metadata current-active;
- Source Registry status_required ↔ actual status;
- Project State/README/roadmap/CURRENT coherentes;
- MIP/MIASI executable registries y source hashes;
- workflow counters/derived state recalculados desde colección viva;
- ApplicationService ↔ OpenAPI ↔ API mapping ↔ route registry ↔ RBAC parity;
- UI route/capability mappings;
- StepActionCatalog actions ↔ RBAC/policy/sensitive-action/tool bindings;
- historical snapshots vs current successors, sin assertions históricas contra mutable-current;
- budgets históricos vs current-active;
- Source ZIP SecretGuard/redaction sobre el árbol exacto que se empaquetará;
- operator evidence schema self-tests contra ejemplos reales;
- Windows wrappers/toolchain resueltos con `shell=False`;
- runtime-ephemeral absent;
- TCR v1/v2;
- `git diff --check`;
- browser evidence validator PASS;
- S0/S1=0.

Cualquier BLOCK se corrige **antes** del marker. No se permite “ver qué dice la full” si un drift determinista ya es conocido.

## 5. Política de la única full regression

Orden de cierre:

1. source authority/integrity;
2. focal E;
3. cumulative A→E;
4. schemas/API/UI/build;
5. readiness strict + MIP/MIASI gates;
6. Test Impact;
7. Historical Contract Sweep;
8. Contract Reconciliation + Predictive Pre-Full Gate;
9. browser acceptance;
10. S0/S1;
11. durable pre-full marker con source fingerprint y browser evidence hash;
12. ejecutar la **única full regression exactamente una vez**;
13. si PASS → repo review/commit/candidate;
14. si FAIL/BLOCK/timeout → conservar immutable marker/log/JUnit/failed-nodeids y **NO repetir**; diagnosticar root cause, corrective acotado, exact failed-nodeid retest, bounded impacted retest, Historical Regression Guard y composite closure;
15. browser no se repite salvo que el corrective cambie comportamiento UX acreditado.

El operador debe impedir técnicamente una segunda full (`maximum_runs=1`, `rerun_allowed=false`).

## 6. Evidencia mínima

- `pre_code_manual_browser_acceptance`;
- screenshots por etapa;
- `transition_trace.jsonl`;
- artifact provenance summary;
- readiness report;
- MIP workflow/gate report;
- MIASI applicability report;
- StepActionAdvisor coverage;
- state/file/Git parity;
- Test Impact;
- historical/contract/predictive sweeps;
- full marker/log/JUnit o composite recovery chain;
- S0/S1;
- candidate + SHA.

PASS: `PRE_CODE_READY` desde UI, readiness strict PASS, mandatory stages no skip, normal-user PowerShell=0, external operator project writes=0, S0/S1=0 y full/composite válida.

BLOCK: artefactos preinyectados por harness, hidden CLI bridge, stage skip, LLM/model authority, unsafe approval bypass, full rerun, known contract drift ignorado.

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


## 7. Git/successor y cierre

Branch: `feat/devpl-gsdlc-05-e-pre-code-wizard-closure`

Commit: `feat(gsdlc-05-e): close manual pre-code workflow`

Candidate lógico: `repo_DevPilot_Local_374_DEVPL_GSDLC_05_E_MANUAL_PRE_CODE_WINDOWS_VALIDATED_CANDIDATE.zip` (validar numeración real).

No declarar backlog 05 `CLOSED/PASS` hasta evidencia Windows + owner adjudication del micro-sprint E y del backlog. GSDLC-06 permanece bloqueado hasta entonces.
