---
doc_id: DEVPL-MP-SUCCESSOR-132-00_PILOT_B_CHARTER_132
title: "Pilot B — Charter de aplicación continua, profesional y E2E"
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
current_execution_baseline: "cd0bce59ec2bf4a7ae7e50a555c1c8a1bd85facc"
r01_gate: "CLOSED_PASS_WITH_FINDINGS"
r02_execution_authority: false
planning_amendment_id: "MP132-AMENDMENT-POST-R02-06-187"
planning_amendment_date: "2026-10-17"
planning_amendment_baseline: "b666c5641c1b8231c5b609216f64490a72ff1763"
planning_amendment_execution_authority: false
---

# Pilot B — Charter de aplicación continua, profesional y E2E

## 1. Propósito

Pilot B es una aplicación real creada desde cero por DevPilot desde una necesidad de una microempresa de productos de bienestar/cuidado personal con catálogo, inventario, ventas, alertas y recomendaciones. **No** se preescriben los requisitos definitivos, el stack ni RF de Pilot A. Las decisiones nacen en las pantallas normales de DevPilot y sus actas Owner. Su resultado comprueba generalidad del SDLC y asistencias D/L/Agent.

## 2. Principios no negociables

- **Un solo proyecto/workspace B0–B7**, con documentación `docs/` portable, release real, operaciones y evolución. No reiniciar workspace entre olas para maquillar resultado.
- `operator_project_writes=0`, `normal_user_terminal_escapes=0`, `journey_actions_via_devpilot_ui=true`. Scripts del operador sólo arrancan/inspeccionan/fijan evidencia/servidores DevPilot, nunca fabrican artefactos de negocio o source del piloto.
- Project Entry registra negocio/constraints y proyecto neutral; stack se decide tras Requirements+Architecture. Modelo local sólo opt-in e instalado, evaluado y visible; external fuera del Pilot B normal.
- MIPSoftware siempre; MIASI sólo cuando B6 incorpore componentes IA dentro de la aplicación; no exigir Tool Card al inventario convencional por usar IA para programarlo.
- Cada transición consulta PESP, Coverage Gate y apropiados quality gates. Owner revisa alternativas, scope, consecuencias y aprobación sensible; LLM no escoge por él.

## 3. Milestones y entregables

| B | Tarea Owner en UI | Artefactos portables y evidencia |
|---|---|---|
| **B0** | Crear proyecto, describir necesidad, restricciones, roots, modelo deseado | `idea_intake`, contexto, PESP provisional, permisos de root y Git inicial |
| **B1** | Vision/Scope/Requirements; comparar propuestas D/L | Markdown FROZEN, lineage, schema, scores semánticos e Owner review |
| **B2** | Arquitectura, ADRs, datos/API/UX según aplicabilidad, Security, Test Strategy, Technology | docs Markdown vigentes, Coverage PASS, scaffold posterior con permisos y manifests |
| **B3** | Roadmap/Backlog/Sprints/Stories y capacidad | Documentos durables bajo docs/08_planning, story READY traceable |
| **B4** | Solicitar historia no trivial → candidate → review/diff/approve/apply/tests/Quality/Git | Código compilable en stack elegido, commits exactos, E2E funcional, negativas de drift/double apply |
| **B5** | Release, instalación/startup/health, upgrade/rollback | Deploy real, manifests separados, SBOM/secret scan, guía de operación y evidencia de restauración |
| **B6** | Activar un advisory agent con tool limits | MIASI Cards, evals, recomendaciones grounded; ningún stock/price/publicación sin permiso específico |
| **B7** | Recorrer viaje completo y cambios de evolución | Auditoría independiente E2E y una change request FROZEN→successor seguida de release nuevo |

## 4. Aceptación profesional real

Un test `pytest PASS` o un build UI no certifica etapa completa. Es obligatorio un browser walkthrough que muestre estados correctos, aprobación, next action, ausencia de terminal Git manual, persistencia entre sesiones y artefactos portables. Release se instala/arranca **fuera de DevPilot** y pasa rollback. Debe incluir al menos una evolución posterior al primer diseño para demostrar mantenibilidad.

## 5. Fallos y controles

Timeout local model, salida mal formada, escenario sin capacidad, reinicio de API/browser, expiración de sesión, drift file, locks multi-proceso, conflictos Git, error de dependencies, fail de release y rollback. Estos fallos no pueden generar source loss ni autoautorizar acciones. R9 culmina resiliencia real, pero las pruebas negativas pertinentes son obligatorias en cada gate anterior.

## 6. Segunda prueba de generalidad

El programa requiere **otro dominio independiente** antes de R10; puede ser biblioteca, reservas no sensibles o documentación, elegido por el Owner tras contexto. No permitir un generador específico de inventario disfrazado de motor general. El mismo kernel `GenerationRequest/Envelope` y governance deben funcionar en ambas aplicaciones.

## 7. Límites

Sin APIs externas pagas por defecto. Pilot C las evalúa aparte; ausencia de E no invalida `LOCAL_FIRST_PROFESSIONAL`, pero impide `EXTERNAL_ENABLED`. Sin certificaciones regulatorias ni SLA enterprise inventados. Findings UX heredados revalidados contextualmente y ninguna reparación sin auditoría focal.


