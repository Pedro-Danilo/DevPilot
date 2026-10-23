---
doc_id: DEVPL-MP-SUCCESSOR-132-04_DECISIONES_PENDIENTES_Y_PREPARACION_132
title: "Matriz de preparación: qué falta antes de autorizar implementaciones"
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
---

# Matriz de preparación: qué falta antes de autorizar implementaciones

## 1. Estado verificable por documento de este paquete

| Grupo | Estado que puede aprobarse ahora | Completar/actualizar antes de implementar |
|---|---|---|
| Programa maestro y roadmap | `OWNER_APPROVED_PROGRAM` por decisión 133 | **Pendiente:** publicación gobernada en Source Registry vivo, verificando SHA y HEAD |
| 11 backlogs por ola | `OWNER_APPROVED_PROGRAM` para prioridades y AC iniciales; ítems individuales no iniciados | **Cada ítem**: audit-first live, Reuse/Delta Map, scope de sprint, tests, límites de costo y aprobación |
| ADR-001..008 | `OWNER_ACCEPTED` tras auditoría 133 de código y ADRs históricos | Antes del primer cambio: Reuse/Delta Map del HEAD vivo, schemas y pruebas; ADR-008 requiere gate Windows B |
| ADR-009 Agent/Tool Boundary | `OWNER_ACCEPTED` arquitectura de seguridad, activación de tools condicionada | Threat model, matriz exacta de tools y workspace permissions antes de R7 writes |
| ADR-010 External Trust | `OWNER_ACCEPTED_ARCHITECTURE / EXTERNAL_ACTIVATION_DEFERRED` | Egress/PII/legal/costo, secret refs, provider exacto, decisión Owner antes de cualquier llamada |
| ADR-011 UI State | `OWNER_ACCEPTED` decisión UI transversal | Mapa de superficies, source audit, pruebas browser/state y contratos UI antes de cambiar source |
| PESP/Catalog/Coverage | Especificación conceptual versionable | Extraer estándares vigentes de `.md`, profiles actuales, schemas reales y mínima vertical R1; confirmar aplicabilidad por proyecto |
| Publicación/FROZEN/Impact | Semántica de autoridad y estados | Resolver interacción real stores/Markdown/Source Registry/Git; compatibilidad con documentos FROZEN; migrations y tests |
| GenerationRoute/ModelCapability | Reglas D/L/E/fallback y capacidades | Auditar interfaces existentes, hardware real y dataset de evaluación; API external continúa denegada |
| Configuration Matrix | Dominios/scope/precedencia propuestos | Auditoría SettingsView, settings_service, endpoint RBAC/policy, storage; plan de migración; negatives |
| Project Layout | Contrato logical-path e implementación tardía | Resolver TechnologyCatalog, root policy, portabilidad por stack; no elegir stack durante Intake |
| Pilot B Charter | Negocio y gates verificables | Intake humano dentro de UI, dataset sintético, entorno aceptado, Owner aprueba límites y éxito |
| Matriz riesgos/deuda | Registro revisado por fuente | Refresh sobre HEAD que se modifique; ledger UX v1.32 es histórico y necesitará nueva adjudicación por reproducción |
| Git estrategia B | `OWNER_ACCEPTED_CONDITIONAL_PREFLIGHT` | Tracked/untracked/ignored, procesos, upstream, backups, rollback y pruebas Windows; sin traslado actual |

## 2. Orden mínimo de autorización futuro

`Aprobación 132 y G5 ratificado (actas Owner-133)` → `publicación gobernada de supersession/Source Registry sobre HEAD vivo` → `auditar y decidir worktree R0` → `ratificar compatibilidad focal de ADRs ya OWNER_ACCEPTED y completar contratos aplicables al primer delta` → `audit-first real/Reuse-Delta` → `proyectar y aprobar sprint + prompt (futuro, no aquí)` → `dry-run` → `execute/canary` → `evidencia Windows` → `Owner adjudication`.

Ningún componente que trate datos personales, coste o acciones mutativas se activa mediante cambio de UI/config sin threat model y policy aprobados. Si el audit-first revela `NO-OP` no crear bundle de implementación.

## 3. Criterios de GO / NO-GO programáticos

