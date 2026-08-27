---
doc_id: "PROMPT-DEVPL-GSDLC-06-D"
title: "Prompt operativo DEVPL-GSDLC-06-D — TokenBudgetPolicy, ContextBudget and routing"
status: "approved/ready-after-06-C"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-08-26"
approval: "approved_by_owner"
execution_source_policy: "owner-adjudicated-successor-of-06-C"
---

# 04 — PROMPT DEVPL-GSDLC-06-D

Implementa **GSDLC-06-D — TokenBudgetPolicy, ContextBudget and routing** únicamente tras 06-C `CLOSED/PASS`.

## 1. Objetivo

Gobernar tokens, contexto y costo antes/durante/después de cada run, con routing determinístico por capability/privacy/locality/cost/health y fallback explícito.

## 2. Contratos y ledger

1. Evoluciona `CostGuard` y `modeling/budget.py` sin romper contratos históricos. Define `TokenBudgetPolicy` por request, artifact, story, session, day y workspace.
2. `ContextBudget` debe modelar input reserve, output reserve, safety margin, truncation/summary/RAG budget y hard ceiling.
3. Estimación pre-run: tokens/costo con `known/estimated/unknown` explícito; nunca presentar unknown como cero.
4. Ledger v2: planned vs actual, provider/model/route/workload, currency/source/freshness, reason de ajuste y provenance.
5. Hard stop server-side. Un agente/modelo no puede ampliar su propio budget.

## 3. Router

Orden mínimo vinculante: capabilities → privacy/offline → provider enablement → region/terms/auth/data class → cost ceiling → health → workload benchmark → safe fallback/BLOCK.

Routing y fallback deben explicar qué regla eligió/rechazó cada ruta. No silent fallback. Una ruta external/high-cost puede requerir approval, pero route decision nunca concede tool permission.

## 4. Context management

Implementa estrategias determinísticas `diff-first`, summary, retrieval budget, hard trim y refusal/BLOCK cuando no pueda preservarse la invariante del workload. No diseñes loops autónomos sin límite.

## 5. Pruebas

- hard budget exceed before call;
- exceed during/after actual usage;
- actual cost unknown;
- deterministic routing;
- privacy/offline precedence;
- provider disabled;
- health degradation;
- fallback audit;
- context trim boundaries;
- ledger arithmetic/parity;
- route decision cannot escalate tools.

## 6. Validación/evidencia

`budget_test_matrix.json`, `cost_ledger_samples.json`, routing decision matrix, context-budget cases, source delta/Test Impact, Historical Contract Sweep, Contract Reconciliation Sweep, docs/state/TCR. **No full regression.**

PASS: ningún run supera hard budget y tokens/costo son explicables. BLOCK: overspend, silent fallback, unknown cost presentado como conocido, agent budget escalation.

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
