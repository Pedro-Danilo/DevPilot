---
doc_id: MP132-A188-APPROVED
status: OWNER_APPROVED_PROGRAM_AMENDMENT
version: "1.0.0"
execution_authority: false
owner_approval: APPROVED_2026_10_22
reference_baseline: "3a0a170f3c646e9955966576dd9212d3f87450e6"
sprint_r02_08_execution: NOT_STARTED
---
# Enmienda 188 aprobada — Calidad y coherencia transversal de artefactos

## Propósito
Hacer **operativo y medible** el principio ya adoptado en ADR-MP132-013/187: el proveedor L genera una propuesta semántica; DevPilot valida su admisibilidad, asegura trazabilidad y gobierna edición/aprobación/publicación. No es una autoridad nueva, un nuevo publisher, un agente ni una obligación de usar API externa.

## Decisiones adoptadas
1. **Contrato único de proceso, perfil específico por tipo.** Toda tarea de autoría resuelve `(artifact_type, profile_version, project_facts, stage, risk, applicable_standards, upstream_refs, model_capability)`. Ningún contrato de producción usa identificadores literales de Pilot B para permitir o negar calidad. Un perfil define propósito, estructura, hechos upstream, invariantes, antiobjetivos, negativos, testabilidad, dependencias y límites de decisión Owner.
2. **Frontera de confianza.** Respuesta del modelo = no confiable; normalizar/parsear/sanity-check → candidato inmutable + provenance; Quality Gate contextual → revisión Owner versionada → diff/preimage → approval → apply → FROZEN; jamás entrada textual del modelo con permisos de publicación.
3. **Capas de verificación, sin juez omnisciente.** Seguridad/permisos, schema, integridad/grounding de referencias, cobertura y completitud sustantiva, contradicción con upstream y entre artefactos, pruebas/evidencia por tipo. D decide únicamente hechos verificables; evaluación semántica asistida distingue hallazgo probable de prueba determinística.
4. **Severidad proporcional.** `BLOCK` para riesgo material, obligación REQUIRED ausente, contradicción verificable o acto no autorizado. `REVIEW_REQUIRED` para decisiones de negocio verdaderamente abiertas/evidencia insuficiente. `WARN` para correcciones no materiales de estilo y perfil RECOMMENDED. Solo el Owner resuelve decisiones de producto, riesgos y excepciones materiales; no aprobación humana de un hash, índice, encabezado o formato inocuo.
5. **Dependencias y unidad.** Un artefacto aceptado referencia hashes FROZEN upstream y evidencia de coherencia. Cambios reales originan análisis de impacto y successor del descendiente afectado; no reabrir FROZEN in-place ni recertificar toda la aplicación por una modificación cosmética.
6. **Economía de cómputo.** Preflight D, contexto selectivo, inferencia local elegible L, evaluación D+tests, reparación focalizada sobre defectos identificados y `max_attempts/time_budget`; agentes y E únicamente cuando estén autorizados según privacy/egress/cost y cuando añadan beneficio verificable. Cache por hash de contexto/perfil, sin sobrescrituras y sin loops autónomos.
7. **Evaluación de generalización.** R02-08 valida la primera vertical Product Definition para Pilot B y al menos un **segundo dominio** sintético/no sensible. La aceptación de los perfiles para Architecture, Planning, Construction, Release y Operations será incremental en sus olas propietarias: la enmienda no amplía automáticamente R02-08 a todas las etapas.

## Contrato de recibo de calidad mínimo
`artifact_type`, `profile_version`, `project_context_hash`, `upstream_refs[stage/hash]`, `candidate_sha256`, `route_receipt`, `checks[{rule_id,classification,source_ref,observed,expected,remediation,severity}]`, `cross_artifact_impact`, `limitations`, `human_decisions_required`, `final_disposition`, `elapsed_ms`, `model_cost_or_resource_measurement`. Se omiten secretos y contenido empresarial en los recibos portables.

## Evidencia de desempeño (medida, no inventada)
- Primera propuesta L: defectos sustantivos por tipo, requisitos sin fuente, contradicciones y pruebas no ejecutables.
- Proporción de correcciones **técnicas** realizadas por Owner frente a decisiones **empresariales**. El objetivo es reducir las primeras, no forzar PASS por longitud del texto.
- Latencia, reintentos, memoria/costo, negativas, regreso desde estados persistidos, precision de BLOCK y falso bloqueo.
- Dataset por tipo y riesgo con positivos/negativos y un caso externo a Pilot B.

## Gobierno y transición
Esta es una **enmienda programática aprobada por el Owner el 2026-10-22**. No cambia el HEAD publicado, no autoriza API externa ni modifica el status ejecutable de R02-08. Su adopción ratifica una única decisión arquitectónica de calidad; las comprobaciones mecanizables no se someterán a aprobaciones Owner adicionales. La implementación técnica seguirá asignada a sus sprints y al baseline exacto de Windows.

## Ancla de la aprobación
- Decisión Owner explícita: aprobación de la enmienda 188 en la conversación del 2026-10-22.
- Baseline técnico verificado de cierre R02-07: `3a0a170f3c646e9955966576dd9212d3f87450e6`; workspace FROZEN: `04ca8f83618176f5b14470bcaa092f979e3b6e72`.
- Alcance: **solo programa y planificación**. No otorga `SPRINT_EXECUTION_APPROVED` a R02-08, no modifica Git ni habilita agentes/APIs externas.
- Referencias vinculantes: `ARTIFACT_AUTHORING_QUALITY_CONTRACT_188.md`, `ADR_MP132_016_CALIDAD_ARTEFACTOS_188.md`.
- Versiones históricas ADR-013 y enmienda 187: conservadas. Las evidencias de R02-07 son cierre histórico, no promesa de generalización industrial.
