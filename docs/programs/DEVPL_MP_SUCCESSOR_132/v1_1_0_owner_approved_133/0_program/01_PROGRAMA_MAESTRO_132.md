---
doc_id: DEVPL-MP-SUCCESSOR-132-01_PROGRAMA_MAESTRO_132
title: "Programa maestro Multiprovider v1.1 — Ingeniería industrial asistida por IA"
version: "1.1.1-r00-succ"
status: "OWNER_APPROVED_PROGRAM"
baseline_commit: "66ab2e6227072c951b5bd2ac9160e8515b1b9fc0"
historical_baseline_commit: "8db5b44694abcced3231183e05731e732f5b8f24"
owner: "Owner DevPilot"
supersedes_program: "DEVPL_MP_SUCCESSOR_131 v1.0.0"
execution_authority: false
approval_revision: 1
approval_date: "2026-10-13"
approved_by: "Owner Ordóñez (instrucción explícita en conversación)"
approval_scope: "PROGRAMMATIC_PLANNING_ONLY"
successor_execution_authority: false
owner_decision_ref: "DEVPL-MP-132-OWNER-APPROVAL-133"
current_execution_baseline: "cd0bce59ec2bf4a7ae7e50a555c1c8a1bd85facc"
r01_gate: "CLOSED_PASS_WITH_FINDINGS"
r02_execution_authority: false
planning_amendment_id: "MP132-AMENDMENT-POST-R02-06-187"
planning_amendment_date: "2026-10-17"
planning_amendment_baseline: "b666c5641c1b8231c5b609216f64490a72ff1763"
planning_amendment_execution_authority: false
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


---

## Addendum operacional M0→R1 — sucesor de planificación (14-10-2026)

- **Asunto:** Programa maestro.
- **Actualización concreta:** Actualizar checkpoint operativo desde 8db5… hasta 66ab2e…; M0 CLOSED_PASS_WITH_FINDINGS, ruta B consolidada; conservar histórico Owner-133 y egress deny.
- **Evidencia vinculada:** COR-143 (migración B), R00-03/COR-145 (publicación 57 documentos), R00-04/COR-147 (auditoría Settings), COR-150 (paridad 1752), COR-151 (cierre Owner M0).
- **HEAD de autoridad técnica:** `66ab2e6227072c951b5bd2ac9160e8515b1b9fc0`. Las referencias a `8db5b44694abcced3231183e05731e732f5b8f24` y los indicadores `STOP ACTIVE` en secciones históricas no se reescriben como si fueran estados presentes.
- **Autoridad:** copia sucesora propuesta para adopción documental posterior; no constituye un commit, promoción Git, autorización de R1, de MP-1B, de modelo/API externa ni una aceptación funcional de Settings.
- **Transferencias vigentes:** `MP132-R0-09` → R2 para mediciones reales; UX Settings pendiente de reproducción y validación; egress externo DENY; no duplicar ownership entre olas.


---

## Adenda sucesora post-M1 — 15-10-2026 (no retroactiva)

- **Baseline Git publicado:** `cd0bce59ec2bf4a7ae7e50a555c1c8a1bd85facc` (`evolution/multiprovider-v2`), sucesor de `feaac2723c1f8a467f5cdb7d456e4e7679dd0f82` por R01-15/COR-171. - **R01:** 15/15 incrementos aceptados; 16 IDs propietarios cubiertos; cierre M1 `PASS_WITH_FINDINGS` con 108 tests focales y 8 del operador PASS en Windows. - **Evidencia:** `RESULT_171.json`, `M1_REPORT_171.json`, `R01_15_EVIDENCE.zip`, `repo_R01_15_CLEAN.zip` y SHA256. - **Autoridad:** R02 se desagrega sólo para planificación. Ningún `SPRINT_EXECUTION_APPROVED`, ningún push, bootstrap Pilot B, inferencia local, external egress o MP-1B queda autorizado por esta adenda. - **Limitaciones:** `model_local_real=NOT_TESTED`, `semantic_llm_judge=NOT_TESTED`, `rag_groundedness_real=NOT_TESTED`, `external_real=DENIED`; no confundir pruebas de servicio con un recorrido completo Product Definition UI.
- **Nivel real:** primera vertical determinista candidate → policy → docs → Settings a nivel servicios + aceptaciones de navegador de R01-11/12/13. No constituye E2E browser de la cadena completa ni generación semántica probada por un modelo.
- **Transición:** R02 comprueba modelos locales y Product Definition B0–B1, nunca convierte ausencia de Ollama/LM Studio en un falso PASS.

