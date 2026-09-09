---
doc_id: "PROMPT-DEVPL-GSDLC-10-ACTIVATION"
title: "DEVPL-GSDLC-10 — Integrated activation/rebind before 10-A"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-09-09"
approval: "approved_by_owner/rebound_repo414_on_canonical_repo413"
execution_source_repo: "repo_DevPilot_Local_414_DEVPL_GSDLC_09_FINAL_AUTHORITY_POINTERS_WINDOWS_VALIDATED_CANDIDATE.zip"
execution_source_commit: "adccda6a8fe296a96511bc313be5b883dad32767"
execution_source_sha256: "1ab8b2d38a243ae04caffbf3cd62360c6e613eda3f181cb9d5210b25d549bfe3"
canonical_product_baseline_repo: "repo_DevPilot_Local_413_DEVPL_GSDLC_09_FINAL_CLOSURE_RECONCILIATION_WINDOWS_VALIDATED_CANDIDATE.zip"
canonical_product_baseline_commit: "b27f50c1747cae3462e6d689fa00bfd1b8ead6c9"
canonical_product_baseline_sha256: "61a7753ff4d87947b34112aa8aef33902a5e3ee6380ba2c4f003fb542ab6a3fb"
standalone_micro_sprint: false
standalone_successor_repo_allowed: false
must_be_folded_into: "GSDLC-10-A"
functional_mutation_in_activation_phase: false
full_regression_runs_allowed: 0
browser_runs_allowed: 0
---
  
# 00 — Activation/rebind integrado de DEVPL-GSDLC-10

Este prompt **no crea un micro-sprint adicional**. Ejecutarlo como primera fase del trabajo de 10-A y consolidar sus cambios con el mismo commit/bundle/evidencia de 10-A.

Objetivo: materializar el binding current-active de GSDLC-10 sin perder el corrective de punteros contenido en repo414 y sin reescribir hechos históricos de GSDLC-09.

## Política transversal obligatoria

- Ingeniería acumulativa: nunca retroceder a un repo histórico para simplificar implementación.
- **Execution source:** usar el successor Windows-validado inmediatamente anterior. Para el inicio de GSDLC-10 es repo414; repo413 se conserva como baseline canónico funcional de cierre de GSDLC-09.
- No `reset --hard`, `git clean`, force push ni eliminación de `.git`.
- Operadores Windows: Python preferido, reentrantes y deliberadamente pequeños; validar solo lo necesario según Test Impact.
- Cada instrucción PowerShell de una guía Windows debe ir en una sola línea, claramente identificada como `Powershell`, y terminar en PASS verde o BLOCK rojo.
- API/UI solo cuando el micro-sprint necesite browser; cuando se requieran, exactamente tres consolas separadas y API/UI siempre foreground.
- Runtime stores (`auth.db*`, `devpilot.db*` y equivalentes), secretos, `.git`, `.venv`, caches, `outputs/` y `node_modules/` quedan fuera de fixtures/evidence/packages finales.
- LF/CRLF jamás puede causar BLOCK: comparar contenido Git o hashes semánticos UTF-8/LF, no representación física accidental.
- Historical Contract Authority y Contract Reconciliation Sweep se ejecutan de forma proporcional al impacto. No editar tests históricos solo para hacerlos pasar.
- Clasificación de contratos: `historical-freeze`, `current-active`, `successor-needed`, `deprecated-after-proof`, `derived`, `runtime-ephemeral`.
- **Drift documental puntual:** si no rompe seguridad, autoridad, trazabilidad, DoD ni la invariante funcional, se corrige dentro del micro-sprint activo/siguiente; no crear micro-sprint, operador ni repo independiente solo por ese drift.
- FRX low-level knobs (`planner`, `max_nodeids`, nodeid transport, workers directos) no pertenecen a operadores GSDLC. El `FullRegressionExecutionProfile` current-active es autoridad.
- Agentes/modelos pueden proponer; nunca obtienen por la ruta/modelo autoridad para aprobar, waivar, stage, commit o ejecutar mutaciones.


## Trabajo requerido

1. Verificar de forma barata y reproducible:
   - repo414 SHA/identidad suministrada;
   - GSDLC-09 y 09-E cerrados;
   - `gsdlc_10_authorized=true` y `gsdlc_next_backlog_authorized=DEVPL-GSDLC-10`.
2. Reconciliar dentro del **mismo delta de 10-A**:
   - `gsdlc_current_backlog=DEVPL-GSDLC-10`;
   - `gsdlc_current_micro_sprint=DEVPL-GSDLC-10-A`;
   - backlog 10 = `APPROVED/ACTIVE/GSDLC-10-A`;
   - execution source = repo414;
   - canonical product baseline = repo413;
   - README/roadmap/source registry solo si requieren la transición current-active.
3. No tocar funcionalidad de Test Impact durante esta fase de rebind; esa implementación sigue en el mismo sprint 10-A inmediatamente después.
4. No generar repo, commit o Windows bundle exclusivos para activation.
5. Drift documental menor encontrado aquí se incorpora al delta 10-A; no abrir corrective independiente salvo violación de seguridad/authority/DoD.

## Gates mínimos

- Project State current binding;
- Documentation Governance sobre los paths realmente cambiados;
- Evidence Freshness solo si se altera una autoridad que ese gate consume;
- ancestry/source identity.

No full. No browser.

## Entregables obligatorios de implementación/Windows

Al terminar este micro-sprint, entregar únicamente artefactos coherentes entre sí:

- source delta manifest exacto;
- implementation report con capacidades, archivos creados/modificados, riesgos y limitaciones;
- Test Impact + focal/acumulativa y gates que correspondan al delta;
- historical contract sweep / Contract Reconciliation proporcional;
- Windows validation bundle con operador Python pequeño y reentrante;
- guía única `.md` para Windows, orientada a personal beginner-medio; comandos PowerShell de una sola línea, identificados como `Powershell`, PASS verde/BLOCK rojo;
- evidencia machine-readable y manual/browser solo cuando aplique;
- después de PASS Windows: repo ZIP limpio + components ZIP + SHA-256 + packaging result;
- identidad Git pre/post y commit sugerido/real.

El operador no debe instalar dependencias ad hoc, no debe ejecutar checks ajenos al delta solo “por seguridad”, y debe reconocer/reutilizar estados PASS previos cuya evidencia esté hash-bound e íntegra.

## PASS

- GSDLC-10 current-active y 10-A current micro-sprint;
- repo414 no se pierde;
- repo413 preservado como canonical functional baseline;
- S0/S1=0;
- activación queda absorbida por el artefacto de 10-A.
