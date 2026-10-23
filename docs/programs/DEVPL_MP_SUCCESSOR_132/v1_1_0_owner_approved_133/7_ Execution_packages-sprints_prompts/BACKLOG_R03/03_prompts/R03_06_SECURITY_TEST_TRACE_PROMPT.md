---
doc_id: MP132-R03_06_SECURITY_TEST_TRACE-PROMPT
status: DRAFT_AWAITING_OWNER_INCREMENT_APPROVAL
version: 1.0.0
sprint_ref: 02_sprints/R03_06_SECURITY_TEST_TRACE_SPRINT.md
baseline_reference: 1f15fa5b770db37c684e870a49572dcb569bd3a4
execution_authority: false
owner_increment_approval: PENDING
---
# Prompt operativo — R03_06_SECURITY_TEST_TRACE

**Ejecútese SOLO después de aprobación Owner individual.** Antes de modificar código, lee literalmente el programa vigente, `BACKLOG_R03_132.md`, el sprint hermano, contratos A187/A188 y ADR-013/016, el repo real de HEAD aprobado y evidencias predecesoras. Si cualquier archivo falta, BLOCK especificando cual: no suplirlo con suposiciones.

**Objetivo:** Security, Test Strategy y Traceability coherentes.

**Tarea:** Derivar perfiles de Security, Test Strategy y Traceability desde Requirements/Architecture con riesgos reales, amenazas y MIASI solamente cuando el producto usa IA.

**Implementación obligatoria:**
1. Auditar/reutilizar los componentes existentes e identificar delta mínimo y archivos exactos; reconocer estado persistido y drift, sin refactor tangencial ni hardcode de Pilot B.
2. Rebindear sprint/prompt a HEAD de Windows vigente. Especificar matriz REUSE/NO-OP/DELTA; cualquier nueva decisión arquitectónica material genera ADR.
3. Implementar el alcance acotado de este micro-sprint; separación ModelAdapter/seguridad/permisos; `dry-run` y presupuesto fijo; no egreso externo sin autorización.
4. Demostrar: Referencias RF→Architecture→Security→Test/Trace; pruebas negativas de inventos, falsa cobertura y prompt injection; aprobación no duplicada.
5. Ejecutar validación focal positiva/negativa, pruebas de reanudación/idempotencia de riesgo; `git diff --check` sin comparar CRLF a mano; build/UI sólo por impacto.
6. Entregar **bundle ZIP Windows de nombre corto** con operador Python de mínima complejidad y **única** `GUIA_UNICA_WINDOWS.md` consecutiva desde `C:\Users\Pedro\Downloads`, PowerShell one-liners PASS/BLOCK color, capturas UI descritas y evidencia compacta.
7. La guía debe incluir commit selectivo, sync upstream normal/skip explícito y repo ZIP limpio `git archive HEAD` con SHA-256. No dar por cerrado el sprint antes de recibir evidencia Windows.

**Fronteras:** ningún documento se vuelve profesional por encabezados. Históricos se preservan; FROZEN nunca se reescriben in-place; Owner sólo autoriza decisiones materiales. No Full Regression sin excepción documentada. No emitir falso PASS por cobertura estructural.

**Salida:** ZIP + SHA, guía única, cambios source/tests/docs estrictamente necesarios, matrix REUSE/DELTA, registro de pruebas/negativos y criterios PASS/BLOCK. No pedir al operador decisiones adicionales si pueden derivarse de la evidencia.
