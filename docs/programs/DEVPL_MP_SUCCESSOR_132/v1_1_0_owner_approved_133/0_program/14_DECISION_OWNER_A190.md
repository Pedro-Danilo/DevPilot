---
doc_id: MP132-OWNER-DECISION-A190
status: OWNER_APPROVED_PROGRAM_AMENDMENT
version: "1.0.0"
date: "2026-10-24"
owner: Owner DevPilot
scope: EARLY_ARTIFACT_AUTHORING_QUALITY_HARDENING
execution_authority: false
in_flight_exception: R03_03_C06_CORRECTIVE_ONLY
supersedes: null
---
# Decisión Owner A190 — Afinamiento temprano de la autoría A188

## Ratificación

El Owner aprobó expresamente **«A190 — Propuesta de afinamiento temprano del contrato de autoría A188»** el 2026-10-24. Se ratifica la propuesta preservada en `temporal/PLAN_A190_PROPUESTA.md`, que históricamente tenía estado `DRAFT_OWNER_DECISION`. Esta decisión, y no una reescritura retroactiva del borrador, establece la nueva autoridad programática. A187, A188 y ADR-016 continúan vigentes.

## Cambios efectivos desde la corrección activa R03_03

1. **Núcleo transversal temprano** en cada ruta nueva de autoría L, reusando las autoridades existentes: identidad/tipo/PESP, fuentes y upstream FROZEN íntegros, distinción fuente completa/extracto, presupuesto de contexto y salida, segmentación solo cuando aporte cobertura, ModelAdapter local, salida tratada como no confiable, recibo de candidata inmutable y alternativa trazable, validaciones negativas demostrables, coherencia con decisiones Owner aprobadas, incertidumbre y revisión Owner, diff/approval/FROZEN gobernados, idempotencia y estado persistente sin doble inferencia.
2. **Especialización por tipo** sin un prompt universal: Architecture incorpora drivers, límites y datos, RF/RNF, ADRs, decisiones previas y condicionales de seguridad/API/UX; R03_04 incorpora ADR/Technology, R03_05 artefactos condicionales, R03_06 Security/Test Strategy/Traceability, R03_07 lifecycle/successor. R04–R06 aplican perfiles propios a Planning/Construction/Release; R07–R08 conservan sus autorizaciones independientes; R09–R10 evalúan resiliencia y generalización.
3. **Severidad proporcionada**: `BLOCK` solo por defecto material probado (corte, contradicción verificable, ausencia REQUIRED, fuente falsificada, decisión aprobada reabierta como no resuelta, mutación no autorizada); `REVIEW_REQUIRED` ante juicio semántico incierto o decisión genuina pendiente; `WARN` cosmético.
4. **Economía observada**: llamadas, unidades, tokens presupuestados, duración, fallos/recuperación y correcciones Owner; recursos no medidos=`NOT_AVAILABLE`, nunca costo computacional cero supuesto.
5. **Pruebas focales por riesgo** positivas/negativas, segundo dominio progresivo, reentrada real y LF/CRLF evaluado por contenido Git cuando corresponda; **SHA de recibos de bytes inmutables no se normaliza**.

## Autoridad y exclusiones

- Esta ratificación permite ajustar documentación normativa/contratos y alinear **el correctivo C06 del sprint R03_03 ya autorizado**. No concede nuevas tareas ni nuevas aprobaciones a R03_04–R03_11, R04–R10.
- No habilita proveedores E, costos externos, agentes mutativos, regeneraciones silenciosas, sobrescritura de C04/C05 ni cambios directos al workspace Pilot B. `UI_FIRST_PILOT_B_V1` se conserva.
- No autoriza commit/push ni FROZEN de Architecture: la candidata regenerada debe pasar evaluación semántica independiente antes de abrir ese gate.
- Un caso de test sintético con representación física LF/CRLF diferente de su propio hash se corrige en el **fixture**. Los recibos reales se verifican por SHA-256 exacto de bytes; un mismatch verdadero requiere revisión.

## Aplicación y seguimiento

La implantación sigue R03_03 → R03_04…R03_07 → R03_08…R03_11 → R04…R06 → R07…R08 → R09…R10, con un perfil probado por unidad y sin sobredimensionar R03_03. Los artefactos de programa, ADR-016, contrato A188, backlog y sprint/prompt R03_03 incorporan esta adenda. El checkpoint real de R03_03 permanece **BLOCK por test Windows C05** hasta probar C06; no se le declara PASS por aprobación documental.
