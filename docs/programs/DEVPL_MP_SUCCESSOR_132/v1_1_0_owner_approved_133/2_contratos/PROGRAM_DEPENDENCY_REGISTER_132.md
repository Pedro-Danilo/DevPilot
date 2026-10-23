---
doc_id: DEVPL-MP-SUCCESSOR-132-PROGRAM_DEPENDENCY_REGISTER_132
title: "Dependencias, owner de backlog y bloqueos entre olas"
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

# Dependencias, owner de backlog y bloqueos entre olas

## Unidad de dependencia

`dependency_id`, `source_item_id`, `target_item_id_or_gate`, `dependency_kind HARD|SOFT|OPTIONAL`, `required_capability`, `evidence`, `owner`, `current_status`, `decision_ref`, `allowed_parallelism`. Cada item pertenece a un único backlog de ola; el índice maestro deriva links, no crea clones de prioridad/estado.

## Cadena crítica

R0 program/Git/authority → R1 Candidate/Route/PESP/Coverage/Settings mínimo → R2 L real/Product Definition → R3 design/scaffold → R4 planning/evolution → R5 arbitrary Story→Quality/Git → R6 release/rollback → R10 independent E2E. R7 read-only agents puede empezar con fundamentos R1/R3, pero write agents sólo tras guard R5 y autorización específica. R8 provider externo separado, no dependiente para Pilot B local-first, requerido para `EXTERNAL_ENABLED`. R9 acumula hardening desde temprano y gate final tras funcionalidad relevante.

## Dependencias más sensibles

- Git worktree R0-03 decide carpeta antes del **primer source mutation**, no requiere borrar 63 worktrees históricos.
- PESP/Artifact Profiles requiere estándares versionados, no impedir Pilot B por todos los perfiles del mundo.
- Publication/Successor antes de FROZEN Pilot B para evitar artefactos provisionales sin lineage.
- Settings autoridad antes de exponer local model UX; route/eval antes de declarar modelo `ELIGIBLE`.
- ADR external y CostGuard antes de cualquier llamada API remota.
- Config Agent trust/Tools antes de handoffs mutativos.
- D06 process crash/HTTP/Git receipt-loss antes de claim recuperación producción, no confundir con S1–S6 PASS fixture.

## Replanificación

Si auditoría declara `NO-OP`, cerrar item con receipt, sin commit nuevo. Si descubre dependencia contradictoria, bloquear el sprint y publicar successor de dependencias/roadmap con Owner; no reordenar silenciosamente a mitad de ejecución.


---

## Addendum operacional M0→R1 — sucesor de planificación (14-10-2026)

- **Asunto:** Dependencias.
- **Actualización concreta:** Actualizar R0→R1 y orden de R01-01..15; liberar dependencia M0, preservar gates R2/modelo local y R8/egress.
- **Evidencia vinculada:** COR-143 (migración B), R00-03/COR-145 (publicación 57 documentos), R00-04/COR-147 (auditoría Settings), COR-150 (paridad 1752), COR-151 (cierre Owner M0).
- **HEAD de autoridad técnica:** `66ab2e6227072c951b5bd2ac9160e8515b1b9fc0`. Las referencias a `8db5b44694abcced3231183e05731e732f5b8f24` y los indicadores `STOP ACTIVE` en secciones históricas no se reescriben como si fueran estados presentes.
- **Autoridad:** copia sucesora propuesta para adopción documental posterior; no constituye un commit, promoción Git, autorización de R1, de MP-1B, de modelo/API externa ni una aceptación funcional de Settings.
- **Transferencias vigentes:** `MP132-R0-09` → R2 para mediciones reales; UX Settings pendiente de reproducción y validación; egress externo DENY; no duplicar ownership entre olas.


---

## Adenda sucesora post-M1 — 15-10-2026 (no retroactiva)

