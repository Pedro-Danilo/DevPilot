---
doc_id: DEVPL-ARCH-PROGRAM-REBASELINE-116
title: "DevPilot — Propuesta de rebaseline Pilot A / convergencia Multiprovider"
version: "1.1.0"
status: "APPROVED / OWNER-DECISION-RECORDED / EXECUTION-GATED"
date: "2026-10-11"
approval: "OWNER-APPROVAL-2026-10-11-REBASELINE-116"
supersedes: "PROPUESTA_116_ORIGINAL.md"
phase_authorized: "P0 documentary formalization only"
d05_status: "NOT-YET-FROZEN"
d06_status: "NOT-YET-QUALIFIED"
sync1_status: "NOT-AUTHORIZED"
programs_affected:
  - DEVPL-GSDLC-13-GREENFIELD
  - DEVPL-MULTIPROVIDER-v2.1
proposal_type: "ARCHITECTURE-AND-PROGRAM-DECISION"
implementation_authority: false
source_mutation_authorized: false
multiprovider_stop_lifted: false
---

# PROPUESTA DE REBASELINE 116

> **ACTO DE APROBACIÓN (2026-10-11).** El Owner ha aprobado expresamente elevar esta propuesta y derivar los artefactos hasta P3. Se aceptan las decisiones D-01 a D-05 descritas en la sección 15, **como cambio de estrategia de programa**. Los enunciados originales «propuesta», «pendiente» y «no autoriza» se conservan a continuación como relato de la versión previa y **no prevalecen sobre esta resolución**. La decisión G0 queda aprobada; G1 (publicación/reconciliación de successors), G2 (freeze D05), G3 (D06), G4 (auditoría/preflight) y G5 (SYNC-1 PASS) siguen pendientes. Este documento NO ejecuta acciones, no declara MVP completo, no levanta STOP ni modifica Git.

**Cláusula prevalente y continuidad:** P0 puede formalizar los successors aprobados aquí; P1 solo tras G1; P2 solo tras G2; P3 auditoría solo tras G3; el merge de P3 requiere además la auditoría y una autorización Owner **separada sobre su plan de integración exacto**. El programa Multiprovider general no se replanifica globalmente hasta el resultado de P3; el STOP y el protocolo SYNC se adaptan limitadamente como puente.


## De Pilot A determinístico extendido a plataforma SDLC generalizable con núcleo determinístico

> **Naturaleza del artefacto.** Documento para **decisión del Owner**. No es una adjudicación PASS de 13-D-05, una autorización para ejecutar SYNC-1, una orden de modificación de branches ni una guía operativa. Los artefactos previamente aprobados mantienen su autoridad hasta la aprobación y publicación de sus *successors* coherentes. Ninguna fuente histórica FROZEN debe reescribirse.

## 1. Decisión ejecutiva propuesta

**Recomiendo adoptar un rebaseline coordinado de Greenfield y Multiprovider**, en vez de (a) programar capacidades de generación determinística para cada nueva historia del piloto o (b) saltar inmediatamente a Multiprovider sin demostrar recovery.

1. **Congelar la expansión funcional de Pilot A** con las tres stories demostradas (`RF-001..003`), sin borrar, revertir ni declarar implementadas `RF-004..008`.
2. **Adjudicar D05 como `PARTIAL_ACCEPTANCE / REBASELINED_STOP`**, no `CLOSED/PASS-MVP`. Declarar qué contratos técnicos quedaron probados y qué requisitos de MVP quedaron **insatisfechos**.
3. **Redefinir D06 como calificación de resiliencia del núcleo SDLC** sobre el estado ya alcanzado, con escenarios controlados, reversibles y evidencia independiente. D06 dejará de depender de que ocho stories estén DONE; *no* se exime de recovery.
4. Solo después de `D06-REBASELINED/PASS` y los requisitos adicionales de gobernanza, **autorizar `SYNC-1` determinístico → Multiprovider**, sin rebase ni importación inversa. `STOP MULTIPROVIDER` continúa activo hasta un SYNC-1 efectivo y adjudicado PASS.
5. **Concentrar la generación semántica y contextual generalizable en el programa Multiprovider**, reutilizando el núcleo autoritativo y evitando un router/ModelAdapter paralelo en la rama determinística.
6. **Trasladar el objetivo de aplicación completa, flujo de inventario y venta, instalación, recuperación, release y aceptación E2E** a una demostración integral del Pilot B y a los gates oportunos de la nueva secuencia. Pilot A no puede considerarse un Greenfield E2E PASS con tres stories.

La propuesta preserva el aprendizaje del piloto, evita trabajo desechable en templates específicos y mantiene una prueba de recuperación antes de introducir motores generativos reales.

## 2. Fundamento: hecho documentado vs. juicio arquitectónico

### 2.1 Hechos verificados en las fuentes y evidencia acumulada

