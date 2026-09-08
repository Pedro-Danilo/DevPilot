---
doc_id: "PROMPT-DEVPL-GSDLC-09-C"
title: "DEVPL-GSDLC-09-C — SourceChangePlan, diff, approval, atomic apply and rollback"
status: "approved"
version: "1.0.1"
owner: "Ordóñez"
updated: "2026-09-08"
approval: "approved_by_owner/rebound_repo409_frx_v2_4"
precondition: "GSDLC-09-B CLOSED/PASS/WINDOWS-VALIDATED"
base_authority_repo: "repo_DevPilot_Local_409_DEVPL_GSDLC_09_B_CODE_WORKBENCH_WINDOWS_VALIDATED_CANDIDATE.zip"
base_authority_commit: "3c06d72445525e9b6d246726e5d6c6eb58fd20d4"
base_authority_sha256: "857084478f2661c471bc3421e23a68dfb027855e3321f52bd05ac21a7db64573"
execution_source_policy: "successor-of-GSDLC-09-B/repo409"
frx_execution_profile_id: "frx-v2.4-current"
frx_execution_profile_sha256: "2339df5fd79134fa8a675092e71ed71c8c11300b46747f055e86628e72679219"
full_regression_runs_allowed: 0
browser_required: true
---

# 03 — GSDLC-09-C

> **Execution rebind 2026-09-08.** Ejecutar exclusivamente sobre `repo_DevPilot_Local_409_DEVPL_GSDLC_09_B_CODE_WORKBENCH_WINDOWS_VALIDATED_CANDIDATE.zip` / `3c06d72445525e9b6d246726e5d6c6eb58fd20d4` / SHA-256 `857084478f2661c471bc3421e23a68dfb027855e3321f52bd05ac21a7db64573`. FRX-v2.4 current profile permanece obligatorio; 09-C consume `full=0` y exige browser real.

Implementa exclusivamente `SourceChangePlan`, full diff, Test Impact preview, risk/approval binding, preimage revalidation, atomic apply y rollback.

## Política transversal obligatoria

- Ingeniería acumulativa: nunca retroceder a un repo histórico para simplificar.
- No `reset --hard`, `git clean`, force push ni eliminación de `.git`.
- Operador Windows reentrante, Python preferido; cada comando PowerShell termina PASS verde o BLOCK rojo.
- API/UI exactamente en Consola 2/3 foreground cuando se ejecuta browser; Consola 1 queda para operador/comandos.
- Runtime stores (`auth.db*`, `devpilot.db*`, equivalentes), caches, outputs y secretos quedan fuera de fixtures/evidence/packages salvo evidencia explícitamente empaquetada fuera del repo fuente.
- LF/CRLF no puede producir BLOCK; payload y pre/postimage de texto se comparan por contenido UTF-8 normalizado LF.
- Historical Contract Authority y Contract Reconciliation Sweep son precondiciones de cierre.
- No editar aserciones históricas para hacer pasar pytest; usar `historical-freeze/current-active/successor-needed/deprecated-after-proof/derived/runtime-ephemeral`.
- La única Full Regression del backlog sigue reservada para 09-E.

## Operación mutante

`draft → immutable plan → dry-run → policy/RBAC → human approval → preimage revalidation → atomic execute → verify → evidence`.

- multi-file all-or-nothing;
- backup/preimage hash;
- stale plan/path inesperado/rol incorrecto = BLOCK;
- fault injection produce compensating rollback completo;
- rollback manual requiere approval diferente;
- `patch.apply`, shell, terminal, Git stage/commit, agent self-apply y writes fuera del exact-path allowlist continúan bloqueados.

## Browser

Demostrar plan/diff/Test Impact/risk, approval owner real, apply, stale-preimage BLOCK aislado, rollback approval separado y source hash parity/restauración final.

## Regresión

No full. Focal + security/fault injection + acumulativa A-C + Test Impact + Historical Contract Authority + Contract Reconciliation.

PASS: writes = plan aprobado, no partial residue, rollback limpio, browser real PASS, S0/S1=0.
