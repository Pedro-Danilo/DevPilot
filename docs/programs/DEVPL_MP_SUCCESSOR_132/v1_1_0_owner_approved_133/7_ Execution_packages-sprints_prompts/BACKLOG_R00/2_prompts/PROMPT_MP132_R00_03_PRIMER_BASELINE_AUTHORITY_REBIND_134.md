---
doc_id: PROMPT-MP132-R00-03-134
version: 1.0.0
status: DRAFT_AWAITING_OWNER_INCREMENT_APPROVAL
linked_sprint: SPRINT-MP132-R00-03-134
execution_authority: false
---
# PROMPT R00-03 — Primer baseline nuevo, rebind documental integral

## Orden de implementación

Desarrolla **solo** `SPRINT_MP132_R00_03_PRIMER_BASELINE_AUTHORITY_REBIND_134.md`, después de los gates Windows R00-01 y R00-02 y orden escrita específica del Owner. Este es el **primer source-changing increment de R0**; no crear cualquier otro baseline antes de publicar el rebind. Consulta literalmente los **57 Markdown** de `DEVPL_MP_SUCCESSOR_132_v1_1_0_OWNER_APPROVED_133.zip` y SHA `d4e22170b9ecefa6434a10e0eeefdb535714b55ea1cd6ac750516d16147e8049`, la autoridad Git viva, 11 ADR OWNER_ACCEPTED, 10 contratos, actas Owner-133, Source Registry 1693 original, Project State, overlay, Authority Graph, tests existentes de documentación, COR-130 y los recibos A/B. Si falta algo imprescindible, BLOCK.

## Resultado contractual obligatorio

Un único commit/promoción normal genera `repo_MP132_R00_03_<HEAD12>_CLEAN.zip` que incluye sin alteración de bytes **las 57 piezas aprobadas**, identificadas en Source Registry sin colisiones, con las decisiones **G5 OWNER_RATIFIED**, **COR-130 OWNER_RATIFIED_PASS**, **global STOP OWNER_LIFTED**, `131 SUPERSEDED/HISTORICAL_ONLY`, ADRs 132 `OWNER_ACCEPTED`, ubicación A/B real y `MP-1B NOT_AUTHORIZED_PENDING_SPECIFIC_INCREMENT`. No reescribir históricos `*_at_sync1_merge`, GSDLC-13, Pilot A, evidencias G5/128/129/130 o los propios ZIP. Campos vigentes y pruebas actuales consistentes. External model egress permanece denied.

## Implementación — estricto fail-closed

1. Primero **auditoría focal** `REUSE_DELTA_MAP`: leer schemas/validators/test suites reales, detectar origen efectivo de cada flag (`mp_stop_status`, `reb117_g5`, `mp_g5_adjudication`, `mp_1b_activation`, `current_phase`, `current_micro_sprint`, etc.), no duplicar stores. Justificar owner del registro por campo y resolución de cualquier contradicción.
2. Fijar allowlist **exacta** validada: namespace de los 57 Markdown, `.devpilot/docs_governance/source_registry.json`, `.devpilot/project_state.json`, `rebaseline_p0_overlay.json`, Authority Graph/registro solo si aplican y **tests focales** de autoridad. Antes de copiar archivos, verificar `doc_id`, ruta y schema de source registry; rechazar overwrite de distinta autoridad. El estado 132 se publica en un sucesor, no edita ZIP 131/133.
3. Construir `mp132_r00_03_publish.py` stdlib modular, fases `inspect|prepare|validate|apply|commit|promote|package`; `prepare`/`validate` en directorio Git aislado externo, fuera del worktree actual. `dry-run` por defecto. Guard de HEAD/branch/remote y pathset; prompts Owner distinct para `apply`, `commit` y `promote` con scope exacto; no acciones basadas solo en mensaje LLM.
4. Actualizar schema/metadata mediante patch semántico acotado (no reemplazar Source Registry completo seleccionando ours/theirs), ordenar/deduplicar según contrato **real**; preservar todos los 1693 registros base como contenido histórico salvo cambio tipado probado. Registrar evento de aprobación sin crear falsa firma.
5. Extender pruebas históricas que acrediten valores de snapshot antiguo para que verifiquen **el antiguo** como histórico y el sucesor como actual, sin false FAIL de CRLF/LF; añadir tests de 57 SHA, Source Registry schema, estados actuales y negativos (L/E y agents no habilitados, MP-1B bloqueado, 131 no autoridad, G5 no implica MVP, Git A/B coherente).
6. Presentar al Owner plan/diff/preimage, budget `API=0`, tests y ausencia de paths ajenos. Solo entonces `apply` y confirmaciones independientes para `commit` y `push normal`. Gate Git 3-estados, nuevo HEAD padre 8db5 (si no hay otro cambio legítimo autorizado), remoto coincide y ZIP `git archive` limpio.
7. Packaging idempotente con receipt JSON (`source_head`, `new_head`, `remote_head`, `published_docs=57`, `source_registry_count_before_after`, `owner_approvals`, `full_regression_runs=0`, `pilot_writes=0`, `stop_scope`), sidecar `.sha256`, evidencia, guía única. Jamás decir PASS cuando solo ha sido creado un ZIP.

## Pruebas de aceptación y seguridad

Fixtures para doc_id duplicado con path distinto, misma ruta diferente hash, prueba histórica incompatible con estado presente, schema rechazado, HEAD drift, branch A vs B, ausencia de readme, rechazo Owner, doble llamada `commit`, push ya realizado, receipt perdido, Git conflict, Source Registry incompleto. Repetir focal Windows de COR-130 y nuevos tests; no Full salvo autorización extraordinaria. Verificar 0 escrituras en rutas ejecutables, política externa y Pilot A. Documentos con hash de bytes deben conservarse sin alterar EOL.

## Entrega de implementación

Operador + tests y **una única** `GUIA_UNICA_WINDOWS_R00_03.md`, patch allowlist, evidencia del test local en fixture, mapa de autoridad, plan dry-run, SHA y manifiesto. No ejecutar Windows por cuenta del Owner, no construir R1; recibir evidencia Windows real, adjudicar y actualizar baseline de referencia. Una interrupción de herramienta requiere checkpoint JSON con `last_good_phase` y no puede producir dos commits ni un ZIP falsamente limpio.