- El successor aprobado `SPRINT_13D_v1_3_APPROVED_REBOUND.md` exige en D05 `repeat until MVP`; D06 cubre recovery y el orden actual es `D05 → D06 → SYNC-1`.
- `PROTOCOL_13D_v1_2_APPROVED_REBOUND.md` solo permite cerrar D05 cuando se alcanza el MVP; una story completada equivale a `PASS/PROGRESS`, no al cierre del checkpoint.
- El Charter Greenfield exige un resultado *end-to-end* desde proyecto vacío hasta release, con `operator_project_writes=0` y sin inyección externa de código. El Pilot Brief exige al menos un flujo de inventario **y venta** instalable/reproducible.
- El programa Multiprovider v2.1 ya define una arquitectura de rutas `Deterministic / LocalModel / ExternalModel`, candidate envelopes y núcleo determinístico de autoridad; su `ADR-MP-V2-007` preserva RBAC, approval, apply, tests, Quality, Git, recovery y release.
- `STOP_MULTIPROVIDER_AFTER_MP_1A` prohíbe mutaciones y la continuación de MP-1B hasta el cierre D05/D06 y SYNC-1; `ADR-MP-V2-008` exige worktrees separados y sincronizaciones one-way mediante merge.
- La adjudicación más reciente del piloto acredita `story-rf-001`, `story-rf-002` y `story-rf-003` en `DONE`, no las ocho historias. El baseline de plataforma es `repo_465` / `e5ed25922aa3fb7b1fc7ed9f738ff1ca8a666218`, y el HEAD del piloto después de RF-003 es `0f5f1518f3f76034c1367fe60d637c6d69fa78f8`. Multiprovider permanece en STOP `54085701f39670ec460a80a6b3f9097a9e61a3d1` según la evidencia reportada.
- `repo_465` contiene `GeneralStoryProvider`, dos capacidades determinísticas ligadas al dominio productos y una ruta opt-in de modelo local **no acreditada con inferencia real**. La ADR local del mismo repo reconoce que debe reconciliarse con el programa Multiprovider.

### 2.2 Juicio de ingeniería (propuesta nueva, NO contenido ya aprobado)

La repetición de tres stories prueba el circuito gobernado de construcción en más de un incremento, pero seguir implementando plantillas nuevas del mismo dominio **aumenta poco la generalidad**. El valor marginal decrece mientras crecen el mantenimiento, los tests ad hoc y el riesgo de arquitectura duplicada. La cualidad industrial diferencial no es la cantidad de historias preprogramadas sino la capacidad de manejar requisitos no vistos, registrar incertidumbre y rechazar candidatos incorrectos sin sacrificar controles.

La continuación más eficiente es **recuperar evidencia transversal faltante** (resiliencia y sincronización) y dedicar el esfuerzo de nuevas capacidades al plano de generación contextual Multiprovider, no a extender Pilot A por número de historias.

## 3. Alternativas evaluadas

| Criterio | A. Terminar 8 stories con templates | B. Rebaseline coordinado + D06 + SYNC-1 | C. Abandonar Pilot A y pasar ya a MP |
|---|---|---|---|
| Eficiencia del trabajo futuro | Baja: posible especialización por comportamiento | Alta: reduce especialización y reutiliza evidencia | Aparente alta, pero traslada riesgos de recovery |
| Generalización de producto | Baja hasta introducir motores semánticos | Alta: concentra el esfuerzo donde pertenece | Alta en intención, débil en controles demostrados |
| Riesgo de deuda arquitectónica | Alto: overfitting y dos routers | Controlado mediante auditoría de convergencia | Medio/alto por divergencia y gates no probados |
| Evidencia de SDLC real | MVP de Pilot A si se completa efectivamente | Evidencia parcial explícita + futura E2E Pilot B | Queda una validación determinística inconclusa |
| Riesgo operacional | Bajo en generación conocida, coste temporal alto | Acotado: exige D06 real antes de Sync | Mayor: modelo real sin recovery demostrado |
| Conformidad actual | Sí, pero ineficiente | Requiere aprobación formal de successors | Requiere ruptura formal mayor del programa |

**Decisión recomendada: B.** No equivale a renunciar al requisito de aplicación completa: se *reasigna su demostración*, sin falsear que Pilot A ya lo haya satisfecho.

## 4. Límites arquitectónicos que se conservan y ajustes propuestos

**Conservar como invariantes de producto:** humanos/roles y permisos; `PathGuard`, allowlists y preimages; diferencias de `draft`, `proposal`, `approved` y `applied`; atomicidad y rollback; Test Impact/required jobs; Quality/COMMIT_READY; approvals diferenciados Git; trazas/provenance; recovery, migración y release autoritativos; `operator_project_writes=0`; fail-closed; CostGuard y redes explícitas.

**No seguir desarrollando en el track determinístico:** generadores funcionales `RF004…`, nuevo classifier basado en keywords como solución universal, integración de Ollama/LM Studio específica de Pilot A ni un segundo `GenerationRouteResolver`.

