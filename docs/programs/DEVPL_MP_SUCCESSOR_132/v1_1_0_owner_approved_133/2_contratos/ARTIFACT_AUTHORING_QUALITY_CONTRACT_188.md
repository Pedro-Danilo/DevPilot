---
doc_id: MP132-ARTIFACT-AUTHORING-QUALITY-188
status: OWNER_APPROVED_PROGRAM_CONTRACT
version: "1.0.0"
date: "2026-10-22"
source_decision: MP132-OWNER-DECISION-188
execution_authority: false
---
# Contrato transversal de autoría y calidad por perfil — A188

## A. Alcance, autoridad y principios
Norma programática que completa ADR-MP132-013/187 y ADR-MP132-016/188; no constituye un agente, almacén ni publisher separado. Se aplica progresivamente a Product Definition, Architecture, Planning, Construction, Release y Operations. Reusar `ArtifactCatalog/PESP`, `ModelAdapter`, Candidate Lifecycle, Quality/Coverage Gate, Source Registry, ChangeImpact/Successor, Approval y Publisher existentes, en lugar de introducir autoridades duplicadas.

La **plantilla** determina presentación y estructura; el **perfil de autoría** determina propósito profesional, obligaciones de contenido, invariantes, fuentes, riesgos y testabilidad; el **perfil PESP** determina si un artefacto es `REQUIRED`, `CONDITIONAL`, `RECOMMENDED` o `NOT_APPLICABLE`. No inferir obligatoriedad desde una plantilla ni convertir cada casilla vacía en bloqueo.

## B. Resolución por artefacto y proyecto
`artifact_type`, `profile_version`, `project_facts` verificados, contexto/etapa, estándares aplicables, upstream FROZEN y sus hashes, riesgos, capacidad del proveedor, permisos y restricciones de costo. El resolver no debe depender de un `project_id` literal de Pilot B. Si faltan hechos que solo conoce el Owner, marcarlos `UNKNOWN`/`REVIEW_REQUIRED`, no inventarlos. Un perfil establece `input_fact_schema`, `context_selection_policy`, `expected_semantic_obligations`, `cross_artifact_invariants`, `unsupported_claim_rules`, `testability_checks`, `negative_cases`, `repair_policy`, `materiality_policy`, `owner_decision_surface` y evidencia mínima.

## C. Pipeline compartido y frontera de confianza
1. Audit-first del perfil y hechos, estado upstream y permisos. Preflight D, sin costo de inferencia.
2. Selección `ModelAdapter` L competente o Manual/Import según perfil y tarea; E/agentes siguen bloqueados hasta autorización de costo, privacidad y egress. Cache e idempotencia por contexto/perfil/proveedor/versiones.
3. La respuesta cruda del modelo es **no confiable**: parseo/schema y seguridad/secretos/permiso → candidata inmutable con provenance; se registra por separado `GENERATED` y `ADMITTED_FOR_OWNER_REVIEW`.
4. Evaluación contextual con pruebas deterministas, grounding, completitud material, coherencia entre artefactos y evidencias de testabilidad; guardrails y supervisión de incertidumbre. `QUALITY_ACCEPTABLE` es un estado de evaluación, no `APPROVED`.
5. Reparación focalizada solo de defectos identificados: presupuesto de intentos, timeouts, `dry-run`, diagnóstico por campo y comparación; no regeneración ciega ni loops sin tope.
6. Owner decide sobre objetivos, excepciones, riesgo material y acciones sensibles. Review/diff, approval, apply, FROZEN por lifecycle existente; nunca publicar mediante respuesta del modelo o reescribir un FROZEN in-place.
7. Derivados referencian upstream FROZEN y `profile_version`; cambios materiales activan análisis de impacto y sucesor selectivo; cambios cosméticos no recertifican toda la aplicación.

