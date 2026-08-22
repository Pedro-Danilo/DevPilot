---
doc_id: "DEVPL-PROMPT-GSDLC-04-C"
prompt_number: "03"
title: "Prompt operativo — DEVPL-GSDLC-04-C — Paste, upload and external-source import"
status: "executed/ready-for-windows"
version: "1.0.1"
owner: "Ordóñez"
updated: "2026-08-20"
approval: "owner_approved_backlog_scope"
program_id: "DEVPL-GSDLC"
backlog_id: "DEVPL-GSDLC-04"
micro_sprint: "DEVPL-GSDLC-04-C"
execution_rule: "solo 04-C; successor bloqueado hasta owner adjudication CLOSED/PASS"
source_authority_mode: "dynamic-predecessor-owner-adjudicated-successor"
local_first: true
dry_run_default: true
pilot_workspace_access_allowed: false
full_regression_allowed: false
source_repo: "repo_DevPilot_Local_366_DEVPL_GSDLC_04_B_MANUAL_EDITOR_DRAFT_HISTORY_WINDOWS_VALIDATED_CANDIDATE.zip"
source_git_commit: "b095bf5b75259c9c7c4a9a5c1b5d546cfe049d6f"
source_repo_sha256: "3cfe97a376ee269b6c6fb3465e9549c2eea1e2160ecf5ff4848fd351a776ad92"
predecessor_owner_adjudication: "DEVPL_GSDLC_04_B_OWNER_ADJUDICATION_v1_0_0.md"
predecessor_final_current: "DEVPL_GSDLC_04_B_FINAL_OWNER_CLOSURE_CURRENT.json"
---

# Prompt operativo — DEVPL-GSDLC-04-C

## 0. Rebind de autoridad ejecutado para 04-C

Este prompt deriva literalmente de `03_PROMPT_DEVPL_GSDLC_04_C_v1_0_0.md`, con el único rebind de ejecución requerido por el cierre owner-adjudicated de 04-B.

- predecessor 04-B: `CLOSED/PASS`;
- repo técnico de entrada: `repo_DevPilot_Local_366_DEVPL_GSDLC_04_B_MANUAL_EDITOR_DRAFT_HISTORY_WINDOWS_VALIDATED_CANDIDATE.zip`;
- commit: `b095bf5b75259c9c7c4a9a5c1b5d546cfe049d6f`;
- SHA-256: `3cfe97a376ee269b6c6fb3465e9549c2eea1e2160ecf5ff4848fd351a776ad92`;
- evidencia Windows 04-B: `DEVPL_GSDLC_04_B_WINDOWS_EVIDENCE_v1_0_10.zip` / `787ffa1166020df4c803964265653cb404a639230f78582c94cf0354a0fe41ea`;
- autoridad de cierre: `DEVPL_GSDLC_04_B_OWNER_ADJUDICATION_v1_0_0.md`;
- full regression en 04-C: **prohibida por rutina**; se mantiene reservada para 04-E.

Cualquier ejecución 04-C sobre otra fuente es `BLOCK` antes de mutar source.


## 1. Mandato

Implementa **solo** `GSDLC-04-C — Paste, upload and external-source import`.

Fuente de ejecución: successor owner-adjudicated de GSDLC-04-B, resuelto por adjudicación B. Cualquier mismatch repo/commit/SHA = BLOCK antes de mutar.

## Fuentes obligatorias de autoridad

Antes de modificar source, consultar literalmente como mínimo:

- el backlog aprobado `DEVPL-GSDLC-04_artifact_workbench_governed_authoring_and_import_v1_2_0_APPROVED.md`;
- la adjudicación `DEVPL_GSDLC_03_E_FINAL_OWNER_ADJUDICATION_v1_0_0.md`;
- la adjudicación `DEVPL_GSDLC_03_BACKLOG_CLOSURE_ADJUDICATION_v1_0_0.md`;
- el `DEVPL_GSDLC_03_FINAL_OWNER_CLOSURE_CURRENT.json` corregido;
- `.devpilot/project_state.json`;
- `.devpilot/docs_governance/source_registry.json`;
- `.devpilot/gsdlc/transversal_validation_policy.json`;
- `docs/02_architecture/governance/DEVPL_DOCUMENTATION_CONTRACT_RECONCILIATION_POLICY_v1_0_0_APPROVED.md`;
- `.devpilot/testing/test_contract_registry.json`;
- `.devpilot/testing/test_contract_registry_v2.json`;
- `.devpilot/interfaces/api_route_contract_registry.json`;
- `.devpilot/interfaces/ui_route_contract_registry.json`;
- `.devpilot/interfaces/ui_capability_registry.json`;
- `.devpilot/approval/sensitive_action_catalog.json`;
- `.devpilot/identity/server_rbac_policy_catalog.json`;
- `docs/schemas/schema_catalog.json`;
- `docs/validation/artifact_profiles.json`;
- `src/devpilot_core/validation/artifact_profile_registry.py`;
- `src/devpilot_core/application/workspace_edit_plan_service.py`;
- `src/devpilot_core/application/workspace_edit_execution_service.py`;
- `ui/web/src/pages/WorkspaceDocumentsView.ts`;
- `ui/web/src/components/DocumentEditPlanner.ts`;
- UOC-004/UOC-005 manifests/tests/reports y cualquier successor current que los haya evolucionado.

