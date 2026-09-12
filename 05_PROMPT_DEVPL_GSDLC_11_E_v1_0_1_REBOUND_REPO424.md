---
doc_id: "PROMPT-DEVPL-GSDLC-11-E"
title: "DEVPL-GSDLC-11-E — Clean-install browser release closure and one-full adjudication"
status: "approved"
version: "1.0.1"
owner: "Ordóñez"
updated: "2026-09-12"
approval: "approved_by_owner"
precondition: "GSDLC-11-D CLOSED/PASS/WINDOWS-VALIDATED"
execution_source_policy: "immediate Windows-validated successor of GSDLC-11-D"
full_regression_budget: "exactly 1 logical Full for DEVPL-GSDLC-11 unless already consumed by an explicit owner-approved hard trigger"
frx_execution_profile_id: "frx-v2.4-current"
frx_execution_profile_sha256: "2339df5fd79134fa8a675092e71ed71c8c11300b46747f055e86628e72679219"
browser_policy: "required real-browser release journey before Full"
---

## Rebind de ejecución — repo424 Windows-validado

- execution source: `repo_DevPilot_Local_424_DEVPL_GSDLC_11_D_VERSION_RELEASE_NOTES_TAG_APPROVAL_WINDOWS_VALIDATED_CANDIDATE.zip`;
- source closure commit: `0e711476707a83b596b3476aa7044880ceda430a`;
- source ZIP SHA-256: `53ebaee2289215169322dda1f0565df7603ab59f76ddaf643550f75ede67bdce`;
- GSDLC-11-D: `CLOSED/PASS/WINDOWS-VALIDATED`;
- Full budget entering 11-E: `0/1`; exactly one logical Full remains reserved for this closure micro-sprint;
- FRX execution profile: `frx-v2.4-current` / `2339df5fd79134fa8a675092e71ed71c8c11300b46747f055e86628e72679219`;
- bounded non-critical documentation drift is repaired inside 11-E before the Full and does not create a standalone sprint/operator/repo.

# Objetivo

Cerrar DEVPL-GSDLC-11 demostrando desde UI: readiness → package/checksum/SBOM → clean install → upgrade/rollback evidence → version/release notes → approval/tag → final local release status, y adjudicar la única Full Regression del backlog.

# Invariante E2E

El operador puede preparar fixture/sandbox, iniciar API/UI y recolectar evidencia, pero **no puede sustituir el normal journey** calculando readiness, construyendo el release final, aprobando, ejecutando upgrade/rollback o creando tag mediante scripts externos. Esas acciones deben pasar por DevPilot.

# Browser mínimo obligatorio

Demostrar una única ejecución real-browser que cubra, como mínimo:

1. release candidate y readiness explainable;
2. blocker/missing evidence cuando aplique y transición a READY;
3. package job con commit binding, checksum y SBOM refs;
4. clean install PASS;
5. upgrade plan con backup y rollback verification visible;
6. version/release notes con provenance;
7. approval por rol válido;
8. TagPlan y annotated tag local en commit exacto;
9. final release status/evidence graph coherente;
10. Project Status avanza a `RELEASED` o al estado current-active definido por el lifecycle contract;
11. normal-user external script = 0;
12. no push/publish/deploy.

Capturas únicas y numeradas con verifier machine-readable. No repetir browser por correctives que no cambien el comportamiento demostrado.

# Orden irreversible antes de consumir la Full

1. 11-A→11-D `CLOSED/PASS/WINDOWS-VALIDATED`.
2. Browser release acceptance PASS.
3. Release artifact/commit/checksum/SBOM coherentes.
4. Clean install + rollback verification PASS.
5. Release approval/tag exact commit PASS.
6. S0/S1=0.
7. Source delta final cerrado.
8. Historical Contract Authority sweep PASS.
9. Contract Reconciliation Sweep PASS.
10. Project State / Source Registry / README / roadmap/current release authority coherentes.
11. runtime-ephemeral/secret exclusion PASS.
12. FRX-v2.4 current-profile preflight PASS.
13. budget GSDLC-11 acreditado `0/1`, salvo hard trigger previo owner-approved.
14. profile hash/version y prerequisites current PASS.
15. projected topology/ETA/evidence path registrados.

Solo entonces iniciar la única logical Full.

# Política Full obligatoria

- Invocar `FullRegressionExecutionProfile` por current authority; no pasar planner/max_nodeids/workers/nodeid transport directos.
- No cambiar collection/profile/plan durante la logical session.
- Infra interruption: reanudar la misma session y solo `UNEXECUTED`.
- FAIL/ERROR funcional: preservar Full original inmutable y **NO RERUN**.
- Recovery autorizado: exact failed/error retest + bounded impacted retest + Historical Regression Guard + deterministic post-gates + accounting 100% + segunda Full=0.
- La Full histórica FAIL no se reescribe como PASS; cierre permitido como `PASS/COMPOSITE-FULL-PLUS-SELECTIVE-RECOVERY` si toda la evidencia lo soporta.

# Evidencia mínima

- release browser acceptance + screenshots/verifier;
- release readiness report;
- artifact manifest/checksums/SBOM;
- install/upgrade/rollback evidence;
- release notes/version/tag/approval;
- final release graph/status;
- source delta/HCA/Contract Reconciliation;
- Full session marker/log/JUnit/accounting o composite recovery;
- Git identity pre/post;
- S0/S1;
- package/evidence hashes;
- `network_used`, `external_api_used`, `secrets_exposed`, `mutations_performed`.

# PASS/BLOCK

**PASS:** guided local release UI-complete; reproducible package; clean install/rollback verified; role-bound approval; exact local tag; Full/composite 100% accounted; second Full=0; S0/S1=0.

**BLOCK:** normal journey depende de operador externo, artifact/commit mismatch, rollback no probado, tag sin approval, publish/deploy implícito, segunda Full o trazabilidad rota.

# Cierre

Solo después del PASS Windows final: `GSDLC-11-E = CLOSED/PASS`, `DEVPL-GSDLC-11 = CLOSED/PASS`; entonces se autoriza GSDLC-12.

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
