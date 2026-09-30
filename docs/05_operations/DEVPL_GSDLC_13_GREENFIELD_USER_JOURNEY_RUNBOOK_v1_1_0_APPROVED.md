---
doc_id: "DEVPL-GSDLC-13-GREENFIELD-USER-JOURNEY-RUNBOOK"
title: "DEVPL-GSDLC-13 — Greenfield user journey runbook — 13-D audit-aligned successor"
status: "approved"
version: "1.1.0"
owner: "Ordóñez"
updated: "2026-09-30"
approval: "approved_by_owner_for_pre13d"
supersedes_on_approval: "02_DEVPL_GSDLC_13_GREENFIELD_USER_JOURNEY_RUNBOOK_v1_0_0_APPROVED.md"
source_user_journey: "Cómo se desarrollaría una app con DevPilot.docx"
project_workspace: 'D:\Projects\DevPilot_Workspaces\inventory-sales-local-greenfield'
audit_input: "DEVPL_IMPLEMENTATION_RELEASE_CAPABILITY_AUDIT_PRE_13D_v1_0_0.md"
---

# Greenfield user journey runbook

Este successor conserva el journey aprobado B/C/E y alinea específicamente los pasos 18–38
con las capabilities reales auditadas en el repo vigente. Los ejemplos funcionales siguen siendo
**ilustrativos**, no oracle design.

## Mapa maestro

| Pasos | Sprint | Propósito |
|---|---|---|
| 1–8 | 13-B | instalar/arrancar, login, crear proyecto, idea/constraints, plan/approval, bootstrap, Project Status |
| 9–17 | 13-C | Vision, Scope, Requirements, Architecture/Security/Tests/ADRs, readiness, Roadmap/Backlog/Sprint/Stories |
| 18–32 | 13-D | Story/Coding cycle, tests, quality, Git, repetición hasta MVP, recovery scenarios |
| 33 | UX-P1 transversal | observar/medir/clasificar/corrective bounded/resume |
| 34–38 | 13-D | Release Readiness, package/checksum/SBOM, metadata/tag, clean install, rollback, local release |
| 39 | 13-E | adjudicación independiente |

## 13-B — Bootstrap (pasos 1–8)

1. **Instalar y arrancar DevPilot.** Terminal solo para operar DevPilot; todavía no existe la app greenfield.
2. **Ingresar y autenticarse.** Login local → Home; debe ser comprensible si existe proyecto activo y cuál es la acción principal.
3. **Elegir Crear proyecto.** Workspace nuevo `inventory-sales-local-greenfield`; no copiar artifacts, DB, código, Git history, configuración ni evidencia del piloto histórico.
4. **Expresar la idea, no la solución.** El Owner describe una app local de inventario/ventas; no entrega tablas/endpoints/arquitectura preconstruidos.
5. **Definir ubicación y restricciones.** Nombre/workspace, restricciones, tipo de aplicación, ejecución y model policy; local-first, mock/no-API baseline.
6. **Revisar antes de ejecutar.** Propuesta → plan → dry-run → efectos → approval; ninguna mutación relevante debe materializarse antes.
7. **Bootstrap gobernado.** DevPilot crea carpeta, estructura inicial, Git, entorno/configuración y Project Context. `git init` manual o project writes externos = BLOCK.
8. **Project Status como centro operacional.** Debe mostrar proyecto, etapa, completado/pendiente, blocker/causa y next valid action.

## 13-C — Engineering + planning (pasos 9–17)

9. **Product Vision.** DevPilot ayuda a formalizar qué problema se resuelve.
10. **Scope.** Delimitar qué entra y qué queda fuera del MVP.
11. **Requirements.** Convertir necesidades en requisitos verificables.
12. **Diseño técnico.** Architecture, Security, Test Strategy, ADRs y traceability; decisiones justificadas, no impuestas por oracle externo.
13. **Pre-code readiness.** MIASI/MIPSoftware y readiness deben revelar faltantes y next action.
14. **Roadmap.** Organizar capacidades/etapas sin bajar todavía a implementación por archivo.
15. **Backlog.** Convertir capacidades en trabajo priorizable y trazable.
16. **Sprint.** Seleccionar trabajo coherente para una iteración.
17. **Stories ejecutables.** Stories con acceptance criteria y readiness suficiente para pasar a implementación.

## PRE-13D

Antes del paso 18:

- identificar repo/commit DevPilot efectivo;
- confirmar Pilot A activo;
- Planning FROZEN + `IMPLEMENTING_READY`;
- resolver cualquier ambiguity entre Git/finalize authority y Project State/Source Registry current fields;
- no precrear StoryExecution mediante operador;
- Full runs = 0.

## 13-D — pasos 18–38 audit-aligned

### 18. Story activation + Story/Coding Workbench

Desde Planning FROZEN:

