---
doc_id: "PROMPT-DEVPL-GSDLC-11-C"
title: "DEVPL-GSDLC-11-C — Install, upgrade and rollback workflows"
status: "approved"
version: "1.0.1"
owner: "Ordóñez"
updated: "2026-09-11"
approval: "approved_by_owner"
precondition: "GSDLC-11-B CLOSED/PASS/WINDOWS-VALIDATED"
execution_source_policy: "repo_DevPilot_Local_422_DEVPL_GSDLC_11_B_REPRODUCIBLE_PACKAGE_SBOM_WINDOWS_VALIDATED_CANDIDATE.zip / 836145a853fbae502f58e43b1cdab5126983a987 / f6285bb75e79873f594f8edc47621c113a8100c301af4ff1ef64bcf01700c23c"
full_regression_budget: "0 in 11-C"
browser_policy: "required for install/upgrade/rollback workflow UI introduced by 11-C"
---


## Rebind de ejecución obligatorio — repo422

La única autoridad de ejecución de GSDLC-11-C es `repo_DevPilot_Local_422_DEVPL_GSDLC_11_B_REPRODUCIBLE_PACKAGE_SBOM_WINDOWS_VALIDATED_CANDIDATE.zip`, commit `836145a853fbae502f58e43b1cdab5126983a987`, SHA-256 `f6285bb75e79873f594f8edc47621c113a8100c301af4ff1ef64bcf01700c23c`. Repo421 y anteriores quedan como historia/diseño, no como baseline ejecutable. `GSDLC-11-B = CLOSED/PASS/WINDOWS-VALIDATED`; `Full Regression GSDLC-11 = 0/1`.

**FRX-v2.4 A/B aplicado:** reconciliar drift determinista current-active dentro de 11-C; preservar snapshots/facts históricos; HCA + Contract Reconciliation + Test Impact/focal/acumulativa; Full de 11-C = 0 salvo hard trigger owner-approved explícito.

**Maturidad:** 11-C implementa una primera versión local/sandbox-only de install/upgrade/rollback. No equivale a instalación de producción, migración de datos reales ni lifecycle remoto/enterprise.

# Objetivo

Validar clean install, upgrade y rollback local desde un workflow UI gobernado, usando únicamente targets controlados y sin tocar datos de producción.

# Implementación requerida

1. Crear `InstallPlan` tipado desde el package commit-bound de 11-B.
2. Ejecutar clean install smoke en sandbox/target controlado bajo árboles DevPilot ya gobernados; no crear nuevas rutas raíz operativas.
3. Verificar arranque/capability mínima de la instalación, identidad de versión y checksums.
4. Crear `UpgradePlan` con preflight y backup obligatorio antes de cualquier mutación.
5. Separar `rollback dry-run` de `rollback execute`; execute solo con policy/RBAC/approval aplicables.
6. Inyectar fallo controlado exclusivamente en sandbox para probar rollback, sin datos reales.
7. Verificar restauración por hashes/estado/capabilities, no solo por exit code.
8. Exponer remediation/next action desde UI; el operador Windows puede preparar sandbox y recolectar evidencia, pero no sustituir el normal journey.
9. Hacer reentrantes install/upgrade/rollback receipts para sobrevivir interrupciones; no repetir una fase ya acreditada salvo que su input authority cambie.
10. Redactar logs/secret values y registrar explícitamente mutaciones.

# Pruebas mínimas

- clean install positive/negative;
- install checksum/version mismatch;
- backup-required gate;
- upgrade plan/dry-run;
- fault-injected rollback;
- restore verification;
- interrupted/retry receipt reconciliation;
- unauthorized role negative;
- browser acceptance del workflow;
- Test Impact + focal/acumulativa.

No ejecutar Full Regression.

# Evidencia mínima

- `install_smoke_report.json`;
- `upgrade_rollback_report.json`;
- backup manifest/hash refs;
- rollback verification report;
- browser verifier/screenshots únicos;
- source delta/Test Impact/HCA/Contract Reconciliation;
- S0/S1 y riesgos.

# PASS/BLOCK

**PASS:** clean install PASS; upgrade gobernado; backup acreditado; rollback restaurado y verificado; normal journey UI sin scripts externos del usuario.

**BLOCK:** upgrade sin backup, rollback sin restore proof, mutación fuera del sandbox, estado parcial no reconciliado o autoridad UI-local.

# Salida

Autoriza GSDLC-11-D después de PASS Windows.

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
