---
doc_id: DEVPL-MP-SUCCESSOR-132-03_SUPERSESSION_AUTORIDAD_Y_GATES_132
title: "Supersession total de v131, cadena de autoridad y gates de activación"
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

# Supersession total de v131, cadena de autoridad y gates de activación

## 1. Regla de reemplazo documental

La versión `DEVPL_MP_SUCCESSOR_132 v1.1.0` **reemplaza íntegramente los 12 documentos de `DEVPL_MP_SUCCESSOR_131 v1.0.0` para el diseño y la planificación**: ningún documento 131 queda como fuente ejecutable autónoma, ni como contrato vigente en paralelo. Sus decisiones compatibles están expresamente recogidas o incorporadas en esta propuesta. Los documentos originales se preservan bit a bit como historia, sin editarles encabezados ni cambiar su SHA.

**Autoridad confirmada:** el Owner aprobó explícitamente v132 para planeación y levantó el STOP global mediante actos separados Owner-133. v131 queda `SUPERSEDED_BY_132 / HISTORICAL_ONLY`; no se edita el ZIP 131. El registro en Source Registry del repositorio vivo **queda pendiente de publicación gobernada**. Este acto no aprueba sprints ni mutaciones Git ni ejecuta migraciones.

## 2. Equivalencias exhaustivas 131 → 132

| Archivo 131 | Sucesores responsables 132 | Disposición |
|---|---|---|
| `00_INDICE_Y_CONTROL_131.md` | `0_program/00`, `06`, `6_trazabilidad/00` | SUPERSEDED |
| `01_PROGRAMA_MAESTRO_131.md` | `0_program/01`, `02`, `1_arquitectura` | SUPERSEDED |
| `02_BASELINE_SUPERSESSION_Y_GATE_131.md` | `0_program/03`, `04`, `2_contratos/01` | SUPERSEDED |
| `03_GOBERNANZA_AUDIT_FIRST_131.md` | `3_gobernanza/00`, `2_contratos/08` | SUPERSEDED |
| `04_ROADMAP_INDUSTRIAL_131.md` | `0_program/02` y `4_backlogs/00..R10` | SUPERSEDED |
| `05_BACKLOG_MAESTRO_131.md` | `4_backlogs/00`, 11 backlogs R0–R10 | SUPERSEDED, 66 IDs preservados |
| `06_PILOT_B_CHARTER_131.md` | `5_pilotos/00` | SUPERSEDED |
| `07_GIT_WORKTREE_Y_OPERACION_131.md` | `3_gobernanza/02`, `1_arquitectura/ADR-132-008` | SUPERSEDED |
| `08_MATRIZ_RIESGOS_DECISIONES_131.md` | `3_gobernanza/01`, `2_contratos/01` | SUPERSEDED |
| `09_ADJUDICACION_COR130_131.md` | `6_trazabilidad/02` | HISTORICAL EVIDENCE retained; standalone 131 superseded |
| `10_FUENTES_Y_VERIFICACION_131.md` | `6_trazabilidad/00`, `01` | SUPERSEDED |
| `11_MANIFEST_INTEGRIDAD_131.md` | `6_trazabilidad/03_MANIFEST..._132.md` | Historical hash record retained |

## 3. Autoridad histórica que no se destruye

El historial aprobado de `REBASELINE_P0_P3_117`, G0–G5, los ADRs MP v2.1 aplicables y las pruebas de Pilot A se conserva como evidencia/contratos vigentes **solo donde no hayan sido reemplazados**. El paquete MP v2.1 `APPROVED` no puede ejecutar viejos `MP-1B` sobre HEAD nuevo. Mantener ADR 001,002,003,006,007 como principios vigentes; 004/005/009 requieren sucesores/adaptación; ADR-008 exige ajuste por worktree; ADR-010 external sigue diferida hasta decisión de egress. No crear contradicción documental entre esos ADRs y los de 132: Los nuevos pasaron a `OWNER_ACCEPTED` mediante acto separado 133; sus reglas **compatibles** son sucesoras y no invalidan controles de seguridad históricos.

## 4. Gates antes de modificar fuente

