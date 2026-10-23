---
doc_id: SPRINT-MP132-R00-02-134
version: 1.0.0
status: DRAFT_EXECUTION_GATED
approval_scope: PROPOSED_INCREMENT_ONLY
program_authority: DEVPL-MP-SUCCESSOR-132/OWNER-133
source_baseline: 8db5b44694abcced3231183e05731e732f5b8f24
requires_owner_sprint_approval: true
execution_authority: false
source_mutation_authorized: false
conditional_worktree_operations: OWNER_APPROVAL_AFTER_PREFLIGHT
---
# R00-02 — Selección y migración condicional de la ubicación canónica

## A. Objetivo

Resolver **antes del primer cambio de source del sucesor** si la rama canónica MP se opera en el worktree principal `D:\Projects\DevPilot_Local` (opción B preferida) o permanece en `D:\Projects\DevPilot_Worktrees\DevPilot_Multiprovider` (A, fallback). La decisión B está aceptada por Owner-133 **solo si Windows preflight PASS**; aceptación arquitectónica no sustituye aprobación ejecutiva del plan exacto. No crear un nuevo merge, Git root ni rama duplicada.

## B. Precondiciones

`G-R00-01 AUDIT_PASS`, recibo live git y mapa de riesgos, confirmación Owner sobre plan exacto/HEAD/path/backup, operadores/guía revisados; procesos críticos detenidos por Owner si fuera pertinente, no detener servicios automáticamente. Prohibir trabajar si `.venv`, tracked/untracked/ignored o locks no están reconciliados. Si remote ha cambiado, BLOCK y retorno a auditoría de **nueva versión** sin repetir fases ya selladas.

## C. Flujo B cuando `B_PREFLIGHT_PASS`

1. `inspect`: validar HEAD y paridad branch/upstream de ambos, checkouts libres de cambios no autorizados, backup verificable de estados locales autorizados, sin filtros de archivos sensibles en ZIP.
2. `prepare`: registrar preimages de branch/HEAD y rutas, preservar explícitamente `official/devpilot-local` como **ref histórica**, verificar que la rama MP está activa en un solo worktree. Plan de recuperación separado para error antes/después de cambiar el checkout.
3. `owner-confirm`: requerir aprobación exacta de `MIGRATE_WORKTREE_B_R00_02`, sin inferirla del acto global 133.
4. `execute`: liberar `evolution/multiprovider-v2` del linked worktree mediante operaciones Git soportadas y no destructivas, y activarla en main worktree; prohibir `--ignore-other-worktrees`, `reset --hard`, `rebase`, force, copiar `.git`, eliminar worktrees. Utilizar comandos construidos sólo tras auditar estado real; **no** codificar secuencia destructiva universal.
5. `validate`: demostrar una única rama MP checked-out, HEAD todavía `8db5b446…`, remote/upstream coherentes, backups y referencias intactos, import/runtime correctos, smoke focal sin writes persistentes. Ningún proyecto externo o histórico modificado.
6. `package`: sellar recibo, matriz de before/after y evidencia. Estado `MIGRATED_B_PASS` únicamente con todas las pruebas.

## D. Flujo alternativo A cuando B está bloqueada

No intentar parcialmente B. Crear decisión formal `RETAIN_A_B_BLOCKED` con resultado del preflight, autorización Owner para continuar R00-03 en MP, advertencias y condicionantes. No generar commit de migración ni presentar B como elegida. La alternativa A puede cerrar **este sprint** si su decisión y evidencia están completas; no equivale a corregir B.

## E. Entregables

`R00_02_LOCATION_DECISION_134.md`, `R00_02_EXECUTION_RECEIPT_134.json` con `chosen_worktree`, `chosen_branch`, `head`, `remote`, `mode=B|A`, `migration_operations`, `rollback_state`, `source_commits=0`, `worktrees_preserved`, `operator_project_writes=0`; evidencia ZIP+SHA, guía única Windows y checkpoint idempotente. Si se opta por B y un control post falla: `BLOCK_MIGRATION`, preservar estado y reportar recuperación aprobable, **sin reset hard**.

## F. Gate para R00-03

`G-R00-02 WORKTREE_LOCATION_DECIDED`: resultado `MIGRATED_B_PASS` o `RETAINED_A_APPROVED`; un HEAD equivocado o instalación incierta bloquea. Este sprint no publica los 57 documentos; los siguientes reciben el worktree elegido y lo verifican otra vez. No actualizar el Source Registry en R00-02: el primer baseline sucesor **será R00-03**.
