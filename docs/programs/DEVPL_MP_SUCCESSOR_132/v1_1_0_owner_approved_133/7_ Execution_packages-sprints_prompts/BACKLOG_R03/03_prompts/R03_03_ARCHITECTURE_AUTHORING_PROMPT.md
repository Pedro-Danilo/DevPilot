---
doc_id: MP132-R03_03_ARCHITECTURE_AUTHORING-PROMPT
status: OWNER_APPROVED
version: 1.0.0
sprint_ref: 02_sprints/R03_03_ARCHITECTURE_AUTHORING_SPRINT.md
baseline_reference: b9a655c13afff1d22da0dcdcfeec2998002fa3bb
execution_authority: true
owner_increment_approval: APPROVED_2026_10_23
---
# Prompt operativo — R03_03_ARCHITECTURE_AUTHORING

**Aprobado individualmente por el Owner el 2026-10-23.** Ejecutar R03-03 sobre `b9a655c13afff1d22da0dcdcfeec2998002fa3bb`; conservar aprobaciones específicas para red externa, dependencias o mutaciones sensibles. Antes de modificar código, leer literalmente programa, backlog, contratos A187/A188, ADR-013/016 y evidencia previa.

**Objetivo:** TechnicalDesignCandidate y perfil Architecture.

**Tarea:** Autoría L local por ModelAdapter + plantilla y `ArchitectureProfile` A188; drivers, requisitos, límites, riesgos, alternativas/decisiones materialmente relevantes, datos/API/UX condicionales; candidate no publica.

**Implementación obligatoria:**
1. Auditar/reutilizar los componentes existentes e identificar delta mínimo y archivos exactos; reconocer estado persistido y drift, sin refactor tangencial ni hardcode de Pilot B.
2. Rebindear sprint/prompt a HEAD de Windows vigente. Especificar matriz REUSE/NO-OP/DELTA; cualquier nueva decisión arquitectónica material genera ADR.
3. Implementar el alcance acotado de este micro-sprint; separación ModelAdapter/seguridad/permisos; `dry-run` y presupuesto fijo; no egreso externo sin autorización.
4. Demostrar: UI propone Markdown editable con provenance, deterministic gate y negativos para unsupported claims; segundo dominio sintético. Datos faltantes=REVIEW_REQUIRED, no valores inventados.
5. Ejecutar validación focal positiva/negativa, pruebas de reanudación/idempotencia de riesgo; `git diff --check` sin comparar CRLF a mano; build/UI sólo por impacto.
6. Entregar **bundle ZIP Windows de nombre corto** con operador Python de mínima complejidad y **única** `GUIA_UNICA_WINDOWS.md` consecutiva desde `C:\Users\Pedro\Downloads`, PowerShell one-liners PASS/BLOCK color, capturas UI descritas y evidencia compacta.
7. La guía debe incluir commit selectivo, sync upstream normal/skip explícito y repo ZIP limpio `git archive HEAD` con SHA-256. No dar por cerrado el sprint antes de recibir evidencia Windows.

**Fronteras:** no hardcode Pilot B, no otra authority. Históricos se preservan; FROZEN nunca se reescriben in-place; Owner sólo autoriza decisiones materiales. No Full Regression sin excepción documentada. No emitir falso PASS por cobertura estructural.

**Salida:** ZIP + SHA, guía única, cambios source/tests/docs estrictamente necesarios, matrix REUSE/DELTA, registro de pruebas/negativos y criterios PASS/BLOCK. No pedir al operador decisiones adicionales si pueden derivarse de la evidencia.
