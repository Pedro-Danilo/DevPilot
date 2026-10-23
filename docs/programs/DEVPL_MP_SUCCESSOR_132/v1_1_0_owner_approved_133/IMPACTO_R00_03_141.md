# Rebind documental después de COR-141 — lectura literal de MP132

## Fuentes auditadas

Se consultaron los 76 `.md` del paquete extraído `DEVPL_MP_SUCCESSOR_132_v1_1_0_OWNER_APPROVED` (315459 bytes de texto cargado), incluidos `3_gobernanza/02_ESTRATEGIA_GIT_WORKTREE_132.md`, `1_arquitectura/ADR-MP-132-008.md`, `0_program/09_DECISION_OWNER_GIT_B_CONDICIONAL_133.md`, `4_backlogs/BACKLOG_R00_132.md`, sprint/prompt 134 de R00-02 y R00-03, el plan de desagregación y el contrato de autoridad. Se mantuvieron sin alterar los textos/bytes aprobados, cuyo contenido es autoridad histórica.

## Contradicciones y sucesiones detectadas

1. `PROMPT_MP132_R00_02_GIT_LOCATION_DECISION_134.md` dice no borrar linked worktree. La orden Owner actual requiere desactivarlo definitivamente. La excepción queda limitada a la ADR-S1 con un gate destructivo separado.
2. COR-140 solo ofrece A; `R00_02_OWNER_DECISION_140.txt` quedó PENDING. COR-141 reemplaza ese paso de ejecución, **no** altera ni firma falsamente el acta histórica COR-140.
3. El sprint R00-02 134 habla de migración B sin borrar worktrees; la nueva evidencia añade `retire` posterior a verify, y debe incorporarse a la futura versión publicada, sin reescribir los 57 MD originales.
4. El antiguo path MP sigue documentado como *histórico de entrada* en ADR-008 y estrategia 132. R00-03 publicará el path real seleccionado, sin cambiar la procedencia histórica.

## Actualizaciones exigibles en R00-03, condicionadas a PASS Windows

- Publicar los 57 Markdown de autoridad aprobada **byte-idénticos** (no alterar la fuente aprobada).
- Registrar un sucesor/adenda en namespace gobernado para ADR-008, ubicación B y retiro de linked MP.
- Reconciliar `source_registry.json`, `.devpilot/project_state.json`, `.devpilot/docs_governance/rebaseline_p0_overlay.json`, registers de autoridad, índice de ADR/ledger y tests focales afectados por path/branch/HEAD **según auditoría de existencia real** (sin inventar claves).
- Guardar `R00_02_B_RECEIPT_141.json` como evidencia decisional externa previa; añadir referencia a backup y adjudicación Owner; dejar antiguos estados A-only como históricos, no activos.
- Validar que todos los scripts posteriores del programa resuelvan worktree MP desde registro actual (`D:\Projects\DevPilot_Local`) y no de constante del antiguo linked.
- No ejecutar R00-03, commit, push ni actualizar autoridad dentro de Git en COR-141.

## Próximas acciones

1. Ejecutar COR-141 en Windows y devolver ZIP/SHA, consola y, en caso de bloqueo, último JSON de progreso.
2. Adjudicar `G-R00-02` usando evidencia real; no adelantar `MIGRATED_B_PASS` en ausencia de retirada sellada.
3. Solo tras adjudicación, autorizar individualmente R00-03 y rebind a branch/HEAD/path reales.
