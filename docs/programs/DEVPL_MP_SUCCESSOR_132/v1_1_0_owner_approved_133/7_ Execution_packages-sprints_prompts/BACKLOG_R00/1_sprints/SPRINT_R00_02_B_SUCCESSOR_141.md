# MP132 R00-02 — Addendum de ejecución B / COR-141

- **Versión focal:** 1.0.2, sucesora de COR-140 solo para la opción B.
- **Estado:** SPRINT_EXECUTION_APPROVED por instrucción explícita de Owner para preparación y ejecución condicionada a preflight y doble confirmación.
- **Autoridad:** Owner-133 (preferencia B), R00-01 AUDIT_PASS_WITH_LIMITS, R00-02 PAUSED_BY_OWNER en Paso 7 COR-140, presente decisión de resolver B.
- **Fuente inmutable:** `DEVPL_MP_SUCCESSOR_132_v1_1_0_OWNER_APPROVED`, `SPRINT_MP132_R00_02_GIT_LOCATION_DECISION_134`, `PROMPT_MP132_R00_02_GIT_LOCATION_DECISION_134`.

## Scope

Consolidar checkout canónico MP en `D:\Projects\DevPilot_Local` (common `.git` permanece allí), hacer smoke focal en entorno Windows, retirar exclusivamente `D:\Projects\DevPilot_Worktrees\DevPilot_Multiprovider` y sellar evidencia Git B. No crear commit ni push; no modificar source/57 MD/programa antes del siguiente incremento; no tocar los otros worktrees.

## Contrato de aceptación

`B_PREFLIGHT_PASS` live más backup de refs verificado, decisiones Owner separadas para migrar y retirar, MP branch y HEAD exactos en MAIN, fuente importada desde MAIN, historical ref preservada, viejo MP desregistrado y directorio ausente, otros worktrees no mutados. `MIGRATED_B_PASS` solo al superar sellado final y adjudicación posterior. Cualquier drift/riesgo => BLOCK con resultado parcial explícito y sin retry autónomo.

## Rebind frente a 134

- Se **sustituye focalmente** la prohibición de eliminar linked MP porque la solicitud Owner actual exige su desactivación definitiva; el retiro se separa y requiere token destructivo específico.
- Se sustituye la modalidad A-only de COR-140 sin alterar su evidencia histórica.
- La comparación remota live y el smoke local siguen siendo gates; no hay pruebas de API/UI extensivas ni full regression.
- Se registran preimages, Git bundle, receipts externos, recuperación anterior a retire y ZIP/SHA de evidencia.
- R00-03 queda bloqueado hasta adjudicar `G-R00-02 WORKTREE_LOCATION_DECIDED`.
