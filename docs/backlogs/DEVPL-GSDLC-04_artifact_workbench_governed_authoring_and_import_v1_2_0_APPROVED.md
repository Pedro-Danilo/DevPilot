---
doc_id: "DEVPL-GSDLC-04"
title: "DEVPL-GSDLC-04 — Artifact Workbench, governed authoring and external-source import"
status: "approved"
version: "1.2.0"
owner: "Ordóñez"
updated: "2026-08-20"
approval: "approved_by_owner"
approved_at: "2026-08-20"
approval_decision: "APPROVE"
program_id: "DEVPL-GSDLC"
source_repo: "repo_DevPilot_Local_364_DEVPL_GSDLC_03_E_PROJECT_ENTRY_BROWSER_COMPOSITE_WINDOWS_VALIDATED_CANDIDATE.zip"
source_git_commit: "7f6c9ed8a49fd9300d8b10eb3255969256eb2865"
source_repo_sha256: "84879093ae88e46dd967adf0b5d857cf2912fc9c98f7d8173c59a485c008c8f2"
source_branch: "feat/devpl-gsdlc-03-e-project-entry-browser-closure"
predecessor_backlog: "DEVPL-GSDLC-03"
predecessor_micro_sprint_closure: "DEVPL_GSDLC_03_E_FINAL_OWNER_ADJUDICATION_v1_0_0.md"
predecessor_backlog_closure: "DEVPL_GSDLC_03_BACKLOG_CLOSURE_ADJUDICATION_v1_0_0.md"
historical_baseline_repo: "repo_DevPilot_Local_359_DEVPL_GSDLC_02_E_COMPOSITE_WINDOWS_VALIDATED_CANDIDATE.zip"
historical_baseline_commit: "98e4b2f3f033580bfdd5fc027bf5afcd632f8169"
historical_baseline_sha256: "bb155968cd10c35a320cdcee3af1f9db4cb64ebed4acbca773f24918c3d58995"
execution_source_policy: "fixed/owner-adjudicated-gsdlc-03-successor"
local_first: true
ui_complete_normal_journey: true
dry_run_default: true
backlog_id: "DEVPL-GSDLC-04"
backlog_status: "approved/executable-design"
micro_sprints_total: 5
validation_policy: "A-D cumulative-selective; E exactly-one-full-regression; no rerun after failure; composite recovery"
documentation_contract_policy: "DEVPL_DOCUMENTATION_CONTRACT_RECONCILIATION_POLICY_v1_0_0_APPROVED"
runtime_ephemeral_fixture_policy: "exclude auth.db*, devpilot.db* and equivalent runtime stores"
---

# 0. Aprobación, rebind y autoridad de ejecución

**Decisión owner:** `APPROVED / EXECUTABLE-DESIGN`.

GSDLC-04 se rebindea al successor owner-adjudicated de GSDLC-03:

```text
repo
repo_DevPilot_Local_364_DEVPL_GSDLC_03_E_PROJECT_ENTRY_BROWSER_COMPOSITE_WINDOWS_VALIDATED_CANDIDATE.zip

commit
7f6c9ed8a49fd9300d8b10eb3255969256eb2865

SHA-256
84879093ae88e46dd967adf0b5d857cf2912fc9c98f7d8173c59a485c008c8f2
```

Autoridades externas de cierre que deben incorporarse al repo **antes de cualquier cambio funcional de 04-A**:

- `DEVPL_GSDLC_03_E_FINAL_OWNER_ADJUDICATION_v1_0_0.md` — `CLOSED/PASS`;
- `DEVPL_GSDLC_03_BACKLOG_CLOSURE_ADJUDICATION_v1_0_0.md` — `CLOSED/PASS`, autoriza GSDLC-04;
- `DEVPL_GSDLC_03_FINAL_OWNER_CLOSURE_CURRENT.json` corregido a `owner_adjudication_pending=false`.

`repo_DevPilot_Local_359_DEVPL_GSDLC_02_E_COMPOSITE_WINDOWS_VALIDATED_CANDIDATE.zip` permanece como **baseline histórico de cierre de GSDLC-02 y ancestro de GSDLC-03**. Ya no es la fuente de ejecución de GSDLC-04 y no debe usarse para revertir capacidades GSDLC-03.

## 0.1 Invariantes heredadas de GSDLC-03