**Congelar sin borrar:** `GeneralStoryProvider`, su ADR y contrato vigente en `repo_465` permanecen en la historia y en el baseline de validación. Su ruta local no acreditada se clasifica como **experimental/no habilitada para aceptación de Pilot A**. La auditoría de SYNC-1 determinará si se **reutiliza, adapta o depreca** frente a los contratos MP existentes, con tests de equivalencia; no se decide por nombre o semejanza superficial.

**Convergencia final:** el objetivo no es mantener dos productos o dos routers en paralelo indefinidamente. MP-8 debe decidir una única línea de producto oficial con rutas de generación intercambiables, núcleo autoritativo compartido y retirada controlada de adaptadores redundantes; Pilot A permanece como evidencia histórica y fixture de regresión, no como una segunda arquitectura con evolución autónoma.

**No elevar a hecho:** no existe un generador determinístico universal de software correcto para cualquier requisito libre. Las capacidades determinísticas componibles pueden resolver familias formalizadas; la generación contextual más general necesita modelos/síntesis con validaciones y no implica garantía de corrección.

## 5. Nuevo contrato propuesto para D05

### 5.1 Cambiar el objetivo de cierre, NO reescribir los resultados

**Contrato anterior:** `D05 = CLOSED/PASS` únicamente tras completar el MVP y demostrar activación sucesora.

**Contrato sucesor propuesto:** `D05 = REBASELINED_STOP / PARTIAL_ACCEPTANCE` una vez auditados y congelados los tres ciclos disponibles y formalizado el *residual backlog*.

Criterios de adjudicación específicos:

1. `RF-001/002/003` demuestran, con evidencia ya preservada, activación, ContextPack, proposal, revisión Owner, Drafts, SourceChangePlan, dry-run, approvals, apply, TestPlan/jobs, Quality, Git y `DONE` según el alcance aplicable a cada run.
2. Evidencia de continuidad `DONE → next READY → prepare/start` al menos en las transiciones ya observadas, incluyendo los bloqueos/correctivos y su resolución, sin repetir artificialmente first-attempt.
3. No existen operaciones de story pendientes o mutaciones inseguras en curso; los cambios de proyecto normales están fijados a sus SHAs. Artefactos runtime no versionados se distinguen de cambios de source y se preservan.
4. **RF-004..RF-008 quedan `DEFERRED_BY_PROGRAM_DECISION / NOT_IMPLEMENTED`**, en el ledger de programa, *sin cambiar su estado FROZEN/READY en el proyecto si hacerlo exigiera una mutación*. No marcarlas `DONE`, `CANCELLED` ni `OUT_OF_SCOPE` retrospectivamente.
5. Se documentan las limitaciones: MVP inventario+venta **no completo**; release E2E de Pilot A **no aprobado**; cobertura de funciones no vistas **no demostrada**.
6. Se publica una adjudicación cuyo estado diferencie **capacidad de circuito aceptada** de **objetivo de producto pendiente**. No convertir un `PARTIAL_ACCEPTANCE` en `CLOSED/PASS` mediante cambio de etiqueta.

`D05-REBASELINED_STOP` habilitaría **solo el D06 revisado**; no autoriza por sí mismo `SYNC-1` ni MP-1B.

## 6. Nuevo contrato propuesto para D06

### 6.1 Justificación

Recovery/reconciliation es una precondición transversal para agentes y modelos: ante operaciones interrumpidas, no es admisible que un candidate nuevo sobrescriba el source, replique un approval o corrompa el índice Git. Es valioso probarlo **antes** de habilitar un LocalModel, incluso si el MVP de Pilot A aún está incompleto.

### 6.2 Alcance de calificación

Mantener los **seis escenarios previstos**, evaluados sobre estados reproducibles y reversibles derivados de los tres story cycles existentes, con entornos aislados cuando requieran introducir conflicto:

1. restart / nueva sesión y recuperación de contexto persistido;
2. interrupción de operación segura (sin mutación doble ni approval duplicado);
3. edición externa y detección de drift de preimage;
4. dirty working tree y delimitación de paths gobernados;
5. branch/divergence/conflict con reconciliación explícita y no destructiva;
6. stale lock / recuperación de exclusión o bloqueo.

Para cada escenario, conservar first-attempt, estado inicial/autorización, transición, resultado, diagnóstico y estado final. Una prueba ya PASS y respaldada por evidencia no se repite por cambios de sesión. **No aceptar un scenario PASS solo porque el operador fabricó el estado final que debía producir DevPilot.**

### 6.3 Criterio D06 revisado

`D06-REBASELINED/PASS` exige que la plataforma sea capaz de detectar, explicar y resolver o bloquear correctamente los escenarios dentro de su contrato; cero pérdida de source/evidencia, cero bypass y cero operación destructiva. Si no puede recuperarse de un caso crítico, D06 sigue `BLOCK` y procede correctivo focal de núcleo determinístico, con nuevo baseline y ZIP limpio.

