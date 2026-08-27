---
doc_id: "PROMPT-DEVPL-GSDLC-06-D"
title: "Prompt operativo DEVPL-GSDLC-06-D — TokenBudgetPolicy, ContextBudget and routing"
status: "approved/ready-after-06-C"
version: "1.0.1"
owner: "Ordóñez"
updated: "2026-08-26"
approval: "approved_by_owner"
execution_source_policy: "fixed/repo377-owner-adjudicated-successor-of-06-C"
---

# 04 — PROMPT DEVPL-GSDLC-06-D

## 0. Rebind de ejecución 06-D

Esta versión rebound sustituye exclusivamente la autoridad de ejecución del prompt original. La autoridad vigente es `repo_DevPilot_Local_377_DEVPL_GSDLC_06_C_EXTERNAL_PROVIDER_ENABLEMENT_WINDOWS_VALIDATED_CANDIDATE.zip` / `6f0fdbd9142c2ad3470bcfe07a3b764a370b3698` / `0a7cf1bcd818706d4cb46c44a88b00b4b2fd71731c0b4ed32bec635f51e4b62c`, adjudicada `CLOSED/PASS` para GSDLC-06-C mediante `DEVPL_GSDLC_06_C_FINAL_OWNER_ADJUDICATION_v1_0_0.md`. El diseño funcional restante del prompt v1.0.0 se conserva.

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

- **Baseline único de ejecución rebindeado:** `repo_DevPilot_Local_377_DEVPL_GSDLC_06_C_EXTERNAL_PROVIDER_ENABLEMENT_WINDOWS_VALIDATED_CANDIDATE.zip` / `6f0fdbd9142c2ad3470bcfe07a3b764a370b3698` / `0a7cf1bcd818706d4cb46c44a88b00b4b2fd71731c0b4ed32bec635f51e4b62c`. Corresponde a GSDLC-06-C `CLOSED/PASS`; no volver a repo374, repo376, repo341 ni a otro predecessor anterior.
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
