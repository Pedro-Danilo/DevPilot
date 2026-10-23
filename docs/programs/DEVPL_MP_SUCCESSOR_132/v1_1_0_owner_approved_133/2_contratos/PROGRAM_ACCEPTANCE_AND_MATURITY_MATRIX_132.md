---
doc_id: DEVPL-MP-SUCCESSOR-132-PROGRAM_ACCEPTANCE_AND_MATURITY_MATRIX_132
title: "Gates y niveles de madurez de DevPilot por alcance demostrado"
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

# Gates y niveles de madurez de DevPilot por alcance demostrado

## Distinción de niveles

| Estado | Prueba necesaria | Lo que NO significa |
|---|---|---|
| `FOUNDATION_PRESENT` | Símbolo/servicio/contrato existente y test focal | Vertical completo |
| `VERTICAL_INTEGRATED` | UI→API→service→candidate→policy→review→apply/quality/git de tarea real | Producto instalable |
| `LOCAL_MODEL_ACCEPTED` | Modelo L real con dataset/version/hardware y candidate validado en Owner UI | Agente autónomo ni API externa |
| `LOCAL_FIRST_PROFESSIONAL` | Pilot B B0–B5 E2E, code/quality/git/release/rollback, seguridad y docs portables | External habilitado |
| `AGENT_ASSISTED` | MIASI policy, bounded handoffs/tools, Pilot B B6, adversarial evals | Tool unrestricted / multiuser enterprise |
| `EXTERNAL_ENABLED` | ADR externa, CostGuard, egress, privacy, Pilot C external real, neg suites | Gratis/siempre encendido |
| `INDUSTRIAL_ACCEPTANCE` | B0–B7, segundo dominio, independent security/ops/evals, Owner acceptance, 0 S0/S1 critical path | Certificación regulatoria o escalabilidad enterprise automática |

## Gates por ola y validación

M0 program authority + Git; M1 kernel/policy/profiles básicos y neg suites; M2 Product Definition L real; M3 Technical Design FROZEN, tech approved, scaffold; M4 Planning trazable; M5 Story arbitraria con source real, Quality/Git; M6 release/restore; M7 agentes evaluados; M8 external o `NOT_ENABLED`; M9 fault injection/UX/perf/launcher; M10 E2E y dictamen independiente. Cada gate conserva si se probó fixture, service-only, full UI o real deployment; nunca usar `PASS` sin alcance.

## Evidencia de salida

`acceptance_id`, `milestone`, `baseline`, `scope`, `test_dataset`, `environment`, `artifacts`, `functional_scenarios`, `negative_scenarios`, `security`, `usability`, `operation`, `known_limits`, `owners`, `status PASS|PASS_WITH_FINDINGS|PARTIAL|BLOCK|NOT_APPLICABLE`, `decision_ref` y SHA. Medidas cuantitativas se calibran con hardware y dataset explícitos, no por intuición.

## Condición de producto profesional

No bastan 144 unit tests de integración, build Vite ni nuevo Git merge. Es indispensable demostrar un proyecto desde necesidad hasta release y recuperación por UI normal, sin escribir source del piloto mediante scripts de operador.


---

## Addendum operacional M0→R1 — sucesor de planificación (14-10-2026)

- **Asunto:** Aceptación.
- **Actualización concreta:** M0 cerrado con findings y scope documental; M1 requiere vertical demostrada, negativas, browser cuando aplique; no elevar madurez por mock.
- **Evidencia vinculada:** COR-143 (migración B), R00-03/COR-145 (publicación 57 documentos), R00-04/COR-147 (auditoría Settings), COR-150 (paridad 1752), COR-151 (cierre Owner M0).
- **HEAD de autoridad técnica:** `66ab2e6227072c951b5bd2ac9160e8515b1b9fc0`. Las referencias a `8db5b44694abcced3231183e05731e732f5b8f24` y los indicadores `STOP ACTIVE` en secciones históricas no se reescriben como si fueran estados presentes.
- **Autoridad:** copia sucesora propuesta para adopción documental posterior; no constituye un commit, promoción Git, autorización de R1, de MP-1B, de modelo/API externa ni una aceptación funcional de Settings.
- **Transferencias vigentes:** `MP132-R0-09` → R2 para mediciones reales; UX Settings pendiente de reproducción y validación; egress externo DENY; no duplicar ownership entre olas.


---

## Adenda sucesora post-M1 — 15-10-2026 (no retroactiva)

- **Baseline Git publicado:** `cd0bce59ec2bf4a7ae7e50a555c1c8a1bd85facc` (`evolution/multiprovider-v2`), sucesor de `feaac2723c1f8a467f5cdb7d456e4e7679dd0f82` por R01-15/COR-171. - **R01:** 15/15 incrementos aceptados; 16 IDs propietarios cubiertos; cierre M1 `PASS_WITH_FINDINGS` con 108 tests focales y 8 del operador PASS en Windows. - **Evidencia:** `RESULT_171.json`, `M1_REPORT_171.json`, `R01_15_EVIDENCE.zip`, `repo_R01_15_CLEAN.zip` y SHA256. - **Autoridad:** R02 se desagrega sólo para planificación. Ningún `SPRINT_EXECUTION_APPROVED`, ningún push, bootstrap Pilot B, inferencia local, external egress o MP-1B queda autorizado por esta adenda. - **Limitaciones:** `model_local_real=NOT_TESTED`, `semantic_llm_judge=NOT_TESTED`, `rag_groundedness_real=NOT_TESTED`, `external_real=DENIED`; no confundir pruebas de servicio con un recorrido completo Product Definition UI.
- **M1:** `PASS_WITH_FINDINGS` limitado a integración determinista y aceptación UI de superficies, `LOCAL_MODEL_ACCEPTED` aún NO.
- **M2:** requiere conexión real loopback, modelo identificado/versionado con dataset reproducible, latencia real y salida estructurada; revisión semántica humana de propuesta, provenance/costo `NOT_AVAILABLE` si no medido, tres documentos Markdown FROZEN, navegación completa UI y negativas timeout/JSON invalido/reinicio. No permitir que fixture/mock sustituya llamada local real.

