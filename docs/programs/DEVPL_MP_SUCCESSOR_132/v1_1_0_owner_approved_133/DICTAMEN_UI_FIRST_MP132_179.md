---
doc_id: MP132-UI-FIRST-PILOT-B-DECISION-REVIEW-179
status: PROPOSED_PROGRAM_AMENDMENT_NOT_APPLIED
reviewed_program: DEVPL_MP_132_POST_M1_R02_172.zip
current_repo_baseline: 735ecfd82e9604a4755fd7d4e7c386976984ed71
active_sprint: R02_05_PILOT_B_ENTRY_RESUME
active_sprint_status: LOCAL_PASS_WINDOWS_PENDING
scope: PROGRAM_CONTRACT_REVIEW_AND_R02_05_CORRECTIVE_DESIGN
---

# Dictamen de adecuación: Pilot B 100 % DevPilot UI, de bootstrap a release

## 1. Veredicto y delimitación

**SE REQUIERE ADENDA PROGRAMÁTICA + CORRECTIVO ACOTADO DE R02-05.** El programa contiene la intención UI-first, pero no su delimitación operacional universal y medible; la guía COR-178 y el operador acoplan una identidad de Pilot B introducida por PowerShell al journey. Se conserva la evolución R0–R10 y la aprobación individual por incremento. Este documento propone modificaciones, **no altera ni autoriza código Git, ni modifica el ZIP programático sellado o el sprint aprobado**.

## 2. Base consultada literalmente

- `0_program/01_PROGRAMA_MAESTRO_132.md`: flujo humano, mecanismos determinísticos de autorización y Git/release, UX normal Guided/Expert.
- `0_program/02_ROADMAP_INDUSTRIAL_132.md`: Pilot B B0–B7, R2–R6 y R10, UI sin terminal en M2.
- `5_pilotos/00_PILOT_B_CHARTER_132.md`: `operator_project_writes=0`, `normal_user_terminal_escapes=0`, `journey_actions_via_devpilot_ui=true`, un workspace continuo. La frase `Release se instala/arranca fuera de DevPilot` crea ambigüedad sobre el disparador de deploy.
- `2_contratos/PROGRAM_ACCEPTANCE_AND_MATURITY_MATRIX_132.md`: madurez B0–B5, UI normal y evidence real.
- `2_contratos/PROGRAM_DEPENDENCY_REGISTER_132.md`: dependencias R2→R3→R4→R5→R6→R10.
- `2_contratos/CONFIGURATION_AUTHORITY_MATRIX_132.md`, `PROGRAM_AUTHORITY_AND_DECISION_REGISTER_132.md`: autoridades de instalación/proyecto/runtime.
- `4_backlogs/BACKLOG_R02_132.md` a `BACKLOG_R10_132.md`: hitos de producto y release, launcher propio de DevPilot en R9.
- `7_ Execution_packages-sprints_prompts/BACKLOG_R02/00_PLAN_R02_172.md`, `01_REGLAS_R02_172.md`, sprints y prompts R02-05 a R02-10.
- `1_arquitectura/ADR-MP-132-011.md`: proyección coherente de estados y next action; no regula exclusivamente la frontera usuario/UI/operador.
- Código `src/devpilot_core/policy/path_guard.py` del Git archive Windows R02-04: `DEVPILOT_ALLOWED_WORKSPACE_ROOTS` admite raíces externas explícitas; PathGuard acepta descendientes bajo esas raíces. Eso NO equivale a un workflow UI de autorización de nuevos roots.
- `R02_05_178.zip`: `GUIA_UNICA_WINDOWS.md` pasos 1, 7, 10, 12, 18; `operador178.py` funciones `check_pilot_b`, `b0_before_restart`, `browser` y argumentos `--pilot-id`, `--pilot-root`.

## 3. Contrato normativo recomendado — UI_FIRST_PILOT_B_V1

