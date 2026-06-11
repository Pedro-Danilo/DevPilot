---
title: "Auditoría FUNC-SPRINT-40 — Patch preflight con verificación segura"
doc_id: "DEVPL-AUDIT-FUNC-SPRINT-40-001"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-06-11"
approval: "approved_by_owner_direction"
---

# Auditoría FUNC-SPRINT-40 — Patch preflight con verificación segura

## 1. Propósito

Validar que `FUNC-SPRINT-40` agrega una fase de preflight para patches que combina revisión determinística, política de seguridad y verificación de aplicabilidad con `git apply --check`, sin aplicar cambios al workspace productivo.

## 2. Estado

Estado: `implemented-initial`.

La capacidad queda implementada como `PatchPreflightEngine` y comando CLI `patch check`. No habilita sandbox, ChangeSet, rollback, patch apply, Git write ni refactor execution.

## 3. Funcionamiento técnico

El flujo ejecuta:

1. validación de path y política para el patch file;
2. revisión con `PatchReviewEngine`;
3. bloqueo temprano si existen hallazgos de seguridad;
4. `git apply --check` mediante `SafeSubprocessRunner` y allowlist explícita;
5. comparación de estado Git antes/después para evidenciar que el working tree no cambió;
6. emisión de `CommandResult` y reportes opcionales.

## 4. Integración con DevPilot

La implementación se integra con:

- `PatchReviewEngine`;
- `PolicyEngine`;
- `PathGuard`;
- `SecretGuard`;
- `SafeSubprocessRunner`;
- `GitAdapter`;
- `ReportEngine`;
- MIASI Tool Registry y Policy Matrix.

## 5. Rol dentro de DevPilot

`patch check` es la frontera previa a `PatchSandbox` y `ChangeSet`. Su rol es responder si un patch es revisable y aplicable sin ejecutarlo. No debe confundirse con aplicación real de patches.

## 6. Criterios PASS

- `patch check --patch-file ... --json` devuelve `CommandResult` parseable.
- Un patch aplicable retorna `PASS`.
- Un patch no aplicable retorna `FAIL`.
- Un patch con riesgo de seguridad retorna `BLOCK`.
- `git apply --check` se ejecuta solo mediante allowlist.
- El working tree permanece sin cambios.
- No se emite contenido sensible crudo.
- MIASI declara `patch.check`.

## 7. Criterios BLOCK

- El preflight modifica archivos.
- El preflight usa `subprocess` sin `SafeSubprocessRunner` o sin allowlist.
- Un patch con secreto se revisa con `git apply --check` en lugar de bloquearse antes.
- Un patch malformado causa crash.
- Se habilita patch apply, Git write, sandbox o rollback en este sprint.

## 8. Riesgos

- `git apply --check` depende de Git instalado.
- Patches grandes pueden requerir límites más estrictos.
- La aplicabilidad no equivale a corrección semántica.
- La primera versión no crea sandbox ni ChangeSet.

## 9. Veredicto

`FUNC-SPRINT-40` queda aprobado como primera versión de preflight seguro de patches. La capacidad es local-first, dry-run y preliminar; deberá evolucionar en `FUNC-SPRINT-41` hacia sandbox/ChangeSet sin tocar el workspace productivo.
