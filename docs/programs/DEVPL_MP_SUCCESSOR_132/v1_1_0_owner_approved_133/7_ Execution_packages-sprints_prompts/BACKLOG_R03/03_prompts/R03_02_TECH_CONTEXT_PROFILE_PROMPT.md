---
doc_id: MP132-R03_02_TECH_CONTEXT_PROFILE-PROMPT
status: OWNER_APPROVED
version: 1.0.0
sprint_ref: 02_sprints/R03_02_TECH_CONTEXT_PROFILE_SPRINT.md
baseline_reference: 9c51d987a6965822f1d171142e25a159a8bfbeb2
execution_authority: true
owner_increment_approval: APPROVED_2026_10_23
---
# Prompt operativo — R03_02_TECH_CONTEXT_PROFILE

**Aprobado individualmente por el Owner el 2026-10-23**, rebindeado al HEAD limpio y confirmado `9c51d987a6965822f1d171142e25a159a8bfbeb2`. La aprobación se limita a R03-02. Antes de modificar código, consulta programa, backlog, sprint, A187/A188, ADR-013/016, repo y COR3; una ausencia material obliga BLOCK, no suposición.

**Objetivo:** ContextPack técnico y aplicabilidad.

**Tarea:** TECHNICAL_RAG_SOURCE_PROFILE y resolver PESP de contexto: RF/Vision/Scope FROZEN, ADR vigentes, security risks, límites de memoria/contexto; ignore changelog superseded.

**Implementación obligatoria:**
1. Auditar/reutilizar los componentes existentes e identificar delta mínimo y archivos exactos; reconocer estado persistido y drift, sin refactor tangencial ni hardcode de Pilot B.
2. Rebindear sprint/prompt a HEAD de Windows vigente. Especificar matriz REUSE/NO-OP/DELTA; cualquier nueva decisión arquitectónica material genera ADR.
3. Implementar el alcance acotado de este micro-sprint; separación ModelAdapter/seguridad/permisos; `dry-run` y presupuesto fijo; no egreso externo sin autorización.
4. Demostrar: Pruebas contra referencias obsolete/poisoned, fuentes falsificadas, stage/hash drift, segunda industria y `NOT_APPLICABLE` sustentado; no API externa.
5. Ejecutar validación focal positiva/negativa, pruebas de reanudación/idempotencia de riesgo; `git diff --check` sin comparar CRLF a mano; build/UI sólo por impacto.
6. Entregar **bundle ZIP Windows de nombre corto** con operador Python de mínima complejidad y **única** `GUIA_UNICA_WINDOWS.md` consecutiva desde `C:\Users\Pedro\Downloads`, PowerShell one-liners PASS/BLOCK color, capturas UI descritas y evidencia compacta.
7. La guía debe incluir commit selectivo, sync upstream normal/skip explícito y repo ZIP limpio `git archive HEAD` con SHA-256. No dar por cerrado el sprint antes de recibir evidencia Windows.

**Fronteras:** no inventar decisiones ni usar `project_id` como semántica. Históricos se preservan; FROZEN nunca se reescriben in-place; Owner sólo autoriza decisiones materiales. No Full Regression sin excepción documentada. No emitir falso PASS por cobertura estructural.

**Concreción audit-first aprobada:** reutilizar `PreCodeWizardApplicationService` (hash y estados FROZEN), `ArtifactProfileRegistry/ProjectApplicability` (PESP) y la generación técnica existente, sin reemplazarlas. Seleccionar sólo entradas explícitamente confiables, con hashes de bytes aprobados y límite de contexto, excluir superseded/poisoned/forged. No implementar la autoría Architecture de R03-03 ni incorporar una segunda ruta de publicación. UI inalterada ⇒ capturas no exigibles por este delta.

**Salida:** ZIP + SHA, guía única, cambios source/tests/docs estrictamente necesarios, matrix REUSE/DELTA, registro de pruebas/negativos y criterios PASS/BLOCK. No pedir al operador decisiones adicionales si pueden derivarse de la evidencia.