No declarar que esta calificación prueba la recuperación de un **MVP completo**: solo del circuito ya implementado.

## 7. SYNC-1 y STOP — gate sucesor propuesto

La secuencia revisada sería:

`D05/PARTIAL_ACCEPTANCE formalizado → D06-REBASELINED/PASS → SYNC-1 con revisión arquitectónica reforzada → MP-1B autorizado`.

**SYNC-1 no cambia su dirección**: `official/devpilot-local → evolution/multiprovider-v2`, mediante merge documentado, sin rebase de commits sellados. El STOP se mantiene hasta el *receipt* de SYNC-1 PASS y no se levanta al aprobar simplemente esta propuesta.

A los controles vigentes de SYNC-1 (branches clean/pushed, autoridad, conflicto semántico, doc rebind, focal/impact, UI smoke si aplica, evidence, commit/push) agregar:

- **inventario de componentes reutilizables** desarrollados desde el fork: source, schemas, servicios, UI, contratos y cambios de estado;
- **matriz `GeneralStoryProvider` vs. `GenerationRouteResolver/ProviderSelectionPolicy`**: no duplicación; decidir por componente `KEEP / ADAPT / DEPRECATE`, con rationale y pruebas;
- **paridad de authority:** ninguna propuesta de modelo puede crear ni aprobar SourceChangePlan, test waiver, Quality PASS o Git commit;
- **compatibilidad del repositorio y las historias Pilot A:** preservación de evidencias y capacidad de leer sus artifacts, sin regenerarlos;
- **rollback plan del merge/reconciliación** gobernado, sin comandos destructivos ad hoc;
- **fuente de verdad nueva**: Source Registry, ADR successor, contratos y catálogo rebind;
- **no contaminación de Pilot A**: sin importar MP→deterministic, sin ejecutar modelo local sobre el piloto congelado.

**Decisión de STOP:** publicar un successor que sustituya únicamente la condición `D05 MVP PASS` por `D05 PARTIAL_ACCEPTANCE aprobado + D06-REBASELINED PASS + SYNC-1 PASS`, preservando las demás restricciones; MP-1B abre solamente tras la adjudicación efectiva de SYNC-1.

## 8. Efecto sobre D07/D08, 13-E y release

Este es el mayor efecto colateral del rebaseline y **no puede quedar implícito**.

El contrato original liga D07/D08 a release readiness, paquete, SBOM, tag, clean install, rollback y final local release de Pilot A. Con tres stories, especialmente sin flujo completo de ventas, **no corresponde emitir `Pilot A local release PASS` ni `13-E E2E PASS`**.

Se propone separar dos evidencias:

- **Calificación de capacidades determinísticas de release/operación**: en una fase posterior a MP-2 y **antes de que MP-5 dependa de dichas capacidades**, demostrar packaging, checksum/SBOM, versión, instalación, upgrade/rollback y restore usando un **fixture desechable adecuado y explícitamente etiquetado**. Los gates RELEASE_READY no se eluden: si el fixture no puede alcanzarlos legítimamente, la calificación permanece `BLOCK`. Este trabajo necesita su propio contrato de aceptación, no una ficción de Pilot A MVP.
- **Aceptación E2E del producto**: ejecución completa y fresca sobre **Pilot B**, en los checkpoints MP-4/MP-5/MP-8 que correspondan, con funcionalidades reales, pruebas, Git, recovery y release. Esta aceptación no hereda automáticamente PASS de Pilot A; la evidencia transversal sí es reutilizable cuando resulta válida.

`13-E` original queda **DEFERRED / NOT-EVALUABLE-UNDER-OLD-CHARTER** hasta aprobar su successor o cancelar formalmente esa modalidad; no declarar cierre antiguo. La autorización para Legacy Adoption se mantiene condicionada a un nuevo gate E2E real y aprobado.

`SYNC-2` debe revisarse en la matriz de dependencias: solo es necesario como merge one-way adicional si existen **deltas nuevos de la rama determinística** derivados de la calificación de release. Si no hay delta, se emite un *no-op sync receipt* auditable; no se simula un merge.

## 9. Ruta de programa propuesta (conceptual, sin micro-sprints ni operadores)

| Fase conceptual | Resultado verificable | Habilita |
|---|---|---|
| P0 — Aprobación del rebaseline | Decisión Owner + matriz de successors aprobada | Nueva autoridad documental |
| P1 — Freeze D05 | Adjudicación parcial RF001..003 + cinco pendientes + estado Git/evidencia | D06 revisado |
| P2 — D06 bounded | Six-scenario recovery PASS, sin escrituras de operador | Solicitud de SYNC-1 |
| P3 — SYNC-1 reforzado | Merge determinístico→MP, paridad, docs, pruebas y new authority | Levantamiento condicionado del STOP |

