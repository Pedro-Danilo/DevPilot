---
doc_id: "PROMPT-DEVPL-GSDLC-11-A"
title: "DEVPL-GSDLC-11-A — Release readiness aggregation"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-09-11"
approval: "approved_by_owner"
precondition: "DEVPL-GSDLC-10 CLOSED/PASS/WINDOWS-VALIDATED/COMPOSITE-RECOVERY"
execution_source_policy: "repo420 + activation/rebind absorbed into this micro-sprint"
full_regression_budget: "0 in 11-A; GSDLC-11 budget remains 0/1"
browser_policy: "required only for new readiness UI behavior introduced by 11-A"
---

# Objetivo

Construir `ReleaseReadinessProjection` y `ReleaseReadinessView` determinísticos y explicables, reutilizando la maquinaria current-active de Quality, testing, security, traceability, approvals y release ya existente.

# Implementación requerida

1. Integrar el activation/rebind de GSDLC-11 descrito en el prompt 00 dentro de este mismo delta.
2. Inventariar y reutilizar POST-H-017/026/027 y las capacidades actuales de GSDLC-10; no crear una segunda pila de release/readiness.
3. Definir un modelo tipado de readiness con blockers, severity, owner, evidence_ref, policy_source, pending_approval y `next_action`.
4. Derivar `RELEASE_READY` únicamente cuando estén presentes todas las evidencias obligatorias current-active; ausencia/unknown debe fail-closed.
5. Exponer la proyección en API/UI project-scoped con sesión/RBAC server-side. Browser storage es UX-only.
6. Separar `readiness computation` de `release approval`: un estado READY no equivale a aprobación de release.
7. Aplicar autoridad release-manager/owner donde corresponda; modelos/agentes no pueden crear approval/waiver.
8. Prohibir claims enterprise/compliance/public-release no respaldados.
9. Actualizar contracts/schemas/registries/docs current-active afectados y producir HCA + Contract Reconciliation proporcional.

# Pruebas mínimas

- fixtures READY/BLOCKED/UNKNOWN;
- missing evidence y stale evidence;
- blocker owner/next action determinísticos;
- role negative y approval separation;
- no-overclaim;
- API/UI mapping y project-scope fail-closed;
- Test Impact + focal/acumulativa del delta.

No ejecutar Full Regression.

# Evidencia mínima

- `release_readiness_report.json`;
- source delta manifest;
- Test Impact;
- historical contract sweep;
- contract reconciliation sweep;
- identity Git pre/post;
- browser verifier/screenshots solo si la UI cambió y requiere acceptance;
- implementation report con riesgos/limitaciones y S0/S1.

# PASS/BLOCK

**PASS:** todos los blockers son explícitos y trazables; `RELEASE_READY` solo con gates completos; authority separada; S0/S1=0.

**BLOCK:** READY con evidencia faltante/stale, rol no autorizado, claim no soportado o UI/API derivando autoridad desde estado local.

# Salida

Autoriza GSDLC-11-B solo después de PASS Windows y successor repo limpio/hash-bound.

## Reglas transversales obligatorias

- Ingeniería acumulativa: partir únicamente del successor Windows-validado inmediato; nunca retroceder a un repo histórico para simplificar.
- `dry-run` por defecto para mutaciones; `plan → dry-run → policy/RBAC → approval → execute → verify → evidence`.
- No `reset --hard`, `git clean`, force push, rebase destructivo, publish ni deploy remoto.
- No arbitrary shell desde el usuario. Jobs y mutaciones deben ser operaciones tipadas/allowlisted.
- Runtime stores, secretos, `.git`, `.venv`, `outputs/`, `.pytest_cache/`, `__pycache__/`, `node_modules/` y `.devpilot/devpilot.db` quedan fuera de fixtures/packages finales.
- Operadores Windows: Python preferido, pequeños, reentrantes, idempotencia por evidencia/commit/contenido; evitar assumptions de `git common-dir`, cwd o dependencias hard-coded.
- Dependencias/runtime: derivar desde `pyproject.toml`/contrato vigente y comprobar capacidad real; no instalar dependencias ad hoc en el operador.
- LF/CRLF no puede bloquear: comparar semántica UTF-8/LF o contenido Git.
- Drifts documentales puntuales no críticos se reparan en el micro-sprint activo/siguiente; no crear sprint/operator/repo independiente por sí solos.
- HCA/Contract Reconciliation proporcional en cada micro-sprint; no editar facts históricos para hacer pasar tests current-active.
- Si una evidencia PASS previa está hash-bound e íntegra y el corrective no toca esa superficie, se reutiliza; no repetir browser ni pruebas costosas por rutina.
- Cualquier guía Windows resultante debe ser una sola `.md`, pasos consecutivos, bundle desde `C:\Users\Pedro\Downloads`, comandos PowerShell dentro de triple backticks y cada comando físicamente en una sola línea.
- API/UI solo cuando corresponda y siempre foreground. Cuando se requiera browser, usar las tres consolas operativas separadas: operador, API 8787, UI 5173.
- `network_used`, `external_api_used`, `secrets_exposed` y `mutations_performed` deben quedar explícitos en evidencia.
