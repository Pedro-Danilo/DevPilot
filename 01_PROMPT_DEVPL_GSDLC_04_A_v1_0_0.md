---
doc_id: "DEVPL-PROMPT-GSDLC-04-A"
prompt_number: "01"
title: "Prompt operativo — DEVPL-GSDLC-04-A — Artifact lifecycle, source and provenance contracts"
status: "ready_for_execution"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-08-20"
approval: "owner_approved_backlog_scope"
program_id: "DEVPL-GSDLC"
backlog_id: "DEVPL-GSDLC-04"
micro_sprint: "DEVPL-GSDLC-04-A"
execution_rule: "solo 04-A; successor bloqueado hasta owner adjudication CLOSED/PASS"
source_authority_mode: "fixed-owner-adjudicated-gsdlc03-successor"
local_first: true
dry_run_default: true
pilot_workspace_access_allowed: false
full_regression_allowed: false
---

# Prompt operativo — DEVPL-GSDLC-04-A

## 1. Mandato

Implementa **solo** `GSDLC-04-A — Artifact lifecycle, source and provenance contracts`.

Fuente de ejecución fija:
- repo: `repo_DevPilot_Local_364_DEVPL_GSDLC_03_E_PROJECT_ENTRY_BROWSER_COMPOSITE_WINDOWS_VALIDATED_CANDIDATE.zip`
- commit: `7f6c9ed8a49fd9300d8b10eb3255969256eb2865`
- SHA-256: `84879093ae88e46dd967adf0b5d857cf2912fc9c98f7d8173c59a485c008c8f2`

`repo_DevPilot_Local_359_DEVPL_GSDLC_02_E_COMPOSITE_WINDOWS_VALIDATED_CANDIDATE.zip` (`bb155968cd10c35a320cdcee3af1f9db4cb64ebed4acbca773f24918c3d58995`) es contexto histórico GSDLC-02, **no baseline mutable**.

### Checkpoint A0 — activation rebind obligatorio

Antes de source funcional:
1. verificar repo364/commit/SHA;
2. validar las dos adjudicaciones GSDLC-03;
3. corregir/consumir `DEVPL_GSDLC_03_FINAL_OWNER_CLOSURE_CURRENT.json` con `owner_adjudication_pending=false`;
4. incorporar al repo las adjudicaciones externas de 03-E y backlog 03;
5. reconciliar Project State/Source Registry/README/roadmap a:
   - GSDLC-03 = CLOSED/PASS;
   - GSDLC-04 = authorized/active;
   - current micro-sprint = GSDLC-04-A;
6. crear/seleccionar `feat/devpl-gsdlc-04-artifact-workbench` o la branch A derivada;
7. ejecutar Project State + Docs Governance + TCR + source-registry checks;
8. BLOCK antes de funcionalidad si existe cualquier contradicción.

El checkpoint A0 no es un sexto micro-sprint y no ejecuta full regression.

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

Modelar un lifecycle gobernado de artefactos y su provenance reutilizando las primitivas existentes, sin crear un segundo motor de escritura.

Implementar contratos/versiones para:
- `ArtifactState`: MISSING → DRAFT → VALIDATING → FINDINGS → READY_FOR_REVIEW → APPROVAL_REQUIRED → APPROVED → FROZEN → REVALIDATION_REQUIRED;
- `ArtifactSourceType`: MANUAL, PASTE, UPLOAD, IMPORT, AGENT_ASSISTED, EXTERNAL_EDITOR;
- provenance: source hash, normalized hash, artifact version, base commit, actor/session principal, reviewer, created/updated timestamps y lineage;
- transition ownership por rol;
- profile-specific authoring/import permissions.

## 3. Diseño e implementación

### Decisiones arquitectónicas obligatorias

- `ArtifactProfileRegistry` y `docs/validation/artifact_profiles.json` son inputs; no duplicar profile truth.
- UOC-004 `WorkspaceEditPlanApplicationService` y UOC-005 `WorkspaceEditExecutionApplicationService` son predecessors de planning/apply; evaluar extensión/composición antes de crear servicios paralelos.
- El lifecycle debe ser server-authoritative. UI state/localStorage no puede promover estados.
- DRAFT no es evidence ni source aprobado.
- FROZEN no es mutable; hash drift produce `REVALIDATION_REQUIRED`.
- AGENT_ASSISTED se modela ahora como provenance type, pero ejecución agentic real permanece fuera de alcance hasta GSDLC-07.
- Upload/path policy debe existir aunque upload real llegue en 04-C.
- No habilitar writes genéricos en 04-A salvo metadata/control estrictamente necesaria.

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
- schema positive/negative;
- legal transition matrix completa;
- illegal transition negative;
- role/actor/reviewer transition matrix;
- deterministic hashing y normalization;
- provenance roundtrip;
- frozen→mutation negative;
- external hash drift→REVALIDATION_REQUIRED;
- unknown source type deny;
- Source Registry/schema catalog/API/UI/TCR/Project State;
- histórico UOC-004/UOC-005 y GSDLC-03 impacted contracts;
- Test Impact analyze/dry-run.

PASS-CANDIDATE:
- lifecycle determinístico;
- provenance completa;
- ninguna transición sensible depende del browser;
- ningún runtime DB entra en fixtures;
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

`feat/devpl-gsdlc-04-a-artifact-lifecycle`

Commit sugerido:

`feat(gsdlc-04-a): define governed artifact lifecycle`

Nombre lógico esperado del candidate Windows:

`repo_DevPilot_Local_365_DEVPL_GSDLC_04_A_ARTIFACT_LIFECYCLE_WINDOWS_VALIDATED_CANDIDATE.zip`

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

- 04-A solo puede pasar a `CLOSED/PASS` después de evidencia Windows y owner adjudication.
- El siguiente micro-sprint no se implementa en este prompt.
- Si existe BLOCK, entregar diagnóstico y corrective mínimo; no continuar “para ganar tiempo”.