1. Project Home es la superficie pre-proyecto; las superficies project-scoped se habilitan solo después de `Create/Open/Import = PASS`.
2. Approval Center es contextual durante entry; el handoff exacto no depende de listar todos los approvals.
3. `sessionStorage/localStorage` son UX-only y nunca autoridad de autenticación, RBAC, approval o project binding server-side.
4. `auth.db*`, `devpilot.db*` y stores equivalentes son `runtime-ephemeral`; fixtures/sandboxes no pueden copiarlos como source state.
5. Mutaciones siguen `plan → dry-run → policy/RBAC → approval cuando aplique → execute → verify → evidence`; no arbitrary shell.
6. Timeouts se clasifican por operación; no se reutiliza accidentalmente el timeout corto de requests ordinarios para planning/validation/apply.
7. La evidencia browser/full histórica de GSDLC-03 permanece inmutable y no se reejecuta durante el rebind de GSDLC-04.

## 0.2 Activación de 04-A

04-A debe comenzar con un **activation rebind checkpoint** que:

- verifique commit/SHA de repo364;
- incorpore las adjudicaciones externas de 03-E/backlog 03;
- reconcilie Project State, Source Registry, README y roadmap a `GSDLC-03 CLOSED/PASS` + `GSDLC-04 authorized/active`;
- cree/seleccione la rama `feat/devpl-gsdlc-04-artifact-workbench`;
- ejecute solo validación administrativa/focal;
- bloquee antes de source funcional si existe drift.

Este checkpoint forma parte de 04-A y **no crea un sexto micro-sprint**.

## 0.3 Estado de ejecución acumulativo — 2026-08-20

- `GSDLC-04-A = CLOSED/PASS`; authority: `DEVPL_GSDLC_04_A_OWNER_ADJUDICATION_v1_0_0.md`.
- Successor autoritativo para 04-B: `repo_DevPilot_Local_365_DEVPL_GSDLC_04_A_ARTIFACT_LIFECYCLE_WINDOWS_VALIDATED_CANDIDATE.zip`, commit `6b6cb70eb16c94f4aa374fc74d9ff2f8f8b6c893`, SHA-256 `0359182b736d8cbb1f90ad92cf56fd02c7081fc357674597c02c2706fedb67a6`.
- `GSDLC-04-B = CLOSED/PASS`; owner adjudication `DEVPL_GSDLC_04_B_OWNER_ADJUDICATION_v1_0_0.md`; successor repo366 commit `b095bf5b75259c9c7c4a9a5c1b5d546cfe049d6f`, SHA-256 `3cfe97a376ee269b6c6fb3465e9549c2eea1e2160ecf5ff4848fd351a776ad92`.
- `GSDLC-04-C = IMPLEMENTED / READY-FOR-WINDOWS`; browser/evidencia Windows y owner adjudication permanecen pendientes.
- Full regression consumida en el backlog: `0`; sigue reservada a 04-E.


# DEVPL-GSDLC-04 — Artifact Workbench, governed authoring and external-source import

## 1. Objetivo

Transformar Workspace Documents en un workbench de creación/revisión de artefactos con editor, paste/upload/import, provenance, validación, approval, apply/freeze y detección de cambios externos.

## 2. Invariante de producto que esta ola debe demostrar

> Los documentos no llegan preinyectados por operadores: el usuario los crea, pega, adjunta o importa desde UI y DevPilot conserva origen, hash, lifecycle y decisiones.

Esta invariante es parte del criterio de cierre. No basta con que existan clases, endpoints o archivos: debe demostrarse el comportamiento de producto descrito.

## 3. Dependencias y precondiciones de entrada

- GSDLC-03 CLOSED/PASS

Si alguna precondición no puede verificarse de forma reproducible, el backlog entra en `BLOCK` antes de mutar source.

Precondición transversal adicional: debe existir un proyecto activo/server-validado proveniente del journey GSDLC-03 para toda superficie project-scoped; Settings/Account globales no sustituyen project context.

## 4. Alcance funcional y técnico

### 4.1 Incluido

- Markdown/JSON governed artifacts
- manual editor
- paste/upload files
- source provenance
- draft/version
- validate/findings/diff
- approval/apply/freeze
- external revalidation

### 4.2 Fuera de alcance

- arbitrary binary editor
- cloud document sync
- agent generation real

## 5. Superficies y fuentes que probablemente serán afectadas