1. DevPilot debe conducir al Owner a la first READY story.
2. DevPilot debe evaluar Story DoR.
3. Debe materializar `StoryContextPack` y `StoryExecution` por ruta normal.
4. PLANNED debe poder pasar a IN_PROGRESS por acción normal.
5. El Owner debe poder revisar o inspeccionar suficientemente:
   - story/objetivo;
   - AC;
   - requirements;
   - architecture/constraints;
   - test intent;
   - context/provenance/hash.

`no active story` sin una acción normal de activación = BLOCK.

### 19. Ruta de implementación

- Manual es first-class.
- Agent-assisted mock/fake-local puede usarse.
- real local/external no es requerido para Pilot A.
- cualquier model/provider route debe dejar provenance.
- model route no concede tool/source/apply/approval authority.

### 20. Change Plan

DevPilot deriva un SourceChangePlan immutable desde drafts runtime-only.

Revisar:

- plan ID/hash;
- exact paths;
- risk;
- Test Impact preview.

### 21. Diff

Revisar full diff.

### 22. Dry-run / recheck

Revalidar preimages y estado.

### 23. Approval

Approval humana exacta del plan.

### 24. Apply

Atomic apply del plan exacto.
Registrar apply manifest.
No operator project write.

### 25. Pruebas pertinentes

`Test Impact v2 → StoryTestPlan → targeted typed jobs`.

El signal Full es informativo.
**No ejecutar Full en 13-D.**

### 26. Remediation

`finding/fail → propuesta → review → approval → bounded apply → successor test plan → targeted retest`.

No `rerun everything` por defecto.

### 27. Quality Gate

Debe explicar:

- tests requeridos/recomendados;
- resultados;
- waivers permitidos/no permitidos;
- findings;
- decision;
- commit readiness.

S0/S1 no se waive.

### 28. Git review / CommitPlan / stage

Revisar exact dirty path set.

Flow:

`CommitPlan → stage approval → exact-path stage → staged recheck`.

No `git add .`.

### 29. Governed commit

`commit approval → commit → GitCommitRecord`.

No push/force/rebase/reset-hard.

Story debe avanzar `COMMIT_READY → DONE`.

### 30. Project Status

Debe mostrar current story DONE y next valid action.

### 31. Repeat until MVP

No basta con volver a Planning.

El loop debe demostrar:

`DONE → next READY story → nueva StoryExecution → D01–D04`.

Sin operator runtime seed.

### 32. Recovery scenarios

Probar controladamente:

- restart/new session;
- interrupted safe work;
- external edit;
- dirty;
- branch/divergence/conflict;
- stale lock.

Recovery no destructivo.
Preservar drafts/evidence.

### 33. UX-P1

Sin cambio metodológico.

### 34. Release Readiness

Read-only/fail-closed.

Debe integrar:

- current Story DONE;
- Quality/required jobs PASS;
- clean Git;
- GitCommitRecord;
- pending approvals=0;
- release machinery available.

READY no es release approval.

### 35. Package + metadata/tag

Package:

- exact commit/tree;
- checksum;
- SBOM baseline;
- byte reproducibility;
- forbidden runtime/secrets absent.

Metadata:

- version decision;
- release notes;
- TagPlan exact-commit dry-run;
- release approval owner/release-manager;
- annotated local tag;
- tag verification.

No push/publish/deploy.

### 36. Clean install

Desde package actual, en disposable local sandbox.

### 37. Upgrade/rollback

- backup antes de mutable upgrade;
- controlled upgrade;
- rollback;
- restore/hash parity;
- production data untouched.

### 38. Local release

ReleaseClosure graph exige:

- package PASS;
- install PASS;
- rollback PASS/restore verified;
- metadata/tag PASS.

Finalize local release y Project Status RELEASED.

No equivale a public distribution, remote deployment o signing enterprise.

## 13-E — Adjudicación (paso 39)

39. **Independent adjudication.** Verificar que el proyecto nació desde cero, `operator_project_writes=0`, mandatory terminal escapes=0, approvals/provenance/recovery/release son reproducibles, S0/S1=0 y la instalación limpia es real.

## Rutina diaria central

`Project Status → Next Action → Story activation/context → Draft/Plan → Diff → Dry-run → Approval → Apply → Test Impact/Jobs → Quality → CommitPlan → stage approval/stage → commit approval/commit → Project Status`.

## Rutina macro

`IDEA → Create Project → Vision → Scope → Requirements → Architecture/Security/Tests/ADRs → Roadmap → Backlog → Sprint → Story activation/context → Plan/Diff/Dry-run/Approval/Apply → Tests/Quality/Remediation → governed Git Commit → siguientes stories → Release Readiness → Package/Checksum/SBOM → Version/Notes/Tag → Clean Install → Rollback → LOCAL RELEASE`.

## Regla de aceptación

No intervenir para hacer que DevPilot parezca funcionar. Si una etapa normal exige escribir manualmente
archivos, inicializar/mutar Git por fuera, sembrar StoryExecution desde operador, modificar código desde
PowerShell o fabricar artefactos externos para desbloquear el journey, preservar el evento como evidencia
y adjudicarlo; no ocultarlo.
