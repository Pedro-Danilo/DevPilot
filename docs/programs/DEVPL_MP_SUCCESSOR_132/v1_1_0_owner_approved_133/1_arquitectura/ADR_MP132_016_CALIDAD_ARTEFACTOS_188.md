---
doc_id: ADR-MP132-016-A188
status: OWNER_APPROVED_PROGRAM_ADR
version: "1.0.0"
execution_authority: false
owner_approval: APPROVED_2026_10_22
reference_baseline: "3a0a170f3c646e9955966576dd9212d3f87450e6"
sprint_r02_08_execution: NOT_STARTED
---
# ADR MP132-016 — Autoría y Quality Gate universales por perfil

**Estado:** aprobada por Owner el 2026-10-22, complementaria a ADR-MP132-013; no la sustituye.

## Contexto
En R02-07 se acreditó generación real L y lifecycle FROZEN para Vision/Scope/Requirements, pero el código efectivo aún filtra el identificador `admon_empresa_unipersonal_con_agentes` en `r02_07_semantic.py` y `pre_code_wizard_service.py`. Los RNF funcionales, la incoherencia de saldos y el error falso `SECTION_EMPTY` mostraron que schema + Markdown correcto no implica calidad profesional. El Owner corrigió finalmente contenido sustantivo.

## Decisión
La arquitectura aprobada establece la implementación incremental de un **pipeline compartido** con hooks por artefacto, sin otro almacén ni otra autoridad:

`ProjectFacts verificados → Perfil por artifact_type/version → ContextPack upstream FROZEN + fuentes → ModelAdapter L / Manual → Respuesta no confiable → Schema y validaciones de seguridad → Candidato inmutable → QualityReport por reglas del perfil + relaciones entre artefactos → Owner resuelve únicamente cuestiones materiales → Review/Diff/Approval/Apply/FROZEN existente → Impacto y successor`.

Las reglas universales atienden procedencia, autenticidad de fuentes, integridad, riesgo, permisos, coherencia del grafo y trazabilidad. Las reglas **del perfil** atienden corrección profesional (Vision: destinatarios/outcomes; Scope: IN/OUT/DEFERRED; Requirements: casos negativos/testabilidad; Architecture: ADR, diseño de datos y tradeoffs; Planning: incrementos/hitos; Construction: tests/build; Release: operabilidad; Operations: incidencias). Ninguna plantilla universal convierte en REQUIRED a un artefacto que PESP considere NOT_APPLICABLE.

Los modelos L/E/agentes aportan autoría y crítica **sin autoridad para emitir PASS final ni modificar FROZEN**. La falta de modelo competente se representa como `MODEL_REQUIRED` o `PARTIAL`, con Manual/Import permitidos bajo aprobación, sin fingir equivalencia de D. Un modelo externo solo tras costo, permiso y privacidad expresos.

## Alternativas descartadas
- Un único prompt largo para todos los documentos: no cubre sus invariantes ni testabilidad específica.
- Un sistema de evaluadores y publishers independientes por sprint: rompe autoridad y aumenta drift.
- Convertir toda observación editorial en BLOCK u otra decisión Owner: fricción innecesaria.
- Continuar el hardcode del ID Pilot B en producción: no generaliza.

## Pruebas de aceptación programáticas
Dos proyectos de dominios distintos; candidato correcto y errado por tipo; dependencia stale, afirmación no fundada, MIASI condicional, `NOT_APPLICABLE` evidenciado, casos con unknown, 403 seguro, no doble apply, cero permisos de modelos para editar source y costos medidos. Tests solo por impacto fuera de gates de cierre.

## Límites de vigencia
Adoptada en diseño programático, no equivale a implementación de ese pipeline en todas las olas. No sustituye ADR-013/187; las etapas conservan propietarios, PESP y autoridades existentes. No conceder un PASS absoluto por juicio del mismo modelo que redacta. No reutilizar decisiones Owner de otro artefacto ni gate técnico inocuo como autorización material.
