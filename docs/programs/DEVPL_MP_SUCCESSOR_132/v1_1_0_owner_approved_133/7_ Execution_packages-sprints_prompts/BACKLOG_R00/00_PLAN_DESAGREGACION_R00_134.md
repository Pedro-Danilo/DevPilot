---
doc_id: DEVPL-MP-132-R00-DECOMPOSITION-134
version: 1.0.0
status: DRAFT_EXECUTION_GATED
program_authority: DEVPL_MP_SUCCESSOR_132_v1_1_0_OWNER_APPROVED_133.zip
program_status: OWNER_APPROVED_PROGRAM
baseline_commit: 8db5b44694abcced3231183e05731e732f5b8f24
execution_authority: false
owner: "Owner DevPilot"
---
# R00 / DEVPL-MP-132 — Plan de desagregación ejecutable

## 1. Propósito y límite

**Solo R0.** Desagrega `4_backlogs/BACKLOG_R00_132.md` (nueve ítems) en cinco incrementos verificables; no programa R1–R10, no implementa los cambios y no sustituye ninguna autoridad vigente del paquete 133. Los sprints y prompts de este paquete están **proyectados**, pero requieren auditoría focal vigente y aprobación Owner individual antes de ejecutar, modificar Git o contratar capacidad de proveedor. `OWNER_APPROVED_PROGRAM` no es `SPRINT_EXECUTION_APPROVED`.

La versión 131 queda `SUPERSEDED/HISTORICAL_ONLY` para planeación; MP v2.1, Pilot A, GSDLC-13 y rebaseline-117 se utilizan exclusivamente según vigencia y precedencia documentadas en 132/133. Las 57 piezas Markdown del programa 133 son la autoridad programática **a publicar sin cambiar sus bytes**, no un nuevo programa para reescribir en R0.

## 2. Estado de entrada confirmado y ámbito de certeza

- Source HEAD `8db5b44694abcced3231183e05731e732f5b8f24`, branch `evolution/multiprovider-v2`, worktree MP según evidencia Windows de COR-130; remote paridad demostrada en esa evidencia, **debe reconfirmarse live**.
- ZIP original `DEVPL_MP_SUCCESSOR_132_v1_1_0_OWNER_APPROVED_133.zip`, SHA256 `d4e22170b9ecefa6434a10e0eeefdb535714b55ea1cd6ac750516d16147e8049`, 57 `.md`, CRC PASS.
- Actos Owner-133: G5 ratificado, COR-130 ratificado, STOP **global** `OWNER_LIFTED`, 11 ADRs `OWNER_ACCEPTED`, B **condicionada** a preflight, external activation **DEFERRED**, old MP-1B aún no ejecutable.
- El snapshot Git anterior a 133 retiene campos actuales obsoletos (`mp_stop_status=ACTIVE`, `reb117_g5=TECHNICAL_PASS_OWNER_RATIFICATION_PENDING`, `current_micro_sprint=NONE/MP_PROGRAM_SUCCESSOR_PENDING`); no se cambia el commit de entrada, se publica sucesor auditable.
- No se dispone aquí de inspección live de procesos/worktrees/ignored ni de salud actual de Windows. Ninguna declaración de `GIT_B_PASS`, `R00_CLOSED` o `NEW_BASELINE_PASS` es anticipable.

## 3. Secuencia, hitos y entregables

| Sprint | Naturaleza / scope | Ítems R0 principales | Resultado | Gate |
|---|---|---|---|---|
| **R00-01** | Solo lectura, auditoría focal de autoridad + Git B | R0-03, R0-04, MP132-R0-06, R0-02 | Preflight Windows, mapa de autoridad, Reuse/Delta Map y candidato A/B | `G-R00-01 PREFLIGHT_AUDITED` |
| **R00-02** | Migración operativa **condicional**, sin source commit | R0-03, MP132-R0-06 | B probada/ejecutada y verificada, **o** A elegida por BLOCK de B | `G-R00-02 WORKTREE_LOCATION_DECIDED` |
| **R00-03** | Primera mutación de source **solo documentos/metadata/tests de autoridad** | R0-01, R0-02, R0-04, MP132-R0-07 | **Primer baseline nuevo** con los **57 MD aprobados** y **todas** las decisiones Owner-133 vinculadas; repo ZIP limpio | `G-R00-03 AUTHORITY_REBOUND_WINDOWS_PASS` |
| **R00-04** | Auditoría focal Settings/UI + métricas/hardware, read-only por defecto | R0-05, MP132-R0-08, MP132-R0-09 | Arquitectura de autoridad Settings, ledger reconciliado, baseline medido/NA | `G-R00-04 SETTINGS_RISK_AUDITED` |
| **R00-05** | Cierre M0 y handoff a R1, sin nuevos source changes por defecto | Todos los nueve, especialmente R0-04 | Acta M0, matriz de evidencia/NO-OP, backlog R1 readiness | `M0 OWNER_ADJUDICATED` |

**Camino crítico:** 01 → 02 (rama B aprobada solo si PASS; A alternativa segura) → **03** → 04 → 05. R00-04 puede realizar una exploración de solo lectura anterior al 03, pero su adjudicación toma el HEAD ya publicado. No ejecutar 03 hasta resolver 02. No iniciar R1 hasta M0.

