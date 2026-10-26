---
doc_id: MP132-R03_04_TECH_DECISION_ADR-PROMPT
status: OWNER_APPROVED
version: 1.0.2
sprint_ref: 02_sprints/R03_04_TECH_DECISION_ADR_SPRINT.md
baseline_reference: df6a5dcbb6eeb112008db1373d2e975cbc60b18f
execution_authority: true
owner_increment_approval: APPROVED_2026_10_24
---
# Prompt operativo — R03_04_TECH_DECISION_ADR

**Aprobación Owner individual recibida el 2026-10-24, exclusivamente para R03_04.** Se leyó el programa A190, `BACKLOG_R03_132.md`, el sprint hermano, A187/A188/A190, ADR-013/015/016, el repositorio C11 y sus recibos. Baseline autenticado: `df6a5dcbb6eeb112008db1373d2e975cbc60b18f`. Windows debe comprobar HEAD real antes de aplicar. La ejecución no autoriza un approval/apply/freeze de Pilot B.

**Objetivo:** Selección tecnológica y ADR companion.

**Tarea:** Technology Decision Workbench en Architecture; tradeoffs justificadas, costo/soporte/seguridad, ADR gobernada cuando es material. Decisión Owner central consolidada en approval Architecture.

**Implementación obligatoria:**
1. Auditar/reutilizar los componentes existentes e identificar delta mínimo y archivos exactos; reconocer estado persistido y drift, sin refactor tangencial ni hardcode de Pilot B.
2. Rebindear sprint/prompt a HEAD de Windows vigente. Especificar matriz REUSE/NO-OP/DELTA; cualquier nueva decisión arquitectónica material genera ADR.
3. Implementar el alcance acotado de este micro-sprint; separación ModelAdapter/seguridad/permisos; `dry-run` y presupuesto fijo; no egreso externo sin autorización.
4. Demostrar: UI muestra alternativas y rationale, fallo si instala stack al decidir, no ADR trivial, ADR approved lineage y rechazo de decisiones no grounded.
5. Ejecutar validación focal positiva/negativa, pruebas de reanudación/idempotencia de riesgo; `git diff --check` sin comparar CRLF a mano; build/UI sólo por impacto.
6. Entregar **bundle ZIP Windows de nombre corto** con operador Python de mínima complejidad y **única** `GUIA_UNICA_WINDOWS.md` consecutiva desde `C:\Users\Pedro\Downloads`, PowerShell one-liners PASS/BLOCK color, capturas UI descritas y evidencia compacta.
7. La guía debe incluir commit selectivo, sync upstream normal/skip explícito y repo ZIP limpio `git archive HEAD` con SHA-256. No dar por cerrado el sprint antes de recibir evidencia Windows.

**Fronteras:** no auto-install, no stack predeterminado ni Owner approval cosmético. Históricos se preservan; FROZEN nunca se reescriben in-place; Owner sólo autoriza decisiones materiales. No Full Regression sin excepción documentada. No emitir falso PASS por cobertura estructural.

**Salida:** ZIP + SHA, guía única, cambios source/tests/docs estrictamente necesarios, matrix REUSE/DELTA, registro de pruebas/negativos y criterios PASS/BLOCK. No pedir al operador decisiones adicionales si pueden derivarse de la evidencia.

## Ejecución ajustada a contrato real (A190 y cierre C11)

1. Reusar `PreCodeWizardApplicationService` y su approval normal de Architecture; el servicio antiguo `ArchitectureAdrBundleService` solo gobierna materialización C02 histórica. Su ampliación de source write se reserva al lifecycle/successor correspondiente, sin un segundo approval tecnológico.
2. Proyecto Architecture L guardado: proyectar en API una vista **solo lectura** de alternativas, motivación, coste/soporte/seguridad, ADRs propuestas, evidencias y hallazgos. UI Guided y Expert comparten la misma autoridad, sin ejecutar modelo.
3. Si una ADR material se estructura con Contexto/Decisión/Alternativas/Consecuencias, conservar ID, resumen y hash de sección; si no hay ADR estructurada, solicitar revisión humana sin inventar un BLOCK global. `NOT_APPLICABLE` con razón explícita cuando proceda.
4. Gate previo a review: rechazar inequívocamente propuesta que ordene auto-instalar dependencias o reclame aprobación previa inexistente; en otros casos `REVIEW_REQUIRED` hasta evaluación Owner. No reabrir planes históricos de C09 ni limpiar recibos.
5. Sólo mostrar `APPROVED_WITH_ARCHITECTURE` tras comprobar estado FROZEN y bytes aprobados. No se escribe ADR standalone ni se asume que el approval del DRAFT fue aprobado efectivamente.
6. Focal sin full regression: tests positivos/negativos con dos dominios, tests Architecture impactados y build UI. En Windows verificar panel UI y crear dos capturas; no se exige generar un nuevo candidato L ni mutar Project runtime para demostrar el panel.

## Autoridad de la ampliación Owner C02 (2026-10-25) — sustituye la instrucción read-only anterior

La propuesta `R03_04_C02_PROPOSAL.md` está **APROBADA individualmente por Owner**. Los puntos 1–6 previos sirven como historia del checkpoint C00/C01, no como veto a la nueva funcionalidad. Implementar y demostrar generación **real** con Ollama local de 2–3 Technology Options independientes, selección Owner explícita y ADR material con modelo; conservar ambos candidatos con hashes y recibos. Conciliar una nueva Architecture DRAFT anulando el plan histórico, reusar review/approval/apply/freeze y extender el escritor multiarchivo ya gobernado para Technology Options + ADR tras FROZEN. El operador Windows debe detenerse con BLOCK legítimo ante drift, salida L defectuosa o negativa del Owner; no convertirlo en PASS artificial. Capturas guiadas, focal, documentos de ingeniería sincronizados, Git/baseline posterior al PASS; ninguna llamada L obliga instalación, publicación ni llamada externa.
