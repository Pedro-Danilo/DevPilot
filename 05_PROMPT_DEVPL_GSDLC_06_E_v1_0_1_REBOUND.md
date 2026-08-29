---
doc_id: "PROMPT-DEVPL-GSDLC-06-E-REBOUND"
title: "Prompt operativo DEVPL-GSDLC-06-E — Provider Settings UX and controlled model evaluation — REBOUND"
status: "approved/ready-after-06-D"
version: "1.0.1"
owner: "Ordóñez"
updated: "2026-08-27"
approval: "approved_by_owner"
execution_source_repo: "repo_DevPilot_Local_378_DEVPL_GSDLC_06_D_TOKEN_BUDGET_CONTEXT_ROUTING_WINDOWS_VALIDATED_CANDIDATE.zip"
execution_source_commit: "718fa0da5d552f8bf6def39c102f0124ac7fa922"
execution_source_sha256: "25a159294984185b30e2b3db2fc64299568c9dd8d77c484cf73b598fbde36be9"
execution_source_policy: "fixed/owner-adjudicated-successor-of-06-D"
---

# Rebind de autoridad de ejecución

Este successor reemplaza únicamente el **baseline de ejecución** del prompt v1.0.0. La autoridad fija es `repo_DevPilot_Local_378_DEVPL_GSDLC_06_D_TOKEN_BUDGET_CONTEXT_ROUTING_WINDOWS_VALIDATED_CANDIDATE.zip` / `718fa0da5d552f8bf6def39c102f0124ac7fa922` / `25a159294984185b30e2b3db2fc64299568c9dd8d77c484cf73b598fbde36be9`. Repo374 y anteriores quedan como origen histórico, no como execution authority. 06-D está `CLOSED/PASS`. Todas las demás reglas del prompt v1.0.0 permanecen vinculantes.

# 05 — PROMPT DEVPL-GSDLC-06-E

Implementa y cierra **GSDLC-06-E — Provider Settings UX and controlled model evaluation** únicamente después de 06-D `CLOSED/PASS`. Este micro-sprint consume la **única full regression del backlog** solo cuando todos los gates previos están verdes.

## 1. UX de producto

1. Construye `AIControlCenterView` como shell de administración IA y `ModelSettingsView` como sub-vista específica de Model Gateway. No mezclar Agent Runtime/Skills authority.
2. Mostrar por provider/model/access-route: disposition, enabled state, health, capabilities, privacy/data class, region, auth-adapter type, evidence freshness, estimated tokens/cost, budget y fallback.
3. `mock`, local opt-in y external conditional/blocked deben ser visibles; no ocultar `unknown/blocked`.
4. Permitir selección manual o routing policy sin cambiar permisos de tools.
5. Credenciales siempre masked; nunca renderizar raw secret ni incorporarlo al DOM/telemetry.
6. Ejecutar evaluación controlada mock + fake local + fake external. Real API es opcional y requiere ADR/freshness/RBAC/budget/approval; su ausencia no impide PASS.
7. Probar browser disable/revoke/fallback y cost UI parity.

## 2. Browser acceptance

Diseña casos con evidencia screenshot + machine guard para: provider catalog, local route, blocked remote-as-local, external disabled, RBAC config negative, masked credential reference, budget/cost preview, hard-stop, fallback reason, freshness state, route-vs-tool separation, revoke/disable persistence y final product invariant.

El browser acceptance se ejecuta una vez sobre el candidate funcional estabilizado; correctives posteriores que no cambien UX pueden preservar evidencia si un guard machine-readable demuestra equivalencia.

## 3. Predictive Pre-Full obligatorio

Antes del marker de full, ejecutar y sellar:

- Test Impact + focal/acumulativas A→E;
- UI smoke/build;
- Historical Contract Sweep;
- Contract Reconciliation Sweep;
- Documentation Governance;
- Project State;
- TCR v1/v2;
- route/OpenAPI/API mapping/RBAC parity;
- derived counters recalculados desde colección viva;
- `current-active` vs `*_at_close` historical pointers;
- differential SecretGuard contra predecessor + runtime-secret-path scan;
- provider credential redaction;
- runtime-ephemeral absence;
- package preview/forbidden path audit;
- parsers del operador contra schemas reales;
- Windows executable resolution (`.cmd/.exe`) cuando aplique;
- source fingerprint parity antes/después de builds/smokes;
- lazy capability composition checks para que Model Gateway no rompa workspaces históricos que no lo invocan.

