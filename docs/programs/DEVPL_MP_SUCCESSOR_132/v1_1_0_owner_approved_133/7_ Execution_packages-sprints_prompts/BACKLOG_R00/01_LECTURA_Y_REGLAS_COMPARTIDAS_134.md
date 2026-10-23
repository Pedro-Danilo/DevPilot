---
doc_id: DEVPL-MP-132-R00-COMMON-134
version: 1.0.0
status: DRAFT_EXECUTION_GATED
execution_authority: false
---
# Regla común de implementación R00

## Cómo usar este paquete

Este conjunto de 5 sprints y 5 prompts es una **desagregación técnica proyectada** del único `BACKLOG_R00_132.md`. Aunque `DEVPL_MP_SUCCESSOR_132` tiene autoridad `OWNER_APPROVED_PROGRAM`, **ningún sprint de este paquete está todavía aprobado para ejecutar** y ninguna instrucción autoriza mutaciones Git antes de su decisión Owner individual. Las referencias al ZIP 133 son la fuente exacta; no replicarlas a mano ni modificarlas al publicarlas.

Orden de lectura: `0_control/00_PLAN_DESAGREGACION_R00_134.md` → esta regla común → `3_trazabilidad/MATRIZ_R00_COBERTURA_Y_GATES_134.md` → sprint 01 y prompt 01 → evidencia Windows/gate → sprint 02 y prompt 02 → 03 → 04 → 05. El prompt correspondiente solo se entrega al implementador cuando el Owner aprueba el alcance y dispone de fuentes/resultados anteriores.

## Reglas transversales exigibles a todos los implementadores

- Auditoría focal real sobre código y estado Git **vigentes** (no solo el ZIP histórico), con Reuse/Delta Map, assessment de riesgos, pruebas y entregables de `NO-OP` cuando corresponda.
- Fases independientes, duraciones controladas, procesamiento incremental y checkpoints atómicos **fuera de todos los worktrees** para reiniciar desde la última fase PASS sin repetir efectos. Límite de intentos; los prompts no conceden autonomía ilimitada.
- `dry-run` inicial. Acciones Git y source solo cuando el sprint lo prevea y Owner lo autorice con identidad exacta (HEAD, pathset, plan SHA). Ninguna autoridad generativa, agente ni operador puede aprobar su propio cambio.
- Cada incremento produce UNA `GUIA_UNICA_WINDOWS_<ID>.md`: sin pasos repetidos/retrocesos, PowerShell cada comando una línea, beginner-medio, checks PASS/BLOCK explícitos, sin procesos background. Python stdlib salvo justificación de dependency existente. Tres consolas foreground solo cuando realmente se necesiten API+UI.
- Evidencia: ZIP/SHA/CRC, Git 3-estados cuando haya mutación, source paths permitidos, pruebas focales/negativas, owner confirmation, estado `mp_stop`, `mp_1b`, external egress y Pilot A. No Full Regression de rutina; no filtrar credenciales en ZIP/logs.
- No editar ni sobrescribir FROZEN. Si un documento aprobado necesita corrección, crear sucesor y pedir nueva decisión; en el R00-03 publicar **57 Markdown Owner-133 byte-identical**.
- Reconciliar consistentemente `Source Registry`, `Project State`, overlay/Authority Graph sólo cuando la auditoría documente aplicabilidad. Para verificar G5 ratificado mirar estado vigente y distinguir campos `at_merge` históricos; no borrar pasado.
- La actividad R00-03 es el **primer nuevo baseline con los rebind pendientes**. No generar un baseline parcial en R00-01 ni R00-02.
- En caso de falta de fuente, drift, receipt corrupto, bloqueo o interrupción prolongada: preservar checkpoint; parar y pedir evidencia. No inventar capacidad de auto-recuperación ni informar PASS sin pruebas.

## Estrategia de checkpoint de herramientas

Estructura mínima de checkpoint read-only externo:

```json
{
  "schema": "devpilot.mp132.r00.checkpoint.v1",
  "sprint": "R00-xx",
  "phase": "prepare",
  "status": "PASS_OR_BLOCK",
  "source_head": "exact_git_sha",
  "source_worktree": "authorized_path",
  "input_manifest_sha256": "hex",
  "completed_outputs": [],
  "next_phase": "validate",
  "source_write_count": 0,
  "approval_ref": null
}
```

El ejemplo es ilustrativo, no es schema ya existente; cada operador debe definir tipos y validarlo. Guardar el checkpoint mediante creación temporal y reemplazo atómico del **recibo de trabajo no sellado**; una evidencia final `SEALED` es append-only/immutable. En todo restart reconciliar primero HEAD/branch/receipt y no reintentar operaciones con efectos hasta clasificar su resultado anterior.

## R00 — Gate M0 de verdad, no de trámite

M0 solo acredita que la autoridad R0 está preparada y que R1 puede **proponerse**. No declara modelo local integrado, Settings refactorizado, Pilot B iniciado, software profesional terminado ni multiprovider D/L/E aceptado. `PASS+FINDING` acepta solo deuda no bloqueante con Owner, plan y referencias; S0/S1 funcional reproductible bloquea la frontera afectada.
