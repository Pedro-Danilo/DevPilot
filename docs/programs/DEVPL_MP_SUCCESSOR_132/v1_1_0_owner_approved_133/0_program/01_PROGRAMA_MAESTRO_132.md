---
doc_id: DEVPL-MP-SUCCESSOR-132-01_PROGRAMA_MAESTRO_132
title: "Programa maestro Multiprovider v1.1 — Ingeniería industrial asistida por IA"
version: "1.1.0"
status: "OWNER_APPROVED_PROGRAM"
baseline_commit: "8db5b44694abcced3231183e05731e732f5b8f24"
owner: "Owner DevPilot"
supersedes_program: "DEVPL_MP_SUCCESSOR_131 v1.0.0"
execution_authority: false
approval_revision: 1
approval_date: "2026-10-13"
approved_by: "Owner Ordóñez (instrucción explícita en conversación)"
approval_scope: "PROGRAMMATIC_PLANNING_ONLY"
owner_decision_ref: "DEVPL-MP-132-OWNER-APPROVAL-133"
---

# Programa maestro Multiprovider v1.1 — Ingeniería industrial asistida por IA

## 1. Visión y razón del sucesor

DevPilot debe permitir que una persona describa una necesidad real, defina el producto, diseñe arquitectura, planifique, construya, valide, libere, opere y evolucione una aplicación, con asistencia de modelos y agentes donde son eficaces y controles comprobables donde la integridad es imprescindible. No se mide madurez por la cantidad de clases, páginas o templates existentes, sino por **un resultado de software realmente utilizable**, obtenido por la interfaz normal, portable, auditado y recuperable.

**Premisa permanente:** *la inteligencia generativa interpreta, compara y crea propuestas contextuales; el núcleo determinístico aplica estándares y controla identidad, autorización, schemas, preimages, cambios, aprobaciones, calidad, Git, release y recuperación*.

La solución no es un motor de plantillas por historia específica ni una ejecución autónoma sin límites. Para tareas semánticas complejas se prefiere modelo **local** cuando está disponible y evaluado; externos son opt-in gobernado; D subsiste siempre en tareas estructuradas, inspección y ejecución segura. Ausencia de L nunca debe falsificar equivalencia de D (`EQUIVALENT`, `REDUCED`, `MODEL_REQUIRED`).

## 2. Punto de partida acreditado y límites

- Rama MP fusionada: `evolution/multiprovider-v2` HEAD `8db5b44694abcced3231183e05731e732f5b8f24`; archivo ZIP COR-130 íntegro con 4510 entradas. Es la autoridad técnica de entrada, **no** la autorización del programa.
- Línea `official/devpilot-local` a HEAD histórico `f5c4b0f1…`; ambos worktrees comparten `.git` bajo `D:\Projects\DevPilot_Local`.
- COR-130: 9 rutas de rebind documental, 14/14 pruebas focales Windows PASS y commit/push normales; **ratificación administrativa Owner-133 completada**. El antiguo flag STOP `ACTIVE` en el snapshot refleja su fecha; Owner levantó el STOP global programático. MP-1B antiguo **no se activa** por ello.
- G5 técnico SYNC-1: PASS con límites y cierre documental; **ratificación administrativa Owner emitida en acta separada 133**, sin modificar la evidencia original 128/129.
- Ya existen `GenerationRequest`, `ArtifactCandidateEnvelope`, `GenerationRouteResolver`, adaptadores Ollama/LM Studio, RAG ContextPack, servicios agénticos, SourceChangePlan, Quality y Git; **no está demostrada la integración completa ni la calidad de generación L/E en todo el SDLC**.
- Pilot A se cerró `D05/PARTIAL_ACCEPTANCE` sin MVP; RF004–008 diferidas; no se retoma sin nuevo mandato. Pilot B será un proyecto **nuevo y continuo**, no una repetición cosmética de RF001–003.

## 3. Resultados de producto contractuales