| P4 — MP-1B/C/D | LocalModel real en Product Definition + Pilot B desde cero | MP-2 |
| P5 — MP-2 | Technical Design/Scaffold/Provisioning gobernados en Pilot B | Calificación de release y MP-3 |
| P6 — Release core qualification + SYNC-2 si procede | Autoridad de release/install/rollback demostrada por fixture, no Pilot A MVP | MP-3/MP-5 según dependency decision |
| P7 — MP-3/MP-4/MP-5 | Planning, construction contextual y release en Pilot B | MP-6/7/8 |
| P8 — MP-8 | E2E fresh + auditoría independiente + decisión de convergencia | Cierre industrial / legacy gate revisado |

**Principio de precedencia:** cada ola exige el contrato operativo, autoridad Git, evidencia y DoD propios; esta tabla **no** los implementa ni los aprueba. **Posición recomendada para aprobación:** P6 ocurre después de MP-2 y antes de MP-3. El successor formal debe congelar ese orden y definir una alternativa explícita solo si la revisión de dependencias demuestra un riesgo mayor.

## 10. Matriz de cambios documentales necesarios

### 10.1 Paquete `DEVPL_GSDLC_13_GREENFIELD_PACKAGE` — successors propuestos

| Documento actual / familia | Cambio requerido | Naturaleza |
|---|---|---|
| `04_DEVPL_GSDLC_13_REAL_PRODUCT_ACCEPTANCE_REBASELINE_v2_1_0_APPROVED.md` | Reconocer cierre parcial de Pilot A y transferencia explícita de la aceptación E2E; actualizar objetivo, checkpoint graph y autoridad | **Obligatorio — programa** |
| `03_DEVPL_GREENFIELD_E2E_PRODUCT_ACCEPTANCE_CHARTER_v1_1_0_APPROVED.md` | Separar hipótesis original no completada y nueva evidencia válida; no describir Pilot A como producto terminado | **Obligatorio — charter** |
| `DEVPL_GSDLC_13_GREENFIELD_REAL_PRODUCT_ACCEPTANCE_ROADMAP_v1_1_0_APPROVED.md` | Reordenar D05→D06→SYNC-1; reubicar D07/D08/13-E sin fingir release de Pilot A | **Obligatorio — roadmap** |
| `DEVPL_GSDLC_13_REAL_PRODUCT_ACCEPTANCE_BACKLOG_v1_1_0_APPROVED.md` | Etiquetar RF004..008 como trabajo diferido por **programa**, no reescribir las stories FROZEN; documentar obligaciones E2E reasignadas | **Obligatorio — backlog** |
| `SPRINT_13D_v1_3_APPROVED_REBOUND.md` | Nuevo contrato de D05 partial/freeze, D06 resiliencia, D07/D08 no aplicables con old MVP, nuevos DoD sin false PASS | **Obligatorio — sprint successor** |
| `PROTOCOL_13D_v1_2_APPROVED_REBOUND.md` | Estados nuevos `PARTIAL_ACCEPTANCE`, `REBASELINED_STOP`, elegibilidad D06, reglas PASS/BLOCK y evidence | **Obligatorio — protocol** |
| `RUNBOOK_13D_v1_2_APPROVED_REBOUND.md` | Sustituir repetición automática de restantes stories por freeze; recovery delimitado; frontera exacta post-D06 | **Obligatorio — runbook** |
| `PROMPT_13D_v1_3_APPROVED_REBOUND.md` | Impedir emisión de RF004 RUN_04 o generación adicional en Pilot A; enlazar rebaseline al próximo gate, no a código | **Obligatorio — prompt de ejecución** |
| `DEVPL_GSDLC_13_GREENFIELD_PILOT_PROJECT_BRIEF_v1_1_0_APPROVED.md` | Preservar el business need original y marcar sus resultados no logrados; solo un successor de **estado/estrategia**, no cambiar retrospectivamente la necesidad | **Obligatorio — claridad de aceptación** |
| `DEVPL_GSDLC_13_ACCEPTANCE_EVIDENCE_PLAN_v1_1_0_APPROVED.md` | Matriz de evidencia observada vs transferida a Pilot B; no reclamar clean install de Pilot A | **Obligatorio — evidence** |
| Prompt/Sprint `13-E` y adjudicación Greenfield final | Replantear condiciones de cierre y legado; impedir E2E falso | **Obligatorio antes de nuevo E2E** |
| Índice/manifest del paquete, autoridad activa, ledger UX, catálogo de superficies | Registrar successors y freeze; conservar snapshots históricos | **Obligatorio al publicar paquete actualizado** |

**No modificar:** D01–D04 ya cerrados, adjudicaciones históricas, datos FROZEN de Vision/Scope/Requirements/Architecture, captures, commits y acuerdos previos. Se documenta supersession, nunca edición silenciosa retroactiva.

### 10.2 Paquete `DEVPL_MULTIPROVIDER_V2_1_APPROVED_PACKAGE` — successors propuestos

