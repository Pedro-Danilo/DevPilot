---
doc_id: "ADR-DEVPL-MP-POST-SYNC1-130"
title: "ADR — Rebind post-SYNC-1 sin habilitar capacidades nuevas"
status: "APPROVED / EXECUTION-GATED"
version: "1.0.0"
source_head: "1806665881a432231462ecfed51f3e342e365be3"
---
# ADR — Autoridad programática post-SYNC-1

## Contexto
El merge SYNC-1 incorporó la evolución determinística al branch MP, pero mantuvo marcadores previos de P0, D05, D06 y G5; un test afirmaba explícitamente el estado anterior. La ausencia de un successor podría inducir una ejecución MP-1B prematura o falsos FAIL al corregir metadatos.

## Decisión
1. Fuente autoritativa de código: `evolution/multiprovider-v2` tras SYNC-1; commit SHA real en recibo posterior al correctivo, nunca precalculado.
2. Autoridad programática: sucesor de rebind **solo para estados**; el programa MP v2.1 anterior necesita replanificación y aprobación independiente.
3. Proyección de estado actual separada de historia inmutable (`*_at_merge`, histórico GSDLC y evidencias).
4. STOP continúa `ACTIVE`; `MP-1B=BLOCKED` y `ExternalModel` denegado por defecto.
5. Tests históricos de SYNC-1 comprueban historia; tests sucesores comprueban nueva autoridad. No se cambia el código de generación, APIs, agente, seguridad ni UI.
6. Una regla `owner_confirmation` explícita precede a la promoción Git, con hashes de preimagen y allowlist de paths.

## Consecuencias
- A favor: elimina señales actuales obsoletas sin reinterpretar resultados anteriores, sin rebase, sin full regression, sin duplicar kernel de generación.
- Coste/limitación: se necesita un nuevo commit y receipt Windows; la auditoría funcional E2E y el uso real de modelos/agents permanecen pendientes, no acreditados por un rebind documental.
- Riesgo de EOL: comparar contenido Git normalizado; no usar bytes físicos LF/CRLF como gate de equivalencia.

## Alternativas descartadas
Borrar claves históricas: pérdida de trazabilidad. Actualizar solo registry y no tests/project_state: inconsistencia de autoridad. Activar MP-1B automáticamente: violaría el STOP y ausencia de programa sucesor aprobado.
