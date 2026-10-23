---
doc_id: MP132-R03_05_CONDITIONAL_TECH_ARTIFACTS-PROMPT
status: DRAFT_AWAITING_OWNER_INCREMENT_APPROVAL
version: 1.0.0
sprint_ref: 02_sprints/R03_05_CONDITIONAL_TECH_ARTIFACTS_SPRINT.md
baseline_reference: 1f15fa5b770db37c684e870a49572dcb569bd3a4
execution_authority: false
owner_increment_approval: PENDING
---
# Prompt operativo — R03_05_CONDITIONAL_TECH_ARTIFACTS

**Ejecútese SOLO después de aprobación Owner individual.** Antes de modificar código, lee literalmente el programa vigente, `BACKLOG_R03_132.md`, el sprint hermano, contratos A187/A188 y ADR-013/016, el repo real de HEAD aprobado y evidencias predecesoras. Si cualquier archivo falta, BLOCK especificando cual: no suplirlo con suposiciones.

**Objetivo:** Catálogo condicional de datos, API, UX e interfaces.

**Tarea:** PESP activa contratos de dominio, datos, integración/API y UX según hechos y riesgos; elegibilidad REQUIRED/CONDITIONAL/RECOMMENDED/NOT_APPLICABLE, rutas de import/edit desde UI.

**Implementación obligatoria:**
1. Auditar/reutilizar los componentes existentes e identificar delta mínimo y archivos exactos; reconocer estado persistido y drift, sin refactor tangencial ni hardcode de Pilot B.
2. Rebindear sprint/prompt a HEAD de Windows vigente. Especificar matriz REUSE/NO-OP/DELTA; cualquier nueva decisión arquitectónica material genera ADR.
3. Implementar el alcance acotado de este micro-sprint; separación ModelAdapter/seguridad/permisos; `dry-run` y presupuesto fijo; no egreso externo sin autorización.
4. Demostrar: Cobertura por proyecto y segundo dominio; N/A rationale y contradicción de riesgo se clasifican proporcionalmente; sin documentos de relleno.
5. Ejecutar validación focal positiva/negativa, pruebas de reanudación/idempotencia de riesgo; `git diff --check` sin comparar CRLF a mano; build/UI sólo por impacto.
6. Entregar **bundle ZIP Windows de nombre corto** con operador Python de mínima complejidad y **única** `GUIA_UNICA_WINDOWS.md` consecutiva desde `C:\Users\Pedro\Downloads`, PowerShell one-liners PASS/BLOCK color, capturas UI descritas y evidencia compacta.
7. La guía debe incluir commit selectivo, sync upstream normal/skip explícito y repo ZIP limpio `git archive HEAD` con SHA-256. No dar por cerrado el sprint antes de recibir evidencia Windows.

**Fronteras:** sin obligar especificaciones técnicas a todos los proyectos. Históricos se preservan; FROZEN nunca se reescriben in-place; Owner sólo autoriza decisiones materiales. No Full Regression sin excepción documentada. No emitir falso PASS por cobertura estructural.

**Salida:** ZIP + SHA, guía única, cambios source/tests/docs estrictamente necesarios, matrix REUSE/DELTA, registro de pruebas/negativos y criterios PASS/BLOCK. No pedir al operador decisiones adicionales si pueden derivarse de la evidencia.