Cualquier drift determinístico se corrige **antes** del marker. No degradar a warning.

## 4. Única full regression

Cuando browser + Predictive estén PASS y S0/S1=0:

1. comprobar que no exista marker previo;
2. crear marker durable `FULL_REGRESSION_ATTEMPT_STARTED`;
3. ejecutar full exactamente una vez;
4. sellar log + JUnit + result + failed-nodeids.

Si PASS: continuar finalize.

Si FAIL/ERROR/TIMEOUT: **NO RERUN**. Preservar evidencia, diagnosticar causas, aplicar corrective acotado, ejecutar exactamente los failed-nodeids, bounded impacted retest y Historical Regression Guard. Cerrar solo si `composite-full-regression-selective-retest = PASS`; el resultado original de full permanece FAIL/1-of-1.

## 5. Finalize y candidate

Después de full PASS o composite PASS:

- reconciliar CURRENT/closure report/operation declaration/Test Impact/Project State/Source Registry/README/roadmap;
- volver a ejecutar validators baratos post-finalize;
- repo-review, secret guard diferencial, runtime residual scan y `git diff --check`;
- commit limpio;
- candidate ZIP desde Git HEAD;
- evidence package + SHA;
- owner adjudication proposal del micro-sprint y del backlog.

## 6. PASS/BLOCK

PASS: usuario entiende model/provider/access-route/costo/freshness; mock/local/fake mandatory PASS; external remains governed; route decision no concede tools; browser PASS; S0/S1=0; full 1/1 PASS o composite recovery válida.

BLOCK: credential visible, cost absent/engañoso, route cambia sin audit, remote tratado como local, provider habilitado sin gates, full rerun, drift pre-full conocido ignorado.

## 7. Autorización de GSDLC-07

GSDLC-07 solo puede autorizarse tras owner adjudication de 06-E + backlog 06. API real no es requisito; mock y al menos una ruta local/fake-local deben pasar.

## Reglas transversales obligatorias

- **Baseline único de ejecución:** `repo_DevPilot_Local_374_DEVPL_GSDLC_05_E_MANUAL_PRE_CODE_WINDOWS_VALIDATED_CANDIDATE.zip` / `db04b6f158fc4dd366b3f61635fb2d66d63f7d40` / `f87c2a1db339b1d0f2dcf1d694366672c8cc9d57c27bfcd33a460a3889706152`. Nunca reconstruir desde repo341 ni desde un predecessor anterior.
- Local-first. Mock obligatorio. Ninguna API de pago es requisito de PASS.
- No asumir `OPENAI_API_KEY` ni otra credencial. Secretos solo por referencias tipadas; nunca persistir raw keys en repo, logs, evidencia o DB versionable.
- `ModelRouteDecision` no concede permisos de tools/skills. `ToolExecutionDecision` permanece separado.
- `dry-run` por defecto para cualquier cambio de settings/provider y para acciones con costo/red.
- Sin arbitrary shell como capacidad del producto. Los operadores de evaluación pueden ejecutar herramientas de validación, pero no deben escribir artefactos gestionados del fixture por fuera de la UI/API tipada.
- Runtime stores (`auth.db*`, `devpilot.db*`, outputs efímeros, node_modules, caches) no entran en baselines/candidates.
- Antes de modificar una aserción histórica, clasificarla `historical-freeze`, `current-active`, `successor-needed`, `deprecated-after-proof`, `derived` o `runtime-ephemeral`.
- No corregir tests históricos solo para “hacer pasar pytest”. Si un test consulta un pointer mutable, crear/usar snapshot `*_at_close` o contrato successor explícito.
- Evitar composición eager: una capability 06-X no puede convertirse en precondición de construcción para servicios/workspaces históricos que no la invocan.
- SecretGuard de cierre debe ser **diferencial contra predecessor validado** para material nuevo, manteniendo bloqueo de rutas runtime/secretas; no usar regex whole-tree ad-hoc como único gate.
- A→D: **full regression = 0 por rutina**. Una full intermedia requiere hard-trigger explícito + owner approval y consume la única corrida del backlog.
- 06-E: ejecutar cheap gates + Contract Reconciliation Sweep + Predictive Pre-Full + browser acceptance antes del marker durable. Luego una sola full. Ante FAIL: no rerun; exact failed-nodeids + bounded impacted + Historical Regression Guard + composite closure.
