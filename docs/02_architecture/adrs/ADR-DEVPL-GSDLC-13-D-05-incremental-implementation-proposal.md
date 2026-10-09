---
doc_id: "ADR-DEVPL-GSDLC-13-D-05-INCREMENTAL-IMPLEMENTATION-PROPOSAL"
title: "ADR — 13-D-05 deterministic incremental implementation proposal over governed source"
status: "approved"
version: "1.0.1"
owner: "Ordóñez"
updated: "2026-10-09"
approval: "corrective_projected_for_owner_windows_validation"
checkpoint_id: "13-D-05"
finding_id: "FUNC-13D05-INCREMENTAL-PROPOSAL-003"
---

# ADR — 13-D-05 deterministic incremental implementation proposal over governed source

## Contexto

`13-D-05/RUN_01` demostró que la activación repetible sí funciona: `story-rf-001` quedó `DONE`, `story-rf-002` fue preparada, obtuvo ContextPack/DoR y pasó a `IN_PROGRESS`. Sin embargo, Story Code deshabilitó `Proponer implementación desde contexto` porque el provider D02 estaba contractual y físicamente limitado a `StoryExecution=IN_PROGRESS + source-empty`.

Ese límite era correcto para D02, pero ya no es suficiente para D05: una segunda Story necesariamente parte de un baseline source gobernado por la Story anterior. Obligar al Owner a escribir manualmente la implementación de RF-002 preservaría la gobernanza de SourceDraft/SourceChangePlan, pero violaría el Operating Model Greenfield `Owner opera DevPilot; DevPilot produce project content` que originó el ADR D02.

El `CodingAgent` mock/fake-local vigente tampoco sustituye esta capacidad: es proposal-only por source seleccionado y no produce de forma autónoma un delta multi-file completo y trazable para RF-002.

## Decisión

Extender el mismo contrato `ImplementationProposal` de D02 con un modo incremental determinístico **bounded** para `story-rf-002` sobre el baseline RF-001 existente.

1. Se conserva `devpilot-local` como provider local determinístico y sin red.
2. El provider incremental solo se habilita para RF-002/list-available-products y fail-closed para otras Stories existentes hasta existir un successor gobernado.
3. El input sigue siendo StoryContextPack + Architecture FROZEN + source tree server-authoritative.
4. Todo `EDIT` queda ligado a `source_id + source_preimage_sha256`; todo `CREATE` exige target ausente.
5. La propuesta de RF-002 produce exactamente un delta bounded de cuatro artefactos: dos `EDIT` y dos `CREATE` sobre Domain/Application/Infrastructure/Test.
6. La propuesta no inventa campos de negocio: reutiliza `Product` y sus atributos opacos ya gobernados, añade una lectura `list_available` y filtra por la propiedad `available` existente.
7. `ACCEPT` materializa únicamente un Draft Set runtime-only con operaciones mixtas `EDIT/CREATE`; no escribe source.
8. El motor 09-C permanece único: Draft Set → SourceChangePlan → diff → recheck/dry-run → Owner approval → atomic apply.
9. La ruta Manual y la asistencia agent proposal-only permanecen como overrides; no reciben apply/approval/Git authority.
10. Full Regression permanece en cero para este corrective D05.
11. El reconocimiento estructural del baseline es independiente de LF/CRLF y conserva los EOL físicos del source existente; diferencias de representación de línea no constituyen drift semántico.

## Seguridad y fail-closed

- source mutation antes de apply = false;
- network/external API/model call = false;
- source preimages revalidados al aceptar;
- StoryContextPack y Architecture revalidados al aceptar;
- CREATE target existente = BLOCK;
- source drift semántico = BLOCK; LF/CRLF por sí solo no es drift;
- Story distinta de RF-002 sobre source existente = BLOCK hasta provider successor;
- proposal/draft apply authority = false;
- approval authority = false;
- Git authority = false.

## Consecuencias

Positivas:

- D05 puede demostrar que D02 es repetible después de la primera Story;
- el Owner vuelve a revisar una propuesta DevPilot antes de cualquier draft/source write;
- se reutilizan SourceDraftBuffer y SourceChangePlan en vez de crear un motor incremental paralelo;
- el delta queda vinculado a preimages exactos y es trazable a RF-002/TEST-002;
- futuras estrategias local/API podrán implementar el mismo candidate contract sin adquirir authority.

Limitaciones deliberadas:

- esta versión solo implementa el provider incremental determinístico para RF-002, porque Pilot A debe demostrar primero el boundary real sin convertir el corrective en un generador genérico no validado;
- las Stories RF-003+ deben fail-closed si no existe un provider successor compatible;
- D03/Quality sigue siendo la authority que decide si el código aplicado satisface la Story; el provider no se auto-certifica.

## PASS/BLOCK

**PASS:** RF-002 IN_PROGRESS + baseline RF-001 intacto → proposal source-aware 2 EDIT + 2 CREATE → review humano → ACCEPT → Draft Set runtime-only → SourceChangePlan, sin source mutation previa.

**BLOCK:** propuesta sin preimages exactos, source drift, Story no soportada tratada como genérica, source write previo a apply, bypass de 09-C, red/modelo externo, o authority de apply/approval/Git concedida al provider.

## Relación con ADR D02

Este ADR **extiende**, no invalida, `ADR-DEVPL-GSDLC-13-D-02-deterministic-implementation-proposal-before-source-plan.md`:

- D02 source-empty bootstrap permanece vigente para la primera Story;
- D05 añade el successor incremental bounded para el baseline no vacío de RF-002.

## Verificación

```text
python -m pytest -q tests/test_devpl_gsdlc_13_d_05_incremental_proposal.py tests/test_devpl_gsdlc_13_d_02_implementation_proposal_bridge.py tests/test_devpl_gsdlc_09_b_code_workbench.py tests/test_devpl_gsdlc_09_c_source_change.py
```