| Documento actual / familia | Cambio requerido | Naturaleza |
|---|---|---|
| `DEVPL_MULTIPROVIDER_IMPLEMENTATION_PROGRAM_v2_1_0_APPROVED.md` | Successor v2.2: actualizar estado real, estrategia de pilotos, DoD, secuencia de §14/§25/§26, riesgos y deps, sin reemplazar toda la arquitectura | **Obligatorio — programa** |
| `STOP_MULTIPROVIDER_AFTER_MP_1A_v1_0_0_APPROVED.md` | Successor explícito: preservar STOP hasta rebaseline D05 + D06 PASS + SYNC-1 PASS | **Obligatorio — stop authority** |
| `MP_V2_SYNCHRONIZATION_GATE_PROTOCOL_v1_0_0_APPROVED.md` | SYNC-1 con nueva elegibilidad, paridad de `GeneralStoryProvider`, registry y auditoría de fuente; tratamiento condicional SYNC-2 | **Obligatorio — gate** |
| `ADR-MP-V2-008-branch-worktree-sync-and-final-convergence_v1_0_0_APPROVED.md` | ADR successor que autorice cambiar **cuándo** se sincroniza, no la dirección ni la prohibición de rebase | **Obligatorio — ADR** |
| `MP_V2_PILOT_STRATEGY_AND_ACCEPTANCE_CHARTER_v1_0_0_APPROVED.md` | Pilot A evidence/reference parcial; Pilot B responsable de E2E real; Pilot C condicional | **Obligatorio — charter** |
| `MP_V2_MASTER_ROADMAP_v1_0_0_APPROVED.md` y `MP_V2_WAVE_DEPENDENCY_MATRIX_v1_0_0_APPROVED.md` | Nueva ruta explícita D05 freeze / D06 / SYNC-1 / Release qualification / posible SYNC-2 | **Obligatorio — roadmap/matrix** |
| `MP_V2_MASTER_BACKLOG_v1_0_0_APPROVED.md` y backlogs impactados `MP-1`, `MP-4`, `MP-5`, `MP-8` | Reasignar obligaciones E2E, evaluar generalización real, release core y convergencia; sin prometer nuevas funciones sin scope | **Obligatorio al replanificar olas** |
| `MP_1_PRODUCT_DEFINITION_SPRINT_PLAN_v1_0_0_APPROVED.md` + MP-1B en estado `PROPOSED` | Rebind de autoridad de entrada; no ejecutar bajo HEAD previo a SYNC-1 | **Obligatorio antes de MP-1B** |
| `MP_V2_SOURCE_REGISTRY_AND_DOCUMENTATION_REBIND_PLAN_v1_0_0_APPROVED.md` | Fijar lineage repo465→merge, state de ADR/contratos de GENERAL-113, tests legacy y docs vigentes | **Obligatorio — doc/authority** |
| `MP_V2_CHECKPOINT_ADJUDICATION_PROTOCOL_v1_0_0_APPROVED.md` | Incorporar adjudicación partial/rebaseline para hito externo sin confundirla con PASS de MP wave | **Recomendado si cruza categorías de estados** |
| Índices/manifests/README y registro oficial de ejecución/STOP | Actualizar referencias de sucesores, nunca sustituir silenciosamente artefactos APPROVED históricos | **Obligatorio — publicación** |

**Preservar sin modificar en esta decisión:** `ADR-MP-V2-001..007` (en especial ADR-007), contratos de candidatos, perfiles y políticas de seguridad/costos, salvo que un análisis posterior identifique una incompatibilidad concreta. **No usar este rebaseline para introducir modelos, nuevas APIs ni permisos.**

### 10.3 Nivel de repositorio y source registry

La aprobación del **documento propuesto** no implica commit automático de esos cambios. En una fase documental posterior deberán publicarse successors en el repositorio/branch correspondiente, con `source_registry`, `active_authority`, índices, tests de documentación, evidencia de aprobación y Git promotion. Antes de editar, comprobar el registro canónico de cada doc: algunos artefactos residen en paquetes de programa y otros también en Git. El programa aprobado debe identificar cuál copia es autoridad y cuál es archivo de referencia.

## 11. Gates formales de aprobación y transición

| Gate | Condición exigida | Si falla |
|---|---|---|
| G0 — Decisión Owner | Aprueba rebaseline y reconoce expresamente que Pilot A **no** completó MVP ni E2E | Mantener contratos actuales; no activar MP |
| G1 — Paquetes successor consistentes | Ambos programas/charters/sprints/STOP/ADRs/roadmap/matrix/registro reconciliados y aprobados | Ninguna ejecución bajo contrato nuevo |
| G2 — D05 freeze acreditado | 3 DONE, remaining 5 NOT DONE, autoridad Git/ZIP, deuda/UX, sin actividad mutable abierta | BLOCK de D06 revisado |
| G3 — D06 recuperación real | Seis escenarios no destructivos PASS, logs/evidencia y cero bypass/source loss | Corrective focal y revalidación D06 |
| G4 — SYNC-1 preflight | Ramas clean/pushed; authorities y lineage correctos; Reuse/Delta Map; MP sigue congelado | STOP permanece activo |
| G5 — SYNC-1 adjudicado | Merge determinístico→MP, conflictos resueltos, docs y tests PASS, receipt y new MP authority | MP-1B no autorizado |
| G6 — MP-1B habilitado | `G0..G5` con evidencia + policy/model budget aplicable | No generar con modelo local |
| G7 — Release core y E2E | Calificación release propia antes de depender de ella; Pilot B demuestra E2E fresco | No declarar cierre general del programa |

