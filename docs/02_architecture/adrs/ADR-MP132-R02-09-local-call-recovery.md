---
doc_id: ADR-MP132-R02-09-LOCAL-CALL-RECOVERY
status: accepted-for-r02-09-owner-implementation
version: 1.0.0
owner: DevPilot / Owner
updated: 2026-10-22
---

# ADR — Recibos previos para llamadas locales y recuperación conservadora

## Contexto

Las operaciones de autoría local de Product Definition cuentan con checkpoints de candidatos, calidad, publicación y límites de reintento. En la generación segmentada se registraban fallos solo después de una respuesta. Una interrupción anterior a ese registro podía permitir repetir la misma solicitud con resultado desconocido. Vision y Scope compartían el riesgo en llamadas directas.

## Decisión

- Introducir recibos mínimos `R0209.local_call.v1` persistidos **antes** de la llamada al modelo. Vincularlos al hash de entrada, modelo, obligación y número acotado de intento.
- Permitir transiciones `STARTED → RESPONSE_RECEIVED → COMPLETED|FAILED` o `STARTED → UNKNOWN`. Nunca inferir PASS a partir del simple envío o de una respuesta parcial.
- Bloquear silenciosamente la reejecución de una llamada `STARTED`, `RESPONSE_RECEIVED` o `UNKNOWN` tras interrupción. Dejar el estado íntegro para investigación y sucesor autorizado; no borrar el recibo ni emitir un candidato sintético.
- Un fallo completamente observado puede consumir un intento y habilitar otro **solo mediante otra acción humana explícita** dentro del presupuesto. Reutilizar los límites históricos y no ampliar cuotas.
- Verificar que un checkpoint nuevo tenga un recibo de éxito coincidente. Los checkpoints anteriores a R02-09 conservan su legitimidad sin migración destructiva.
- Persistir solo códigos, hashes y estados; **no** guardar prompt, respuesta, contexto, secretos ni credenciales en estos recibos.
- Conservar a cargo del lifecycle previo todos los permissions, review/diff, approval, apply y FROZEN. Los recibos no son otra autoridad de publicación.

## Alternativas rechazadas

- Reintentar automáticamente al caer la conexión: puede duplicar inferencias y candidatos.
- Borrar locks o recibos tras reiniciar: oculta resultados desconocidos y rompe evidencia.
- Modificar Vision/Scope/Requirements FROZEN para ejercitar fallos: vulnera autoridad y no es necesario.

## Validación y limitaciones

Pruebas de fallos de transporte, caída de servidor de prueba durante la solicitud, respuesta inválida, recibos incompletos, doble envío, drift, checksum y ausencia de escrituras al proyecto. El test de servidor cerrado usa `127.0.0.1` sobre proceso de prueba controlado; **no es evidencia de un Ollama real detenido**. Conservar este límite en la evidencia Windows. Future hardening: desarrollar UI específica para diagnóstico de recibos `UNKNOWN` y successor controlado, sin fabricar éxito.
