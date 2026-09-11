---
doc_id: "PROMPT-DEVPL-GSDLC-11-B"
title: "DEVPL-GSDLC-11-B — Reproducibility, source package, checksum and SBOM"
status: "approved"
version: "1.0.1"
owner: "Ordóñez"
updated: "2026-09-11"
approval: "approved_by_owner"
precondition: "GSDLC-11-A CLOSED/PASS/WINDOWS-VALIDATED"
execution_source_policy: "repo_DevPilot_Local_421_DEVPL_GSDLC_11_A_RELEASE_READINESS_WINDOWS_VALIDATED_CANDIDATE.zip / 01c28e73994b74699802dcbac9bb06d686841b89 / e105736c539f37ea3ad81b96ad571149035c5bb77602e0303018f304c04e8955"
full_regression_budget: "0 in 11-B; GSDLC-11 budget remains unconsumed unless an explicit owner-approved hard trigger exists"
browser_policy: "only if package/reproducibility UI introduced or materially changed"
---


## Rebind de ejecución obligatorio — repo421

La única autoridad de ejecución de GSDLC-11-B es `repo_DevPilot_Local_421_DEVPL_GSDLC_11_A_RELEASE_READINESS_WINDOWS_VALIDATED_CANDIDATE.zip`, commit `01c28e73994b74699802dcbac9bb06d686841b89`, SHA-256 `e105736c539f37ea3ad81b96ad571149035c5bb77602e0303018f304c04e8955`. Repo420 y anteriores quedan como historia/diseño, no como baseline ejecutable. `GSDLC-11-A = CLOSED/PASS/WINDOWS-VALIDATED`, `Full Regression GSDLC-11 = 0/1`.

**FRX-v2.4 A/B aplicado:** reconciliar drift determinista current-active dentro de 11-B; preservar snapshots/facts históricos; clasificar HCA; ejecutar Contract Reconciliation + Test Impact/focal/acumulativa; Full de 11-B = 0 salvo hard trigger owner-approved explícito.

# Objetivo

Generar desde DevPilot un source/release package reproducible, checksum y SBOM commit-bound, componiendo la maquinaria existente y sin crear un segundo packaging stack.

# Implementación requerida

1. Resolver el commit exacto y tree limpio autorizado por 11-A.
2. Reutilizar `ReleaseManifest`, reproducibility verifier, Windows/local packaging y SBOM machinery existentes; documentar explícitamente cualquier gap antes de extenderlos.
3. Ejecutar packaging como job tipado/allowlisted, no shell arbitrario.
4. Construir `release_artifact_manifest.json` con artifact→commit/tree binding, file count, exclusions, hashes y provenance.
5. Generar sidecars SHA-256 reproducibles y verificables.
6. Generar SBOM con el formato/capacidad ya soportado; no afirmar coverage que el mecanismo no pueda demostrar.
7. Detectar y bloquear secretos, runtime DBs, caches, `.git`, `.venv`, outputs, node_modules y otros forbidden entries.
8. Verificar que dos derivaciones equivalentes del mismo source authority producen manifest/checksum semánticamente reproducibles; timestamps/noise no deben invalidar reproducibility si la política los excluye.
9. No publicar ni subir artefactos a servicios externos.
10. Actualizar UI/API para mostrar package status, commit binding, checksum y SBOM refs sin transferir autoridad al navegador.

# Pruebas mínimas

- archive hygiene/forbidden entries;
- checksum positive/negative;
- artifact→commit mismatch;
- SBOM schema/provenance;
- deterministic/reproducible manifest;
- junction/symlink/path escape fail-closed;
- package job lifecycle y sanitized logs;
- Test Impact + focal/acumulativa.

No ejecutar Full Regression.

# Evidencia mínima

- `release_artifact_manifest.json`;
- checksum sidecars;
- SBOM + schema validation;
- reproducibility comparison report;
- package job result/log refs;
- source delta/Test Impact/HCA/Contract Reconciliation;
- Git identity y package hashes.

# PASS/BLOCK

**PASS:** package reproducible, limpio, checksum/SBOM válidos y ligado al commit exacto.

**BLOCK:** forbidden entry, secret, hash mismatch, artifact no ligado al commit, path escape o segundo packaging stack divergente.

# Salida

Autoriza GSDLC-11-C únicamente tras PASS Windows.

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