**Ningún `G0..G3` levanta el STOP; solamente `G5 PASS` habilita MP-1B.**

## 12. Riesgos críticos y mitigaciones

| Riesgo | Efecto | Mitigación de programa |
|---|---|---|
| Reducir D05 se interpreta como MVP terminado | False PASS, salida engañosa | Estado parcial explícito y deudas rastreables |
| D06 sobre proyecto incompleto oculta escenarios de release | Cobertura insuficiente | Declarar alcance exacto y separar release qualification |
| Sync arrastra dos routers/capas de modelos | Duplicación y drift | Matrix KEEP/ADAPT/DEPRECATE con ownership único |
| MP-1B accede a autoridad antigua | Incompatibilidad de runtime/contracts | STOP hasta SYNC-1 PASS, source rebind |
| Pilot B tarda en llegar a Construction | Beneficio funcional diferido | Criterios de valor por ola, evita crear templates por story |
| Modelo local genera código incorrecto | Riesgo funcional/seguridad | Proposal-only, schemas, pruebas independientes, Owner approval, no autonomía destructiva |
| Falta capacidad release sólida cuando se alcance MP-5 | Dependencia tardía | Gate release core previo y fixture aislado |
| Se ignora el historial de UX S1/S2 | Journey no escalable | Ledger preservado, S1 critical-path antes de acceptance |
| Se alteran artefactos FROZEN / commits | Pérdida de auditoría | Successors y receipts, no rebase/rewrite |
| Full Regression repetida fuera de cierre | Coste y fallos espurios | Focal/impact intermedio; Full solo en cierre autorizado del backlog/programa; una corrida lógica, reutilizar evidencia vigente |

## 13. Política de eficacia y medición de la nueva estrategia

Para no optimizar solamente el tiempo de programación, medir en Pilot B:

- **Generalización:** stories de **clases funcionales distintas**, sin codificar un template especial antes de cada una; distinguir deterministic support y generación LocalModel.
- **Calidad externa al generador:** pruebas de aceptación independientes del candidate; cobertura de edge cases/seguridad; tasa de revisión Owner y rechazo explicado.
- **Gobernanza:** propuestas nunca escriben source; required jobs y Quality siguen condicionando Git; rollback sin pérdida.
- **Costo total:** tiempo de desarrollo de plataforma, tiempo de Owner, latencia/modelo local, regeneraciones, fallos/reruns y mantenimiento de capacidades.
- **Recuperabilidad:** reanudación desde estados persistidos sin duplicación de mutaciones y sin depender del transcript del chat.
- **Transferibilidad:** más de un dominio o conjunto de requisitos, no únicamente renumeración de IDs del mismo inventario.
- **UX:** discoverability y estado terminal coherentes; sin botones post-apply/post-Quality ambiguos en rutas de aceptación.

La evidencia determinará el éxito; no se fijan umbrales numéricos arbitrarios sin baseline medido y decisión posterior.

## 14. Entregables documentales futuros derivados de esta aprobación

Esta propuesta **no los crea ni los aprueba**. Una fase de formalización posterior debe producir: (a) adjudicación de rebaseline con firma Owner; (b) sucesores de programa, charter, sprint, protocolo, STOP y ADR; (c) matriz de compatibilidad/reuse-delta de repo465 vs rama MP congelada; (d) Run Cards de D06 bajo su nuevo contrato, solo después de G1/G2; (e) estrategia SYNC-1 y adjudicación de merge; (f) rebaseline de MP-1B y futuro Pilot B; (g) política de release core/E2E separada.

Ordenar la redacción **por dependencia de autoridad**, no crear doc por cada variante redundante. Mantener documentos con nombres Windows razonablemente cortos, versiones únicas, referencias explícitas y un `authority index` único. Los tests, operadores Python, patches, comandos PowerShell y pasos UI **quedan fuera de alcance de este artefacto**.

## 15. Decisiones solicitadas expresamente al Owner

