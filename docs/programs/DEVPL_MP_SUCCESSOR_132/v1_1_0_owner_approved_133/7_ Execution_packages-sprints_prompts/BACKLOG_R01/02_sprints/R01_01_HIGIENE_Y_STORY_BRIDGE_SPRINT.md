---
doc_id: MP132-R01-01-SPRINT
title: "Higiene documental M0 y primer bridge Story→Envelope"
version: "1.0.0-PROPOSED"
status: "DRAFT_EXECUTION_GATED"
owner: "DevPilot Owner"
baseline_reference_at_planning: "66ab2e6227072c951b5bd2ac9160e8515b1b9fc0"
execution_authority: false
approval_scope: "PLANNING_ONLY"
source_backlog: "BACKLOG_R01_132.md"
---

# R01-01 — Higiene documental M0 y primer bridge Story→Envelope

## Objetivo y alcance
Auditar TODO drift vigente heredado de M0 (campos de autoridad, docs de cierre, referencias presentes/históricas, snapshots y source registry) y ejecutar la reconciliación aprobada junto con un bridge tipado Story→GenerationRequest→ArtifactCandidateEnvelope sin segundo apply authority.

- **Ítems estables cubiertos:** MP131-R1-01.
- **Dependencia de entrada:** M0-COR151 CLOSED; baseline 66ab2e6227072c951b5bd2ac9160e8515b1b9fc0.
- **Fuentes a auditar antes de decidir la allowlist:** `src/devpilot_core/generation/contracts.py`; `src/devpilot_core/generation/runtime.py`; `src/devpilot_core/application/story_implementation_candidate_service.py`; `.devpilot/docs_governance/source_registry.json`; `.devpilot/docs_governance/rebaseline_p0_overlay.json`.
- **No ampliar la ola:** R01 únicamente; R2/R8/R7 no se ejecutan.

## Decisión técnica y porqué
R01-01 es el **primer incremento mutativo**, por lo tanto contiene obligatoriamente el saneamiento documental heredado M0. Reutilizar contratos existentes; un solo owner por capacidad. Un `NO_OP_ACCEPTED` es admisible cuando la evidencia demuestra una capacidad ya existente. Separar claramente `mock`, `service`, `UI browser` y `modelo real`.

## Micro-checkpoints secuenciales (sin regresiones completas)
1. **A0/A1 – Preflight y Reuse/Delta.** Comprobar Git tres estados, rama `evolution/multiprovider-v2`, HEAD vivo, portabilidad de tests y matriz de autoridad; identificar firmas existentes y documentación actual vs histórica.
2. **A2 – Diseño focal.** Delimitar el cambio, contratos afectados, `allowlist` **exacta**, criterios negativos y ADR sucesora solamente si cambia una decisión arquitectónica; no inventar dependencias ni rutas.
3. **A3 – Dry-run controlado.** Crear parche en copia aislada; validar preimage por hash de blobs Git y compatibilidad con el baseline; no modificar source antes de aprobación del cambio material.
4. **A4 – Implementación acotada.** Aplicar exclusivamente los paths aprobados, con idempotencia y reanudación por HEAD y estado Git real; dry-run es el modo predeterminado.
5. **A5 – Validación y promoción.** Pruebas focales positivas/negativas y browser si la superficie es UI; commit y push no forzados bajo autorización conforme al impacto. No publicar sin evidencia funcional.
6. **A6 – Resultado.** Recibo técnico, límites, huellas y estado `PASS|PASS_WITH_FINDINGS|PARTIAL|BLOCK|NO_OP_ACCEPTED`, con una guía Windows única para la ejecución del incremento.

## Criterios de aceptación verificables
- Dos dominios fixture; cierre M0 actual verificable; rechazo de nuevo propietario de apply; ningún drift de contrato global vigente.
- Ningún cambio fuera de la allowlist aprobada y todos los reportes citan el HEAD/resultados reales.
- Sin falsa equivalencia por LF/CRLF: comparar blobs Git o texto canónico únicamente cuando el contrato sea textual; binarios por SHA exacto.
- **Riesgos / límites:** NO_OP donde paridad ya exista; excluir ajustes históricos; no importar código de un Pilot RF específico.

## Entregables y validación Windows
Bundle independiente ZIP de nombre corto con `GUIA_UNICA_WINDOWS.md`, operador Python, patches/diffs, tests, receipts y manifest SHA. Descarga a `C:\Users\Pedro\Downloads`; evidencia fuera del repo; comandos PowerShell en una sola línea con `PASS` verde / `BLOCK` rojo. No copiar toda la documentación histórica al operador.

## Permisos, costo y control
- Ruta base: mock/D sin API key ni costo. L local sólo cuando sea necesario y con autorización; E/external siempre DENY hasta R8.
- No realizar `reset --hard`, `force push`, borrados ni sobreescritura sin consentimiento específico. Evitar autorizaciones para lecturas o verificaciones triviales.
- **Estado inicial:** `DRAFT_EXECUTION_GATED`; el programa Owner-133 autoriza planificar, **no ejecutar** este sprint.

## Criterio de STOP
Bloquear solamente por discrepancia material de autoridad, seguridad, source real, defectos funcionales S0/S1 o pruebas exigidas incumplidas. Hallazgos cosméticos `OBSERVE_ONLY`; documentar sin encadenar microcorrectivos.