- **GO para aprobación conceptual:** fuentes verificadas, 66 ítems preservados, supersession explícita, contratos coherentes, pendientes y riesgos transparentes.
- **NO-GO para mutaciones automáticas hoy:** faltan orden/alcance de incremento, auditoría focal sobre HEAD vivo, preflight/migración Git si se elige B, pruebas y aprobación de promoción. **ADRs ya OWNER_ACCEPTED**; STOP global levantado. Costo/tool/egress sigue requiriendo decisión separada.
- **NO-GO para declarar industrialidad:** no existen aún Pilot B E2E, L real aceptado transversalmente, release probado ni aceptación independiente.


---

## Addendum operacional M0→R1 — sucesor de planificación (14-10-2026)

- **Asunto:** Decisiones pendientes.
- **Actualización concreta:** Sustituir pendientes R0 ya satisfechos por recibos; R1 exige autorización por incremento; R0-09 diferido R2; MP-1B NOT_AUTHORIZED.
- **Evidencia vinculada:** COR-143 (migración B), R00-03/COR-145 (publicación 57 documentos), R00-04/COR-147 (auditoría Settings), COR-150 (paridad 1752), COR-151 (cierre Owner M0).
- **HEAD de autoridad técnica:** `66ab2e6227072c951b5bd2ac9160e8515b1b9fc0`. Las referencias a `8db5b44694abcced3231183e05731e732f5b8f24` y los indicadores `STOP ACTIVE` en secciones históricas no se reescriben como si fueran estados presentes.
- **Autoridad:** copia sucesora propuesta para adopción documental posterior; no constituye un commit, promoción Git, autorización de R1, de MP-1B, de modelo/API externa ni una aceptación funcional de Settings.
- **Transferencias vigentes:** `MP132-R0-09` → R2 para mediciones reales; UX Settings pendiente de reproducción y validación; egress externo DENY; no duplicar ownership entre olas.


---

## Adenda sucesora post-M1 — 15-10-2026 (no retroactiva)

- **Baseline Git publicado:** `cd0bce59ec2bf4a7ae7e50a555c1c8a1bd85facc` (`evolution/multiprovider-v2`), sucesor de `feaac2723c1f8a467f5cdb7d456e4e7679dd0f82` por R01-15/COR-171. - **R01:** 15/15 incrementos aceptados; 16 IDs propietarios cubiertos; cierre M1 `PASS_WITH_FINDINGS` con 108 tests focales y 8 del operador PASS en Windows. - **Evidencia:** `RESULT_171.json`, `M1_REPORT_171.json`, `R01_15_EVIDENCE.zip`, `repo_R01_15_CLEAN.zip` y SHA256. - **Autoridad:** R02 se desagrega sólo para planificación. Ningún `SPRINT_EXECUTION_APPROVED`, ningún push, bootstrap Pilot B, inferencia local, external egress o MP-1B queda autorizado por esta adenda. - **Limitaciones:** `model_local_real=NOT_TESTED`, `semantic_llm_judge=NOT_TESTED`, `rag_groundedness_real=NOT_TESTED`, `external_real=DENIED`; no confundir pruebas de servicio con un recorrido completo Product Definition UI.
- Resueltos: authority Git de R00, kernel/Settings/profiles primera vertical R01, gate M1. Pendientes: disponibilidad/versión/hardware real de Ollama/LM Studio, dataset y modelo aprobado, scope de Pilot B, condiciones de inicio B0, Owner readiness de cada proveedor local y alcance por sprint.
- La primera mutación R02 debe reconciliar **todo drift documental activo identificado** mediante un ledger trazable, sin reescribir snapshots históricos ni reintroducir pruebas con micro-sprints hardcoded. Un hallazgo no material debe ser `OBSERVE_ONLY`, no cadena de correcciones innecesarias.

---

## Adenda Owner 188 — decisiones resueltas y todavía pendientes

**Enmienda 188 Owner-approved (2026-10-22)**. Autoridad `MP132-OWNER-DECISION-188`; contrato `2_contratos/ARTIFACT_AUTHORING_QUALITY_CONTRACT_188.md` y ADR-MP132-016. Complementa 187/ADR-013; se aplica prospectivamente por olas, sin alterar recibos históricos, ni autorizar ejecución de un sprint o proveedor E.

**Resuelta:** adopción del contrato transversal de autoría/calidad y ADR-016. **No resuelto ni implícitamente aprobado:** autorización individual R02-08, habilitación de agentes mutativos, API externa, presupuesto E y decisiones de negocio de otros proyectos. La aprobación del proceso no es aprobación de todas las propuestas que el proceso genere.