1. **Perímetro**: mismo proyecto Pilot B desde B0 (idea/intake/bootstrap) hasta B7 (evolución y segundo release). No sustituir el proyecto por fixtures ni por otro workspace en olas posteriores.
2. **Acciones humanas de negocio/ingeniería**: nombre, ID, root final, necesidad, restricciones, perfil y modelo, propuestas, edición, reviews, aprobaciones, FROZEN, planificación, historias, código, pruebas, Quality, Git, packaging, publicación, despliegue, verificación, operación, rollback y evolución se gobiernan mediante controles normales de DevPilot UI y APIs autorizadas. No CLI externo, DevTools, editor o asistente externo para ejecutar una acción que forma parte del journey.
3. **Ejecución interna**: DevPilot puede usar Git/Python/compiladores/gestores de dependencias/subprocesos detrás de sus herramientas tipadas, con dry-run, scope, PathGuard, permisos, approvals materiales, preimages, idempotencia, límites, logging y rollback. `via_devpilot_ui=true` describe el origen de la orden, NO impide backend execute.
4. **Consolas de operador humano permitidas**: levantar/detener API y UI durante la transición sin instalador; configuración estrictamente operacional de arranque, si es necesaria; auditoría y lectura de logs/hashes/capturas; aplicación/validación de correctivos y evoluciones al **código de DevPilot**. La consola no elige identidad de Pilot B, no escribe/inicializa su workspace, no instala sus dependencias, no crea artefactos, no ejecuta sus jobs ni Git o release en sustitución de la UI.
5. **Roots**: en B0 el Owner elige exclusivamente desde Project Entry el target final y DevPilot debe validar que sea descendiente de una raíz de instalación previamente autorizada o gestionar explícitamente la autorización mediante UI administrativa gobernada. En etapa transicional, la consola que arranca API puede suministrar una raíz padre de instalación ya aprobada, NO el target Pilot B particular y no una raíz extensa indiscriminada (p. ej. todo D:\). Ese allowlist de instalación no concede acceso a otros roots ni elude PathGuard/RBAC/approval.
6. **Evidencia anti-escape**: registrar `journey_action_origin=devpilot-ui`, actor/sesión, `approval_id` cuando corresponda, `action_or_job_id`, target workspace, before/after, evidence IDs y `operator_project_writes=0`, `normal_user_terminal_escapes=0`. Las evidencias de aceptación son del flujo UI normal, no fixtures/acciones manuales para compensar pantallas incompletas.
7. **Release**: DevPilot UI inicia el release plan, packaging, deployment autorizado, health, rollback y su evidencia. El **artefacto resultante debe poder ejecutarse independientemente de DevPilot**, y el destino puede estar fuera de la carpeta de DevPilot. Independencia del producto desplegado NO significa que el Owner deba desplegarlo mediante terminal. Si un runtime/destino no dispone aún de workflow gobernado, el gate M6 es PARTIAL/BLOCK según el contrato; no se sustituye por CLI manual.
8. **Seguridad**: local-first, cero external egress por defecto; modelos solo por policy/evals. No ampliar permisos al hilo de corregir coordinación. Semántica de S0/S1 bloquea; UX cosmética S2/S3 se registra y difiere.

## 4. Documentos que se deben modificar

| Prioridad | Documento | Ajuste concreto |
|---|---|---|
| P0 | `5_pilotos/00_PILOT_B_CHARTER_132.md` | Adenda UI_FIRST_PILOT_B_V1, matriz acciones B0–B7. Reemplazar ambigüedad de `Release ... fuera de DevPilot` distinguiendo independencia del artefacto e inicio/gestión del release por UI. |
| P0 | `0_program/01_PROGRAMA_MAESTRO_132.md` | Hacer la regla transversal y declararla gate E2E, sin confundir operadores de plataforma con agentes/jobs internos. |
| P0 | `2_contratos/PROGRAM_ACCEPTANCE_AND_MATURITY_MATRIX_132.md` | Añadir ejes `ui_initiated_journey`, `operator_project_writes=0`, `normal_user_terminal_escapes=0`, release/rollback UI iniciado, procedencia de jobs y evidence. |
| P0 | `0_program/02_ROADMAP_INDUSTRIAL_132.md` | Explicitar en R2–R6 y M2–M6 UI-first; no posponer un control de UI esencial a R9. |
| P0 | `2_contratos/PROGRAM_DEPENDENCY_REGISTER_132.md` | Vincular gate UI-first de B0–B7 y release UI antes de declarar M6, sin crear nueva ola ni duplicar IDs. |
| P0 | `4_backlogs/BACKLOG_R02_132.md` y `7_.../BACKLOG_R02/01_REGLAS_R02_172.md` | Definición UI-only de identidad y root final, scripts solo auditoría; evidencia lectura de identidad del registro post-UI. |
| P0 | Sucesores de `SPRINT_R02_05_APPROVED_178.md`, `PROMPT_R02_05_APPROVED_178.md` y `GUIA_UNICA_WINDOWS.md` | Corregir COR-178 sin repetir pruebas de fuente ya acreditadas; no pedir PilotID/PilotName/PilotRoot por CLI; operador lee antes/después desde registro autoritativo. |
| P0 futuro | `4_backlogs/BACKLOG_R03_132.md`, `BACKLOG_R04_132.md`, `BACKLOG_R05_132.md` | AC UI normal para aprobación tecnológica/scaffold, Planning, SourceChangePlan, tests, jobs, Quality y Git, sin tareas manuales en terminal. |
| P0 futuro | `4_backlogs/BACKLOG_R06_132.md` | AC explícito de release/instalación/health/rollback UI-iniciado; portabilidad de app que arranca independientemente. |
| P0 futuro | `4_backlogs/BACKLOG_R10_132.md` | Auditoría independiente de cero `normal_user_terminal_escapes` B0–B7 y cadena de recibos real de todas las etapas. |
| P1 | `2_contratos/CONFIGURATION_AUTHORITY_MATRIX_132.md`, `PROGRAM_AUTHORITY_AND_DECISION_REGISTER_132.md` | Distinguir raíz de instalación aprobada vs root final elegido en Project Entry y permisos de job tipado. |
| P1 | `4_backlogs/BACKLOG_R09_132.md` | Mantener launcher/instalador DevPilot R9 como deuda de plataforma y NO como prerrequisito para UI-only del Pilot B. |
| P1 | `0_program/00_LEEME_INDICE_Y_ORDEN_132.md` y `4_backlogs/00_INDICE_BACKLOGS_Y_PRIORIDADES_132.md` | Referenciar adenda/ADR sucesora sin alterar autoridad de actas históricas. |
| Nueva ADR | Sucesor complementario a `ADR-MP-132-011`, p.ej. `ADR-MP-132-012` | Frontera de interacción UI, ejecución gobernada interna, configuración de raíces, independencia de release, evidencia y negativas. NO reescribir ADR-011 aceptada. |

