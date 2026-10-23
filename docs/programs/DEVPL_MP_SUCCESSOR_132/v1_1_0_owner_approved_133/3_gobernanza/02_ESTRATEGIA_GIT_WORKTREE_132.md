---
doc_id: DEVPL-MP-SUCCESSOR-132-02_ESTRATEGIA_GIT_WORKTREE_132
title: "Estrategia Git y alternativa B — Gate de migración pre-primer source change"
version: "1.1.1-r00-succ"
status: "SUCCESSOR_DRAFT_FOR_OWNER_REVIEW"
baseline_commit: "66ab2e6227072c951b5bd2ac9160e8515b1b9fc0"
historical_baseline_commit: "8db5b44694abcced3231183e05731e732f5b8f24"
owner: "Owner DevPilot"
supersedes_program: "DEVPL_MP_SUCCESSOR_131 v1.0.0"
execution_authority: false
approval_revision: 1
approval_date: "2026-10-13"
approved_by: "Owner Ordóñez (instrucción explícita en conversación)"
approval_scope: "PROGRAMMATIC_PLANNING_ONLY"
successor_execution_authority: false
owner_decision_ref: "DEVPL-MP-132-OWNER-APPROVAL-133"
---

# Estrategia Git y alternativa B — Gate de migración pre-primer source change

## 1. Hechos comprobados

`D:\Projects\DevPilot_Local` es main worktree y aloja el common `.git`; `official/devpilot-local` en histórico `f5c4b0f1…`. `D:\Projects\DevPilot_Worktrees\DevPilot_Multiprovider` es linked worktree de ese mismo `.git`, con `evolution/multiprovider-v2` HEAD **8db5b44694ab…**. Salida Windows anterior mostró **63 worktrees** aproximadamente, muchos históricos de validación; compartir Git no significa que sean clones independientes ni que limpiar los worktrees sea necesario para migrar.

## 2. Opciones

- **A Continuar MP:** menor riesgo inmediato, source ya validado allí, principal conserva rama histórica. Adecuado si B preflight falla.
- **B Preferida condicional — mover operación canónica a DevPilot_Local:** favorece `.venv` principal, ruta histórica de arranque y consolidación de uso, si se prueba migración sin pérdida. Cambio de ubicación del checkout, **no nuevo merge ni nuevo Git root**.
- **C Clonar repositorio separado:** sólo si hay necesidad clara de independencia operacional; añade riesgo de autoridad remota duplicada, no recomendado por defecto.

## 3. Gate R0-03 read-only requerido

Verificar HEAD/upstream/paridad, remotes, revisión de tracked/untracked/ignored en ambos worktrees, permisos, `.git/worktrees` y locks, procesos API/UI/workers activos, runtime DB, datos, `.venv`/editable installs/import paths, `.devpilot` local, evidencia histórica y backups verificables. Construir rollback de retorno al worktree MP **sin modificar histórico**, la aprobación Owner-133 es **condicional**, vinculada a preflight Windows PASS y control de rutas/estado del operador, y el ensayo en clones descartables confirma secuencia. Si el preflight da BLOCK no ejecutar B; no se necesita volver a aprobar la preferencia B, pero sí registrar el gate y la ejecución exacta.

Si el gate pasa: liberar checkout MP mediante procedimiento Git autorizado sin borrar el contenido ni usar `--ignore-other-worktrees`, preservar `official/devpilot-local` como referencia histórica, y activar rama canónica en `DevPilot_Local`, con tests focales, imports/source location, arranque API/UI, read-only checks y rollback si falla. No modificar Pilot A, worktrees de evaluación ni archivos ignorados sin respaldo. Si falla: mantener A con `BLOCK_MIGRATION`, no bloquear el programa por entero.

## 4. Prohibiciones

No ejecutar switch/rebase/reset-hard/force-push hoy. No copiar `.git`; no duplicar checkout de rama, no borrar 63 worktrees, no confundir ZIP `git archive` con repo que incluye `.git`, no perder `outputs/` o `venv` locales. Git 3-state y `diff --check` por semántica, sin falsos fallos CRLF/LF.

## 5. Autoridad futura

El `Program Authority Register` conserva rama, HEAD, remote y worktree seleccionado. Cada futuro incremento se rebindea al HEAD real; script que asume MP path antiguo debe revisarse. Se permite decisión de no migrar si el costo/risgo supera beneficios; alternativa B sigue como preferencia, no un dogma.


---

## Addendum operacional M0→R1 — sucesor de planificación (14-10-2026)

- **Asunto:** Git.
- **Actualización concreta:** Topología B acreditada COR-143; D:\Projects\DevPilot_Local es único worktree operativo MP; no recurrir al linked eliminado.
- **Evidencia vinculada:** COR-143 (migración B), R00-03/COR-145 (publicación 57 documentos), R00-04/COR-147 (auditoría Settings), COR-150 (paridad 1752), COR-151 (cierre Owner M0).
- **HEAD de autoridad técnica:** `66ab2e6227072c951b5bd2ac9160e8515b1b9fc0`. Las referencias a `8db5b44694abcced3231183e05731e732f5b8f24` y los indicadores `STOP ACTIVE` en secciones históricas no se reescriben como si fueran estados presentes.
- **Autoridad:** copia sucesora propuesta para adopción documental posterior; no constituye un commit, promoción Git, autorización de R1, de MP-1B, de modelo/API externa ni una aceptación funcional de Settings.
- **Transferencias vigentes:** `MP132-R0-09` → R2 para mediciones reales; UX Settings pendiente de reproducción y validación; egress externo DENY; no duplicar ownership entre olas.
