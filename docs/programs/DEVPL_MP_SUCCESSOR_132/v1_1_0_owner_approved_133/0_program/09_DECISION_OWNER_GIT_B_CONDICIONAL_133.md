---
doc_id: DEVPL-MP-132-GIT-B-CONDITIONAL-133
status: OWNER_ACCEPTED_CONDITIONAL_PREFLIGHT
version: "1.0.0"
owner: "Ordóñez"
decision_date: "2026-10-13"
input_program_sha256: "d9743653686f6b232cdc6cd9e3983685f25a197b072848d53a200525b91647f8"
input_baseline_sha256: "fb9bd0755f702891cb0804c8e2ac03e6477e34ce4e11b77b449c8670b3d483b8"
source_head: "8db5b44694abcced3231183e05731e732f5b8f24"
approval_method: "Declaración explícita del Owner en conversación"
---

# DECISIÓN OWNER-133 — Alternativa B, condicionada

El Owner **acepta como arquitectura preferente** la concentración del desarrollo sobre `D:\Projects\DevPilot_Local`, preservando la rama Git fusionada `evolution/multiprovider-v2`, **solo si** un preflight Windows read-only acredita que la migración es viable antes del primer cambio de source del programa 132.

La aceptación condicionada **no autoriza ejecutar ahora** `git switch`, mover worktrees ni eliminar historial. Gate obligatorio: HEAD/upstream actuales, dirty Git tracked/untracked/ignored, procesos vivos, `.venv` e imports, locks, assets locales, backups y recuperación; ensayo seguro, scope exacto, guía única y confirmación de ejecución. Si BLOCK, conservar alternativa A sin que ello bloquee otras tareas de solo lectura. Nunca `--ignore-other-worktrees`, `reset --hard`, force-push ni borrado masivo de worktrees.

`decision_id=DEVPL-MP-132-GIT-B-CONDITIONAL-133`; `status=APPROVED_CONDITIONAL`; `preflight=WINDOWS_PENDING`; `migration_execution=NOT_AUTHORIZED_YET`.
