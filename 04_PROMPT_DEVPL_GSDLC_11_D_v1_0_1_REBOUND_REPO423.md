---
doc_id: "PROMPT-DEVPL-GSDLC-11-D"
title: "DEVPL-GSDLC-11-D — Version, release notes, tag and approval"
status: "approved"
version: "1.0.1"
owner: "Ordóñez"
updated: "2026-09-11"
approval: "approved_by_owner"
precondition: "GSDLC-11-C CLOSED/PASS/WINDOWS-VALIDATED"
execution_source_policy: "exact Windows-validated repo423 successor of GSDLC-11-C"
execution_source_repo: "repo_DevPilot_Local_423_DEVPL_GSDLC_11_C_INSTALL_UPGRADE_ROLLBACK_WINDOWS_VALIDATED_CANDIDATE.zip"
execution_source_commit: "3161ff7c9e216b039ac657fa52a9667a249d879d"
execution_source_sha256: "836c9bb2e24f547fc3bd6a61235b938557139a8730010ea5208acaf695f23099"
frx_execution_profile: "FRX-v2.4-current; focal+cumulative only; Full=0 in 11-D"
full_regression_budget: "0 in 11-D"
browser_policy: "required for release metadata/tag approval UI introduced by 11-D"
---

## Rebind reproducible — repo423

Este rebound fija como única fuente de ejecución de GSDLC-11-D el successor Windows-validado de 11-C: `repo423` / commit de cierre `3161ff7c9e216b039ac657fa52a9667a249d879d` / SHA-256 `836c9bb2e24f547fc3bd6a61235b938557139a8730010ea5208acaf695f23099`. GSDLC-11-C está adjudicado `CLOSED/PASS/WINDOWS-VALIDATED`; no se permite volver a repo422. FRX-v2.4 aplica drift documental acotado dentro de este micro-sprint y reserva la única Full de GSDLC-11 para 11-E.

# Objetivo

Preparar release metadata, versión, release notes, approval y annotated tag local exacto, con separación estricta entre propuesta y autoridad.

# Implementación requerida

1. Derivar changelog/release notes desde commits, stories, requirements y evidencia trazable; no inventar cambios no presentes.
2. Implementar `VersionDecision` conforme a la política/versionado vigente; divergencias entre package/version/tag deben bloquear.
3. Permitir edición manual y propuesta agent-assisted de release notes, conservando provenance.
4. Los modelos/agentes solo proponen: no pueden aprobar release, ampliar waiver ni ejecutar tag.
5. Construir `TagPlan` dry-run con commit exacto, tag name, message, release evidence refs y approval requirement.
6. Release approval debe resolverse server-side por rol autorizado y quedar bound al TagPlan/hash.
7. Ejecutar únicamente annotated tag local tras approval. No push/publication implícitos.
8. Verificar tag→commit exacto y detectar tag preexistente/conflictivo fail-closed.
9. UI debe mostrar versión, provenance, approval y tag result de forma explicable.
10. Preservar no-go históricos de deploy/publish/enterprise claims.

# Pruebas mínimas

- semantic/version policy positive/negative;
- release notes provenance;
- agent proposal authority separation;
- approval role negative/expiry/hash mismatch;
- annotated tag exact commit;
- existing tag conflict;
- no push/publication;
- browser acceptance;
- Test Impact + focal/acumulativa.

No ejecutar Full Regression.

# Evidencia mínima

- `release_notes.md`;
- `version_decision.json`;
- `tag_plan.json`;
- `release_approval.json`;
- tag/commit verification;
- browser verifier/screenshots;
- source delta/Test Impact/HCA/Contract Reconciliation.

# PASS/BLOCK

**PASS:** versión coherente; notes traceables; approval válido; tag annotated en commit exacto; no push/publication.

**BLOCK:** tag sin approval, version drift, agent/model route otorgando autoridad, tag conflictivo o provenance incompleta.

# Salida

Autoriza GSDLC-11-E solo tras PASS Windows.

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
