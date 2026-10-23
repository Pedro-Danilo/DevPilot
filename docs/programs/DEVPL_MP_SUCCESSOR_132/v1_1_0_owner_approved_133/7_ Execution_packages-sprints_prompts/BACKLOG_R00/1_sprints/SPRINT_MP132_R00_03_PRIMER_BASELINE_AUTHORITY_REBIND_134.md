---
doc_id: SPRINT-MP132-R00-03-134
version: 1.0.0
status: DRAFT_EXECUTION_GATED
approval_scope: PROPOSED_INCREMENT_ONLY
program_authority: DEVPL-MP-SUCCESSOR-132/OWNER-133
source_baseline: 8db5b44694abcced3231183e05731e732f5b8f24
requires_owner_sprint_approval: true
execution_authority: false
source_mutation_authorized: false
first_new_baseline_required: true
---
# R00-03 — Primera publicación documental del programa 132 y rebind integral

## A. Objetivo y regla de cierre

**Este sprint produce el PRIMER NUEVO BASELINE Git del programa 132.** Se completa en **un solo commit gobernado**, salvo que una auditoría demuestre la necesidad de atomicidad técnica distinta y el Owner apruebe su sucesor. Publicar íntegramente la autoridad programática Owner-133 y reconciliar **todos los punteros vigentes afectados**. Sin fragmentar el rebind en commits que dejen `Source Registry`, `Project State`, `Overlay` o ADRs/actas mutuamente incoherentes.

NO construir funciones LLM, Settings funcional, Agent Runtime, modelos, UI ni código de Pilot B. Cambios permitidos: documentación programática, registros/metadata de gobernanza y **pruebas focales de esa autoridad**. Los nombres de claves y paths definitivos surgen de auditoría focal de la implementación real, **no se inventan campos inconexos**.

## B. Dependencias

`G-R00-01 AUDIT_PASS`; `G-R00-02 WORKTREE_LOCATION_DECIDED` (A/B acreditada); aprobación Owner **separada del programa** sobre allowlist y plan/preimage del R00-03; HEAD `8db5b446...` salvo si auditoría detecta cambios externos (entonces rebind explícito y nueva decisión, nunca aplicar a HEAD diferente). Programa ZIP 133 byte-for-byte, checksum `d4e22170b9ecefa6434a10e0eeefdb535714b55ea1cd6ac750516d16147e8049`; baseline fuente ZIP SHA `fb9bd0755f702891cb0804c8e2ac03e6477e34ce4e11b77b449c8670b3d483b8`.

## C. Matriz obligatoria de reconciliación

| Fuente actual | Rebind exigido | Conservación / prueba negativa |
|---|---|---|
| Paquete **57 Markdown** Owner-133 | Publicación íntegra con rutas estables bajo namespace gobernado propuesto `docs/programs/DEVPL_MP_SUCCESSOR_132/v1_1_0_owner_approved_133/`; confirmar namespace literal con el registry instalado, sin colisión | Igualdad SHA/bytes de cada MD frente al ZIP 133; ningún campo `OWNER_APPROVED` alterado; manifiesto incluido, ZIP 131/133 externos inmutables |
| `source_registry.json` | 57 entries `doc_id+path` válidas con `OWNER_APPROVED_PROGRAM`, ADR `OWNER_ACCEPTED`, actas G5/COR-130/STOP, supersession 131, referencias al programa vigente, selección A/B real | No borrar/reescribir 1693 registros existentes por supuesto; resolver colisión por `(doc_id,path)` según contrato actual, schema PASS, sin path con escapes |
| `.devpilot/project_state.json` | `current_phase` sucesor 132 R0; `current_micro_sprint` fiel al estado realmente adjudicado; `mp_g5_adjudication`, `mp_stop_status`, `mp_current_authority_document`, `mp_1b_activation` coherentes con Owner-133; `last_completed_MP` histórico | G5 `OWNER_RATIFIED` sin false E2E; STOP **global** lifted no habilita `MP-1B`, APIs externas, tools ni write sin approval; campos `_at_sync1_merge` intactos |
| `.devpilot/docs_governance/rebaseline_p0_overlay.json` | Extensión/successor de estado **actual** G5/COR-130/programa y referencias al acta/HEAD; histórica `at_sync1_merge` y hash G5 conservados | Los snapshots originales y recibos 128/129/130 no se modifican; sin reescribir `FROZEN` ni hashes históricos |
| Authority Graph / registers / tests / ADR index (si aplican) | Auditar dependencia real; actualizar **solo cuando sea necesario** para evitar dual-authority, stale refs o fallos de validador | `NO-OP` justificado por archivo; no crear segunda autoridad, ni registrar documentación inexistente |
| Versiones v131 y MP v2.1 | Registrar `SUPERSEDED_FOR_PLANNING/HISTORICAL_ONLY` para los doce archivos 131; no activar prompts MP-1B/SYNC-2 antiguos | Referencias históricas y ADRs MP v2.1 compatibles siguen legibles; external ADR-010 activación **DEFERRED** |
| R00-02 ubicación elegida | Actualizar ubicación operativa `B@DevPilot_Local` o `A@DevPilot_Multiprovider` con recibo y branch/HEAD real | Nunca registrar B como completada si no pasó preflight; `.venv` y worktrees no forman parte del ZIP del proyecto |

