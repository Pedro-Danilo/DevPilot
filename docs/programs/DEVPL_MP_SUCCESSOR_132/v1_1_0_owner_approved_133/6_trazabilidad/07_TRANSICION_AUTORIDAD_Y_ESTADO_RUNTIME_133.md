---
doc_id: DEVPL-MP-132-AUTHORITY-TRANSITION-133
status: OWNER_DECISION_EFFECTIVE_REPO_REBIND_PENDING
version: "1.0.0"
owner: "Ordóñez"
decision_date: "2026-10-13"
input_program_sha256: "d9743653686f6b232cdc6cd9e3983685f25a197b072848d53a200525b91647f8"
input_baseline_sha256: "fb9bd0755f702891cb0804c8e2ac03e6477e34ce4e11b77b449c8670b3d483b8"
source_head: "8db5b44694abcced3231183e05731e732f5b8f24"
approval_method: "Declaración explícita del Owner en conversación"
current_execution_baseline: "cd0bce59ec2bf4a7ae7e50a555c1c8a1bd85facc"
r01_gate: "CLOSED_PASS_WITH_FINDINGS"
r02_execution_authority: false
---

# Diferencia entre decisión de programa y valores Git históricos

La aprobación programática y levantamiento global del STOP están **vigentes por acto expreso Owner**, pero el repositorio `8db5...` fue producido antes del acto. Sus banderas internas persistentes `mp_stop=ACTIVE`, estado MP-1B, Source Registry y Project State **no se modificaron** por crear este paquete. Por diseño deben reconciliarse como un incremento documental gobernado en R0 con auditoría focal previa, allowlist y test negativo de autoridad. Hasta entonces:

- La persona puede diseñar/auditar y solicitar autorización de nuevos incrementos del programa 132.
- No interpretar el flag viejo como autorización; si el servicio actual deniega la operación, **no sortearlo por fuera**: corregir la fuente de autoridad con un sucesor aprobado y test.
- No reabrir viejos prompts MP-1B ni usar endpoints de proveedor externo automáticamente.
- G5 y COR-130 no se reejecutan ni se editan en place; permanecen sellados.
- La migración de worktree B queda condicionada a preflight Windows y documentación de rollback.

El próximo incremento R0 puede implementar/publicar esa reconciliación de autoridad **después** de revisión focal y orden ejecutable independiente. No se crean aquí operadores ni se modifica Windows.


---

## Addendum operacional M0→R1 — sucesor de planificación (14-10-2026)

- **Asunto:** Transición de autoridad.
- **Actualización concreta:** Actualizar autoridad vigente mediante sucesor que vincula COR-143, R00-03, COR-150 y COR-151; snapshots de STOP histórico se conservan.
- **Evidencia vinculada:** COR-143 (migración B), R00-03/COR-145 (publicación 57 documentos), R00-04/COR-147 (auditoría Settings), COR-150 (paridad 1752), COR-151 (cierre Owner M0).
- **HEAD de autoridad técnica:** `66ab2e6227072c951b5bd2ac9160e8515b1b9fc0`. Las referencias a `8db5b44694abcced3231183e05731e732f5b8f24` y los indicadores `STOP ACTIVE` en secciones históricas no se reescriben como si fueran estados presentes.
- **Autoridad:** copia sucesora propuesta para adopción documental posterior; no constituye un commit, promoción Git, autorización de R1, de MP-1B, de modelo/API externa ni una aceptación funcional de Settings.
- **Transferencias vigentes:** `MP132-R0-09` → R2 para mediciones reales; UX Settings pendiente de reproducción y validación; egress externo DENY; no duplicar ownership entre olas.


---

## Adenda sucesora post-M1 — 15-10-2026 (no retroactiva)

- **Baseline Git publicado:** `cd0bce59ec2bf4a7ae7e50a555c1c8a1bd85facc` (`evolution/multiprovider-v2`), sucesor de `feaac2723c1f8a467f5cdb7d456e4e7679dd0f82` por R01-15/COR-171. - **R01:** 15/15 incrementos aceptados; 16 IDs propietarios cubiertos; cierre M1 `PASS_WITH_FINDINGS` con 108 tests focales y 8 del operador PASS en Windows. - **Evidencia:** `RESULT_171.json`, `M1_REPORT_171.json`, `R01_15_EVIDENCE.zip`, `repo_R01_15_CLEAN.zip` y SHA256. - **Autoridad:** R02 se desagrega sólo para planificación. Ningún `SPRINT_EXECUTION_APPROVED`, ningún push, bootstrap Pilot B, inferencia local, external egress o MP-1B queda autorizado por esta adenda. - **Limitaciones:** `model_local_real=NOT_TESTED`, `semantic_llm_judge=NOT_TESTED`, `rag_groundedness_real=NOT_TESTED`, `external_real=DENIED`; no confundir pruebas de servicio con un recorrido completo Product Definition UI.
- La afirmación histórica «repo rebind pending» se refiere a entrada de octubre 13, **no** al baseline actual. R00/COR151 y R01/COR171 publicados; los `mp_1a_stop_status` y `mp_v2_baseline_commit` en snapshots vivos son legados clasificados. No se les atribuye autoridad presente: `mp_stop_status=OWNER_LIFTED_INCREMENT_GATES_REMAIN`, `mp_1b_activation=BLOCKED_UNTIL_SPECIFIC_INCREMENT_APPROVAL` y `external_api_allowed=false` se conservan.