- Workspace Documents
- UOC-005 document apply/rollback
- artifact profiles/validators

La lista es orientativa para Test Impact. Cada micro-sprint debe cerrar su manifest exacto antes de ejecutar cambios.

## 6. Micro-sprints secuenciales

### GSDLC-04-A — Artifact lifecycle, source and provenance contracts

**Objetivo.** Modelar estado, origen y lineage de cada artefacto gobernado.

**Entradas obligatorias**
- GSDLC-03 CLOSED/PASS
- Artifact Profiles existentes

**Actividades**
1. Definir lifecycle MISSING→DRAFT→VALIDATING→FINDINGS→READY_FOR_REVIEW→APPROVAL_REQUIRED→APPROVED→FROZEN→REVALIDATION_REQUIRED.
2. Definir source types MANUAL, PASTE, UPLOAD, IMPORT, AGENT_ASSISTED y EXTERNAL_EDITOR.
3. Registrar hash, version, base commit, author actor, reviewer y provenance.
4. Definir qué perfiles permiten edición/importación y qué validadores aplican.
5. Definir transition ownership por rol.

**Entregables verificables**
- ArtifactState schema
- ArtifactProvenance schema
- ArtifactLifecycleService

**Pruebas / validadores**
- transition matrix
- illegal transition negative
- hash/provenance fixtures
- role transition matrix

**Evidencia mínima**
- artifact_lifecycle_contract_report.json

**Seguridad operacional específica**
- upload filename/path sanitization
- size/type limits
- no secret-bearing file auto-version

**PASS**
- todo artefacto tiene state+provenance
- FROZEN no es editable sin revalidation

**BLOCK**
- unknown source accepted silently
- actor/reviewer missing
- invalid transition allowed

**Salida / autorización**
- autoriza GSDLC-04-B


### GSDLC-04-B — Manual editor, draft persistence and version history

**Objetivo.** Permitir escribir directamente documentos Markdown/JSON desde la UI sin tocar filesystem manualmente.

**Entradas obligatorias**
- GSDLC-04-A PASS

**Actividades**
1. Implementar editor Markdown/JSON con preview y schema-aware hints.
2. Persistir draft separado del artefacto aprobado.
3. Implementar autosave, version history, discard/recover draft y conflict banner.
4. Aplicar optimistic concurrency mediante preimage hash.
5. Mantener provenance MANUAL y actor/session.

**Entregables verificables**
- ArtifactEditor
- DraftStore
- VersionHistoryView

**Pruebas / validadores**
- editor unit
- autosave/restart
- concurrent edit
- draft recovery

**Evidencia mínima**
- draft_lifecycle_report.json
- editor browser smoke

**Seguridad operacional específica**
- sanitize rendered Markdown/HTML
- draft no ejecutable como evidence
- no overwrite approved source

**PASS**
- manual authoring usable end-to-end
- draft survives restart
- concurrent lost update blocked

**BLOCK**
- draft overwrites source aprobado
- XSS
- hash preimage ignored

**Salida / autorización**
- autoriza GSDLC-04-C


### GSDLC-04-C — Paste, upload and external-source import

**Objetivo.** Permitir copiar o adjuntar fuentes externas con provenance y sin convertirlas en autoridad implícita.

**Entradas obligatorias**
- GSDLC-04-B PASS

**Actividades**
1. Implementar paste text y captura opcional de source label/URL/reference.
2. Implementar upload de tipos allowlisted con size bounds.
3. Normalizar encoding y crear hash del original y del contenido importado.
4. Convertir import a DRAFT y mostrar preview/diff.
5. Registrar source provenance para auditoría.

**Entregables verificables**
- ImportService
- upload/paste UI
- ArtifactProvenancePanel

**Pruebas / validadores**
- path traversal
- oversize
- unsupported extension
- encoding
- hash reproducibility

**Evidencia mínima**
- import_manifest.json
- redaction_scan.json

**Seguridad operacional específica**
- no executable uploads
- path sandbox
- secret detection/warning before apply

**PASS**
- import permanece DRAFT
- origen y hash visibles
- 0 writes fuera del workspace

**BLOCK**
- upload ejecutable aceptado
- provenance perdido
- path escape

**Salida / autorización**
- autoriza GSDLC-04-D


### GSDLC-04-D — Validate, findings, diff, approval, apply and freeze

**Objetivo.** Unificar revisión y promoción de artefactos.