Los documentos históricamente FROZEN/sellados permanecen inmutables. Los ID R02–R10 se conservan. La ejecución de R02-06 no queda autorizada por esta revisión.

## 5. Corrección prioritaria del COR-178 detenido al inicio

**Situación**: el paso 1 pide `PilotID`, `PilotName`, `PilotRoot`; el paso 7 vuelve a pedir root; pasos 12 y 18 pasan `--pilot-id` y `--pilot-root`. No hay evidencia en esta revisión de que se haya aplicado el correctivo R02-05 o iniciado B0. Evitar continuar la guía tal como está.

**Solución mínima**:

1. El preflight solo verifica plataforma/ZIP/baseline/pruebas y captura snapshot hash del registro persistente previo de proyectos. No pide ni inventa identidad del proyecto.
2. La consola API se inicia con una política de raíz de instalación previamente consentida y restringida, p. ej. `D:\Projects\DevPilot_Workspaces` si ese parent está realmente aprobado por el Owner. No debe crear ni nombrar el hijo Pilot B ni conceder `D:\` general. En una evolución de configuración persistente, administrar el root parent por UI Owner.
3. El Owner abre Project Home, define ID/nombre/ruta/necesidad solo en Project Entry y realiza dry-run, revalidation, approval y bootstrap UI normales.
4. El auditor compara snapshots de registro *antes/después* y exige un único workspace nuevo (o un identificador nuevo inequívoco), project YAML/registration/engineering state consistentes, target dentro de raíz aprobada, Git inicial, neutral scaffold, ausencia de writes operador. Si hay múltiples altas o un root ambiguo, BLOCK por evidencia real, sin seleccionar arbitrariamente.
5. Persistir `B0_BEFORE_RESTART` con identidad capturada de fuente autoritativa; tras detener y reiniciar API (permitido), comparar el registro/estado y screenshots del mismo ID/root. Sin `--pilot-id/--pilot-root` de consola.
6. Mantener Git allowlist y SHA/CRC del código DevPilot, dos confirmaciones materiales ya previstas (commit/promoción de **DevPilot**); approvals del proyecto ocurren exclusivamente en Approval Center UI.
7. Cambiar operator/guía/tests y, si hace falta, documentar política de root parent. No reabrir R02-01..04 ni abrir R02-06.

## 6. Criterios de éxito

- Antes de UI: `pilot_id_defined_outside_ui=false`, `pilot_name_defined_outside_ui=false`, `pilot_target_defined_outside_ui=false`, `operator_project_writes=0`.
- Después de UI: proyecto B0 nuevo, registro/runtime consistente, `project_creation_origin=DevPilot_UI`, permisos PathGuard PASS para target y negativos de root externo PASS.
- Después de reinicio: misma identidad/root y UI Status/Home concuerdan, sin session cache que suplante autoridad.
- En B1–B7: todas las acciones del proyecto tienen origen UI y recibos; R5 Git y R6 release no requieren terminal manual; runtime desplegado sigue siendo autónomo.
- Excepciones de auditoría/arranque permitidas quedan registradas y no cuentan como acciones del journey.

## 7. Autoridad y siguiente movimiento

Decisión de producto indicada por el Owner en el turno actual: UI-only Pilot B B0–B7, consola solo para operar/auditar DevPilot y correctivos de plataforma. Incorporar como **adenda sucesora** con ADR sin alterar hashes históricos, y producir correctivo acotado del bundle COR-178 antes de completar su validación Windows. `R02-05` se mantiene `LOCAL_PASS/WINDOWS_PENDING`; `R02-06` permanece `NOT_AUTHORIZED`. Baseline publicado vigente según evidencia R02-04: `735ecfd82e9604a4755fd7d4e7c386976984ed71`.
