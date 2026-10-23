---
doc_id: MP132-R01-09-SPRINT
title: "Harness de evaluación de candidatos"
version: "1.0.0-PROPOSED"
status: "SPRINT_EXECUTION_APPROVED"
owner: "DevPilot Owner"
baseline_reference_at_planning: "70b5eddce83708c01cfdd6557e82e8369990e878"
execution_authority: true
approval_scope: "R01_09_ONLY"
source_backlog: "BACKLOG_R01_132.md"
---

# R01-09 — Harness de evaluación de candidatos

## Objetivo y alcance
Dataset versionado, schema/semantic gates, groundedness, negativos y reporte reproducible por provider/versión; inicialmente mock/D.

- **Ítems estables cubiertos:** MP131-R1-06.
- **Dependencia de entrada:** R01-08 evidencia focal PASS; HEAD rebindeado antes de implementar.
- **Fuentes a auditar antes de decidir la allowlist:** `tests/test_mp0b_candidate_generation_kernel.py`; `evals/fixtures/`; `src/devpilot_core/generation/`.
- **No ampliar la ola:** R01 únicamente; R2/R8/R7 no se ejecutan.

## Decisión técnica y porqué
Ningún cambio sin inspección previa del HEAD recibido del incremento anterior. Reutilizar contratos existentes; un solo owner por capacidad. Un `NO_OP_ACCEPTED` es admisible cuando la evidencia demuestra una capacidad ya existente. Separar claramente `mock`, `service`, `UI browser` y `modelo real`.

## Micro-checkpoints secuenciales (sin regresiones completas)
1. **A0/A1 – Preflight y Reuse/Delta.** Comprobar Git tres estados, rama `evolution/multiprovider-v2`, HEAD vivo, portabilidad de tests y matriz de autoridad; identificar firmas existentes y documentación actual vs histórica.
2. **A2 – Diseño focal.** Delimitar el cambio, contratos afectados, `allowlist` **exacta**, criterios negativos y ADR sucesora solamente si cambia una decisión arquitectónica; no inventar dependencias ni rutas.
3. **A3 – Dry-run controlado.** Crear parche en copia aislada; validar preimage por hash de blobs Git y compatibilidad con el baseline; no modificar source antes de aprobación del cambio material.
4. **A4 – Implementación acotada.** Aplicar exclusivamente los paths aprobados, con idempotencia y reanudación por HEAD y estado Git real; dry-run es el modo predeterminado.
5. **A5 – Validación y promoción.** Pruebas focales positivas/negativas y browser si la superficie es UI; commit y push no forzados bajo autorización conforme al impacto. No publicar sin evidencia funcional.
6. **A6 – Resultado.** Recibo técnico, límites, huellas y estado `PASS|PASS_WITH_FINDINGS|PARTIAL|BLOCK|NO_OP_ACCEPTED`, con una guía Windows única para la ejecución del incremento.

## Criterios de aceptación verificables
- Reporte determinista y lineage/costos medidos o NOT_AVAILABLE; input adversarial bloqueado.
- Ningún cambio fuera de la allowlist aprobada y todos los reportes citan el HEAD/resultados reales.
- Sin falsa equivalencia por LF/CRLF: comparar blobs Git o texto canónico únicamente cuando el contrato sea textual; binarios por SHA exacto.
- **Riesgos / límites:** No reclamar modelo local evaluado sin ejecutar modelo real (R2).

## Entregables y validación Windows
Bundle independiente ZIP de nombre corto con `GUIA_UNICA_WINDOWS.md`, operador Python, patches/diffs, tests, receipts y manifest SHA. Descarga a `C:\Users\Pedro\Downloads`; evidencia fuera del repo; comandos PowerShell en una sola línea con `PASS` verde / `BLOCK` rojo. No copiar toda la documentación histórica al operador.

## Permisos, costo y control
- Ruta base: mock/D sin API key ni costo. L local sólo cuando sea necesario y con autorización; E/external siempre DENY hasta R8.
- No realizar `reset --hard`, `force push`, borrados ni sobreescritura sin consentimiento específico. Evitar autorizaciones para lecturas o verificaciones triviales.
- **Estado actual:** `SPRINT_EXECUTION_APPROVED`; autorización Owner individual en esta conversación para R01-09 únicamente. Git real pendiente de ejecución Windows.

## Criterio de STOP
Bloquear solamente por discrepancia material de autoridad, seguridad, source real, defectos funcionales S0/S1 o pruebas exigidas incumplidas. Hallazgos cosméticos `OBSERVE_ONLY`; documentar sin encadenar microcorrectivos.

## Rebind operativo COR-162 (15-10-2026)

- Predecesor R01-08/COR-161: CLOSED/WINDOWS_PASS; commit `70b5eddce83708c01cfdd6557e82e8369990e878`.
- Única autorización de ejecución: MP131-R1-06 / R01-09. R01-10 y MP-1B NO AUTORIZADOS.
- Alcance: evaluación reproducible mock/determinística, datasets versionados, schema/semantic/grounding por reglas, negativos, provenance y cost/latency NOT_AVAILABLE. No evaluar modelos reales ni usar LLM-as-judge.
- Baseline canónico: `D:\Projects\DevPilot_Local`, rama `evolution/multiprovider-v2`.
- Cambios Git limitados a 5 rutas según `05_inputs/manifest.json`, con reconciliación de punteros activos y sin modificar snapshot histórico.
- Pruebas focales acumulativas (no full regression), operador reanudable, push no forzado solo tras autorización material.