### Inventario mínimo obligatorio de entradas de autoridad

- `DEVPL-MP-132-OWNER-APPROVAL-133`: programa, versión, SHA de documento/ZIP, actor, scope.
- `DEVPL-MP-132-G5-RATIFICATION-133`: ratifica G5 técnico, **no** Pilot A MVP/E2E.
- `DEVPL-MP-132-COR130-RATIFICATION-133`: ratifica PASS COR-130, HEAD 8db5.
- `DEVPL-MP-132-GLOBAL-STOP-LIFT-133`: global lifted; guards de operación permanecen deny.
- `DEVPL-MP-132-GIT-B-CONDITIONAL-133`: preferencia B; resultado real A/B separado.
- `DEVPL-MP-132-ADRS-OWNER-ACCEPTANCE-133`: ADR 001–011 OWNER_ACCEPTED; ADR-010 external no habilita egress.
- Referencia exacta a `BACKLOG_R00_132.md` y 10 contratos aprobados, sin autorizar R1 ni MP-1B.

## D. Operación sugerida (NO comandos definitivos)

1. **Inspect/Audit**: HEAD worktree elegido, `git status`, manifest de 57 archivos, rutas del Source Registry, schema/tests, ownership y allowlist. `REUSE_DELTA_MAP` del nuevo HEAD; decidir paths exactos y migraciones sin borrar entradas.
2. **Prepare**: generar patch en clon/worktree efímero EXTERNO a project source; preimages SHA y schema; anclar decisión Owner. Reconciliar documentación y machine-readable sin generadores que dependan de un modelo.
3. **Validate candidate**: registro de autoridad con todos los archivos existentes y hashes, tests focales históricos COR-130 + successor, negativos (version131 active, G5 pending, global_stop ACTIVE, MP-1B autorizado, external activated, discrepancia manifest, duplicidad); verificar ausencia de cambios source/app/API/UI.
4. **Review**: mostrar plan/diff, conteos reales, cambio de estado, Source Registry total **calculado** (no fijar a 1693+57 sin verificar duplicados) y justificación de exceptions; Owner aprueba `APPROVE_R00_03_AUTHORITY_APPLY`.
5. **Apply/commit**: aplicar exclusivamente allowlist, `git diff --check`, tests repetibles, segunda confirmación Owner para commit, normal push a upstream autorizado, verificación HEAD remoto y Git 3-estados; **sin force/reset**.
6. **Package**: ZIP git archive limpio del nuevo HEAD, SHA-256, evidence ZIP/sidecar, receipt con nuevos hashes, validación CRC y prohibición `.venv`, secrets, runtime DB, `outputs/**`.

## E. Entregables verificables

`R00_03_AUTHORITY_REBIND_MAP.md`, `R00_03_SOURCE_REGISTRY_DIFF.json`, `R00_03_DECISION_REGISTER.json` o formato existente validado, `R00_03_PREIMAGE_MANIFEST.json`, `R00_03_TEST_REPORT.txt`, `R00_03_REBIND_RECEIPT.json` (`input_head`, `new_head`, `remote_head`, `branch`, `worktree`, `published_docs=57`, `source_registry_before/after`, `historical_records_preserved`, `owner_confirmations`, `full_regression=0`, `source_mutations_allowlisted`, `pilot_writes=0`), `repo_MP132_R00_03_<HEAD12>_CLEAN.zip` + `.sha256`, `R00_03_WINDOWS_EVIDENCE.zip` + `.sha256`, guía única Windows.

## F. Gate PASS/BLOCK

**PASS** solo si: todos los 57 Markdown se publicaron sin alterar bytes, ninguna referencia v131 tiene autoridad ejecutable, G5/COR-130/STOP y Git A/B coinciden en todas las proyecciones, MP-1B sigue sin permiso, esquema/validadores y negativos PASS, commit/promoción Git normales acreditados, ZIP limpio SHA/CRC. **BLOCK** si falla cualquier ítem, si solo se ha generado ZIP sin Git promotion, si un test histórico está anclado al estado viejo y se editó sin sucesor, o si aparece un path ajeno en staged set.

Una prueba heredada que exige el antiguo STOP debe modificarse **solo para comprobar snapshot histórico**, mientras una prueba sucesora valida estado nuevo; no basta actualizar el test para que pase sin evaluar ambos niveles.

## G. Checkpoint y continuidad

Checkpoint externo por fases `inspect`, `prepare`, `validate`, `owner-approve`, `apply`, `commit`, `promote`, `package`. Reanudación después de interrupción identifica el commit ya existente por padres y paths exactos y evita segundo commit; si remoto ya está actualizado, no repush automático. No borrar receipt sellado; packaging idempotente con verificaciones. Si no hay tiempo de completar el commit, dejar `PREPARED_NOT_APPLIED` y no declarar baseline limpio.
