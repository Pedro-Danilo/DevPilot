---
doc_id: ADR-DEVPL-REB-SYNC1-128
version: 1.0.0
status: APPROVED / EXECUTION-GATED
---
# ADR — SYNC-1: núcleo MP y compatibilidad Story incremental

## Contexto
Se integran `official/devpilot-local` (`f5c4b0f1...`) hacia `evolution/multiprovider-v2` (`54085701...`). Se preservan ambos historiales en un merge con dos padres. La auditoría G4A identificó la necesidad de conciliar los contratos de generación y Source Registry, y el preview P3B detectó un conflicto exclusivo en `.devpilot/docs_governance/source_registry.json`.

## Decisión
1. `devpilot_core.generation` de MP conserva ownership del contrato `GenerationRequest`, `ArtifactCandidateEnvelope`, provenance, rutas y política de proveedores.
2. `StoryImplementationCandidateApplicationService` y `GeneralStoryProvider` ingresan únicamente como **compatibilidad funcional gobernada del Pilot A**: no constituyen un segundo route resolver canónico ni implementan autoridad para apply/Quality/Git. Su ruta ModelAdapter opt-in permanece experimental y sin autorización para inferencia real.
3. Sin integración automática encubierta entre `GeneralStoryProvider` y el kernel MP: la adaptación tipada de códigos de story a `ArtifactCandidateEnvelope` se registra como trabajo futuro sujeto a otro contrato; no se simula un puente inexistente. La coexistencia transitoria tiene owners distintos y guardrails medibles.
4. Source Registry se fusiona por identidad `(doc_id, path)`, no por ID aislado; metadatos de entradas compartidas siguen la autoridad MP, entradas exclusivas det se incorporan y los históricos se conservan. El campo de sprint global se repara respecto a `project_state` y se conserva el valor histórico MP en otra clave.
5. No hay permiso para activar ExternalModel, ni MP-1B, ni nueva fuente de mutación. STOP continúa hasta adjudicación final G5 y successor de programa MP.
6. Los hashes EOL-normalizados de documentos P0 se comparan con contenido canonizado LF, no con bytes de working-tree CRLF. Los SHAs Git crudos permanecen autoritativos.

## Validación
Pruebas focales determinísticas y MP combinadas; validación de registry; controles negativos de seguridad; build UI cuando las dependencias offline estén disponibles; Git merge con dos padres, FF-only y paridad remota. BLOCK si hay nuevos conflictos o incompatibilidad semántica. No Full Regression intermedia.

## Diferidos
Convergencia final del router y nuevo adaptador tipado son decisiones de evolución posteriores; no se afirma generalización ni inferencia local real en SYNC-1.
