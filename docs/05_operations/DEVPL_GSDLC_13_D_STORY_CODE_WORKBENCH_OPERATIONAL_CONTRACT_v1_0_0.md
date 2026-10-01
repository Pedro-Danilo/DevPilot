---
doc_id: "DEVPL-GSDLC-13-D-STORY-CODE-WORKBENCH-OPERATIONAL-CONTRACT"
title: "DEVPL-GSDLC-13-D — Story Code Workbench operational contract"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-09-30"
route: "http://127.0.0.1:5173/story/code"
full_regression_runs_allowed: 0
---

# Story Code Workbench — contrato operacional 13-D

## 1. Propósito de la superficie

`Story Code Workbench` es la superficie donde una Story ya seleccionada por Planning se convierte en
trabajo de implementación gobernado. No debe pedir al Owner que reconstruya a mano el contexto técnico,
ni asumir que entrar a la URL equivale a tener una Story activa.

Su frontera inicia con Planning ya aprobado/FROZEN y termina, a través de los checkpoints 13-D-01..04,
con la Story `DONE` y un commit gobernado. Los checkpoints D05–D08 reutilizan después el ciclo para las
Stories siguientes, recovery y release.

## 2. Autoridad de entrada

Story Code debe consumir, sin mutarlos:

- Project Context server-valid;
- SprintPlan FROZEN;
- Backlog/Stories congeladas dentro de la autoridad Planning;
- readiness y blocking reasons de las selected Stories;
- Definition of Ready/Done del Sprint;
- trace links de requirements/ADR/risk/test-intent;
- Pre-code artifacts ya aprobados.

Planning no debe reabrirse ni reescribirse para iniciar una Story.

## 3. Fase A — Activación y contexto (`13-D-01`)

### 3.1 Descubrir la Story ejecutable

La superficie debe mostrar las Stories del Sprint que siguen siendo `READY` y no están completadas.
Debe diferenciar claramente:

- Story ID;
- título;
- readiness;
- blockers si los hubiera;
- acceptance criteria;
- orden/recomendación del Sprint.

Una Story `DONE` no debe reaparecer como candidata.

**Producto:** `StoryActivation projection` con `ready_candidates` y `recommended_story_id`.

### 3.2 Preparar, no iniciar implícitamente

Al pulsar `Preparar contexto`, el backend debe reutilizar el motor de StoryExecution y ejecutar:

1. resolver la Story seleccionada contra Sprint/Backlog FROZEN;
2. evaluar Definition of Ready;
3. resolver requirement, ADR, risk y test-intent contra sus fuentes aprobadas;
4. construir StoryContextPack mínimo y determinístico;
5. persistir únicamente runtime authority/evidence;
6. crear `StoryExecution` en `PLANNED`.

No debe escribir source ni modificar Planning.

**Productos:** `StoryDoRReport`, `StoryContextPack`, `StoryExecutionState(PLANNED)` y hashes/provenance.

### 3.3 Qué debe poder revisar el Owner

Antes de iniciar, Story Code debe mostrar suficientemente:

- Story ID/título/versión;
- acceptance criteria;
- resultado DoR y checks;
- requirement fragments;
- ADR/architecture constraints;
- security/risk fragments;
- test-intent fragments;
- ContextPack ID/hash;
- StoryExecution ID/state hash;
- provenance/source references;
- safety: Planning no mutado, source no mutado.

No se exige que todo esté en una sola tarjeta, pero debe ser descubrible desde la superficie normal.

### 3.4 Iniciar Story

`Iniciar story preparada` debe exigir el `state_sha256` exacto del estado `PLANNED` y producir
`StoryExecution(IN_PROGRESS)`. La transición es Owner/Developer humana y hash-bound.

**Producto:** nuevo `StoryExecutionState` `IN_PROGRESS`, con trace/audit de la transición.

### 3.5 Ruta de implementación

D01 debe mostrar la policy de implementación:

- **Manual:** first-class; el Owner puede crear/editar un runtime draft sin modelo.
- **Agent-assisted mock/fake-local:** proposal-only; puede proponer contenido, nunca escribir source.
- Real local model: no requisito para Pilot A.
- External API: no requisito para Pilot A.

Si se muestra provider/model/access route, su provenance debe ser visible. Seleccionar una ruta de modelo
no concede authority para tools, source mutation, apply, approval, Git o release.

**Producto:** `implementation_route`/provenance visible y bounded.

### 3.6 Stop de D01

D01 termina con Story `IN_PROGRESS`, contexto revisado y route comprendida. Todavía **no** debe existir
SourceChangePlan de D02.

## 4. Fase B — Draft y SourceChangePlan (`13-D-02`)