**Entradas obligatorias**
- GSDLC-04-C PASS
- RBAC/approval auth

**Actividades**
1. Ejecutar validators pertinentes desde el workbench.
2. Navegar findings a sección/línea del editor.
3. Construir immutable change plan y diff.
4. Solicitar approval según rol/risk.
5. Revalidar hash antes de atomic apply; rollback on failure.
6. Freeze approved hash y emitir transition evidence.

**Entregables verificables**
- ArtifactReviewFlow
- FindingNavigator
- ArtifactApplyPlan
- freeze evidence

**Pruebas / validadores**
- validator integration
- wrong-role approval
- stale preimage
- fault rollback
- finding navigation

**Evidencia mínima**
- validation_report
- approval_record
- apply_manifest
- freeze_record

**Seguridad operacional específica**
- write only declared artifact
- backup preimage
- no approval reuse after content drift

**PASS**
- APPROVED/FROZEN solo con gates+approval
- rollback leaves clean state

**BLOCK**
- approval bypass
- stale content applied
- partial write

**Salida / autorización**
- autoriza GSDLC-04-E


### GSDLC-04-E — External edit reconciliation and browser closure

**Objetivo.** Demostrar convivencia segura con VS Code/Git y cerrar manual/import authoring.

**Entradas obligatorias**
- GSDLC-04-D PASS

**Actividades**
1. Detectar edit/rename/delete externo.
2. Mover APPROVED/FROZEN a REVALIDATION_REQUIRED cuando hash cambia.
3. Mostrar Git diff y source provenance en UI.
4. Ejecutar browser flows manual y import hasta aprobación.
5. Validar accesibilidad, errores y recovery.

**Entregables verificables**
- ArtifactReconciliationUX
- browser acceptance report

**Pruebas / validadores**
- external edit fixtures
- branch switch
- browser manual/import
- accessibility

**Evidencia mínima**
- revalidation screenshots
- state/file/Git parity matrix

**Seguridad operacional específica**
- never auto-revert external edits
- no hidden merge
- stale approval invalidated

**Cierre de regresión obligatorio**
- ejecutar gates baratos + Contract Reconciliation Sweep + browser/capability acceptance;
- consumir la única full regression del backlog exactamente una vez, salvo que un hard-trigger anterior ya haya consumido esa corrida;
- ante FAIL no repetir full: aplicar recuperación compuesta selectiva y Historical Regression Guard.

**PASS**
- manual+import routes UI-complete
- external drift detected
- S0/S1=0

**BLOCK**
- approved artifact remains approved after changed hash
- UI hides drift

**Salida / autorización**
- CLOSED/PASS
- autoriza GSDLC-05



## 6.1 Estado de ejecución acumulativo (2026-08-21)

Esta sección es `current-active` y no modifica los criterios históricos aprobados de los micro-sprints:

- `GSDLC-04-A = CLOSED/PASS`.
- `GSDLC-04-B = CLOSED/PASS`; owner adjudication `DEVPL_GSDLC_04_B_OWNER_ADJUDICATION_v1_0_0.md`; successor repo366 commit `b095bf5b75259c9c7c4a9a5c1b5d546cfe049d6f`.
- `GSDLC-04-C = IMPLEMENTED / READY-FOR-WINDOWS`; PASTE/UPLOAD/IMPORT permanece DRAFT, provenance/hashes visibles, source write deshabilitado, full regression `0`.
- `GSDLC-04-D = BLOCKED-BY-SEQUENCE` hasta owner adjudication CLOSED/PASS de 04-C.

## 7. Alcance transversal específico de esta ola

- Artifact Explorer queda como navegación de apoyo; el flujo primario es create/review/advance.
- Cada artefacto declara source: manual, paste, upload/import, external editor o agent-assisted posterior.

## 8. Política de contratos históricos específica

- UOC-001/002 `write_enabled=false` es histórico y acotado; no convertirlo en assertion global post-GSDLC.
- Reutilizar atomic document apply/rollback de UOC-005, evitando segundo motor.

Antes del cierre de **cada** micro-sprint se debe generar un `historical_contract_sweep` que clasifique los tests/contratos impactados como:

1. `historical-freeze`: valida únicamente el hecho histórico;
2. `current-active`: debe evolucionar con la capacidad vigente;
3. `successor-needed`: requiere nuevo contrato sin reescribir el anterior;
4. `deprecated-after-proof`: solo puede retirarse después de demostrar reemplazo equivalente.

