---
doc_id: DEVPL-MP-SUCCESSOR-132-02_ROADMAP_INDUSTRIAL_132
title: "Roadmap industrial R0–R10 — objetivos, gates y dependencias"
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

# Roadmap industrial R0–R10 — objetivos, gates y dependencias

## 1. Principio de ejecución por valor y no por cantidad de archivos

Cada ola habilita una capacidad que se puede **usar y comprobar** en un flujo real. La aplicación Pilot B es continua; no nace otro workspace por ola. R1 no debe convertir PESP, Settings y documentación en una plataforma teórica sin valor al usuario: se implementan primero **contratos mínimos y una vertical**, y se generalizan según demanden los hitos siguientes.

| Ola | Resultado objetivo verificable | Prioridades arquitectónicas v1.1 | Gate y evidencia |
|---|---|---|---|
| **R0 Autoridad/entorno** | Aprobación programática, G5 administrativo separado, Git worktree seguro, auditoría de Settings y métricas iniciales | Gate de alternativa B antes del primer source change; Source Registry successor sólo autorizado | M0: Owner + HEAD/upstream, tracked/untracked/ignored, backups y rollback, STOP scope |
| **R1 Contratos y primera integración** | Kernel Story→Envelope, eval reusable y primera vertical de Settings/PESP/Artifacts | GenerationRoutePolicy D/L/E por tarea; PESP+Coverage; Markdown/publication; FROZEN successor; roles efectivos/configuración; estado UI confiable | M1: pruebas D/Mock, prueba de profile+gate, deny, reentrada, publicación y reversibilidad |
| **R2 Product Definition / Pilot B B0-B1** | Owner crea proyecto neutral y obtiene Vision/Scope/Requirements contextualizados por L real y D | Modelo local competente, preferido para semántica; artefactos humanos; perfil profesional contextual; setup/readiness | M2: Ollama o LM Studio real, provenance/candidate válido, tres FROZEN, UI sin terminal |
| **R3 Technical Design / B2** | Architecture, ADRs, Security, Test Strategy, Traceability y condicionales datos/API/UX; Technology Profile y scaffold posterior | Standards Coverage; RAG técnico, versionado, rutas docs estables, código según stack | M3: consistencia RF→ADR→tests, elección Owner, scaffold/aprovisionamiento aprobado, pruebas negativas |
| **R4 Planning / B3** | Roadmap, backlogs, sprints y stories READY; MIASI condicional | Markdown durable, dependencies, capacidad, successor y cambios de planificación | M4: decisiones aprobadas, coverage Planning, historias trazables, sin falsas estimaciones |
| **R5 Construction / B4** | Story arbitraria → código real → tests/Quality/Git gobernados | L preferente evaluado, ContextPack, adapter único, SourceChangePlan, UI status y ledger UX | M5: al menos dos dominios/pruebas de independencia; no duplicación ni manual project writes |
| **R6 Release / B5** | Instalación, startup, release, SBOM, rollback, backup/restore y portabilidad | Application Deliverable Manifest separado de Engineering Evidence Manifest; runbooks | M6: release iniciado y revertido en entorno real, secrets scan, smoke/restore |
| **R7 Agents / B6** | Agentes de revisión y asesores Pilot B con permisos limitados y handoffs | MIASI operativo, evals, autonomía acotada, tool allowlist, kill, bounded loops | M7: trazas, humano y pruebas adversariales; ninguna mutación directa |
| **R8 External / Pilot C** | Provider externo opcional con egress autorizado, privacy y CostGuard | ADR trust boundary aprobada antes de HTTP; datasets sintéticos, costos máximos | M8: aceptación real externa o `NOT_ENABLED`, nunca falso PASS |
| **R9 Productización/Resiliencia** | UX consolidada, launcher, fault injection real, rendimiento y operación de DevPilot | Consolidar y medir mejoras iniciadas desde R0–R6, no diferir Settings/FROZEN básicos | M9: restart/recovery/rollback y browser E2E instrumentados |
| **R10 Aceptación independiente** | Pilot B B0–B7, segundo dominio, seguridad, operación y madurez adjudicadas | Evaluación independiente, regresión de cierre aprobada, S0/S1=0 del critical path | M10: Owner aceptación por alcance separado L/Agent/E |

## 2. Dependencias y concurrencia

Camino principal R0→R1→R2→R3→R4→R5→R6→R10. Las foundations de R7 pueden iniciar read-only sin esperar toda R6; ningún tool write por agente precede al guard de R5. R8 se habilita sólo tras security/cost gates propios. R9 se distribuye desde el inicio y cierra al final; no es vertedero de todos los defectos.

