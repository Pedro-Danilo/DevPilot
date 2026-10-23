---
doc_id: PROMPT-MP132-R00-02-134
version: 1.0.0
status: DRAFT_AWAITING_OWNER_INCREMENT_APPROVAL
linked_sprint: SPRINT-MP132-R00-02-134
execution_authority: false
---
# PROMPT R00-02 — Operador de migración Git condicional B / decisión A

## Orden de trabajo

Implementa exclusivamente `SPRINT_MP132_R00_02_GIT_LOCATION_DECISION_134.md` cuando `G-R00-01` esté adjudicado y exista orden específica del Owner. Releer 57 MD 133 y `ADR-MP-132-008`, estrategia Git, acto `OWNER_ACCEPTED_CONDITIONAL_PREFLIGHT`, recibos Windows de R00-01 y **estado Git LIVE**; no ejecutar la secuencia sobre el snapshot ZIP extraído. La aceptación Owner-133 **no autoriza** manipular Git sin gate. Si faltan evidencia/procesos/backups/rollback, BLOCK.

## Diseño y fases obligatorias

Crear operador Python stdlib `mp132_r00_02_worktree.py` con `inspect`, `prepare`, `execute`, `verify`, `package` y `--mode B|A`, `--owner-confirmation` solo para B. En `A`, documentar decisión y conservar ambos checkouts: no mutación Git. En `B`: comprobar preflight PASS enlazado a hash, HEAD exacto, status de dos worktrees y backup, liberar rama MP únicamente mediante Git soportado y ponerla en main worktree, preservar `official/devpilot-local`; no borrar linked worktree ni archivos locales. Ejecutar postchecks de branch única, HEAD/remote, imports del Python de `DevPilot_Local`, editable installs y smoke focal; logs de cada acción y preimage. Si una etapa falla después de un cambio, no ejecutar rollback destructivo automático: generar instrucciones de recuperación reversibles sujetas a autorización y estado real.

## Control de coherencia

El resultado es `MIGRATED_B_PASS` o `RETAINED_A_APPROVED` con decisión Owner, no existe resultado implícito. Comprobar que no se produjo source commit (`new_head==8db5`), ni pérdida de worktrees/proyectos, ni `git add .`, force/reset/rebase ni overrides de worktree. No ocultar dirty ignored/outputs; proteger secretos en evidencias. En `A`, justificar por qué `B_BLOCKED` es causa de seguridad y no programar su reintento automático.

## Pruebas

Fixture en Git temporal: switch exitoso, main dirty, MP dirty, rama activa dos veces, refs cambiadas, upstream diverge, backup ausente, proceso activo, bloqueo de Git, error tras `detach` y recuperación guiada. Tests de idempotencia y que modo A no llama Git mutativo. No prometer rollback si no se ha ensayado.

## Entregables y cierre

ZIP operador, tests, una `GUIA_UNICA_WINDOWS_R00_02.md`, receipt JSON, `LOCATION_DECISION.md`, pre/post matrices, checksum SHA y checkpoint. Handoff exacto a R00-03: ruta elegida, rama, HEAD, Source Registry original, riesgos remanentes. Aprobación de migración **y** aprobación separada para posterior commit documental R00-03. No ejecutar documentación 132 en este sprint.
