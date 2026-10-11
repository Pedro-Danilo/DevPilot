---
doc_id: "DEVPL-REB-117-AUTH"
title: "Autoridad documental, precedencia y supersession P0–P3"
version: "1.0.0"
status: "APPROVED / EXECUTION-GATED"
date: "2026-10-11"
owner_decision: "OWNER-APPROVAL-2026-10-11-REBASELINE-116"
implementation_authority: false
multiprovider_stop_lifted: false
---

# Autoridad documental, precedencia y supersession P0–P3

## Decisión y jerarquía
1. `PROPUESTA_REBASELINE_116_APPROVED.md` es la decisión estratégica G0 aprobada; `PROPUESTA_116_ORIGINAL.md` es la evidencia inmutable de la propuesta.
2. Este paquete 117 es **programación aprobada para ejecución condicionada**, no su aplicación en repositorios. Requiere P0: índice puente externo canónico, Source Registry determinístico reconciliado y MP registry diferido hasta P3-C. Un documento ZIP aprobado no reemplaza silenciosamente una autoridad registrada en Git.
3. Contratos antiguos D05 «repeat until MVP», D07/D08 «release Pilot A» y STOP que exige D05 MVP permanecen como **históricos aplicables a ejecuciones previas**. Sus cláusulas prospectivas se sustituyen **solamente** cuando P0 publica successors registrables en ambos tracks y G1 acredita paridad documental.
4. Orden de precedencia después de G1: decisiones programáticas G0+bridge documental 117 → protocolo P0–P3 registrado → planes de sprint/prompt condicionados → contratos históricos solo para trazar hechos antiguos. Seguridad, permisos, PathGuard, gobernanza Git y evidencias no son excepcionados.
5. `MP-1B` **no está habilitado**; la rama MP permanece congelada hasta SYNC-1 PASS y posterior decisión de replanificación.

## Autoridades de entrada declaradas, sujetas a preflight de Git
- Determinístico plataforma: `official/devpilot-local` commit `e5ed25922aa3fb7b1fc7ed9f738ff1ca8a666218` (repo465), snapshot SHA256 `551645013120d93081e36d777fe19581e21ed0a302c37245d6ed1ceabe50b9e4`.
- Pilot A: `inventory-sales-local-greenfield` commit `0f5f1518f3f76034c1367fe60d637c6d69fa78f8` (RF003 DONE).
- Multiprovider STOP: `evolution/multiprovider-v2` commit reportado `54085701f39670ec460a80a6b3f9097a9e61a3d1`; su HEAD, upstream, remote y tree **se deben confirmar al entrar en P3**; el STOP original conserva referencias más antiguas, no son HEAD efectivos.
- `outputs/` no versionado en Pilot A: conservar, no limpiar ni incorporar automáticamente.

## Mecanismo obligatorio de publicación P0
- Archivar paquetes originales y decisiones previas; no editar FROZEN, evidencia histórica ni commits.
- Registrar sucesores y exactos doc_id/path/versión/lifecycle/supersedes en authority index y Source Registry apropiados; verificar fuentes canónicas antes de escribir.
- Publicar un *bridge limitado* de Greenfield (D05/D06, salida D07/D08 y 13-E), MP STOP/SYNC y ADR de transición. No introducir aquí un v2.2 Multiprovider completo.
- Asegurar que todas las Run Cards vigentes apuntan a successors sin referencias activas contradictorias. Controles derivados de docs ejecutados en fase de validación P0.
- Cualquier repo modificado en P0 requiere Git gobernado, HEAD limpio/promovido, ZIP completo `git archive HEAD` y `.sha256` verificados. No sustituirlos por un ZIP de documentos.

## Condiciones terminales
`G1 PASS`: fuente canónica establecida y successor registrado en **ambos** programas, docs/tests PASS, Git limpio/remote parity y receipts; `G1 BLOCK`: paquete en chat aprobado pero no publicado, Source Registry stale, contradicciones activas o STOP flexibilizado prematuramente.
