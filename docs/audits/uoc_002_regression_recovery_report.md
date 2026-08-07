---
doc_id: "DEVPL-UOC-002-REGRESSION-RECOVERY-REPORT"
title: "UOC-002 — Recuperación de regresión general v1.0.1"
status: "implemented-pending-windows-selective-verification"
version: "1.0.3"
owner: "Ordóñez"
updated: "2026-08-06"
approval: "pending_operator_verification"
---

# UOC-002 — Recuperación de regresión general v1.0.1

## Resultado observado

La regresión Windows ejecutó 2045 pruebas: 1987 PASS y 58 FAIL, sin errores ni skips.
Los 58 fallos se agrupan en cuatro causas acotadas: estado `current_repo` no reconciliado con Evidence Freshness; conteos históricos de rutas congelados; contratos UOC-000 que no admitían evolución read-only posterior; y pruebas que confundían dependencias locales ignoradas (`node_modules`) con artefactos versionados.

## Decisión correctiva

No se relajan políticas, PathGuard, IDs opacos, GitAdapter ni zero-write. Se corrigen contratos acumulativos, schemas de ciclo de vida y metadata histórica. La evidencia 1987 PASS se conserva. La verificación de recuperación usa una suite selectiva que cubre los 58 nodos por causa raíz y ejecuta una sola vez los gates compuestos costosos.

## Criterios PASS

- Evidence Freshness y Local Release Candidate PASS.
- API/UI route registries sin drift y con conteos dinámicos.
- UOC-000 preservado como baseline histórico y UOC-001/UOC-002 habilitados de forma read-only.
- Visual Product Smoke PASS con lineage POST-H y política de exclusión de artefactos runtime.
- Quality Gate hardening PASS.
- ReleaseAgent y AgentSession PASS.
- S0=0 y S1=0.

## Limitación

La suite general completa no se repite si la suite selectiva autoritativa pasa y no existe cambio fuera del patch v1.0.1. Cualquier fallo selectivo, hash inesperado o cambio adicional vuelve a exigir adjudicación.


## Correctivo v1.0.2 — aislamiento del índice RAG

El dry-run v1.0.1 detectó correctamente `.devpilot/rag/docs_index.json` como cambio no reconocido. La causa es el contrato heredado `test_rag_cli_index_and_query_json`, que ejecutaba el comando mutante `rag index` sobre `Path.cwd()`; durante `pytest -q`, ese directorio era el checkout real. v1.0.2 mueve la prueba a un workspace temporal, reconstruye en memoria el índice mediante el `LocalRagIndexer`, `PathGuard` y `SecretGuard` reales, compara todo el contenido salvo el timestamp y restaura el blob exacto de `HEAD` antes de aplicar el payload. Un índice alterado manualmente, staged o semánticamente distinto continúa produciendo `BLOCK`.

## Correctivo v1.0.3 — preflight portable LF/CRLF

El dry-run v1.0.2 bloqueó sobre `.devpilot/release/local_release_candidate_criteria.json` porque comparó el hash binario LF del blob Git con los bytes CRLF materializados por el checkout Windows. El contenido JSON era idéntico. v1.0.3 incluye las 42 preimágenes de v1.0.0 y permite únicamente equivalencia UTF-8 de finales de línea LF/CRLF; cualquier otra diferencia continúa bloqueando. La decisión queda registrada por archivo en el reporte de preflight.

## Correctivo v1.0.4 — identidad estable y reanudación selectiva

La ejecución Windows v1.0.3 aplicó correctamente 38 archivos, restauró el índice RAG y superó el caso `rag_cli_runtime_isolation` (`5/5`). El caso siguiente produjo `96 passed / 1 failed`: el Source Registry declaraba `POST-H-EVAL-002-UOC-002-REGRESSION-RECOVERY-v1.0.3`, mientras el contrato histórico/acumulativo exige un identificador de sprint estable. v1.0.4 fija `UOC-002-REGRESSION-RECOVERY`, añade un contrato explícito que evita reincidencia y reemplaza el abort sin reporte por un reporte parcial durable. La verificación se reanuda desde `state_history_and_freshness`; el PASS RAG anterior se reutiliza mediante hash y contenido de log.


## Correctivo v1.0.5 — reconciliación Git-native del índice RAG

La ejecución Windows v1.0.4 no aplicó archivos. Su dry-run bloqueó porque el contrato `EXPECTED_V103_APPLIED_WORKTREE` incluía los 71 archivos del payload v1.0.3 pero no la ruta versionada `.devpilot/rag/docs_index.json`, que Git seguía reportando como modificada después de la verificación selectiva. El operador anterior verificaba estabilidad de SHA, pero no limpieza del índice/worktree. v1.0.5 trata esa ruta como estado conocido sujeto a validación estricta: equivalencia con `HEAD` —exacta o únicamente LF/CRLF— o reconstrucción canónica completa con el indexador real. En execute realiza backup, `git restore --source=HEAD --worktree`, refresh del índice, verificación de diff/status limpio y rollback automático si cualquier escritura posterior falla. El runner reanudado verifica hash y limpieza Git antes y después de cada caso.

## Continuación de cierre v1.0.6

La continuación corrige la comparación literal `D:/...` frente a `D:\...` mediante equivalencia `samefile/resolved-path`, mantiene la identidad estable `UOC-002-REGRESSION-RECOVERY` mientras el sprint está abierto y autoriza `UOC-002-CLOSURE` únicamente después del cierre documental. También reemplaza la interfaz defectuosa del empaquetador por un contrato `git archive` con branch, commit, tracking y remote exactos.
