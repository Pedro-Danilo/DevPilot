---
doc_id: "SPRINT-DEVPL-GSDLC-13-D"
title: "DEVPL-GSDLC-13-D — Coding, quality, Git, release and recovery acceptance — audit-aligned successor"
status: "approved"
version: "1.2.0"
owner: "Ordóñez"
updated: "2026-09-30"
approval: "approved_by_owner_for_pre13d"
supersedes_on_approval: "SPRINT_DEVPL_GSDLC_13_D_v1_1_0_APPROVED.md"
precondition: "DEVPL-GSDLC-13-C/PASS + PRE-13D authority preflight"
authority_commit_at_audit: "bb06260ce94298bf1e9dbb798e057d7ad07ea459"
full_policy: "0"
execution_mode: "OWNER-DRIVEN/DEVPL-EXECUTED/CHATGPT-ADJUDICATED"
journey_steps: "18-38; UX-P1 step 33 cross-cutting"
audit_input: "DEVPL_IMPLEMENTATION_RELEASE_CAPABILITY_AUDIT_PRE_13D_v1_0_0.md"
---

# DEVPL-GSDLC-13-D — Coding/quality/Git/release/recovery

> **Status de este documento:** APPROVED / audit-aligned successor. Sustituye al v1.1.0 para la ejecución de 13-D; el v1.1.0 se conserva como histórico.

## 0. Pre-13D authority preflight

Antes de emitir/adjudicar D01:

- DevPilot execution authority debe identificarse por repo/commit/SHA;
- Project Context del Pilot A debe estar server-valid;
- cualquier `current_repo/current_micro_sprint` stale que pueda ser tratado como authority current
  debe reconciliarse o declararse formalmente no autoritativo;
- no se precrea StoryExecution por operador;
- Pilot A permanece deterministic/pre-multiprovider;
- Full Regression = 0.

## 1. Execution rules

- Owner-driven / DevPilot-executed / ChatGPT-adjudicated.
- 13-D es **acceptance/reuse-first**, no reimplementation de GSDLC-09/10/11/12.
- Owner opera UI y toma decisiones legítimas.
- ChatGPT no escribe project content/código para copy/paste.
- operator puede start/stop/audit/capture, pero `operator_project_writes=0`.
- audit terminal y normal-user terminal escape se registran separados.
- no destructive Git.
- external API no requerida.
- mock/no-API y manual son rutas válidas del Pilot A.
- real local/external model no es requisito.
- corrective únicamente ante defecto real y después de preservar first-attempt.
- selective retest reanuda exact checkpoint.
- D01–D08: **Full Regression prohibida por policy de este sprint**.

## 2. Checkpoints audit-aligned

### `13-D-01` — pasos 18–19

**Misión:**
demostrar el bridge normal entre Sprint FROZEN/READY y una StoryExecution activa.

Debe probar:

1. Project Status/Planning indica la story/sprint ejecutable.
2. Owner llega a Story Code por UI normal.
3. Sin operador seed, DevPilot puede:
   - seleccionar/identificar la first READY story;
   - evaluar DoR;
   - crear StoryContextPack;
   - crear StoryExecution PLANNED;
   - iniciar IN_PROGRESS mediante acción normal.
4. Contexto es suficientemente reviewable:
   - story/objective/AC;
   - requirements/architecture/constraints/test intent;
   - source refs/provenance/hash.
5. Ruta:
   - Manual first-class;
   - agent-assisted mock/fake-local opcional;
   - provider/model/route/provenance si aplica;
   - model route nunca concede tool/source authority.

**BLOCK inmediato:**
`no active story` + no UI action normal para materializar/iniciar StoryExecution.

### `13-D-02` — pasos 20–24

Change Plan → Diff → Dry-run → Approval → Apply.

Evidence mínima adicional:

- draft/runtime-only;
- source/draft preimage;
- plan ID/hash;
- exact path allowlist;
- full diff;
- risk;
- Test Impact preview;
- approval ID exacto;
- preimage recheck;
- apply manifest;
- unexpected paths = 0.

### `13-D-03` — pasos 25–27

Test Impact v2 → StoryTestPlan → targeted typed validation jobs → remediation → Quality Gate.

Invariantes:

- no second Test Impact engine;
- no arbitrary shell;
- required/recommended tests explicables;
- Full signal = informativo;
- `execution_authorized=false`;
- Full runs = 0;
- remediation no self-apply;
- retest successor/targeted.

### `13-D-04` — pasos 28–30

Git flow exacto:

```text
Quality COMMIT_READY
→ CommitPlan
→ stage approval
→ exact-path stage
→ staged recheck
→ commit approval
→ governed commit
→ GitCommitRecord
→ Story DONE
→ Project Status
```

Prohibido:

- `git add .`;
- push;
- force push;
- rebase automático;
- reset-hard;
- operator Git mutation para completar el story.

### `13-D-05` — paso 31

Repetir hasta MVP.

Además de repetir D01–D04, demostrar explícitamente:

`Story DONE → Project Status → next READY story/sprint → nueva StoryExecution`.

No basta con volver a Planning si la siguiente story no puede activarse normalmente.

### `13-D-06` — paso 32

Controlled recovery:

- restart/new session;
- interrupted safe work;
- external edit;
- dirty worktree;
- branch/divergence/conflict;
- stale lock.

Recovery:

- no destructive Git;
- no silent overwrite;
- preserve drafts/evidence;
- explicit REVALIDATE/REPLAN/MANUAL_RECONCILIATION cuando corresponda;
- controlled/reversible scenarios only.

### `13-D-07` — pasos 34–35

Release Readiness debe ser READY/fail-closed.

Luego:

1. package plan/execute;
2. exact commit/tree binding;
3. checksum;
4. SBOM baseline + schema;
5. reproducibility;
6. version decision;
7. release notes;
8. exact-commit TagPlan dry-run;
9. owner/release-manager release approval;
10. annotated **local** tag;
11. tag verification.

No push/publish/deploy.

### `13-D-08` — pasos 36–38

En controlled local/disposable sandbox:

1. clean install;
2. install smoke;
3. upgrade plan con backup;
4. controlled upgrade;
5. rollback;
6. restore/hash parity;
7. production data untouched;
8. release graph READY_TO_FINALIZE;
9. final local release.

`local release` no significa public distribution/deployment/signing.

## 3. UX-P1

Paso 33 se observa en todos los checkpoints.

Aesthetics/copy = OBSERVE_ONLY salvo impacto real.
Defecto reproducible que impide normal journey = ACTIVE-CORRECTIVE.

## 4. PASS sprint

PASS solo si:

- MVP local reproducible;
- first/next story activation funcionan por normal UI;
- context reviewable/provenanced;
- Change Plan/apply governed;
- targeted tests/Quality;
- exact governed Git commits;
- repeat loop until MVP;
- recovery controlado;
- package/checksum/SBOM;
- metadata/tag local;
- clean install/rollback;
- local release graph/finalization;
- operator project writes=0;
- normal-user terminal escapes=0;
- Full Regression=0;
- S0/S1=0.
