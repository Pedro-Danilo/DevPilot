---
doc_id: "PROMPT-DEVPL-GSDLC-12-E"
title: "DEVPL-GSDLC-12-E — Full browser matrix, exactly-one Full regression and local release candidate"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-09-12"
approval: "approved_by_owner"
precondition: "GSDLC-12-D CLOSED/PASS/WINDOWS-VALIDATED"
execution_source_policy: "immediate Windows-validated successor of GSDLC-12-D"
full_regression_budget: "exactly 1 logical Full for DEVPL-GSDLC-12 unless already consumed by an explicit owner-approved hard trigger"
frx_execution_profile_id: "frx-v2.4-current"
frx_execution_profile_sha256: "2339df5fd79134fa8a675092e71ed71c8c11300b46747f055e86628e72679219"
browser_policy: "mandatory real-browser matrix before the Full unless matrix-equivalent evidence already produced in 12-D and hash-bound to unchanged UX"
execution_source_repo: "repo_DevPilot_Local_429_DEVPL_GSDLC_12_D_PERFORMANCE_SECURITY_RESOURCE_HARDENING_WINDOWS_VALIDATED_CANDIDATE.zip"
execution_source_commit: "b0fa8fe1c0a31ccd902c4b47368c15d83f5dc19a"
execution_source_sha256: "b2758b64d6156c0e8f3c1f821dadf5d26571c9e34134992eba63b7bfb7079dd8"
rebound_version: "1.0.1-repo429"
---

# Objetivo

Cerrar DEVPL-GSDLC-12 con una matriz real-browser de las capacidades críticas, clean-install/smoke, current-authority/documentation coherence y la única logical Full del backlog, generando un local RC autoritativo que permita volver al piloto/endurecimiento siguiente.

# Orden irreversible antes de consumir la Full

1. 12-A→12-D `CLOSED/PASS/WINDOWS-VALIDATED`.
2. S0/S1=0 y red-team/performance closure PASS.
3. Browser matrix PASS y evidence hash-bound.
4. Clean-install/smoke preliminar PASS sobre artifact candidato.
5. Source delta final cerrado y Test Impact sin unmatched.
6. Historical Contract Authority sweep PASS.
7. Contract Reconciliation Sweep PASS.
8. Project State / Source Registry / README / roadmap / current RC authority coherentes.
9. TCR v1/v2 y derived counters/registries coherentes.
10. runtime-ephemeral/secret exclusion PASS.
11. FRX-v2.4 current-profile plan/preflight PASS.
12. budget GSDLC-12 acreditado `0/1`, salvo hard trigger previo owner-approved. Si ya está `1/1`, **no lanzar otra Full** y usar esa sesión como autoridad del cierre.
13. profile hash/version, collection hash, topology y evidence path registrados.

# Browser matrix obligatoria

Una ejecución real-browser debe cubrir como mínimo:

- login/session/logout/relogin y restart recovery 12-A;
- Project Home y Project Status coherentes;
- project-scoped guard + registered workspace recovery;
- branch/external edit conflict/revalidation 12-B;
- Pre-code guiado;
- Planning/Roadmap;
- Documents;
- Story Code Workbench;
- Jobs;
- Calidad/Tests;
- Release readiness/package/install/version/closure;
- AI/RAG y AI Control Center si están disponibles por policy;
- Approval Center;
- Guided y Expert parity;
- owner y al menos un role-negative relevante;
- keyboard/focus/accessibility critical path;
- blockers/success/recovery messages explicables;
- no external operator requerido para el normal journey demostrado.

Capturas/machine verifier deben ser mínimos pero suficientes; no crear screenshots redundantes. Correctives que no cambian UX reutilizan la evidencia hash-bound.

# Política Full obligatoria

- Invocar el `FullRegressionExecutionProfile` por current authority; no hardcodear planner/workers/max-nodeids.
- Exactamente una logical Full para DEVPL-GSDLC-12.
- No cambiar collection/profile/plan dentro de la sesión lógica.
- Interrupción infra: reanudar **la misma sesión** únicamente sobre `UNEXECUTED`.
- FAIL/ERROR funcional: preservar Full inmutable y **NO RERUN**.
- Recovery autorizado: exact failed/error retest + bounded impacted retest + Historical Regression Guard + deterministic post-gates + accounting 100% + segunda Full=0.
- La Full histórica FAIL jamás se reescribe como PASS; el cierre puede ser `PASS/COMPOSITE-FULL-PLUS-SELECTIVE-RECOVERY` únicamente si toda la evidencia de recovery pasa.
- Si un hard trigger en A-D ya consumió la Full, E no ejecuta otra; debe verificar y cerrar con esa sesión + evidence composite correspondiente.

# Clean-install y RC

Después de browser/gates y de la adjudicación Full/composite:

1. Generar package/RC únicamente desde el closure commit exacto mediante modo tracked-only (`git archive` o contrato successor equivalente).
2. Excluir `.git`, `.venv`, `outputs`, caches, `node_modules`, runtime DBs, secretos y artifacts no committed.
3. Ejecutar clean-install/smoke del RC en sandbox/target controlado, sin afectar producción ni datos reales.
4. Generar RC manifest con repo ZIP, SHA-256, closure commit, source delta, browser matrix, Full session/accounting, S0/S1 y claims local-only.
5. Promoción oficial solo fast-forward, sin push/publish/deploy implícito.

# Evidencia mínima

- browser matrix + screenshots/verifier;
- `a11y_report`, recovery/conflict summaries y red-team/performance references;
- clean-install/smoke report;
- source delta/Test Impact/HCA/Contract Reconciliation;
- Full session marker/log/JUnit/accounting o composite recovery;
- Git identity pre/post;
- RC manifest + ZIP/SHA;
- S0/S1;
- `network_used`, `external_api_used`, `secrets_exposed`, `mutations_performed`.

# PASS/BLOCK

**PASS:** UI-complete journey probado; recovery/conflicts seguros; Guided/Expert parity; a11y critical path sin blocker; security/performance PASS; clean-install PASS; Full/composite 100% accounted; segunda Full=0; S0/S1=0; RC exact-commit y limpio.

**BLOCK:** normal journey depende de operador externo, contexto se pierde tras restart, conflicto destructivo/silencioso, auth/RBAC bypass, critical a11y blocker, budget/performance crítico incumplido, segunda Full, evidence/hash mismatch o RC con contenido prohibido.

# Cierre

Solo después del PASS Windows final: `GSDLC-12-E = CLOSED/PASS`, `DEVPL-GSDLC-12 = CLOSED/PASS`; entonces se autoriza GSDLC-13 desde el RC autoritativo.

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