## D. Hallazgos y severidad
`BLOCK`: violación material demostrable, ausencia de obligación `REQUIRED`, fuente falsificada, contradicción verificable, riesgo de seguridad, cambio/publicación no autorizado. `REVIEW_REQUIRED`: decisión de negocio real no resuelta, inferencia semántica probable no demostrable o evidencia insuficiente que altera la aceptación. `WARN`: estilo, plantilla opcional o recomendación no material; no impedir FROZEN por formato inocuo. `PASS`: únicamente reglas efectivamente probadas; no declararlo por palabras clave o longitud. No imponer a Vision los casos de Tests o a Scope el detalle de Architecture.

## E. Recibo portable mínimo
`artifact_type`, `profile_version`, `project_context_hash`, `upstream_refs` (stage, hash), `candidate_sha256`, `route_receipt`, `checks[]` con `rule_id`, `classification`, `source_ref`, `observed`, `expected`, `remediation`, `severity`, `cross_artifact_impact`, `limitations`, `human_decisions_required`, `final_disposition`, `elapsed_ms`, `model_cost_or_resource_measurement`. No copiar secretos ni datos empresariales completos a evidencias exportables. Registrar incertidumbre y `NOT_AVAILABLE` en mediciones ausentes.

## F. Eficiencia y madurez verificable
Comparar calidad de la primera propuesta L, falsos PASS/BLOCK, defectos técnicos corregidos por Owner versus decisiones empresariales, grounding, testabilidad, latencia, intentos, impacto y costo marginal de crítica por agente/E. L real no garantiza calidad industrial; D no debe fingir juicio profesional absoluto. E queda `DENY` sin autorización de privacidad/costo por caso. Dataset de positivos/negativos y **dos dominios** para calificar generalización en Product Definition; las demás olas prueban sus perfiles de forma incremental.

## G. Plan de implantación
R02-08 extiende cobertura semántica Product Definition sobre fuentes ya FROZEN (sin mutarlas). R02-09 trata fallos y recuperación; R03 documenta Architecture; R04 Planning, R05 Construction, R06 Release; R07–R08 agentes y E cuando estén autorizados; R09 endurecimiento UX y R10 aceptación independiente. Este contrato **no cambia el status** de los sprints ni autoriza ejecución masiva. No imponer pruebas full fuera de un gate de cierre o una excepción material justificada.

## H. Adenda A190 — activación transversal temprana (Owner, 2026-10-24)

**Autoridad:** `0_program/14_DECISION_OWNER_A190.md`. Se adelanta el *núcleo mínimo reutilizable* dentro de cada nueva ruta L desde R03_03, sin afirmar que todos los perfiles ya están implementados. En preflight se resuelven PESP/`artifact_type`/`profile_version`, hechos efectivos, upstream FROZEN+hashes, alcance real de extractos y decisiones Owner ya aprobadas. Antes de inferir se fijan topes de contexto, salida, unidades y llamadas; si el presupuesto no permite cobertura material, informar la limitación y no esconder truncamiento. Salida L = no confiable, candidata inmutable con procedencia, nunca apply directo; versionar alternativas y preservar recibos precedentes.

**Gate mínimo antes de aprobación:** negativos por corte de frase/material, contradicción demostrable de RF/RNF/decisión ratificada, fuente inexistente, acción no autorizada y requisito REQUIRED ausente. `BLOCK` solo si existe evidencia concreta; `REVIEW_REQUIRED` si no hay certeza y `WARN` para estilo. No usar presencia de palabras clave, longitud, secciones ni barra de avance como certificación semántica. Revisión humana, diff, approval y FROZEN siguen bajo el lifecycle único.

**Especializaciones sin duplicación:** Architecture en R03_03; ADR/Technology en R03_04; condicionales en R03_05; Security/Test Strategy/Traceability en R03_06; sucesores en R03_07; scaffolding y evaluaciones en R03_08–11. Los perfiles de Planning/Construction/Release y agentes/E siguen sus olas y autorizaciones originales. Registrar latencia real, llamadas/unidades y recursos medidos o `NOT_AVAILABLE`; probar identidad, reentrada, falsos PASS/BLOCK y un segundo dominio progresivamente. SHA de recibos generativos verifica bytes exactos, mientras Git/overlays de texto usan comparación semántica o `git diff`, sin falsos fallos LF/CRLF.
