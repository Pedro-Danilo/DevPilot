---
doc_id: "PROMPT-DEVPL-GSDLC-06-B-REBOUND"
title: "Prompt operativo DEVPL-GSDLC-06-B — Local provider discovery and OpenAI-compatible hardening — repo375 rebound"
status: "approved/ready-to-execute"
version: "1.0.1"
owner: "Ordóñez"
updated: "2026-08-26"
approval: "approved_by_owner"
source_repo: "repo_DevPilot_Local_375_DEVPL_GSDLC_06_A_MODEL_GATEWAY_CONTRACTS_WINDOWS_VALIDATED_CANDIDATE.zip"
source_git_commit: "5013eee3c5ddf353f63d2fc19ba5d72faa08cc67"
source_repo_sha256: "9cb01715f9d3f942fc89ebcf375610b906e234ed7b7480b576ea6687d78b196d"
predecessor_owner_adjudication: "DEVPL_GSDLC_06_A_FINAL_OWNER_ADJUDICATION_v1_0_0.md"
execution_source_policy: "fixed/owner-adjudicated-successor-of-06-A"
---

# 02 — PROMPT DEVPL-GSDLC-06-B

Implementa **GSDLC-06-B — Local provider discovery and OpenAI-compatible hardening** únicamente después de 06-A `CLOSED/PASS`. Rebíndate al successor owner-adjudicated de 06-A; no vuelvas a repo374 para simplificar.

## 1. Objetivo

Convertir Ollama/LM Studio y un endpoint local OpenAI-compatible en rutas opt-in, reproducibles, bounded y protegidas contra SSRF, manteniendo mock como fallback seguro.

## 2. Trabajo requerido

1. Audita y evoluciona `ollama_adapter.py`, `lmstudio_adapter.py`, `local_provider_health.py`, `providers.py`, `router.py` y sus tests; reutiliza infraestructura existente.
2. Introduce una política tipada de endpoint local: loopback por defecto; hostname/IP normalizados; rechazo de esquemas no HTTP(S), userinfo, redirects a no-local, DNS/host ambiguo y puertos fuera de policy.
3. Generic OpenAI-compatible local route debe requerir allowlist explícita y **nunca** clasificarse como local solo por usar el wire protocol OpenAI.
4. Health/model discovery: timeouts estrictos, máximo de respuestas/modelos, tamaño de payload acotado, no follow-redirect inseguro, parseo fail-closed.
5. Diferencia `configured`, `reachable`, `healthy`, `model-discovered`, `enabled`. Discovery no habilita ejecución.
6. Agrega hardware-fit hints derivados de R01 como recomendaciones no autoritativas; si faltan/son stale, no bloquean mock.
7. Fallback explícito a mock con reason auditable; no silent fallback.
8. Settings/health API solo expone metadatos redactados.

## 3. Pruebas

Usa servidores fake locales herméticos para Ollama, LM Studio y OpenAI-compatible. Cubrir: success, timeout, malformed list, oversized payload, wrong content-type, redirect no-local, endpoint remoto, IPv6 loopback, hostname tricks y fallback a mock. Un test real contra Ollama/LM Studio puede ser opcional del operador y nunca requisito de PASS.

No API key requerida para rutas locales salvo configuración explícita compatible; esa configuración nunca se persiste como raw secret.

## 4. Validación

Focales + acumulativas A/B, schemas, local endpoint security, Settings API contract, Historical Contract Sweep 06-B, Contract Reconciliation Sweep, docs/state/TCR. **No full regression.**

## 5. Evidencia

`local_provider_health_report.json`, endpoint-policy matrix, SSRF negative matrix, fallback evidence, source delta, Test Impact y closure report.

## 6. PASS/BLOCK

PASS: mock + fake-local PASS, remote nunca se clasifica local, bounded health, fallback explícito. BLOCK: SSRF, remote-as-local, unbounded call, discovery habilita provider, raw secret.

## Reglas transversales obligatorias

- **Baseline único de ejecución:** `repo_DevPilot_Local_375_DEVPL_GSDLC_06_A_MODEL_GATEWAY_CONTRACTS_WINDOWS_VALIDATED_CANDIDATE.zip` / `5013eee3c5ddf353f63d2fc19ba5d72faa08cc67` / `9cb01715f9d3f942fc89ebcf375610b906e234ed7b7480b576ea6687d78b196d`. Nunca reconstruir desde repo374, repo341 ni desde un predecessor anterior.
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
