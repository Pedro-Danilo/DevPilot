---
doc_id: "ADR-DEVPL-GSDLC-13-D-02-IMPLEMENTATION-PROPOSAL-BRIDGE"
title: "ADR — 13-D-02 deterministic implementation proposal before SourceChangePlan"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-10-01"
approval: "projected_corrective_owner_validation_pending_windows"
checkpoint_id: "13-D-02"
finding_id: "FUNC-13D02-IMPLEMENTATION-BRIDGE-001"
---

# ADR — 13-D-02 deterministic implementation proposal before SourceChangePlan

## Contexto

El first-attempt `13-D-02 RUN_01` llegó con una Story `IN_PROGRESS`, source tree vacío y todo el baseline de ingeniería ya aprobado. Story Code solo ofrecía `CREATE/EDIT/RENAME`; `CREATE` mostraba `src/new_file.py` y un textarea vacío. El Owner debía decidir por sí mismo paths, cantidad de archivos, extensión y contenido.

Eso preservaba gobernanza de escritura, pero rompía el Operating Model del Greenfield: `Owner opera DevPilot; DevPilot produce project content`. Manual first-class significa que el humano puede editar o reemplazar una propuesta; no que el producto deba delegarle toda la autoría técnica cuando ya dispone de Requirements, Architecture, Security, Test Strategy, Planning y StoryContextPack.

El `CodingAgent` existente tampoco cierra el gap: requiere un source existente y es proposal-only sobre ese source. El `TestAgent` puede crear un test nuevo, pero no constituye una implementación productiva de la Story.

## Decisión

Añadir un contrato `ImplementationProposal` **antes** de `SourceDraftBuffer/SourceChangePlan` para el caso `StoryExecution=IN_PROGRESS + source-empty`.

Primera implementación:

1. Provider local determinístico `devpilot-local`.
2. Inputs: StoryContextPack + Architecture FROZEN.
3. Output: bundle reviewable 1..N de archivos CREATE con path, contenido, hash, rationale y provenance.
4. No network, external API, tool execution ni source mutation.
5. Owner/Developer humano decide `ACCEPT/REJECT`.
6. `ACCEPT` materializa solamente un `SourceDraftBuffer Set` runtime-only.
7. El lifecycle existente 09-C permanece único: `Draft Set → SourceChangePlan → diff → recheck/dry-run → Owner approval → atomic apply`.
8. SourceChangePlan debe consumir todos los drafts vigentes de la Story, aprovechando el contrato multi-file ya existente.

La ruta Manual `CREATE/EDIT/RENAME` se conserva como override first-class.

## Por qué determinístico primero

Pilot A no requiere un modelo real. Esta versión debe demostrar el boundary de producto y authority sin introducir costo, red ni no determinismo. El contrato queda deliberadamente preparado para que un futuro `LocalModelImplementationCandidateProvider`/`ExternalModelImplementationCandidateProvider` produzca el mismo tipo de candidate sin obtener authority de apply.

## Extensiones y stack

`src/new_file.py` deja de representar una sugerencia arquitectónica. Las extensiones manuales válidas provienen de `.devpilot/code_workbench/source_policy.json`. La propuesta DevPilot deriva su stack desde Architecture FROZEN y debe BLOCK si el perfil no está soportado; nunca cambia de stack silenciosamente.

## Seguridad

- proposal-only;
- source mutation = false;
- SourceDraftBuffer mutation solo después de ACCEPT humano;
- proposal hash + StoryContextPack hash + Architecture hash vinculados;
- source-empty/preimages revalidados antes de ACCEPT;
- apply authority = false;
- approval authority = false;
- Git authority = false;
- Full Regression = 0 en el corrective.

## Consecuencias

Positivas:

- el Owner deja de ser oracle de estructura/código en un greenfield;
- la propuesta queda revisable antes de cualquier draft/source write;
- se reutiliza 09-B/09-C en vez de crear un segundo motor de apply;
- habilita implementación multi-file desde UI;
- conserva Manual first-class y futura evolución multi-modelo.

Limitaciones:

- `deterministic-story-implementation-template-v1` es una **primera versión preliminar**, no una culminación de code generation industrial;
- inicialmente soporta el perfil aprobado `fastapi-python + sqlite`; otros perfiles deben fail-closed hasta tener provider específico;
- D03 sigue siendo authority para descubrir insuficiencias mediante Test Impact/Quality y producir remediation gobernada;
- dependency/scaffold materialization completa sigue siendo un área a evaluar si D03 demuestra que el vertical slice requiere manifests/dependencias adicionales.

## PASS/BLOCK

**PASS:** proposal reviewable → human ACCEPT → Draft Set runtime-only → SourceChangePlan multi-file, sin source mutation antes de apply aprobado.

**BLOCK:** el provider inventa stack no aprobado, escribe source/draft antes de decisión humana, bypassa 09-C, requiere API externa/modelo real para Pilot A o no puede explicar paths/provenance.

## Verificación

```text
python -m pytest -q tests/test_devpl_gsdlc_13_d_02_implementation_proposal_bridge.py tests/test_devpl_gsdlc_09_b_code_workbench.py tests/test_devpl_gsdlc_09_c_source_change.py tests/test_devpl_gsdlc_13_d_01_story_activation_bridge.py
```