- **G-PROGRAM:** `OWNER_APPROVED_PROGRAM` satisfecho por acto 133 y SHA exacto del original; **pendiente** publicar el programa en Source Registry y Documentation Authority Graph con delta documental gobernado.
- **G-G5-ADMIN:** `DONE_OWNER_RATIFIED` mediante decisión independiente 133; no recrear merge ni ZIP 128; conservar limitaciones D06/G5.
- **G-R0-GIT:** arquitectura B **aceptada condicionalmente** por Owner; auditar tracked/untracked/ignored, worktrees, upstream, procesos, .venv/imports, backups y rollback mediante preflight Windows. Si PASS, tramitar operador y ejecución específicos; si BLOCK conservar MP. No realizar switch automático.
- **G-ADR-FOUNDATIONS:** 11 ADRs `OWNER_ACCEPTED` en la **decisión de diseño**, con matriz de auditoría 133. Antes de mutación completar Reuse/Delta Map del HEAD vivo y contratos del incremento; la **activación** de E en ADR-010 sigue diferida y la ejecución de agentes en ADR-009 requiere threat model y permisos.
- **G-EXEC-INCREMENT:** Owner autoriza sprint futuro con HEAD, auditoría, allowlist, costo/red/hardware, tests y plan de rollback. Aprobación del programa NO sustituye G-EXEC.
- **G-ENV:** máquina real Ollama/LM Studio eval-capable antes de declarar M2; si ausente, mock y `LOCAL_PENDING`, no false PASS.

## 5. Estados y fallos de autoridad

`PROGRAM_APPROVED` no implica `GIT_PROMOTION_APPROVED`. `ModelAdapter implemented` no implica `LocalModel accepted`. `M8 NOT_ENABLED` no implica `EXTERNAL_ENABLED`. Cualquier conflicto no resuelto de HEAD, `doc_id`, política, contrato o aprobación bloquea promoción; emitir propuesta sucesora, no editar FROZEN ni usar force-push.


---

## Addendum operacional M0→R1 — sucesor de planificación (14-10-2026)

- **Asunto:** Supersession y autoridad.
- **Actualización concreta:** Registrar publicación real de 57 documentos R00-03, COR-150 y cierre COR-151; preservar actas 133 e históricos sin reescribir.
- **Evidencia vinculada:** COR-143 (migración B), R00-03/COR-145 (publicación 57 documentos), R00-04/COR-147 (auditoría Settings), COR-150 (paridad 1752), COR-151 (cierre Owner M0).
- **HEAD de autoridad técnica:** `66ab2e6227072c951b5bd2ac9160e8515b1b9fc0`. Las referencias a `8db5b44694abcced3231183e05731e732f5b8f24` y los indicadores `STOP ACTIVE` en secciones históricas no se reescriben como si fueran estados presentes.
- **Autoridad:** copia sucesora propuesta para adopción documental posterior; no constituye un commit, promoción Git, autorización de R1, de MP-1B, de modelo/API externa ni una aceptación funcional de Settings.
- **Transferencias vigentes:** `MP132-R0-09` → R2 para mediciones reales; UX Settings pendiente de reproducción y validación; egress externo DENY; no duplicar ownership entre olas.


---

## Adenda sucesora post-M1 — 15-10-2026 (no retroactiva)

- **Baseline Git publicado:** `cd0bce59ec2bf4a7ae7e50a555c1c8a1bd85facc` (`evolution/multiprovider-v2`), sucesor de `feaac2723c1f8a467f5cdb7d456e4e7679dd0f82` por R01-15/COR-171. - **R01:** 15/15 incrementos aceptados; 16 IDs propietarios cubiertos; cierre M1 `PASS_WITH_FINDINGS` con 108 tests focales y 8 del operador PASS en Windows. - **Evidencia:** `RESULT_171.json`, `M1_REPORT_171.json`, `R01_15_EVIDENCE.zip`, `repo_R01_15_CLEAN.zip` y SHA256. - **Autoridad:** R02 se desagrega sólo para planificación. Ningún `SPRINT_EXECUTION_APPROVED`, ningún push, bootstrap Pilot B, inferencia local, external egress o MP-1B queda autorizado por esta adenda. - **Limitaciones:** `model_local_real=NOT_TESTED`, `semantic_llm_judge=NOT_TESTED`, `rag_groundedness_real=NOT_TESTED`, `external_real=DENIED`; no confundir pruebas de servicio con un recorrido completo Product Definition UI.
- Programa v132 permanece autorizado para planificación por Owner-133; STOP global levantado, **MP-1B sigue no autorizado**, egress E negado. Las actas/recibos R00/R01 sellados son evidencia inmutable y no se sobreescriben para resolver rótulos heredados.