## 4. Garantía especial: primer baseline limpio

R00-03 es el **primer commit del sucesor 132**: publica íntegramente el paquete Owner-133, el registro de aprobación y supersession v131, el cierre G5, la ratificación COR-130, `global STOP=OWNER_LIFTED` y la decisión Git A/B **realmente acreditada**. Debe reconciliar Source Registry, Project State, Overlay y, cuando corresponda tras auditoría, Authority Graph/registros de gobernanza/tests. Conserva valores históricos `*_at_merge`, evidencias inmutables 117/128/129/130 y estado `MP-1B=BLOCKED_UNTIL_INCREMENT_APPROVAL`. No se permite dejar el registro documental a medio migrar por falta de tiempo.

**Atomicidad:** preparar patch + esquema + validadores + preview en worktree aislado; aplicar solo sobre allowlist aprobada y HEAD exacto; ejecutar pruebas focales/negativas; confirmar Owner para commit y push normal; verificar remoto; empaquetar Git archive con SHA/CRC. Si no llega a PASS, **BLOCK sin nuevo baseline**, corregir mediante sucesor, sin maquillarlo con un ZIP local no promovido.

## 5. Estrategia de continuidad frente a interrupciones de herramientas

Cada sprint deberá descomponerse en operaciones de duración breve (idealmente 2–8 minutos de cómputo cada una, sujeto a medición, no un SLA), y cada operación emitirá `CHECKPOINT.json` atómico fuera de los repositorios con `phase`, `status`, `head_before`, `head_after_if_any`, `worktree`, `owner_decision_ref`, `input_hashes`, `outputs_hashes`, `next_action`, `source_mutations`, `prohibited_operations`. Las fases largas se dividen, no se dejan en un proceso background. El reinicio **comprueba hashes/receipts** y reanuda desde el último gate válido sin repetir commits, pushes, ZIP ni Full Regression. Todo checkpoint obliga a `PASS/BLOCK`, y los recibos de evidencia no se sobreescriben sin versionar. La interrupción no es permiso para continuar mediante shell manual.

Fases sugeridas por incremento: `inspect → audit/prepare → validate → owner-confirm → execute(if applicable) → postcheck → package`. El operador no debe exigir reejecutar su fase previa después de encontrar un resultado sellado válido; el packaging debe ser idempotente y no introducir los propios logs en un bucle de ZIP cambiante.

## 6. Política de seguridad y validación

- READ_ONLY/dry-run por defecto; allowlist + preimage/HEAD recheck; sin `reset --hard`, `rebase`, force push, `git add .`, `--ignore-other-worktrees`, `git worktree prune` automático ni borrado de 63 worktrees históricos.
- No full regression en R0 salvo evidencia y orden Owner independiente; usar pruebas focales de estado documental, Git, schema y smoke pertinentes.
- No API externa, costes de modelo ni activación de agentes, herramientas, MCP o Pilot B. No source application service/UI changes en R0.
- Proteger Pilot A, rama determinística histórica, `outputs/**`, `.venv`, secrets; evidencia externa a source y ZIP sin runtime/credenciales.
- Un único instructivo Windows `.md` cuando se fabrique cada operador; PowerShell una instrucción por línea física; no fondo; tres consolas foreground solo si se necesita API/UI.

## 7. Decisiones del Owner que siguen siendo necesarias

1. Aprobación específica de R00-01 y del uso de sus instrumentos read-only.
2. Adjudicación de G-R00-01 y aprobación exacta de R00-02 B o de su fallback A, con backups y rollback.
3. Autorización separada de la **primera mutación documental** R00-03 y confirmaciones distintas para apply/commit/push.
4. Adjudicación de la evidencia Windows y del nuevo HEAD; luego autorizar R00-04 y cierre R00-05.
5. M0 Owner PASS/HOLD/BLOCK y orden específica futura para R1. Ninguna de las aprobaciones previas concede permiso para esos pasos.

## 8. Referencias que gobiernan esta desagregación

`4_backlogs/BACKLOG_R00_132.md`, `0_program/02_ROADMAP_INDUSTRIAL_132.md`, `0_program/03_SUPERSESSION_AUTORIDAD_Y_GATES_132.md`, `0_program/04_DECISIONES_PENDIENTES_Y_PREPARACION_132.md`, actos Owner-133 `07..10`, `3_gobernanza/00_AUDIT_FIRST_REUSE_FIRST_132.md`, `3_gobernanza/02_ESTRATEGIA_GIT_WORKTREE_132.md`, ADR-008 y ADR-011, `2_contratos/PROGRAM_AUTHORITY_AND_DECISION_REGISTER_132.md`, `2_contratos/PROGRAM_DEPENDENCY_REGISTER_132.md`, `6_trazabilidad/07_TRANSICION_AUTORIDAD_Y_ESTADO_RUNTIME_133.md`, baseline repo COR-130 y ledger v1.32. Toda modificación requiere consulta nuevamente del HEAD vivo.