1. **Generalidad:** al menos Pilot B E2E y un segundo dominio independiente; código generado por modelos competentes para historias arbitrarias, no por una plantilla codificada por RF.
2. **Ingeniería profesional:** MIPSoftware base obligatorio, MIASI por componente/riesgo real; PESP aprobado, perfiles profesionales, Coverage Gates, artefactos humanos Markdown consultables y artefactos canónicos sin autoridades duplicadas.
3. **Flujo de producto:** Intake neutral → Vision/Scope/Requirements → Technical Design/ADR/Data/Security/Testing/Technology → Planning→Stories→Code/Tests→Quality/Git→Release/Operations→Evolution. El catálogo se materializa según aplicabilidad, sin carpetas/plantillas ficticias.
4. **Multimodelo real:** matriz D/L/E, `ModelAdapter` desacoplado, selección por capacidades medidas, provenance, presupuesto y privacidad; inferencia L real en R2 y story arbitraria en R5. External debe pasar ADR/egress/CostGuard aparte.
5. **Agentes gobernados:** review/enrichment/handoffs delimitados, sin creación propia de permisos ni ejecución directa de cambios, roles evaluados y trazas; MCP opcional con trust boundary independiente.
6. **Ciclo evolutivo:** FROZEN inmutable; cambio por successor e impacto RF→ADR→story→código→tests→release; Planning actualizable durante toda la vida del producto.
7. **Operabilidad:** startup estable, Settings persistente por responsabilidades, permisos y defaults efectivos claros; paquete portable de aplicación y manifiesto separado de evidencia, instalación, observabilidad, rollback y recuperación real.
8. **Experiencia humana:** Guided orientado a tarea y Expert con evidencia; una sola proyección autoritativa de estado, approval legible y feedback local; hallazgos UX corregidos progresivamente, no sólo R9.

## 4. Arquitectura de autoridad inmutable

`Owner/contexto → PESP/policies/datos/presupuesto → GenerationRoutePolicy(D/L/E) → ArtifactCandidateEnvelope → schema/semantic/grounding/evals → revisión humana → canonical lifecycle/SourceChangePlan → dry-run/preimages/approval → apply/test/Quality/Git/release`. Los agentes son consumidores/revisores autorizados alrededor de ese flujo; no existen motores paralelos de mutación por proveedor. Providers generan propuestas, **no** aprueban ni hacen commit.

## 5. Gobernanza del programa

- `AUDIT-FIRST / REUSE-FIRST` antes de **todo** cambio de baseline: HEAD exacto, auditoría de fuente viva, `Reuse/Delta Map`, matriz owner-of-responsibility, ADR sucesor sólo si cambia contrato, allowlist y pruebas positivas/negativas. `NO-OP` y `REUSE-AS-IS` son resultados válidos.
- El STOP global fue **levantado expresamente por el Owner** en la decisión `DEVPL-MP-132-GLOBAL-STOP-LIFT-133`. El levantamiento habilita la **preparación y autorización gradual** del programa, no acciones automáticas. Cada incremento requiere auditoría focal, scope, Owner gate, permisos de source y promoción separados. Egress externo, secretos y herramientas permanecen DENY/default hasta decisiones específicas.
- Una ola es contenedor de objetivos, no necesariamente épica. Backlogs R0–R10 tienen propiedad por ID y un índice derivado; sprints/prompts **no incluidos** por mandato.
- Un gate puede concluir `PASS`, `PASS+FINDING`, `PARTIAL`, `BLOCK` o `NOT_APPLICABLE`, con evidencia y alcance. `PASS` de fixture no es E2E; build UI no es acceptance de interacción; `HEALTHY` de modelo no prueba capacidad de generar buen código.
- Full Regression selectiva para cierres aprobados; pruebas focales, negativas y por vertical antes. Windows: una sola guía `.md` por incremento, comandos PowerShell completos de una línea, procesos foreground, snapshots y hashes, no terminal para escribir Pilot B.

## 6. Estructura de ejecución y aceptación

Roadmap R0–R10 se conserva, con **R1 fundacional acotado** (contratos y primera vertical) y expansión gradual en R2–R8. Pilot B B0–B7 es un único proyecto; Pilot C controla APIs externas sin contaminarlo. Aceptación independiente final distingue `LOCAL_FIRST_PROFESSIONAL`, `AGENT_ASSISTED` y `EXTERNAL_ENABLED` sin afirmar una categoría por alcanzar otra.