Si una fuente requerida no está disponible, **BLOCK antes de implementar**. No inferir contratos ausentes.


## Invariantes heredadas de GSDLC-03

1. Project Home es la superficie pre-proyecto.
2. Artifact Workbench es `project-scoped`: no debe quedar accesible como camino normal hasta que `Create/Open/Import` haya terminado PASS y exista project context.
3. `sessionStorage/localStorage` son únicamente UX state; nunca autoridad de sesión, rol, approval, hash, freeze o autorización de escritura.
4. Human session + Server RBAC + Policy + Approval server-side permanecen autoridad.
5. Approval handoff debe ser exact-id/targeted cuando corresponda; no convertir el listado global de approvals en precondición.
6. `auth.db*`, `devpilot.db*` y equivalentes son `runtime-ephemeral`; todo fixture/sandbox que copie `.devpilot` debe excluirlos.
7. No free-form shell ni comandos del usuario. Subprocess: argv nativo, `shell=False`.
8. Timeouts deben ser class-specific; una operación larga de validation/apply no puede heredar accidentalmente el timeout de request ordinario.
9. Evidencia browser/full sellada de GSDLC-03 no se edita ni reejecuta.


## 2. Resultado funcional

Implementar PASTE/UPLOAD/IMPORT de fuentes externas con provenance, hash original + normalized, preview/diff y promoción inicial únicamente a DRAFT.

## 3. Diseño e implementación

### Requisitos de implementación

- Upload allowlist inicialmente alineada con tipos documentales soportados; no ejecutables.
- Límites de tamaño server-side y client-side; el server manda.
- Filename/path canonicalization, basename policy, traversal/symlink/ADS/UNC/device-name negatives Windows.
- Encoding normalization determinística y hash tanto del original como del normalized content.
- Source label/URL/reference es metadata; **no realizar fetch de URL** en GSDLC-04.
- Secret detection/warning antes de apply; nunca imprimir secret values.
- Import siempre termina DRAFT; no authority escalation.
- Preview/diff antes de persist/promote.
- provenance visible en UI.
- 0 writes fuera del workspace autorizado.

### Inspección obligatoria antes de diseñar paths

La lista de paths anterior es orientativa. Antes de escribir:
- mapear implementaciones existentes;
- identificar servicio/registry/schema owner;
- identificar frozen snapshots y current-active successors;
- ejecutar Test Impact inicial;
- documentar por qué se extiende un componente o por qué, excepcionalmente, se crea uno nuevo.

No introducir una segunda fuente de verdad si ya existe una primitiva equivalente.

## 4. Seguridad y límites

- local-first;
- deny-by-default;
- auth/session/RBAC server-side;
- approval actor derivado de sesión;
- PathGuard + canonicalization;
- no arbitrary shell;
- no network silenciosa;
- no external API requerida;
- no secret values en source/log/evidence;
- no mutación del piloto real;
- toda mutación: `plan → dry-run → policy/RBAC → approval cuando aplique → execute → verify → evidence`;
- operaciones destructivas no forman parte del normal journey.

## Política transversal de validación

Autoridades:

- `.devpilot/gsdlc/transversal_validation_policy.json`;
- `DEVPL_DOCUMENTATION_CONTRACT_RECONCILIATION_POLICY_v1_0_0_APPROVED.md`.

Reglas:

1. GSDLC-04-A→D: focal + acumulativa + Test Impact; **full regression = NO por rutina**.
2. Cada micro-sprint ejecuta `historical_contract_sweep` y clasifica: `historical-freeze`, `current-active`, `successor-needed`, `deprecated-after-proof`, además de `derived` y `runtime-ephemeral`.
3. Antes de cerrar cada micro-sprint, reconciliar schemas, current registries, derived counters, RBAC/Approval/MIASI bindings, UI mappings, Source Registry, Project State, README/roadmap y TCR impactados.
4. Antes de la única full de 04-E ejecutar un `contract_reconciliation_sweep` determinístico. Si existe drift, corregirlo **antes** de consumir la full.
5. 04-E consume la **única full regression del backlog exactamente una vez**, después de browser acceptance.
6. Una full intermedia solo puede existir por hard trigger owner-approved; si ocurre, consume la corrida única y E no puede ejecutar una segunda.
7. Si la full falla: preservar log/JUnit/marker; no repetir; root-cause; exact failed-nodeid retest; bounded impacted retest; Historical Regression Guard; cierre solo con composite PASS.
8. Nunca modificar un snapshot histórico o evidencia sellada únicamente para obtener verde.


## 5. Pruebas y PASS/BLOCK

Tests mínimos:
- traversal, symlink, UNC/device/ADS;
- oversize;
- unsupported extension/MIME mismatch;
- malformed/unknown encoding;
- deterministic hashes;
- secret warning/redaction;
- import stays DRAFT;
- provenance UI/API parity;
- project-route/RBAC negatives;
- A→C cumulative + Test Impact + reconciliation;
- browser smoke paste/upload/import.

PASS-CANDIDATE:
- origen y hashes visibles;
- no path escape;
- no executable upload;
- no hidden network fetch;
- S0=0/S1=0;
- full=0.

BLOCK adicional:
- baseline/adjudicación predecessor no verificable;
- unexpected Git paths;
- frozen historical contract reescrito sin successor;
- runtime DB copiado a sandbox;
- UI concede authority que corresponde al server;
- operator necesita escribir artifacts por el usuario durante browser acceptance.

## 6. Git y successor esperado

Feature branch sugerida:

`feat/devpl-gsdlc-04-c-artifact-import`

Commit sugerido:

`feat(gsdlc-04-c): add governed paste and artifact import`

Nombre lógico esperado del candidate Windows:

`repo_DevPilot_Local_367_DEVPL_GSDLC_04_C_EXTERNAL_SOURCE_IMPORT_WINDOWS_VALIDATED_CANDIDATE.zip`

La numeración/nombre final debe validarse contra la secuencia real antes de empaquetar; el SHA/commit nunca se inventa en el prompt.

## Contrato obligatorio del operador/harness

Todo operador debe:

1. ser Python, state-aware, idempotente y reanudable;
2. dry-run por defecto;
3. no usar `reset --hard`, `git clean`, rebase automático ni force push;
4. subprocess con argv nativo, `shell=False`, timeouts y paths resueltos;
5. `git status --porcelain=v1 -z`;
6. distinguir gross touched surface de net diff;
7. usar Git blob como autoridad cuando LF/CRLF pueda variar;
8. generar checkpoint JSON después de cada gate;
9. conservar evidencia causal al bloquear;
10. no depender de semántica accidental de PowerShell;
11. no renombrar directorios temporales para materializar packages en Windows si puede usarse reemplazo archivo-a-archivo con retry acotado;
12. excluir `auth.db*`, `devpilot.db*` y stores runtime de sandboxes/fixtures;
13. excluir de ZIP final `.git`, `.venv`, `node_modules`, `outputs`, `.pytest_cache`, `__pycache__`, runtime DBs y secretos;
14. nunca acceder a `D:\Projects\DevPilot_Workspaces\inventory-sales-local` durante GSDLC-04.

Topología permitida:

```text
D:\Projects\DevPilot_Local
D:\Projects\DevPilot_E2E_Evaluation
D:\Projects\DevPilot_Artifacts\POST-H-EVAL-002
```

PowerShell de guías: una sola línea física por comando.


## Entregables mínimos del micro-sprint

1. package ZIP de implementación/validación;
2. operator Python + sidecar;
3. source delta exacto;
4. repo PRE-WINDOWS limpio;
5. guía única `.md` para personal no experto;
6. `SOURCE_DELTA_MANIFEST`;
7. `ARTIFACT_HASHES`;
8. `OPERATION_DECLARATION`;
9. `CURRENT`;
10. closure report;
11. `historical_contract_sweep`;
12. `contract_reconciliation_sweep`;
13. Test Impact;
14. evidencia Windows definida explícitamente;
15. candidate Windows + SHA tras PASS;
16. owner adjudication para habilitar el siguiente micro-sprint.

No declarar `CLOSED/PASS` antes de evidencia Windows + owner adjudication.


## 7. Condición de salida

- 04-C solo puede pasar a `CLOSED/PASS` después de evidencia Windows y owner adjudication.
- El siguiente micro-sprint no se implementa en este prompt.
- Si existe BLOCK, entregar diagnóstico y corrective mínimo; no continuar “para ganar tiempo”.