**Crosscutting de prioridad temprana:** PESP/Artifact Coverage, documentación durable, successor FROZEN, `GenerationRoutePolicy`, Settings con autoridad, estado/feedback UX y auditoría focal, todos definidos en R1 y ampliados por vertical. Las prácticas de continuidad y cambio afectan todas las olas.

## 3. Cadena de Pilot B

B0 Project Entry neutral → B1 Product Definition → B2 Technical Design → B3 Planning → B4 Construction → B5 Release/Operations → B6 advisory agents → B7 evaluación E2E. Se mantiene el escenario de microempresa de bienestar/cuidado personal, inventario/ventas, catálogo, stock y propuestas comerciales **como problema inicial**, no como requerimientos/código preescritos para facilitar las pruebas. Owner decide alcance y stack durante el workflow real.

## 4. Gates transversales

Cada incremento: A0 authority, A1 audit/Reuse/Delta Map, A2 ADR/contrato/approval, A3 dry-run/preimage, A4 pruebas semánticas/técnicas/seguridad/UI pertinentes, A5 Git 3-estados/snapshot, A6 Owner acceptance. Cada fase revisa Artifact Coverage y ledger por IDs; las violaciones funcionales S0/S1 bloquean, preferencias S2/S3 no fuerzan cambios fuera de scope.

## 5. Programación futura

Roadmap y backlog son **OWNER_APPROVED_PROGRAM para planeación, no órdenes de ejecución**. Al iniciar una ola se consultará el baseline vivo y la auditoría podrá reorganizar dependencias. Se emitirán posteriormente sprints/prompts autorizables uno a uno: **no forman parte de la presente entrega**.


---

## Addendum operacional M0→R1 — sucesor de planificación (14-10-2026)

- **Asunto:** Roadmap.
- **Actualización concreta:** Marcar M0 cumplido con findings; M1 desagregado en 15 incrementos focales; no adelantar R2 ni mediciones R0-09 antes de R2.
- **Evidencia vinculada:** COR-143 (migración B), R00-03/COR-145 (publicación 57 documentos), R00-04/COR-147 (auditoría Settings), COR-150 (paridad 1752), COR-151 (cierre Owner M0).
- **HEAD de autoridad técnica:** `66ab2e6227072c951b5bd2ac9160e8515b1b9fc0`. Las referencias a `8db5b44694abcced3231183e05731e732f5b8f24` y los indicadores `STOP ACTIVE` en secciones históricas no se reescriben como si fueran estados presentes.
- **Autoridad:** copia sucesora propuesta para adopción documental posterior; no constituye un commit, promoción Git, autorización de R1, de MP-1B, de modelo/API externa ni una aceptación funcional de Settings.
- **Transferencias vigentes:** `MP132-R0-09` → R2 para mediciones reales; UX Settings pendiente de reproducción y validación; egress externo DENY; no duplicar ownership entre olas.


---

## Adenda sucesora post-M1 — 15-10-2026 (no retroactiva)

- **Baseline Git publicado:** `cd0bce59ec2bf4a7ae7e50a555c1c8a1bd85facc` (`evolution/multiprovider-v2`), sucesor de `feaac2723c1f8a467f5cdb7d456e4e7679dd0f82` por R01-15/COR-171. - **R01:** 15/15 incrementos aceptados; 16 IDs propietarios cubiertos; cierre M1 `PASS_WITH_FINDINGS` con 108 tests focales y 8 del operador PASS en Windows. - **Evidencia:** `RESULT_171.json`, `M1_REPORT_171.json`, `R01_15_EVIDENCE.zip`, `repo_R01_15_CLEAN.zip` y SHA256. - **Autoridad:** R02 se desagrega sólo para planificación. Ningún `SPRINT_EXECUTION_APPROVED`, ningún push, bootstrap Pilot B, inferencia local, external egress o MP-1B queda autorizado por esta adenda. - **Limitaciones:** `model_local_real=NOT_TESTED`, `semantic_llm_judge=NOT_TESTED`, `rag_groundedness_real=NOT_TESTED`, `external_real=DENIED`; no confundir pruebas de servicio con un recorrido completo Product Definition UI.
- **M0** y **M1** cerrados con findings acotados. **M2** pendiente hasta Pilot B B0–B1 real, modelo local competente efectivamente invocado, Vision/Scope/Requirements FROZEN y evidencia UI/portabilidad.
- R02 tiene **10 borradores de sprint y 10 prompts** en `7_ Execution_packages-sprints_prompts/BACKLOG_R02`; cada uno requiere autoridad Owner separada. La regla histórica «se emitirán posteriormente» se satisface ahora a nivel documental, no operativo.