## 7. Diferenciación de estado / aprobación

`OWNER_APPROVED_PROGRAM` (**este paquete**, Owner-133) ≠ `SPRINT_AUTHORIZED` ≠ `PROMOTION_AUTHORIZED` ≠ `PRODUCT_E2E_ACCEPTED`. G5 quedó ratificado **por decisión separada**, no por inferencia de la aprobación del programa.

## 8. Exclusiones y límites honestos

No se retoma Pilot A, SYNC-1, SYNC-2 ni MP-1B histórico; no se autoriza renombrar una rama, activar agentes, comprar API o ejecutar modelos remotos; no se afirma certificación regulatoria/enterprise; no hay aceptación industrial hasta pruebas de producto completo, seguridad, portabilidad, recuperación y evaluación independiente. No se inventarán métricas sin hardware/dataset/presupuesto aprobados.

## Actualización operativa MP132 post-M1 — R02-01

**Programa post M1.** Madurez M1 `PASS_WITH_FINDINGS`, 14 recibos, 3 browser attestations; modelos locales reales `NOT_TESTED`, externos `DENIED`; único micro-sprint activo R02-01. No elevar M2 por esta auditoría.

**Autoridad:** esta sección actualiza el *estado operativo*, no modifica el `status: OWNER_APPROVED_PROGRAM` de la aprobación histórica Owner-133, ni autoriza R02-02. Source Registry mantiene el `doc_id` y `path` originales.


## Adenda de estado operativo — R02-03/COR-176 (sucesora, no retroactiva)

- **Predecesores acreditados:** R02-01 `CLOSED/WINDOWS_PASS` en `4a4443f1631acdbfcd19e1e2fca4be36f707daf9`; R02-02 `CLOSED/WINDOWS_PASS` en `8a9b1cf915f8cfb9d08b35d6d1c13467d0bd08fc`. Las adendas R02-01 anteriores se conservan como historia, no son la autoridad de ejecución actual.
- **Autorización individual vigente:** únicamente `R02_03_OLLAMA_REAL_CANDIDATE_SPRINT.md` = `SPRINT_EXECUTION_APPROVED` y su prompt = `OWNER_APPROVED`; baseline R02-02 acreditado y rama `evolution/multiprovider-v2`. Este bloque NO constituye recepción Windows de R02-03.
- **Gate de salida R02-03:** al menos tres candidatas sintéticas generadas mediante invocación **real** a Ollama en loopback, con procedencia, hashes, recibos JSON, revisión browser, negativas y ninguna publicación FROZEN ni cambio de enabled global. Hasta observarlo, `LOCAL_PASS/WINDOWS_PENDING`; `EVALUATED`/`ELIGIBLE` NO se conceden automáticamente.
- **Límites:** R02-04 a R02-10 = `DRAFT/NOT_AUTHORIZED`; proveedores externos y MP-1B = `DENIED/NOT_AUTHORIZED`; M2 no declarado. Se conservan todos los `doc_id`, el status histórico `OWNER_APPROVED_PROGRAM` y los 1.752 registros del Source Registry.


## Adenda R02-04 — ejecución individual 2026-10-16

- R02-03 acreditado en Windows: `f2f7bf817e45b38feeb7bb64e638d3df626f825e`, `146/146` pruebas, tres candidatas Ollama reales, cinco capturas, push normal. La **generación** está validada; calidad semántica, aprobación y FROZEN permanecen pendientes.
- R02-04: `SPRINT_EXECUTION_APPROVED` exclusivamente para paridad opcional LM Studio, `OWNER_APPROVED` para su prompt, ejecución sobre el HEAD R02-03 indicado; no supone habilitación global ni requerimiento de instalación de LM Studio.
- LM Studio ausente → `DEFERRED_WITH_REASON`, nunca `REAL_PASS` ni bloqueo del futuro M2 con Ollama. Laboratorio de inferencia separado de Configuración por UX; sin activar R02-05.
- R02-05 y posteriores: `NOT_AUTHORIZED`. Mantener históricos y 1.752 entradas Source Registry inmutables.