---

## Adenda sucesora post-M1 — 15-10-2026 (no retroactiva)

- **Baseline Git publicado:** `cd0bce59ec2bf4a7ae7e50a555c1c8a1bd85facc` (`evolution/multiprovider-v2`), sucesor de `feaac2723c1f8a467f5cdb7d456e4e7679dd0f82` por R01-15/COR-171. - **R01:** 15/15 incrementos aceptados; 16 IDs propietarios cubiertos; cierre M1 `PASS_WITH_FINDINGS` con 108 tests focales y 8 del operador PASS en Windows. - **Evidencia:** `RESULT_171.json`, `M1_REPORT_171.json`, `R01_15_EVIDENCE.zip`, `repo_R01_15_CLEAN.zip` y SHA256. - **Autoridad:** R02 se desagrega sólo para planificación. Ningún `SPRINT_EXECUTION_APPROVED`, ningún push, bootstrap Pilot B, inferencia local, external egress o MP-1B queda autorizado por esta adenda. - **Limitaciones:** `model_local_real=NOT_TESTED`, `semantic_llm_judge=NOT_TESTED`, `rag_groundedness_real=NOT_TESTED`, `external_real=DENIED`; no confundir pruebas de servicio con un recorrido completo Product Definition UI.
- Pilot B sigue NO iniciado. B0 y B1 corresponden a R02, pero **no** se genera data de negocio ni se escribe source por operador. Reutilizar un solo workspace B0-B7; el Owner selecciona identidad/ruta y necesidad real desde la UI.
- No presentar `inventory-sales-local-greenfield` histórico como nuevo Pilot B; sirve para tests de regresión, no como evidencia B0 recién creado.

## Adenda Owner UI-first 179 — UI_FIRST_PILOT_B_V1

La regla vinculante es `UI_FIRST_PILOT_B_V1`: toda acción del proyecto Pilot B B0–B7 debe originarse en la UI normal de DevPilot; el backend puede ejecutar herramientas gobernadas (Git, Python, jobs, packaging, deploy, rollback), pero el operador humano no sustituye ningún workflow del piloto con CLI, editores externos, DevTools o scripts. La consola se limita al arranque/parada de API/UI hasta disponer de instalador, preconfiguración operacional de la instalación, auditoría y correctivos sobre **la plataforma**. `operator_project_writes=0`, `normal_user_terminal_escapes=0`, `journey_actions_via_devpilot_ui=true`.

**Resolución de la ambigüedad Release:** donde el charter histórico diga que el release “se instala/arranca fuera de DevPilot”, léase que **el artefacto desplegado funciona autónomamente**, no que el Owner lo despliegue con terminal. Preparación, release plan, aprobación, ejecución, verificación y rollback corresponden a acciones iniciadas dentro de DevPilot. Si falta un workflow UI, reportar `PARTIAL/BLOCK`, no usar CLI de compensación.

**B0:** Parent autorizado de instalación (ej. `D:\Projects\DevPilot_Workspaces`) es política operacional de PathGuard, independiente del target final, que se elige solo en Project Entry. El operador compara snapshots de registro antes/después sin teclear ID/nombre/root. El registro persiste la identidad y la UI verifica recuperación después de reiniciar API.

**Matriz de trazabilidad B0–B7:** B0 Project Entry/bootstrap; B1 Product Definition; B2 arquitectura; B3 Planning; B4 Code/tests/Git; B5 Release/Operations; B6 agentes; B7 evolución/segundo release. En cada uno exigir recibos iniciados en UI, actor/authority/targets, 0 escrituras del operador; no basta una simulación de Python.

---

## Enmienda programática post-R02-06 · 187

**Pilot B B1→B5, continuidad prospectiva:** B1 exige Product Vision/Scope/Requirements semánticos Markdown `.md` FROZEN mediante una ruta L real elegible; no se requiere comparar D/L, y no se congela un simple resumen de B0. B2 decide TechnologyProfile/ADRs según drivers y crea scaffold **aprobado y reproducible** (smoke/startup). B3 publica Roadmap por outcomes, `Release/Increment Plan` con dependencias/aceptación, backlog y primer sprint READY. B4 entrega por lo menos un slice probado en integración (no solo story DONE) y su commit Git gobernado. B5 empaqueta y demuestra arranque autónomo, health, documentación y recuperación/rollback según riesgo. B6 valida MIASI de los agentes advisory, B7 aceptación total y segundo dominio. Los valores de producto, capacidades y stacks definitivos solo se confirman por los documentos Owner FROZEN; el ejemplo de partición I0..I5 no concede scope implícito.

---

## Lecciones de aceptación Pilot B y generalización A188

Pilot B acreditó FROZEN de Vision, Scope y Requirements, pero demandó corrección Owner sustantiva y demostró que schema válido puede coexistir con contradicciones de negocio. La evaluación local debe registrar esas carencias sin prometer autoría autónoma profesional. A188 exige un segundo dominio independiente; aprobar B0–B1 no certifica contratos universales. No modificar el workspace ni el historial FROZEN por esta enmienda programática.
