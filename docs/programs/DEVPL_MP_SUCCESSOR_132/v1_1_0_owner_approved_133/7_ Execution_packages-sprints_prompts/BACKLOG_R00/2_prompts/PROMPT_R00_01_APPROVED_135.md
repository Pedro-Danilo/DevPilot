---
doc_id: PROMPT-MP132-R00-01-134
version: 1.0.0
status: OWNER_APPROVED
linked_sprint: SPRINT-MP132-R00-01-134
approved_by: "Owner (autorización expresa en turno actual)"
approval_ref: "DEVPL-MP132-R00-01-OWNER-EXEC-135"
approval_method: "Conversation declaration, not digital signature"
program_zip_sha256: "9952fdf08fc9647f3b35e25c38c55a29c51eb79e699c7f1e2d4e6e7d91701764"
source_baseline_head: "8db5b44694abcced3231183e05731e732f5b8f24"
execution_authority: READ_ONLY_ONLY
---
# PROMPT R00-01 — Implementar operador Windows read-only: auditoría y preflight B

## Orden de trabajo para el implementador

Desarrolla **únicamente** `SPRINT_MP132_R00_01_PREFLIGHT_AUTHORITY_GIT_134.md`, con aprobación individual ya emitida por Owner en este turno. Consulta **literalmente** el ZIP aprobado 133 (57 MD), `BACKLOG_R00_132.md`, actos 133, source ZIP COR-130, evidencia 130, estrategia Git, contratos de registros y autoridad, auditoría COR-130, ledger v1.32 y la implementación instalada. Si falta cualquier fuente esencial, **BLOCK y solicitarla, no sustituirla por recuerdos ni docs online**. El HEAD 8db5 es ancla histórica, no garantía de estado actual. `source_changes=0`.

## Implementación requerida

1. Construye un pequeño operador Python **stdlib** (`mp132_r00_01_readonly.py`) con `--phase inspect|audit|preflight|package`; entradas explícitas `--main --mp --pilot --program-zip --baseline-zip --evidence --artifacts`; opcional `--expected-head` fail closed. No modificar `.git`, Source Registry, Pilot ni runtime, ni ejecutar Git remoto mutativo. Preferir comandos de lectura y checks estables Windows. Capturas de procesos/ignored seguras y acotadas; redactar rutas sensibles.
2. `inspect`: hashes/CRC de ZIP, lista de 57 MD y aprobación, HEAD/branch/tree/upstream/remotes de main y MP, `git worktree list --porcelain`, status tracked/untracked/ignored y locks. No marcar ausencia de proceso como PASS si no se pudo medir.
3. `audit`: identificar literalmente campos actuales históricos de Source Registry, project_state, overlay, Authority Graph; localizar schemas, tests y interfaces de publicación. Producir `REUSE_DELTA_MAP` con `REUSE|ADAPT|NEW|NO_OP` por campo/ruta y riesgo. No prescribir copiar archivos completos para evitar duplicación.
4. `preflight`: verificar paridad y condiciones de migración B; fixture Git **descartable** que demuestre secuencia de liberación/activación de rama sin mutar repo real; diseñar rollback y backups sin guardarlos automáticamente si contienen secrets. Registrar `B_PREFLIGHT_PASS|BLOCK|INCONCLUSIVE` y resultado independiente `AUDIT_PASS|BLOCK`.
5. `package`: bundle de evidencia y `.sha256`, operator self-test y recibos con `last_safe_phase`/hash. No crear ZIP circular de logs ni modificar evidence sellada en re-runs.

## Pruebas exigidas

Simular con dos worktrees Git divergentes temporales, HEAD drift, branch ya ocupada, dirty tracked/untracked, archivos ignored, lock, proceso desconocido, ruta inválida, `.venv` que importa source equivocado, ZIP corrupto, duplicación e idempotencia; ninguna prueba debe escribir repos reales. Comparar antes/después git status/HEAD y hashes de los archivos relevantes. Distinguir `NO_PERMISSION/UNKNOWN` de `PASS`.

## Entrega para el Owner

Bundle `.zip` de operador + suite focal + **una única** `GUIA_UNICA_WINDOWS_R00_01.md`, comandos PowerShell una línea física por paso, rutas configurables, criterios por fase, `PASS/BLOCK` y cómo retomar. Markdown de auditoría y propuesta A/B. Manifiesto SHA de archivos. Incluye test de imports/syntax, test negativo y ensayo completo en fixture. No declarar preflight Windows PASS hasta obtener evidencia Windows del Owner.

## Prohibiciones de alcance

No fabricar implementación de R00-02/03, no `git worktree` mutativo en real, no egress, LLM, UI, full regression, source writes ni remover worktrees. Al recibir evidencia se adjudica R00-01 y se pide aprobación **separada** de R00-02. Ante cierre de ventana de herramientas, crear `CHECKPOINT_134.json/md` con archivos terminados, pruebas y siguiente acción verificable.

## Rebind (135)

Esta versión del prompt está autorizada únicamente para producir el operador y evidencia de R00-01. Ninguna fase Windows puede mutar repositorios. Las observaciones manuales se guardan en evidencia externa, y el preflight B es una conclusión condicional; R00-02 requiere aprobación específica.