Una vez IN_PROGRESS, el Source tree/editor puede trabajar con `SourceDraftBuffer` runtime-only.
En greenfield puede ser normal que aún no exista un source allowlisted; en ese caso `CREATE` debe permitir
proponer el primer archivo sin escribirlo directamente.

### 4.1 Draft

- `EDIT`: ligado a source ID/preimage hash.
- `CREATE`: target path validado por policy.
- `RENAME`: bounded y preimage-bound.

Guardar un draft no cambia el source tree.

**Producto:** `SourceDraftBuffer` revisionado/hash-bound.

### 4.2 Change Plan

DevPilot deriva un `SourceChangePlan` immutable con:

- plan ID/hash;
- exact path allowlist;
- full diff;
- source/draft preimages;
- risk;
- Test Impact preview;
- required approval role.

### 4.3 Diff, dry-run y approval

El Owner debe revisar full diff y revalidar preimages. La approval queda ligada al plan/hash exactos.
Cambiar draft/plan/preimage invalida la autoridad anterior.

### 4.4 Atomic apply

Solo el plan aprobado puede materializarse. El apply debe ser exact-path, atomic y emitir manifest/receipt.
No hay operator project writes.

**Productos D02:** SourceDraftBuffer, SourceChangePlan, Diff, dry-run/recheck, Approval, ApplyManifest.

## 5. Fase C — Tests, remediation y Quality (`13-D-03`)

Después de apply:

1. Test Impact v2 deriva impacto desde paths/contratos;
2. StoryTestPlan determina required/recommended tests;
3. jobs tipados ejecutan la validación focal;
4. findings se muestran con evidencia;
5. si falla, remediation crea un nuevo ciclo proposal/review/apply/retest bounded;
6. Quality Gate decide si se alcanza `COMMIT_READY`.

Full Regression es solo señal informativa en 13-D y `execution_authorized=false`.

**Productos D03:** TestImpactReport, StoryTestPlan, ValidationJob results, remediation evidence si aplica,
QualityReport/COMMIT_READY.

## 6. Fase D — Git gobernado (`13-D-04`)

Con Quality COMMIT_READY:

1. DevPilot deriva `CommitPlan` con exact dirty-path set;
2. Owner otorga stage approval;
3. exact-path stage;
4. staged recheck;
5. Owner otorga commit approval independiente;
6. DevPilot crea commit y GitCommitRecord/trace;
7. Story pasa `DONE`;
8. Project Status vuelve a mostrar next valid action.

`git add .`, push automático, force push, auto-rebase y reset-hard no son sustitutos válidos.

**Productos D04:** CommitPlan, StageApproval, staging receipt, staged recheck, CommitApproval,
GitCommitRecord, StoryExecution(DONE).

## 7. Repetición (`13-D-05`)

Una Story DONE debe quedar archivada como runtime evidence y excluida de `ready_candidates`.
La siguiente Story READY debe poder recorrer otra vez:

`READY → DoR → ContextPack → PLANNED → IN_PROGRESS → D02 → D03 → D04 → DONE`.

No se permite sembrar StoryExecution desde operador para demostrar repetibilidad.

## 8. Productos persistentes y su authority

| Producto | Authority | Mutación de source |
|---|---|---|
| StoryActivation projection | runtime/read-only | no |
| StoryDoRReport | runtime evidence | no |
| StoryContextPack | runtime evidence | no |
| StoryExecutionState | runtime authority | no |
| Implementation route/provenance | runtime/read-only | no |
| SourceDraftBuffer | runtime draft | no |
| SourceChangePlan | runtime immutable plan | no |
| Approval | approval authority | no |
| ApplyManifest | execution evidence | sí, solo apply aprobado |
| TestImpact/StoryTestPlan | quality authority/evidence | no |
| Validation jobs/results | evidence | no salvo outputs autorizados |
| QualityReport | quality authority | no |
| CommitPlan/approvals | Git authority | no por sí mismos |
| GitCommitRecord | Git evidence | commit gobernado |

## 9. Lo que Story Code no debe hacer

- inventar Stories fuera del Sprint FROZEN;
- reabrir Planning para activar una Story;
- iniciar automáticamente una Story al cargar la página;
- escribir source al preparar contexto;
- ocultar DoR/context/provenance al Owner;
- dar authority a un modelo por seleccionar provider/model;
- crear plan/apply/commit sin approval humana exacta;
- ejecutar Full Regression dentro de 13-D;
- pedir terminal al usuario normal para materializar una Story.

## 10. Criterio específico de D01

D01 PASS exige demostrar por navegador normal, como mínimo:

`Project Status → Planning FROZEN → Story Code → READY candidate → Prepare context → DoR PASS → ContextPack visible → PLANNED → Start → IN_PROGRESS → route/provenance visible → STOP antes de D02`.