- **Baseline Git publicado:** `cd0bce59ec2bf4a7ae7e50a555c1c8a1bd85facc` (`evolution/multiprovider-v2`), sucesor de `feaac2723c1f8a467f5cdb7d456e4e7679dd0f82` por R01-15/COR-171. - **R01:** 15/15 incrementos aceptados; 16 IDs propietarios cubiertos; cierre M1 `PASS_WITH_FINDINGS` con 108 tests focales y 8 del operador PASS en Windows. - **Evidencia:** `RESULT_171.json`, `M1_REPORT_171.json`, `R01_15_EVIDENCE.zip`, `repo_R01_15_CLEAN.zip` y SHA256. - **Autoridad:** R02 se desagrega sólo para planificación. Ningún `SPRINT_EXECUTION_APPROVED`, ningún push, bootstrap Pilot B, inferencia local, external egress o MP-1B queda autorizado por esta adenda. - **Limitaciones:** `model_local_real=NOT_TESTED`, `semantic_llm_judge=NOT_TESTED`, `rag_groundedness_real=NOT_TESTED`, `external_real=DENIED`; no confundir pruebas de servicio con un recorrido completo Product Definition UI.
- R01→R02 liberado como dependencia de **planificación**. Primer incremento que mute Git audita drift activo; Ollama opt-in exige health/readiness/policy, UI espera servicio local y origen; documentos FROZEN esperan publication/successor. LM Studio es complementario: si no está disponible, se documenta `DEFERRED_WITH_REASON`, sin false PASS; para M2 basta al menos una ruta local real aceptada.

## Adenda Owner UI-first 179 — UI_FIRST_PILOT_B_V1

**Dependencia transversal `UI_FIRST_PILOT_B_V1`:** la salida R2/M2 debe preservar identidad B0 creada por UI; R3/R4/R5/R6 heredan esa identidad y cero escrituras/acciones manuales, R10 revisa la cadena completa. El release autónomo de R6 depende de flujos de packaging/deploy/rollback iniciados por UI, no del launcher DevPilot de R9. R02-05 COR-179 reemplaza solo la coordinación de COR-178, sin autorizar R02-06. No se añade una nueva ola o gate de aprobación inocuo.

---

## Enmienda programática post-R02-06 · 187

**HARD chain futura:** `R02-06 CLOSED` → R02-07 candidato L Markdown+pre-FROZEN quality → R02-08 cobertura/cross-document audit → R02-09 resiliencia → R02-10 M2 real → R3 TechnologyProfile/ADRs/Scaffold healthy → R4 Release/Increment Plan + roadmap/backlog/sprint → R5 story+increment acceptance → R6 release/deploy/restore. `SoftwareIncrementPlan` no impone un nuevo approval si el approval del plan de release ya contiene la decisión exacta. Soft: R7 agent read-only independiente cuando hay safety/evals; R8 E opcional y DENY por defecto; R9 productización transversal.

**Límites:** no congelar futuros sprints masivamente, no pasar a construcción con stack `undecided`, ni iniciar la instalación de dependencias durante la aprobación de Architecture. Cada transición utiliza evidencias de finalización por etapa y clasifica gates `NOT_APPLICABLE` con motivo. R02-06 D/L y R02-07 L-only no se contradicen: el primero es ensayo ya cerrado, el segundo autoría normal.

---

## Dependencias A188 posteriores al cierre R02-07

R02-07 `CLOSED/PASS_WITH_FINDINGS`, HEAD `3a0a170f3c646e9955966576dd9212d3f87450e6`. A188 aporta el contrato transversal como **precondición documental** para diseñar R02-08, no una obligación de reescribir R02-07. R02-08 requiere su propia autorización de sprint + rebinding a baseline exacto. Product Definition se ensaya con dos dominios; R03–R10 especializan perfiles en sus olas, sin dependencias circulares ni activación masiva de agentes/API E.

---

## Adenda de cierre R02 → planificación R03 — 2026-10-22

Dependencia R02/M2 → R03/M3: **cumplida para planificar**; recibos y HEAD `1f15fa5b770db37c684e870a49572dcb569bd3a4`. R03_01=precondición HARD de R03_02..11 para detectar/reconciliar drift material activo sin reescribir historia. Cada micro-sprint queda supeditado a cierre focal de su predecesor y rebinding exacto de HEAD. No se instala scaffold al aprobar Architecture: plan/diff, policy, aprobación material e idempotencia preceden ejecución. No habilitar egreso a API externa ni dependencias no consentidas.

## Registro histórico R02 conservado — recuperación R03-01 COR2

Esta sección conserva literalmente antecedentes R02 del repositorio predecesor `1f15fa5b770d` que fueron omitidos al reconciliar R03. **Es historia, no autoridad operativa vigente**: los estados y las autorizaciones actuales son los establecidos por las adendas R03/A189 anteriores y el estado de ejecución de DevPilot. No revive sprints ni concede permisos.

## Actualización operativa MP132 post-M1 — R02-01

**Dependencia de ejecución R02-01.** M1 cerrado en cd0bce59ec2bf4a7ae7e50a555c1c8a1bd85facc. R02-01 = auditoría y reconciliación; R02-02 readiness depende de Windows PASS y Owner individual; no instalar proveedor ni activar red en R02-01.

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
