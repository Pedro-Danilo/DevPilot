---
doc_id: "PROMPT-DEVPL-GSDLC-12-ACTIVATION"
title: "DEVPL-GSDLC-12 — Activation/rebind on repo425"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-09-12"
approval: "approved_by_owner"
execution_source_repo: "repo_DevPilot_Local_425_DEVPL_GSDLC_11_E_CLEAN_INSTALL_BROWSER_RELEASE_CLOSURE_WINDOWS_VALIDATED_CANDIDATE.zip"
execution_source_commit: "b341370633e66355add6bb2611879b32f277ad0f"
execution_source_sha256: "d4a9cf4b3b8d544b71ee9b568e7ba3388cf39e74ce8d213d3b0e9f9d2946695d"
activation_mode: "absorbed-into-GSDLC-12-A/no-standalone-sprint-repo-operator"
full_regression_budget: "GSDLC-12 starts 0/1; no Full in activation/A by routine"
frx_execution_profile_id: "frx-v2.4-current"
frx_execution_profile_sha256: "2339df5fd79134fa8a675092e71ed71c8c11300b46747f055e86628e72679219"
---

# Objetivo

Materializar el binding de ejecución de DEVPL-GSDLC-12 sobre repo425 **dentro del delta de GSDLC-12-A**, sin crear un sprint administrativo independiente.

# Precondiciones reproducibles

1. Verificar SHA-256 del ZIP repo425 y commit `b341370633e66355add6bb2611879b32f277ad0f`.
2. Verificar `GSDLC-11-E` y `DEVPL-GSDLC-11` en `CLOSED/PASS/WINDOWS-VALIDATED/COMPOSITE-RECOVERY`.
3. Verificar Full GSDLC-11 `1/1`, original FAIL preservada `3077/65/0/5/3147`, recuperación `65/65 + 93/93 + Historical Regression Guard + post-gates`, segunda Full `0`.
4. Verificar `S0/S1=0`, repo425 current, `GSDLC-12 authorized=true`, y coherencia Project State/Source Registry/README/roadmap.
5. No mutar source si repo/commit/hash o autoridad current-active discrepan.

# Rebind a integrar en 12-A

- Establecer `DEVPL-GSDLC-12 = ACTIVE/GSDLC-12-A` en superficies current-active pertinentes.
- Mantener repo425 como baseline canónico y registrar el successor de 12-A únicamente tras PASS Windows.
- Preservar snapshots/facts históricos de GSDLC-11, incluida la Full FAIL original y su adjudicación composite.
- Iniciar budget propio de GSDLC-12 en `0/1` reservado para 12-E salvo hard trigger owner-approved.
- Absorber como gap current-active la contradicción UX donde `Project Status` puede mostrar agregado `BLOCKED` pese a `Lifecycle RELEASED`; no reabrir GSDLC-11 ni alterar evidencia sellada.

# Validación

Solo autoridad/binding + Test Impact/HCA/Contract Reconciliation necesarios para 12-A. `Full Regression = 0`. No browser separado de activación; el browser pertenece a 12-A si el comportamiento de resume/recovery cambia.

# PASS/BLOCK

**PASS:** repo425/commit/hash coherentes; predecessor CLOSED/PASS; GSDLC-12 autorizado; rebind integrado en 12-A; budget 0/1; ninguna autoridad histórica sobrescrita.

**BLOCK:** mismatch de repo/commit/hash, predecessor no cerrado, S0/S1 abiertos, segunda Full histórica distinta de 0 o current-authority incompatible.

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
