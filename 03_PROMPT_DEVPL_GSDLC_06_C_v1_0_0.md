---
doc_id: "PROMPT-DEVPL-GSDLC-06-C"
title: "Prompt operativo DEVPL-GSDLC-06-C — External API credential and enablement flow"
status: "approved/ready-after-06-B"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-08-26"
approval: "approved_by_owner"
execution_source_policy: "owner-adjudicated-successor-of-06-B"
---

# 03 — PROMPT DEVPL-GSDLC-06-C

Implementa **GSDLC-06-C — External API credential and enablement flow** solo después de 06-B `CLOSED/PASS`. El cierre obligatorio funciona con **fake vendor providers**; ninguna API real ni gasto es requisito.

## 1. Gate previo

Antes de habilitar una ruta externa real, exige ADR provider-specific que resuelva los 12 gates del backlog: provider/model/route, region, auth, terms/billing/privacy, data classes, budget, health/fallback, logging/redaction, kill switch/rollback, eval threshold, RBAC y freshness TTL. Revalida evidencia F0/F1 dentro de TTL. Si no existe, la ruta permanece `conditional/blocked`.

## 2. Credenciales y auth adapters

1. Implementa `ProviderCredentialReference` sin valores secretos.
2. Auth adapters tipados: `LocalLoopbackNoSecretAdapter`, `EnvApiKeyAdapter` y provider-native identity adapter cuando corresponda. `ConsumerSessionAdapter` debe permanecer explícitamente bloqueado.
3. Lectura de secreto solo en boundary de ejecución, con redaction estructural y sin serializar valor en logs, responses, evidence o DB versionable.
4. Missing/invalid credential = BLOCK claro, sin revelar valor.

## 3. Enablement

- provider disabled by default;
- toggle gobernado por RBAC/policy y, cuando aplique, approval;
- privacy/terms/cost/data-class notice antes de habilitar;
- connectivity test redacted y bounded;
- disable/revoke con audit trail;
- network disabled por defecto;
- no scraping, cookies ni reutilización de sesión consumer web.

## 4. Testing

Fake OpenAI/Gemini/Mistral/HF-like adapters o el mínimo conjunto requerido por la arquitectura, sin dependencias de SDK innecesarias. Cubrir no-consent, missing key, invalid key, denied role, expired freshness, disabled route, kill switch, redaction, network-disabled y unsupported consumer-session.

Opcionalmente puede existir un protocolo para prueba real owner-approved, pero debe estar separado de PASS, disabled por defecto y protegido por budget/approval.

## 5. Validación

Focales + acumulativas A-C, secret leak scan diferencial, RBAC, provider enablement ADR schema, Historical Contract Sweep, Contract Reconciliation Sweep, docs/state/TCR. **No full regression.**

## 6. Evidencia

`provider_enablement_audit.json`, `secret_leak_scan.json`, ADR gate report, enable/disable audit, source delta/Test Impact/closure report.

## 7. PASS/BLOCK

PASS: externa disabled hasta configuración completa, secretos no expuestos, enable/disable auditado. BLOCK: secret en log/source, API antes de consentimiento/budget, consumer web session, route externa habilitada por simple compatibilidad.

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