## Adenda Owner UI-first 179 — UI_FIRST_PILOT_B_V1

La regla vinculante es `UI_FIRST_PILOT_B_V1`: toda acción del proyecto Pilot B B0–B7 debe originarse en la UI normal de DevPilot; el backend puede ejecutar herramientas gobernadas (Git, Python, jobs, packaging, deploy, rollback), pero el operador humano no sustituye ningún workflow del piloto con CLI, editores externos, DevTools o scripts. La consola se limita al arranque/parada de API/UI hasta disponer de instalador, preconfiguración operacional de la instalación, auditoría y correctivos sobre **la plataforma**. `operator_project_writes=0`, `normal_user_terminal_escapes=0`, `journey_actions_via_devpilot_ui=true`.

**Condición E2E:** el mismo workspace/ID persiste de intake a release y evolución; no equivalen a aceptación las acciones manuales que compensen capacidades faltantes. Release, deploy, health y rollback deben iniciarse en UI; la aplicación desplegada se ejecuta autónomamente sin depender de DevPilot. ADR sucesora `ADR-MP-132-012.md`; M2–M6/M10 verifican continuidad y origen.

---

## Enmienda programática post-R02-06 · 187

### Política vinculante de autoría semántica

1. El **LLM elegible** interpreta contexto y propone Vision, Scope, Requirements, arquitectura, planeación semántica y código no trivial. Se ofrece **un candidato inicial por artefacto**; comparación, regeneración y segundo modelo son opcionales. El determinismo no compite como autor semántico de una plantilla que reproduce el intake.
2. DevPilot conserva D para PESP, schemas, context packs, perfiles, scaffolds tipados, diff, preimages, aprobación, QA, Git, release y recuperación. D puede producir *esqueleto o diagnóstico* pero no se califica `EQUIVALENT` a propuesta semántica sin pasar su mismo contrato de calidad.
3. Ruta L local, HEALTHY + EVALUATED + ELIGIBLE_FOR_TASK, es preferente. Modelo insuficiente → edición/refinamiento humano, otro L o E **solo si E está específicamente habilitado** con credenciales referenciadas, egreso, privacidad y CostGuard; jamás fallback externo silencioso. Ausencia de modelo competente da estado `MODEL_REQUIRED/PARTIAL` honesto.
4. El Owner revisa siempre un candidato **Markdown `.md` real, versionado y con hash**, editable por UI con nuevas revisiones; metadata técnica y canonical store pueden ser JSON, pero no una segunda autoridad mutable. `FROZEN` solo tras revisión, quality gate, diff y approval existentes.

### Resultado de software por incrementos

La secuencia profesional queda: Product/Technical Baseline FROZEN → **TechnologyProfile + Technical Scaffold** → Roadmap de outcomes/capacidades → **Release/Increment Plan** → Backlog/Sprints/Stories → **Construction Readiness** → implementación+tests+Quality+Git → **Increment Acceptance** → Release/Deploy/Restore → feedback y Successor. Un `DONE` de story no acredita incremento; incremento aceptado no es release listo. Se gobierna con el nuevo `SOFTWARE_INCREMENT_AND_DELIVERY_CONTRACT_132.md` sin introducir otra autoridad para Planning ni un gate humano trivial. El siguiente sprint se compromete con la evidencia del anterior, sin congelar artificialmente todos los futuros.

### Aplicabilidad de estándares y niveles demostrados

MIPSoftware aplica a todo producto y a cada incremento según riesgo; MIASI solo a componentes de IA *del software creado*, no por usar IA en DevPilot. Calidad y documentación son condicionales y verificables; no se declaran profesionales por existencia de encabezados. Pilot B B0 ya demostrado, R02-06 cerrado por comparación/persistencia **sin** calidad documental profesional. R02-07 requiere propuesta L y Markdown profesional antes de FROZEN. R3–R10 incorporan entregas integradas y sus pruebas sin cambiar IDs históricos.

### Autoridad y límites de esta enmienda

Modificación exclusivamente programática, basada en `repo_R02_06_CLEAN.zip` y HEAD `b666c5641c1b8231c5b609216f64490a72ff1763`. El addendum prevalece para planificar **incrementos futuros** donde contradiga una instrucción heredada (por ejemplo `D/mock primero` para escritura semántica); no altera hechos históricos, el baseline Git, status de ejecución, commits o cierres R00–R02-06 ni autoriza R02-07/R08/egreso. Los tres ADR de esta enmienda describen fronteras **programáticas** pendientes de materialización con gates específicos.

---

## Adenda normativa 188 — calidad y unidad transversal

