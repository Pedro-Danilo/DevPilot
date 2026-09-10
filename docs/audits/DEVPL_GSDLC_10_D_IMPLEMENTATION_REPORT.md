---
doc_id: "DEVPL-GSDLC-10-D-IMPLEMENTATION-REPORT"
title: "DEVPL-GSDLC-10-D — RBAC-governed stage and commit with traceability — implementation report"
status: "implemented-initial/local-qualified/windows-validation-pending"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-09-10"
approval: "pending_windows_validation"
---
# 1. Resultado de implementación local

GSDLC-10-D implementa el cierre gobernado de una story desde `COMMIT_READY` hasta un commit Git local exacto y trazable. La autoridad permanece server-side: Quality PASS es precondición, no permiso; stage y commit requieren decisiones independientes de RBAC/approval y una ruta/modelo de IA nunca concede autoridad Git.

**Estado:** `IMPLEMENTED/LOCAL-QUALIFIED/WINDOWS-VALIDATION-PENDING`. **Full Regression consumida:** `0`.

# 2. Capacidades implementadas

- `CommitPlan` inmutable/hash-bound a story, change plan, test plan, quality report, HEAD/branch y exact path set.
- Revalidación inmediatamente antes de stage/commit: Quality vigente/no stale, expected paths, unexpected dirty paths, preimages semánticas y sesión/rol.
- Stage de paths exactos; `git add .` y staging implícito quedan fuera.
- Aprobaciones separadas para stage y commit.
- `GitCommitRecord` con commit hash real, identidad/sesión, mensaje, exact paths y trace links.
- Traceability requirement→story→change-plan→tests→quality→commit.
- UI normal journey mediante el `WorkspaceGitOperationsPanel` existente; no se creó un segundo Git engine.
- No push, force push, rebase ni reset-hard.

# 3. Arquitectura y seguridad

La implementación reutiliza `WorkspaceGitOperationsApplicationService → GovernedGitMutationAdapter`. El adaptador conserva Git tipado con `shell=False`. El límite histórico UOC-006 de 20 paths no se expande globalmente; 10-D usa un override explícito y story-bound de hasta 32 paths. Las comparaciones de preimage normalizan UTF-8/LF para que CRLF/LF no produzca un BLOCK accidental.

El browser Windows debe operar contra un workspace Git aislado. El operador prepara y verifica el fixture, pero **no ejecuta stage/commit de la story**: esas mutaciones deben originarse en DevPilot bajo prueba.

# 4. Contratos y drift reconciliados

Se corrigieron únicamente contratos `current-active/derived`: puntero activo que aún refería 10-C, ocho rutas Git no registradas, mapping UI atrasado de 10-B/10-C y 10-D, marker `ui.quality` y release criteria aún ligado al predecessor. Los hechos históricos y snapshots sellados no se reescribieron.

# 5. Pruebas locales

- Focal 10-D: **10/10 PASS** antes de la reconciliación final; el bundle la ejecuta de nuevo sobre Windows.
- Type-check dirigido del delta TypeScript: **PASS**.
- Prueba programática con repositorio Git aislado: commit real exacto, doble approval, traceability y worktree clean: **PASS local**; no sustituye browser Windows.
- Full Regression: **0**, conforme a la política de GSDLC-10-D.

Existe un diagnóstico global TypeScript heredado en `ArtifactAIPanel.ts` relacionado con `DevPilotApiError.findings`, ya presente fuera del delta 10-D. No se oculta ni se usa para alterar el alcance: la verificación dirigida del delta es PASS y el operador no introduce un global typecheck ajeno al Test Impact. Se registra como limitación heredada no-S0/S1.

# 6. Riesgos y limitaciones

- Esta es la primera versión integrada del journey story-bound stage/commit; no incluye push ni operaciones destructivas.
- La prueba browser Windows sigue siendo obligatoria antes del cierre.
- El commit real de validación ocurre únicamente en el fixture Git aislado; nunca sobre el repo oficial como parte del journey de story.
- El operador no consume Full Regression y no intenta resolver drifts fuera del impacto declarado.

# 7. Criterios PASS/BLOCK

**PASS:** commit contiene exactamente el delta aprobado; fixture queda clean; RBAC y dos approvals acreditados; ningún path no aprobado es staged; traceability completa; S0/S1=0; Full=0.

**BLOCK:** unexpected dirty/staged path; wrong role/session; Quality stale/no PASS; approval faltante/reutilizado; commit tree distinto del plan; traceability incompleta; operación destructiva/push disponible en este journey; runtime store/secreto incluido en evidencia o ZIP.

# 8. Verificación

La guía única Windows del bundle es la autoridad operacional. No ejecutar comandos alternativos ni Full Regression para este micro-sprint.