No se permite modificar una aserción histórica únicamente para “hacer pasar pytest”; la modificación debe quedar justificada por esta clasificación.

### Contract Reconciliation Sweep obligatorio

La política `docs/02_architecture/governance/DEVPL_DOCUMENTATION_CONTRACT_RECONCILIATION_POLICY_v1_0_0_APPROVED.md`, materializada durante GSDLC-03-E, es transversal para esta ola.

Además del `historical_contract_sweep` de cada micro-sprint, antes de la full regression de cierre debe ejecutarse un `contract_reconciliation_sweep` que bloquee si detecta cualquiera de estas condiciones:

1. schema estricto inválido o metadata `current-active` contradictoria;
2. summary/counter/registry derivado desincronizado de su colección viva;
3. sensitive action sin RBAC/approval/MIASI/tool binding cuando aplique;
4. UI route/capability sin mapping current correspondiente;
5. `source_registry`, Project State, README, roadmap o CURRENT en estados incompatibles;
6. test histórico consultando un `current-active` mutable cuando existe snapshot `*_at_close`;
7. reutilización de un puntero histórico por otra ola;
8. fixture/sandbox que copie stores `runtime-ephemeral`, incluidos `auth.db*`, `devpilot.db*` o equivalentes;
9. evidencia sellada reescrita después de calcular su hash;
10. contrato successor agregado sin actualizar el historial/registry que deba reconocerlo.

La clasificación mínima continúa siendo `historical-freeze`, `current-active`, `successor-needed` y `deprecated-after-proof`; se añade la distinción explícita `derived` y `runtime-ephemeral`.

**Regla:** corregir drift determinista antes de consumir la única full regression del backlog.

## 9. Seguridad operacional específica

- Path traversal, XSS, upload abuse, secret leakage, stale approval y concurrent overwrite son riesgos principales.

Toda acción mutante debe seguir `plan → dry-run → policy/RBAC → approval cuando aplique → execute → verify → evidence`. Cualquier excepción requiere ADR o backlog correctivo separado.

## 10. Estrategia de pruebas de la ola

- artifact lifecycle
- import negative suite
- validator integration
- approval/apply rollback
- external edit
- browser

Regla de regresión:

- A→D usan Test Impact, pruebas focales, acumulativas y validadores determinísticos; **full regression = NO por rutina**.
- El micro-sprint E ejecuta la **única full regression del backlog exactamente una vez**, después de gates baratos, Contract Reconciliation Sweep y browser/capability acceptance pertinente.
- Una full intermedia solo puede ocurrir por hard trigger de riesgo explícito, owner-approved y documentado; si ocurre, **consume la única corrida full permitida** y E debe cerrar mediante evidencia compuesta sin lanzar otra.
- Si la full falla: preservar log/JUnit/marker inmutables, prohibir rerun, diagnosticar causa, ejecutar exact failed-nodeid retest + bounded impacted retest + Historical Regression Guard y cerrar solo con `composite-full-regression-selective-retest = PASS`.
- Browser acceptance se ejecuta únicamente cuando el micro-sprint introduce/cierra UX; no se repite por correctives que no cambian comportamiento browser demostrado.

## 11. Evidencia autoritativa esperada

- provenance manifests
- validation reports
- approval/apply evidence
- browser screenshots

Además, cada micro-sprint debe conservar:

- manifest de source delta;
- identidad Git pre/post;
- resultados PASS/BLOCK machine-readable;
- lista de S0/S1;
- browser screenshots cuando corresponda;
- hashes de artefactos empaquetados;
- declaración explícita `network_used`, `external_api_used`, `secrets_exposed`, `mutations_performed`.

## 12. Definition of Done del backlog

- manual/import authoring complete
- governed write
- revalidation
- S0/S1=0

El backlog solo puede adjudicarse `CLOSED/PASS` si todos los micro-sprints A→E han cerrado en secuencia y no quedan S0/S1 abiertos.

## 13. Criterio de autorización del siguiente backlog

- GSDLC-05 solo si un artefacto puede recorrer lifecycle completo sin CLI.

Un `PASS-WITH-GAPS` solo puede autorizar el siguiente backlog cuando los gaps estén clasificados S2/S3, tengan owner, evidencia y no invaliden la invariante de producto de esta ola.