**Enmienda 188 Owner-approved (2026-10-22)**. Autoridad `MP132-OWNER-DECISION-188`; contrato `2_contratos/ARTIFACT_AUTHORING_QUALITY_CONTRACT_188.md` y ADR-MP132-016. Complementa 187/ADR-013; se aplica prospectivamente por olas, sin alterar recibos históricos, ni autorizar ejecución de un sprint o proveedor E.

**Premisa industrial medible:** toda propuesta generada debe conservar procedencia, completitud y coherencia con las otras partes de la aplicación; el Owner revisa hechos de negocio, excepciones, decisiones y riesgos y no reconstruye defectos técnicos rutinarios. Un contrato de proceso con perfiles por artefacto y PESP variable, no un prompt genérico universal. La madurez de R02-07 es piloto supervisado, no generalización ya alcanzada. Referencia actual de planificación `3a0a170f3c646e9955966576dd9212d3f87450e6`.

---

## Adenda de cierre R02 → planificación R03 — 2026-10-22

**Cierre acreditado y no retroactivo:** `R02-10 = CLOSED/PASS_WITH_FINDINGS`, M2 `PASS_WITH_FINDINGS`, `BACKLOG_R02_132 = CLOSED/PASS_WITH_FINDINGS`, HEAD `1f15fa5b770db37c684e870a49572dcb569bd3a4` (upstream `origin/evolution/multiprovider-v2`), baseline oficial `repo_R02_10_CLEAN_1f15fa5b770d.zip` (SHA-256 `cc8327cb5cf5413187625cd6d59986c2972a260bd72b776ee30833090a72d743`), evidencia R02-10 SHA `9d2d7859849f385c440899c9cfdce72df43bd4de1aea3ef17bd0890f91c08e3d`. Pruebas focales R02-10: 52 PASS, 0 FAIL, 0 SKIP; Full Regression 0.

**Límites permanentes:** el modelo local + revisión Owner produjo tres FROZEN; no demuestra calidad autónoma de primera propuesta ni equivalencia semántica profunda. Capturas pre/post reinicio idénticas: continuidad apoyada en consola HTTP 200 y narración Owner, no en cambio visual. Se conserva recibo histórico `api.json` BLOCK por inicio duplicado (fue un fallo de la guía), sin reescribirlo como PASS. No se midió calidad multi-modelo independiente, API E permanece DENY. No se alteran los tres FROZEN de Pilot B.

**Transición:** dependencia M2→R03 liberada para **planificación únicamente**. La desagregación R03 es `DRAFT_EXECUTION_GATED` por sprint; cada prompt `DRAFT_AWAITING_OWNER_INCREMENT_APPROVAL`; no otorga source writes, scaffold, red, proveedor E ni autorización colectiva. El primer sprint R03_01 ejecutará reconciliación de documentación activa y Source Registry, con inventario de drift real vs histórico. Se mantiene UI-first y `operator_project_writes=0`.

## Registro histórico R02 conservado — recuperación R03-01 COR2

Esta sección conserva literalmente antecedentes R02 del repositorio predecesor `1f15fa5b770d` que fueron omitidos al reconciliar R03. **Es historia, no autoridad operativa vigente**: los estados y las autorizaciones actuales son los establecidos por las adendas R03/A189 anteriores y el estado de ejecución de DevPilot. No revive sprints ni concede permisos.

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

## Actualización de ejecución R02-05 — COR178 (Owner individual)

- Entrada canónica: `735ecfd82e9604a4755fd7d4e7c386976984ed71` (R02-04 Windows PASS_WITH_FINDINGS; LM Studio `DEFERRED_WITH_REASON`).
- `R02-05/PILOT-B-ENTRY-RESUME`: `SPRINT_EXECUTION_APPROVED`, solo la unidad B0. `R02-06`: `NOT_AUTHORIZED`.
- Se reutilizan los mecanismos existentes de `CREATE_NEW` neutral, PathGuard, dry-run, revalidación, aprobación, bootstrap y runtime registry persistente.
- El cambio R02-05 es la evidencia/control de entrada de Pilot B por la interfaz y la identidad clara del proyecto activo en Home; no inicia B1 ni establece RF, stack, scaffold o proveedor por defecto.
- El baseline de planificación histórico no se reescribe. El sucesor Git solo se acredita cuando Windows apruebe browser, B0 creado por UI y Git normal.
- Los defectos de select de modelo y espaciado del Laboratorio de modelos (`R02-04`) permanecen findings UX; no se introducen modificaciones de modelo en esta unidad.
