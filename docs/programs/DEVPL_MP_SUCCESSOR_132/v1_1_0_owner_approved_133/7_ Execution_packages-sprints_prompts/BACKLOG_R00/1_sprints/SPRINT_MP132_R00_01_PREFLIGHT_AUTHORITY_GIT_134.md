---
doc_id: SPRINT-MP132-R00-01-134
version: 1.0.0
status: SPRINT_EXECUTION_APPROVED
approval_scope: PROPOSED_INCREMENT_ONLY
program_authority: DEVPL-MP-SUCCESSOR-132/OWNER-133
source_baseline: 8db5b44694abcced3231183e05731e732f5b8f24
requires_owner_sprint_approval: true
execution_authority: false
source_mutation_authorized: false
---
# R00-01 — Auditoría focal de autoridad y preflight Git B

## A. Objetivo y límites

Obtener evidencia **live Windows de solo lectura** suficiente para elegir con seguridad la topología Git del sucesor y planificar el primer commit de sincronización documental. **No** migrar worktrees ni publicar programas ni cambiar configuración. Auditoría obligatoria según `AUDIT-FIRST`, incluyendo rutas actuales, tests y contratos existentes. Capacidad central de R00-01: determinar si B es **VIABLE / BLOCKED / INSUFFICIENT_EVIDENCE**, no dar por hecho que B funciona porque `--git-common-dir` es compartido.

## B. Ítems y autoridades

`MP131-R0-03`, `MP131-R0-04`, `MP132-R0-06`; preparación focal de `MP131-R0-02` y `MP132-R0-07`. Fuentes obligatorias: 57 documentos del ZIP 133 (en especial Owner-133, ADR-008, Git, Source Registry contract), SHA/HEAD del repo COR-130, decisiones/rebaseline G5 128/129 y ledger v1.32. Test de integridad ZIP fuente, no atribuir valor ejecutivo a 131/MP v2.1.

## C. Alcance técnico de auditoría

1. Identificar `git rev-parse` para `D:\Projects\DevPilot_Local` y `D:\Projects\DevPilot_Worktrees\DevPilot_Multiprovider`: common-dir, git-dir, HEAD/tree/branch, upstream/remote, refs y `git worktree list --porcelain`; **sin modificar refs**.
2. Capturar por separado estados tracked (`git status --porcelain=v1`), untracked e ignored (listado acotado/contajes y rutas sensibles redactadas), changes staged, lock files, procesos API/UI/workers, handles cuando la herramienta lo permita; si el proceso no puede verificarse, UNKNOWN/BLOCK_MIGRATION.
3. Verificar `.venv` Python, paths de imports y editable installs, `sys.path`, rutas absolutas, UI node/runtime y datos persistentes. Solo comandos de inspección; no `pip install`, build que escriba source ni apagado de procesos.
4. Comprobar referencia `official/devpilot-local@f5c4b0f1…` histórica y `evolution/multiprovider-v2@8db5b446…`; verificar remote sin red si está accesible localmente; cualquier necesidad de fetch/red debe declararse y solicitar autorización separada.
5. Auditar `source_registry.json` (1693 entradas en snapshot), `.devpilot/project_state.json`, `rebaseline_p0_overlay.json`, Authority Graph, tests y schemas ya existentes para diseñar `REUSE_DELTA_MAP_R00_01.md`: campos de estado actuales vs históricos, 57 docs a publicar y reglas de validación; ninguna edición.
6. Elaborar `MIGRATION_B_SAFETY_PLAN` con backup verificable, proceso de liberación temporal de rama MP, activation en main worktree, rollback pre/post-commit **sin reset destructivo**, smoke focal y conservación de worktrees históricos. Distinguir dependencias de carpeta y entorno.

## D. Entregables observables

- `R00_01_PREFLIGHT_134.json`: autoritativo en la evidencia del gate, con hashes/HEAD, ramas, env, procesos, resultado B.
- `R00_01_GIT_TOPOLOGY_AND_RISKS_134.md`: reporte humano, también incertidumbres.
- `R00_01_AUTHORITY_REUSE_DELTA_MAP_134.md`: tabla campo/ruta/read/write potencial, validadores y tests existentes; `NO_OP` permitido.
- `R00_01_MIGRATION_B_SAFETY_PLAN_134.md`: pasos propuestos, precondiciones y rollback; **no** ejecutables sin R00-02.
- `R00_01_CHECKPOINT_134.json`, ZIP de evidencia, sidecar SHA-256, una única guía Windows, consola solo ante BLOCK relevante.

## E. Gate y prueba

`G-R00-01` PASS cuando los datos coinciden con la fuente y el informe enumera de forma exhaustiva riesgos, delta documental, preflight A/B y pruebas reproducibles; `B_PREFLIGHT_PASS` es independiente del `AUDIT_PASS`. Pueden existir resultados `AUDIT_PASS / B_BLOCKED`, permitiendo elegir A en R00-02. Si hay drift HEAD o credenciales expuestas, `BLOCK`. Repetición del operador debe reutilizar receipt existente al comprobar inputs idénticos; un HEAD modificado produce nueva corrida/versionado, nunca sobreescritura silenciosa.

**NO incluir:** cambios de Git, `git worktree remove`, source edits, nuevas features de Settings, MP-1B, Pilot B, llamadas L/E, full regression.

## F. Evidencia y handoff

Informe Owner: `APROBAR_B_CONDICIONAL` solo si PASS; si B BLOCK, registrar `CONSERVAR_A` y criterios de reapertura futura, sin convertir B automáticamente en PASS. Para continuar se requiere aprobación específica del Owner de la acción R00-02 y copia íntegra de evidencia + mapa de autoridad. Anotar `last_safe_phase`, inputs/hashes/paths en el checkpoint externo a los repos.