## Adenda Owner UI-first 179 — UI_FIRST_PILOT_B_V1

La regla vinculante es `UI_FIRST_PILOT_B_V1`: toda acción del proyecto Pilot B B0–B7 debe originarse en la UI normal de DevPilot; el backend puede ejecutar herramientas gobernadas (Git, Python, jobs, packaging, deploy, rollback), pero el operador humano no sustituye ningún workflow del piloto con CLI, editores externos, DevTools o scripts. La consola se limita al arranque/parada de API/UI hasta disponer de instalador, preconfiguración operacional de la instalación, auditoría y correctivos sobre **la plataforma**. `operator_project_writes=0`, `normal_user_terminal_escapes=0`, `journey_actions_via_devpilot_ui=true`.

**Criterio de salida B0–B7:** `journey_actions_via_devpilot_ui=true`, `operator_project_writes=0`, `normal_user_terminal_escapes=0`, origen de acción y evidencia verificable. B0 exige project identity NUEVA registrada después de Project Entry UI, snapshot anterior, mismo ID/root tras reinicio. R5/M5 exige Git del proyecto gobernado desde UI. R6/M6 exige release/deploy/rollback iniciado y verificado desde UI, aunque la aplicación liberada opere independientemente. `PARTIAL/BLOCK` si una acción crítica requiere terminal humana; S2/S3 meramente estético permanece OBSERVE_ONLY. No imponer aprobación Owner para lecturas/recibos que la evidencia acredita.

---

## Enmienda programática post-R02-06 · 187

**Aceptación por nivel:** `STORY_DONE`: AC + pruebas focales + Quality + cambios Git autorizados; `INCREMENT_ACCEPTED`: stories integradas + objetivos de producto/escenarios E2E + negativas según riesgo + evidencia; `RELEASE_READY`: incrementos incluidos aceptados + build/packaging/deploy/health/rollback/docs/seguridad y validación operativa. Ningún nivel superior resulta automáticamente del inferior.

**Gates revisados:** M2 no necesita D/L obligatorios, sí L real competente en **un** candidato por artefacto, tres Markdown profesionales FROZEN y provenance; M3 TechnologyProfile aprobado+scaffold; M4 roadmap por outcomes + plan de incremento/release verificable + sprint con dependencias; M5 software funcional integrado y Git/Quality; M6 instalable/recuperable. R10 verifica segundo dominio y madurez por criterios independientes. MIASI se mide sobre componentes AI cuando se activen; `E_NOT_ENABLED` no bloquea LOCAL_FIRST_PROFESSIONAL si egress opcional no fue autorizado.

---

## Calidad y madurez tras aprobación A188

**Enmienda 188 Owner-approved (2026-10-22)**. Autoridad `MP132-OWNER-DECISION-188`; contrato `2_contratos/ARTIFACT_AUTHORING_QUALITY_CONTRACT_188.md` y ADR-MP132-016. Complementa 187/ADR-013; se aplica prospectivamente por olas, sin alterar recibos históricos, ni autorizar ejecución de un sprint o proveedor E.

No confundir `HTTP 200`, JSON/schema PASS, plantilla o FROZEN gobernado con autoría profesional autosuficiente. Madurez se acredita con pruebas multi-dominio, defectos materiales detectados, falsos PASS/BLOCK, esfuerzo de corrección técnica del Owner, trazabilidad de upstream y pruebas específicas del artefacto; sin mediciones, `NOT_TESTED`. R02-07 prueba piloto supervisado, no capacidad generalizada R0–R10 ni elegibilidad automática de E.

---

## Adenda de cierre R02 → planificación R03 — 2026-10-22

M2 `PASS_WITH_FINDINGS` 2026-10-22, HEAD `1f15fa5b770db37c684e870a49572dcb569bd3a4`; su alcance probado es Product Definition L local y revisión Owner. Pendientes medibles: calidad autónoma primera propuesta, equivalencia semántica, métricas completas de hardware/dataset, evidencia visual inequívoca de restart. M3 todavía `NOT_TESTED`; el gate M3 requiere UI normal (B2), cuatro etapas técnicas FROZEN, ADR/TechnologyProfile justificados, scaffold con lockfile, inicio real, health/smoke y negativas, sin intervención de consola sobre el proyecto. Ningún cierre R02 autoriza automáticamente R03 ni MP-1B.

## Registro histórico R02 conservado — recuperación R03-01 COR2

Esta sección conserva literalmente antecedentes R02 del repositorio predecesor `1f15fa5b770d` que fueron omitidos al reconciliar R03. **Es historia, no autoridad operativa vigente**: los estados y las autorizaciones actuales son los establecidos por las adendas R03/A189 anteriores y el estado de ejecución de DevPilot. No revive sprints ni concede permisos.

## Actualización operativa MP132 post-M1 — R02-01

**Matriz de madurez vigente.** R01 primera vertical determinista: `PASS_WITH_FINDINGS`, no E2E multi-modelo; local real / semantic judge / grounded RAG real: `NOT_TESTED`; externo `DENIED`. M2 no evaluado y R02-02..10 no autorizados.

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
