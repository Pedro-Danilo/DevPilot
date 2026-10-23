---
doc_id: DEVPL-MP-SUCCESSOR-132-CONFIGURATION_AUTHORITY_MATRIX_132
title: "Configuración por scope, persistencia, permisos y UX"
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

# Configuración por scope, persistencia, permisos y UX

## Matriz de dominios

| Dominio | Fuente candidata | Alcance | Modificación |
|---|---|---|---|
| Preferencias globales | installation settings versionados | Instalación | Validación typed; no secrets en archivo visible |
| Workspaces/root authorized | workspace registry / policy | Workspace | Owner + boundary check |
| Perfil de proyecto/estándares | `.devpilot/project.yaml` y PESP | Proyecto | Successor con revisión |
| Security/egress/CostGuard | `.devpilot/policy.yaml`, policies canónicas | Deny floor global + scopes | Approval-gated, no project override weaker |
| Providers/config | Provider registry/config con secrets-by-reference | Global/proyecto según policy | Plan / validate / controlled apply |
| Runtime kill/revoke | Runtime operational store | Proceso/referencia | Acción operacional independiente auditada |
| Diagnostics/traces/health | Observability store | Read-only | No mutable settings |
| Guided/Expert | User/session preference | UI | Nunca concede RBAC |

Cada setting: `key,namespace,scope,authority_ref,persisted_location,type/default,effective_value,origin,override_rule,permission,approval,restart_required,effect,rollback,status`. Mostrar origen/effective en Guided y diagnostico en Expert.

## UI objetivo

Settings Home: preparación global, configuración efectiva y accesos. Subsuperficies `General`, `Modelos/Proveedores`, `Seguridad/Políticas`, `Proyecto Activo`; Runtime Control/kill y Diagnostics fuera de la edición persistente, aunque tengan links desde Settings. No una pantalla infinita con acordeones. Cada botón muestra efecto, scope, permiso y feedback in situ.

## Migración y seguridad

Auditar `SettingsView.ts`, `settings_service.py`, endpoints provider y stores en HEAD vivo; no editor YAML write-anything ni sobrescritura de archivos. Preserve MP-0F disclosure parcial. Tests persist/restart, RBAC/CSRF, concurrent changes, rollback, kill switch, no egress, no secrets y UI browser. Fase temprana R0 audit, R1 vertical, R2 local model, R7 agents, R8 external.


---

## Addendum operacional M0→R1 — sucesor de planificación (14-10-2026)

- **Asunto:** Settings.
- **Actualización concreta:** Incorporar R00-04 PASS_WITH_FINDINGS pero UI NOT_TESTED; Settings persistente tipado y separación de runtime divididos entre R01-10/R01-11.
- **Evidencia vinculada:** COR-143 (migración B), R00-03/COR-145 (publicación 57 documentos), R00-04/COR-147 (auditoría Settings), COR-150 (paridad 1752), COR-151 (cierre Owner M0).
- **HEAD de autoridad técnica:** `66ab2e6227072c951b5bd2ac9160e8515b1b9fc0`. Las referencias a `8db5b44694abcced3231183e05731e732f5b8f24` y los indicadores `STOP ACTIVE` en secciones históricas no se reescriben como si fueran estados presentes.
- **Autoridad:** copia sucesora propuesta para adopción documental posterior; no constituye un commit, promoción Git, autorización de R1, de MP-1B, de modelo/API externa ni una aceptación funcional de Settings.
- **Transferencias vigentes:** `MP132-R0-09` → R2 para mediciones reales; UX Settings pendiente de reproducción y validación; egress externo DENY; no duplicar ownership entre olas.


---

## Adenda sucesora post-M1 — 15-10-2026 (no retroactiva)

- **Baseline Git publicado:** `cd0bce59ec2bf4a7ae7e50a555c1c8a1bd85facc` (`evolution/multiprovider-v2`), sucesor de `feaac2723c1f8a467f5cdb7d456e4e7679dd0f82` por R01-15/COR-171. - **R01:** 15/15 incrementos aceptados; 16 IDs propietarios cubiertos; cierre M1 `PASS_WITH_FINDINGS` con 108 tests focales y 8 del operador PASS en Windows. - **Evidencia:** `RESULT_171.json`, `M1_REPORT_171.json`, `R01_15_EVIDENCE.zip`, `repo_R01_15_CLEAN.zip` y SHA256. - **Autoridad:** R02 se desagrega sólo para planificación. Ningún `SPRINT_EXECUTION_APPROVED`, ningún push, bootstrap Pilot B, inferencia local, external egress o MP-1B queda autorizado por esta adenda. - **Limitaciones:** `model_local_real=NOT_TESTED`, `semantic_llm_judge=NOT_TESTED`, `rag_groundedness_real=NOT_TESTED`, `external_real=DENIED`; no confundir pruebas de servicio con un recorrido completo Product Definition UI.
- R01-10/11 acreditan Settings persistente/browser, no habilitación automática de Ollama/LM Studio ni licencia para egress. R02-02 separa descubrimiento, health y readiness operativa de `settings` declarativa. Guardar preferencia no cambia runtime.

## Adenda Owner UI-first 179 — UI_FIRST_PILOT_B_V1

| Dato/operación | Autoridad de entrada | Límite |
|---|---|---|
| Parent de workspaces autorizados | Política de instalación/arranque de DevPilot; provisión transitoria de operador de plataforma | Parent existente y acotado, nunca un volumen entero ni el target Pilot B |
| ID/nombre/root final/necesidad | Exclusivamente Project Entry de DevPilot | No `Read-Host`, variable de consola ni template predefinido |
| Proyecto activo/recuperación | Registro runtime persistente + metadata de proyecto | Auditor solo lee snapshots anteriores y posteriores, nunca selecciona o activa proyecto |
| Git/release/deploy/rollback Pilot B | Workflows tipados iniciados desde UI con permisos y receipts | Terminal humana fuera de scope; aplicaciones desplegadas autónomas |