- **D-01:** ¿Aprobar congelar Pilot A después de tres stories, reconociendo que el MVP Greenfield y el E2E original no han sido completados?
- **D-02:** ¿Aprobar D06 delimitado a recuperación del circuito de construcción ya demostrado, sin pretender validar funcionalidad aún ausente?
- **D-03:** ¿Aprobar sustituir el STOP por un successor condicionado a `D05/PARTIAL_ACCEPTANCE + D06/PASS + SYNC-1/PASS`, sin levantarlo anticipadamente?
- **D-04:** ¿Aprobar transferir la demostración integral de MVP, release y experiencia de producto al Pilot B, conservando una calificación independiente de release core previa a su consumo?
- **D-05:** ¿Aprobar que `GeneralStoryProvider` no se amplíe más en la rama determinística y se someta a auditoría de convergencia en SYNC-1?

**Propuesta de resolución:** `APPROVE_WITH_DOCUMENTARY_SUCCESSORS_REQUIRED`, sin autorización de source mutation ni MP-1B antes de G1..G5. Si el Owner rechaza cualquier decisión, se reevalúa explícitamente el dependency graph; ninguna decisión se asume por silencio.

## 16. Fuentes literalmente consultadas y trazabilidad

Paquetes íntegros consultados desde los ZIP presentes en esta conversación:

**Greenfield** (`DEVPL_GSDLC_13_GREENFIELD_PACKAGE_vig.zip`):

- `DEVPL_GSDLC_13/03_DEVPL_GREENFIELD_E2E_PRODUCT_ACCEPTANCE_CHARTER_v1_1_0_APPROVED.md` — propósito E2E y PASS originales.
- `DEVPL_GSDLC_13/04_DEVPL_GSDLC_13_REAL_PRODUCT_ACCEPTANCE_REBASELINE_v2_1_0_APPROVED.md` — fases D/E.
- `DEVPL_GSDLC_13/DEVPL_GSDLC_13_GREENFIELD_PILOT_PROJECT_BRIEF_v1_1_0_APPROVED.md` — flujo mínimo inventario + venta.
- `DEVPL_GSDLC_13/DEVPL_GSDLC_13_REAL_PRODUCT_ACCEPTANCE_BACKLOG_v1_1_0_APPROVED.md` y `DEVPL_GSDLC_13_GREENFIELD_REAL_PRODUCT_ACCEPTANCE_ROADMAP_v1_1_0_APPROVED.md` — secuencia.
- `DEVPL_GSDLC_13/DEVPL_GSDLC_13-D-Artefactos_ajustados/ajuste-post-MP-1A-04/{SPRINT_13D_v1_3_APPROVED_REBOUND.md,PROTOCOL_13D_v1_2_APPROVED_REBOUND.md,RUNBOOK_13D_v1_2_APPROVED_REBOUND.md,PROMPT_13D_v1_3_APPROVED_REBOUND.md,DECISION_D05_D06_REBIND.md}` — reglas y gate actualmente aprobado.

**Multiprovider** (`DEVPL_MULTIPROVIDER_V2_1_APPROVED_PACKAGE_vig.zip`):

- `00_program/DEVPL_MULTIPROVIDER_IMPLEMENTATION_PROGRAM_v2_1_0_APPROVED.md`, especialmente §§0, 1, 14, 15, 22, 24–28.
- `01_architecture_governance/{ADR-MP-V2-007...,ADR-MP-V2-008...,MP_V2_SYNCHRONIZATION_GATE_PROTOCOL...,MP_V2_GIT_BRANCH_WORKTREE_GOVERNANCE...,MP_V2_PILOT_STRATEGY_AND_ACCEPTANCE_CHARTER...,MP_V2_SOURCE_REGISTRY_AND_DOCUMENTATION_REBIND_PLAN...}`.
- `03_backlog_waves/{MP_V2_MASTER_ROADMAP...,MP_V2_WAVE_DEPENDENCY_MATRIX...,MP_V2_MASTER_BACKLOG...}`.
- `04_ Execution_packages-sprints_prompts/MP_1_Product_definition/STOP_MULTIPROVIDER_AFTER_MP_1A_v1_0_0_APPROVED.md`.

**Estado acumulado**: `repo_465_13D05_GENERAL_CLEAN.zip` y su `.sha256`; `13D05_RF003_CLOSE_115/ADJUDICACION_RF003_115.md`; `RUN_PACKET_RF003_115.md`; salida de GENERAL-113 y resultados de la validación de RF-003. Son evidencia posterior a los SHAs históricos que aún muestran los paquetes; esos metadatos deben actualizarse **mediante successor**, no mediante edición retrospectiva.

---

### Declaración final

**La decisión óptima es detener el crecimiento del piloto determinístico *como fábrica de funcionalidades específicas*, no detener su aportación a la confiabilidad industrial.** Preservar sus tres ciclos, demostrar recovery y converger formalmente permite dedicar el desarrollo posterior a generación contextual generalizable, seguridad, calidad y operación: lo que distingue a DevPilot como plataforma profesional de IA asistiendo al SDLC.

**Estado histórico de la propuesta original:** pendiente de autorización. **Estado vigente de este successor:** `APPROVED / G0 PASS`; G1–G7 permanecen por acreditar. Ningún gate operativo se ejecuta por el mero cambio de estado.
