---
doc_id: "PROMPT-DEVPL-GSDLC-11-ACTIVATION"
title: "DEVPL-GSDLC-11 — Activation/rebind on repo420"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-09-11"
approval: "approved_by_owner"
execution_source_repo: "repo_DevPilot_Local_420_DEVPL_GSDLC_10_E_STORY_CYCLE_BROWSER_CLOSURE_WINDOWS_VALIDATED_CANDIDATE.zip"
execution_source_commit: "8d37c29214a67b28d1dfd70a204a8c9596c53ae8"
execution_source_sha256: "b45f53c28599df6755aedb14eeec6318ca30df8da27a8526727d0ff8a9e98822"
activation_mode: "absorbed-into-GSDLC-11-A/no-standalone-sprint-repo-operator"
full_regression_budget: "GSDLC-11 starts 0/1; no Full in activation/A by routine"
frx_execution_profile_id: "frx-v2.4-current"
frx_execution_profile_sha256: "2339df5fd79134fa8a675092e71ed71c8c11300b46747f055e86628e72679219"
---

# Objetivo

Materializar el binding de ejecución de DEVPL-GSDLC-11 sobre repo420 **dentro del delta de GSDLC-11-A**, sin crear un sprint administrativo independiente.

# Precondiciones reproducibles

1. Verificar SHA-256 del ZIP repo420 y commit `8d37c29214a67b28d1dfd70a204a8c9596c53ae8`.
2. Verificar que Project State, Source Registry, README y roadmap declaran `GSDLC-10-E` y `DEVPL-GSDLC-10` cerrados por composite recovery y GSDLC-11 autorizado.
3. Verificar `S0/S1=0`, Full de GSDLC-10 `1/1` histórica, segunda Full `0`.
4. No mutar source si cualquiera de esas autoridades discrepa.

# Rebind a integrar en 11-A

- Establecer `DEVPL-GSDLC-11 = ACTIVE/GSDLC-11-A` en superficies current-active pertinentes.
- Mantener repo420 como baseline canónico del predecessor y registrar el successor de 11-A únicamente después de PASS Windows.
- Reconciliar Project State, Source Registry, README, roadmap y local release criteria en el mismo source delta de 11-A.
- Preservar snapshots/facts históricos de GSDLC-10; no reinterpretar la Full FAIL original como PASS.
- Registrar como drift documental no bloqueante heredado que `docs/audits/DEVPL_GSDLC_10_E_IMPLEMENTATION_REPORT.md` menciona `v1.0.7` en su narrativa de cierre, aunque la evidencia Windows autoritativa demuestra que el operador final fue `v1.0.11`. Corregirlo dentro del delta natural de 11-A mediante erratum/current-doc reconciliation, sin reescribir evidencia sellada ni cambiar el hecho de cierre.

# Validación

Solo checks de autoridad/binding y Test Impact necesarios para 11-A. `Full Regression = 0`. No browser separado de activación; si 11-A introduce UI, su browser acceptance pertenece a 11-A.

# PASS/BLOCK

**PASS:** repo420/commit/hash coherentes; predecessor CLOSED/PASS; rebind integrado al delta de 11-A; ninguna autoridad histórica sobrescrita.

**BLOCK:** mismatch de repo/commit/hash, GSDLC-10 no cerrado, S0/S1 abiertos o current-authority incompatible.

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
