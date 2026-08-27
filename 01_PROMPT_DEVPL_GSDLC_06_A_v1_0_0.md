---
doc_id: "PROMPT-DEVPL-GSDLC-06-A"
title: "Prompt operativo DEVPL-GSDLC-06-A — Model capability and access-route contracts"
status: "approved/ready-to-execute"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-08-26"
approval: "approved_by_owner"
source_repo: "repo_DevPilot_Local_374_DEVPL_GSDLC_05_E_MANUAL_PRE_CODE_WINDOWS_VALIDATED_CANDIDATE.zip"
source_git_commit: "db04b6f158fc4dd366b3f61635fb2d66d63f7d40"
source_repo_sha256: "f87c2a1db339b1d0f2dcf1d694366672c8cc9d57c27bfcd33a460a3889706152"
---

# 01 — PROMPT DEVPL-GSDLC-06-A

Implementa **GSDLC-06-A — Model capability and access-route contracts** sobre el baseline canónico indicado. El objetivo no es crear otro wrapper superficial de `ModelAdapter`: debes establecer una frontera industrial y versionada entre `provider`, `model`, `access route`, `gateway adapter`, `auth adapter` y `capabilities`, preservando compatibilidad histórica.

## 1. Precondición y activation rebind

Antes de source funcional, verifica hash/identidad del baseline y materializa el activation rebind administrativo definido en `DEVPL_GSDLC_06_ACTIVATION_REBIND_MANIFEST_v1_0_0.md`. Reconciliar Project State / Source Registry / README / roadmap a GSDLC-05 `CLOSED/PASS` y GSDLC-06 `APPROVED/ACTIVE`. Si hay drift, BLOCK antes de funcionalidad.

Verifica también R01 CLOSED/PASS y su autoridad de investigación; consumir R01 como input, no como autorización automática de providers externos.

## 2. Ingeniería requerida

1. Audita `src/devpilot_core/modeling/contracts.py`, `providers.py`, `router.py`, `budget.py`, `application/model_service.py`, Settings API/UI y tests existentes. No dupliques contratos ya presentes; evoluciona con successors versionados.
2. Introduce `ModelCapabilityCatalog` machine-readable + schema. Debe representar al menos context window, structured output, tools, vision, coding, embeddings, token/cost metadata y evidence freshness.
3. Introduce `ProviderAccessRoute` separando `provider_id`, `model_id`, `access_route_id`, `gateway_adapter_id`, `auth_adapter_id`, locality, endpoint class, disposition (`enabled/disabled/conditional/unknown/blocked`), reason, evidence refs y freshness.
4. Define contratos tipados `ModelRoutingRequest` y `ModelRouteDecision` con `workload_id`, required capabilities, privacy/data classes, cost ceiling, offline/region constraints, route/evidence refs y blocked reason.
5. Asegura que `ModelRouteDecision` no contenga ni pueda implicar autorización de tool/skill execution. Añade negative test explícito.
6. Importa disposición R01 inicial: `mock=default-safe`; Ollama/LM Studio local=`allowed` pero opt-in; externas=`conditional/unknown/blocked` y runtime-disabled. Compatibilidad OpenAI no equivale a provider autorizado.
7. Capability matching debe ser provider-agnostic y determinístico. Unknown route = deny. Mock debe permanecer siempre disponible.
8. Añade migración/compat layer para `ModelProviderConfig` histórico sin quebrar CLI/tests existentes.

## 3. Seguridad y límites

No red real. No API key. No provider externo real. No cambio de permisos de tools. No hardcoded vendor model dentro de Guided SDLC. No secrets en catálogo.

## 4. Validación mínima y suficiente

- schema/catalog validation;
- capability matching matrix;
- unknown route deny;
- mock route availability;
- identity separation;
- route decision cannot grant tool execution;
- focales existentes de model adapter/provider registry;
- Documentation Governance, Project State, TCR v1/v2;
- `historical_contract_sweep` 06-A;
- `contract_reconciliation_sweep` limitado a superficies tocadas.

**No ejecutar full regression.** Si aparece hard trigger real, detente y solicita adjudicación antes de consumir la corrida única del backlog.

## 5. Evidencia/entregables

- `model_catalog_snapshot.json`;
- `capability_match_cases.json`;
- source delta manifest exacto;
- Test Impact;
- historical contract sweep;
- contract reconciliation sweep;
- closure report;
- owner adjudication proposal;
- candidate repo sucesor solo después de validación Windows.

## 6. PASS/BLOCK

PASS: workflow pide capabilities, no vendor; mock válido; unknown deny; identidades separadas; S0/S1=0.

BLOCK: vendor hardcoded en workflows, unknown allowed, route decision concede tool permission, external route enabled por compatibilidad, drift documental conocido, runtime secret store en candidate.

## 7. Salida

Cierra 06-A únicamente con evidencia Windows cumulative-selective PASS y full=0. Entonces autoriza 06-B.

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
