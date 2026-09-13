---
doc_id: "PROMPT-DEVPL-GSDLC-12-D-REBOUND-REPO428"
title: "DEVPL-GSDLC-12-D — Performance, security red-team and resource/cost hardening — execution rebound repo428"
status: "approved"
version: "1.0.1"
owner: "Ordóñez"
updated: "2026-09-13"
approval: "approved_by_owner/rebound_repo428_after_12_c_windows_pass"
execution_source_repo: "repo_DevPilot_Local_428_DEVPL_GSDLC_12_C_GUIDED_EXPERT_ACCESSIBILITY_HELP_WINDOWS_VALIDATED_CANDIDATE.zip"
execution_source_commit: "de3f3008dcc0fcbc6071462bffb70a18e2ab6109"
execution_source_sha256: "4aba885046eacaf2a6c2f3e6b33bec3c40aba845d65522ae440a9c6c94a52c1e"
full_regression_budget: "0 in 12-D; 0/1 GSDLC-12 reserved for 12-E"
---

# Execution rebound

12-C está `CLOSED/PASS/WINDOWS-VALIDATED`; esta ejecución parte exclusivamente de repo428. No se permite regresar a repo427/repo425. La aceptación browser de 12-C se reutiliza hash-bound porque 12-D no cambia UX/control surfaces.

# Objetivo

Someter DevPilot a cargas, abuso de recursos y ataques realistas, cerrando S0/S1 antes del RC sin convertir red-team en ejecución peligrosa real.

# Implementación requerida

1. Resolver execution source desde successor Windows-validado de 12-C.
2. Crear performance baseline actual: startup, critical API latency, large repo/docs indexing/listing, Project Status, major workbenches, browser responsiveness, memory/process ceilings y bounded job queues.
3. Definir budgets current-active con justificación y hard ceilings; congelar históricos anteriores como snapshots, no sobrescribirlos.
4. Red-team auth/session/CSRF/RBAC/approval: fixation, stale/revoked sessions, role downgrade, cross-workspace access, approval reuse/hash mismatch, duplicate execute.
5. Red-team filesystem/upload/path: traversal, symlink/reparse handling, rename/delete races, archive extraction, oversized/invalid input y secret paths.
6. Red-team prompt/model/tool: prompt injection, model-route→tool escalation, forbidden `filesystem.delete`, autonomous recovery after tool error, hidden external fallback, stale provider evidence, consumer-session piggyback y real MCP/write attempt contra fake/local controlled provider only.
7. Demostrar explícitamente `ModelRouteDecision != ToolExecutionDecision`: modelo no puede concederse tool permission ni approval.
8. Resource/cost hardening: job flood, repeated planning, token/model budget abuse, queue/process bounds, cancellation y timeouts. No loop autónomo sin límite.
9. Supply-chain: dependency install remains plan/allowlist/approval-bound; no paquetes reales dañinos ni red no necesaria.
10. Guided/Expert/AI Control Center deben aplicar la misma autoridad server-side.
11. Toda finding S0/S1 debe corregirse dentro de 12-D antes del PASS; S2/S3 puede quedar solo si tiene owner/evidence y no viola la invariante del backlog.

# Pruebas mínimas

- security negative suites determinísticas;
- fuzz/boundary inputs acotados;
- large fixture performance sin runtime stores;
- resource exhaustion simulada con ceilings;
- model/tool/provider/MCP negatives usando mocks/fakes/local-only;
- no-network/no-external fallback assertions;
- regression focal/acumulativa + Test Impact;
- no Full por rutina.

# Browser policy

Solo ejecutar browser si 12-D modifica una surface UX/control que necesite acceptance. Si no cambia UX, reutilizar evidencia 12-C hash-bound y validar transporte/policy por tests determinísticos.

# Evidencia mínima

- `industrial_hardening_report.md`;
- `performance_budget.json` y `performance_results.json`;
- `red_team_report.json` con finding severity, exploitability, evidence, fix y retest;
- resource/cost report;
- source delta/Test Impact/HCA/Contract Reconciliation;
- S0/S1 ledger = 0 al cierre.

# PASS/BLOCK

**PASS:** amenazas críticas bloqueadas; S0/S1=0; budgets cumplidos o explícitamente justificados dentro de hard ceiling; no authority escalation; network/external use conforme política.

**BLOCK:** auth/RBAC bypass, path escape, destructive Git/filesystem, model→tool authority escalation, hidden external fallback, unbounded spend/resource, supply-chain bypass o exploit S0/S1 abierto.

# Salida

Autoriza GSDLC-12-E solo después de PASS Windows. Si una Full hard-trigger fue consumida en 12-D, registrar sesión/evidencia y marcar que 12-E **no puede ejecutar otra Full**.

## Reglas transversales obligatorias

- Ingeniería acumulativa: partir únicamente del successor Windows-validado inmediato; nunca retroceder a repo425 ni a otro histórico después de que exista un successor válido.
- `dry-run` por defecto; toda mutación sensible sigue `plan → dry-run → policy/RBAC → approval cuando aplique → execute → verify → evidence`.
- Prohibidos `reset --hard`, `git clean`, force push, rebase destructivo, borrados implícitos, publish o deploy remoto.
- No arbitrary shell desde el usuario. Jobs y mutaciones son operaciones tipadas/allowlisted.
- Runtime stores, secretos, `.git`, `.venv`, `outputs/`, `.pytest_cache/`, `__pycache__/`, `node_modules/`, `auth.db*`, `devpilot.db*` y equivalentes quedan fuera de fixtures/packages finales.
- Operadores Windows: Python preferido; pequeños, reentrantes, idempotentes por evidencia/commit/contenido y state-aware. No asumir cwd, `git common-dir`, remotes, branches ni procesos previos.
- LF/CRLF no puede provocar BLOCK: usar contenido Git o comparación semántica UTF-8/LF.
- Drifts documentales no críticos y acotados se corrigen dentro del micro-sprint activo o del siguiente natural; no crear sprint/operator/repo aislado solo por drift.
- HCA + Contract Reconciliation proporcional antes del cierre de cada micro-sprint; no reescribir hechos históricos para hacer pasar contratos current-active.
- Evidencia PASS hash-bound se reutiliza cuando el corrective no toca esa superficie; no repetir browser ni pruebas costosas por rutina.
- Cada guía Windows resultante será una sola `.md`, pasos consecutivos, orientada a personal beginner-medio, bundle desde `C:\Users\Pedro\Downloads`, y cada comando PowerShell físicamente en una sola línea.
- API/UI solo cuando corresponda, siempre foreground; para browser usar tres consolas separadas: operador, API `8787`, UI `5173`.
- Cada cierre registra explícitamente `network_used`, `external_api_used`, `secrets_exposed`, `mutations_performed`, identidad Git pre/post, S0/S1 y hashes de artefactos.
- A→D: no Full por rutina. E: única logical Full del backlog salvo hard trigger previo owner-approved que ya haya consumido el budget. FAIL funcional = preservar y NO RERUN; recovery composite selectivo obligatorio.
