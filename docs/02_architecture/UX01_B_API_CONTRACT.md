# UX01-B — Contrato backend para UX01-C

Estado: candidato de implementación; no aprobación profesional ni cierre Windows.
Autoridad: sprint UX01 v1.1.0 aprobado y prompt UX01-B v1.0.0.

## Ruta y autoridad

Se amplía `POST /api/v1/guided-sdlc/pre-code/technology-action`, conservando router, dispatcher, facade, identidad Owner, workspace scope y lifecycle existentes. Ninguna nueva ruta escribe documentos del proyecto. Los campos anteriores conservan sus defaults.

Campos aditivos: `artifact_kind` (`architecture`, `technology_options`, `adr`, default `architecture`), `expected_sha256` (SHA hex de 64 caracteres o vacío), `generation_epoch` (hasta 128 caracteres o vacío). UX01-C debe enviar la identidad observada para detectar una pantalla obsoleta; los clientes anteriores siguen vinculando la elección al candidato actual en el servidor.

- `select_option`: `option_id`, SHA del archivo candidato Technology y epoch observado. El servidor registra `selected_by`, `selection_at`, `selected_technology_sha256`, `selection_epoch`. Cambiar una elección ya registrada requiere `successor=true` e invalida ADR/conciliación.
- `generate_options`: una inferencia manual o reutilización exacta del recibo. Nuevo contexto/modelo con candidato existente requiere `successor=true`. Incluso una respuesta idéntica tiene nuevo candidate_id/parent y obliga a elegir otra vez.
- `generate_adr`: exige selección registrada, Technology íntegro y epoch vigente. Un ADR contradictorio se conserva como BLOCK de calidad; no puede conciliarse.
- `owner_revise_options` / `owner_revise_adr`: revisión inmutable con `before_owner` conservado. Options invalida selección/ADR. `expected_sha256` se refiere al candidato del documento editado.
- `reconcile`: vincula hashes, IDs de ambos candidatos y epoch; conserva secciones Owner e invalida el plan mediante `save_draft` existente. `expected_sha256` se refiere a Architecture.
- `export_handoff`: devuelve `data.handoff` con el Markdown íntegro. `artifact_kind` elige documento; `expected_sha256` se refiere a ese candidato (Architecture usa hash del DRAFT; Options/ADR usan hash del archivo inmutable).
- `adr_not_applicable`: acto explícito Owner con justificación en `content`, sin selección/ADR existente. Registra motivo, actor, SHA Architecture y epoch; no llama modelo ni crea ADR trivial. La revisión y aprobación ordinarias de Architecture siguen siendo obligatorias. Un cambio de Architecture invalida la justificación.

## Respuestas y errores

`data.r03_04_authoring.technology` y `.adr` añaden `candidate_id`, `generation_epoch`, `quality`, `elapsed_ms`, `format_findings`. `quality.current` es el DTO UX01-A vigente; `quality.before_owner` conserva el resultado original. Architecture expone lo mismo en `derivation.ux01_quality`.

`status=COMPLETE` significa que terminó la operación de generación y existe un candidato, no que su calidad sea aceptable. Una salida incompleta segura puede tener COMPLETE + REVIEW_REQUIRED y tareas de reparación. Salidas inseguras/errores del proveedor conservan recibo BLOCK. No hay inferencia automática de reparación.

GET de estado incorpora `r03_04_authoring.activity`: último recibo por tipo, IN_PROGRESS/COMPLETE/BLOCK, inicio/final, duración medida, error y llamadas. No contiene porcentaje, ETA ni cancelación ficticia. Una operación Technology concurrente devuelve `UX01_B_ACTION_IN_PROGRESS` sin inferencia. Si Architecture cambia durante inferencia, `UX01_B_STATE_CHANGED_DURING_INFERENCE` conserva el candidato y evita sobrescribir el estado concurrente.

Los errores utilizan el CommandResult/HTTP 409 existente, sin elevarlos a 500: `UX01_B_STALE_EPOCH`, `UX01_B_STALE_CANDIDATE`, `UX01_B_STALE_ARCHITECTURE`, `UX01_B_STALE_TECHNOLOGY_EPOCH`, `UX01_B_OWNER_SELECTION_STALE`, `UX01_B_ADR_LINEAGE_DRIFT`, `UX01_B_OPTIONS_SUCCESSOR_REQUIRED`, `UX01_B_SELECTION_SUCCESSOR_REQUIRED`, `UX01_B_HANDOFF_SOURCE_DRIFT`, `UX01_B_HANDOFF_EPOCH_DRIFT`, `UX01_B_BUSINESS_NEED_DRIFT`. La ruta conserva el finding general `R0304_LOCAL_AUTHORING_BLOCK` y el código específico en el mensaje; fallos de recibos Owner se clasifican `UX01_B_REVISION_RECEIPT_BLOCK`.

## Handoff offline y calidad

El paquete incluye Markdown, hashes lógicos, secciones y hashes de cuerpo, RF/RNF, matriz de comparación, hallazgos/severidad/reparaciones, B0 con origen/hash, restricciones y elección Owner inmutables, before_owner y lineage. `offline_section_proposal` cambia solo el cuerpo de una sección y devuelve una propuesta sin persistir/aprobar. Bloquea la sección Decisión y las que citan decisiones D-*. La aceptación posterior pasa por revisión Owner y el lifecycle existente; no hay importación externa automática.

SHA del archivo candidato verifica bytes exactos (incluye newline final). `quality.current.candidate_sha256` y el paquete verifican el Markdown lógico de la respuesta (normalización LF/CRLF). Son identidades distintas y no deben compararse como si fueran intercambiables.

STRUCTURALLY_VALID solo describe verificadores técnicos. HANDOFF_READY requiere evaluación de utilidad que este pipeline no autoatribuye; PROFESSIONAL_REVIEWED permanece false. Las muestras son sintéticas, REVIEW_REQUIRED, y no acreditan mejora profesional por otro proveedor.

## Persistencia, compatibilidad y reversión

Sin migración de DB. Se agregan claves JSON en recibos/estado ya existentes y recibos por intento/revisión dentro de `outputs/mp132_r03_04`. Architecture conserva sus recibos segmentados; la regeneración explícita crea otro epoch y archiva el puntero anterior. Una acción manual genera como máximo una unidad; no se reejecutan unidades completas.

Los datos históricos C02 no se reescriben. Un candidato anterior sin calidad UX01 no se exporta como si tuviera informe: `UX01_B_HANDOFF_QUALITY_MISSING`. Para continuar un candidato antiguo no conciliado, regenerar explícitamente según lifecycle. Los bindings FROZEN históricos sin epoch siguen válidos; los nuevos companions comprueban epoch y candidate IDs además de SHA/approval.

Rollback de código: revertir únicamente el delta B tras revisión Git, preservando todos los outputs y recibos; no resetear bases, borrar candidatos ni modificar FROZEN. Antes de operar con código anterior, revisar los estados que contienen nuevas decisiones/epochs. No hay rollback automático del contenido del producto.

## Ejemplos reproducibles

`python scripts/ux01_b_offline_example.py` reproduce las muestras de `docs/examples/ux01_b`. No hace llamadas de red ni usa Ollama. `handoff.json` y `offline_proposal.json` muestran el DTO real. La elección T1 de ese fixture es sintética, no una decisión real del Owner.
