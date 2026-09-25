---
doc_id: "SPRINT-DEVPL-GSDLC-13-C-01-DRAFT-FIRST-SEMANTIC-REVIEW-CORRECTIVE"
title: "DEVPL-GSDLC-13-C-01 — Sprint bounded corrective Draft-first + Decision Inbox"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-09-25"
source_authority: "repo443 / 7a5afa2c28fc30240ee6e347dde345231134384a"
target_successor: "repo444"
checkpoint: "13-C-01"
source_retest: "13-C-01-retest-03"
full_regression_runs: 0
---

# Sprint bounded corrective — Draft-first + Decision Inbox

## Objetivo

Implementar el corrective aprobado `DEVPL_GSDLC_13_C_01_DRAFT_FIRST_SEMANTIC_REVIEW_CORRECTIVE_PROJECTION_v1_0_0_APPROVED.md` sin ampliar el alcance fuera de `13-C-01`.

## Authority

- baseline obligatorio: repo443 `7a5afa2c28fc30240ee6e347dde345231134384a`;
- branch: `official/devpilot-local`;
- successor Windows candidate: repo444;
- Greenfield de acceptance no debe recibir writes del operador;
- `13-C-01-retest-03` se conserva como evidencia BLOCK y no se reutiliza como PASS.

## Work packages

### WP-A — Draft-first orchestration

- conservar `PreCode Semantic Model v1` como representación interna;
- primer `DEVPL_MOCK` produce DRAFT completo;
- Vision/Scope no quedan bloqueados por decisiones que pertenecen a Requirements;
- no exponer microconfirmación semántica como gate normal.

### WP-B — Decision Inbox

- mostrar únicamente decisiones necesarias para la etapa actual;
- agrupar/filtrar preguntas;
- Semantic Model completo permanece disponible solo como detalle avanzado;
- filas opcionales vacías no entran como items inválidos.

### WP-C — Owner edit + API/UX errors

- editar DRAFT manteniendo `DEVPL_MOCK` y provenance;
- edición invalida plan/diff/approval anterior;
- `403` reservado a autorización;
- contenido semántico inválido usa contrato accionable (`422` o equivalente coherente);
- mensajes deben apuntar a la corrección necesaria.

### WP-D — pruebas + Windows validation

- selective pytest afectados;
- UI static smokes;
- Vite build;
- source delta exacto;
- candidate repo444;
- `Full Regression=0`.

## PASS criteria

El sprint cierra únicamente si:

1. DRAFT completo aparece antes de cualquier detalle semántico avanzado.
2. Semantic Model sigue persistente, trazable y resume-aware.
3. flujo normal no exige revisar semantic items uno a uno.
4. Decision Inbox contiene solo decisiones relevantes para la etapa actual.
5. Product Vision/Scope no quedan bloqueados por detalle requerido solo en Requirements.
6. Owner puede editar DRAFT sin cambiar a `MANUAL`.
7. provenance conserva `origin_mode=DEVPL_MOCK` y hashes de generación/edición.
8. editar DRAFT invalida plan/diff previo.
9. fila opcional vacía no bloquea el request.
10. error semántico normal no produce 403.
11. 401/403 de auth/RBAC conservan su semántica.
12. semantic quality gates continúan bloqueando artefactos realmente inválidos.
13. C-02 permanece sin cambios.
14. network/external API requeridos = false/false.
15. operator project writes = 0.
16. Greenfield source y runtime de `retest-03` se preservan durante el corrective.
17. selective pytest = PASS sin FAIL/ERROR/SKIP inesperados.
18. UI smokes = PASS.
19. Vite build Windows = PASS.
20. Full Regression = 0.
21. source delta y packaging = exactos.
22. promoción Git final queda local=origin y worktree limpio.

## Regression Execution Policy

No ejecutar Full Regression. Un fallo en tests afectados debe adjudicarse como defecto focal y detener packaging/promoción. No ampliar suite por rutina histórica.

## Stop condition

Si la implementación exige cambiar lifecycle/approval global, Project Context incompatible, introducir LLM obligatorio, tocar C-02 o migrar documentos históricos, detener y replanificar en vez de ampliar silenciosamente este sprint.