## Adenda Owner UI-first 179 — UI_FIRST_PILOT_B_V1

| Tramo | Criterio UI-first acumulativo |
|---|---|
| R2/M2, B0–B1 | El Owner define ID, nombre, ruta final, necesidad y aprobaciones únicamente por Project Entry; la consola no anticipa identidad. Recovery B0 desde registro persistido. |
| R3/M3, B2 | ADR, selección tecnológica, pre-code, revisión y FROZEN por UI; sin documentos manuales para suplir acciones. |
| R4/M4, B3 | Roadmap, backlog, sprint, stories y sucesores mediante workflows UI. |
| R5/M5, B4 | Draft/code, Quality, jobs y Git por herramientas tipadas iniciadas en UI; sin terminal humana. |
| R6/M6, B5 | Packaging, release, deploy, smoke/health y rollback iniciados en UI; aplicación final autónoma. |
| R7/M7 y R10/M10, B6–B7 | Agentes limitados y auditoría E2E del mismo workspace; ningún escape no autorizado. |

R9 (instalador de DevPilot) no condiciona la ejecución UI-first del piloto durante R2–R6: hasta entonces la consola puede levantar la plataforma, nunca ejecutar el proyecto por fuera.

---

## Enmienda programática post-R02-06 · 187

**Reordenación sin añadir olas:** R2 entrega Product Definition profesional, un L inicial por etapa con Markdown Owner y FROZEN. R3 certifica TechnologyProfile, ADR, datos/API/seguridad y Technical Scaffold reproducible con health/smoke. R4 incorpora Roadmap por outcomes y `Release/Increment Plan` con dependencias, evidencia de aceptación, sprint commitment y backlog evolutivo. R5 construye slices funcionales integrados con pruebas de aceptación por incremento y Git gobernado. R6 produce release candidate/release autónomo con package/restore/rollback por UI. R7 incorpora MIASI solo a componentes inteligentes, R8 habilita E bajo autorización separada, R9 endurece UX/recovery y R10 valida independencia, segundo dominio y cumplimiento por madurez.

**Hitos comprobables:** M2=3 `.md` profesionales FROZEN por UI con L real; M3=decisión tecnológica aprobada+scaffold reproducible; M4=plan de al menos un incremento con outcomes/dependencias/AC y sprint comprometido; M5=stories+tests+integración+incremento aceptado; M6=entregable instalable, restore y rollback. No confundir package de evidencia con aplicación liberable ni evaluación de modelo con autoría aceptada. Las definiciones detalladas están en las ADR 013–015 y el nuevo contrato de incrementos.

---

## Adenda de planificación A188 — implantación incremental

**Enmienda 188 Owner-approved (2026-10-22)**. Autoridad `MP132-OWNER-DECISION-188`; contrato `2_contratos/ARTIFACT_AUTHORING_QUALITY_CONTRACT_188.md` y ADR-MP132-016. Complementa 187/ADR-013; se aplica prospectivamente por olas, sin alterar recibos históricos, ni autorizar ejecución de un sprint o proveedor E.

**Distribución por olas:** R02-08 demuestra Product Definition/contexto/PESP y un segundo dominio; R03 especializa Architecture, R04 Planning, R05 Construction, R06 Release/Operations, R07 agentes bajo límites, R08 APIs externas opt-in, R09 UX/resiliencia y R10 aceptación integrada. Las etapas sucesoras no se adelantan a R02-08. Evaluación por tarea, calidad y costo, con control de impacto, sin reabrir FROZEN por apariencia.

---

## Adenda de cierre R02 → planificación R03 — 2026-10-22

M2 Product Definition cerrado con reservas, HEAD `1f15fa5b770db37c684e870a49572dcb569bd3a4`; M3 sigue `NOT_TESTED`. R03 queda desagregado en once micro-sprints consecutivos (`R03_01`–`R03_11`), sin autoridad de ejecución hasta aprobación Owner **individual**. Su gate M3 requiere Technical Baseline Architecture/Security/Test Strategy/Traceability y ADR materiales FROZEN, TechnologyProfile aprobado, scaffold ejecutado y smoke/startup reproducibles iniciados por UI normal. R03_01 corrige drift documental activo antes de cambios funcionales. No declarar nivel `LOCAL_FIRST_PROFESSIONAL` en M3.
