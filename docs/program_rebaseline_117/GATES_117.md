---
doc_id: "DEVPL-REB-117-GATES"
title: "Criterios de gate, adjudicación y evidencia P0–P3"
version: "1.0.0"
status: "APPROVED / EXECUTION-GATED"
date: "2026-10-11"
owner_decision: "OWNER-APPROVAL-2026-10-11-REBASELINE-116"
implementation_authority: false
multiprovider_stop_lifted: false
---

# Criterios de gate, adjudicación y evidencia P0–P3

## Semántica de estados
- `G0 APPROVED`: decisión estratégica tomada (hecho actual).
- `G1 APPROVED/PUBLISHED`: ambos programas poseen successors registrables, publicados y coherentes. **NO basta este ZIP**.
- `D05 REBASELINED_STOP/PARTIAL_ACCEPTANCE`: cierre delimitado, NO `MVP PASS` y NO story RF004 DONE.
- `D06 REBASELINED/PASS`: seis escenarios calificados con fuente de estado válida.
- `PRE_SYNC_AUDIT_PASS`: inventario dual y reutilización fundamentada.
- `SYNC_PLAN_APPROVED`: aprobación Owner explícita posterior a auditoría; no inferible de G0.
- `SYNC1/PASS`: operación Git real, validaciones, autoridad MP publicada.
- `MP_RESUME_ELIGIBLE`: estado posterior a SYNC1/PASS, además requiere successor roadmap/programa MP que reautorice MP-1B. No ejecutar MP prematuramente.

## Matriz fail-closed
| Control | PASS requiere | BLOCK si |
|---|---|---|
| G1 | docs bridge Greenfield+MP, ADR successor, STOP, índice externo verificable, Source Registry determinístico actualizado y MP registry diferido a P3-C, tests/document authority PASS | docs históricas siguen activas en conflicto o MP sale de STOP |
| G2 | RF001..003 DONE autenticados; RF004..008 NOT IMPLEMENTED; snapshot y evidencias; no mutable work | omisión, cierre ficticio, fuente distinta, story activa sin adjudicación |
| G3 | 6 escenarios separados con pre/post, resultados y logs | pérdida, bypass, acción destructiva, conflicto sin resolver |
| G4a | auditoría **de ambas ramas** y capacidades concretas; health, security, docs, tests, git delta | datos faltantes, inferencia por nombre, HEAD no confirmado |
| G4b | matriz de opciones, plan de merge+tratamiento de conflictos, pruebas/rollback y approval Owner | merge directo por inercia, duplicación de routers, aprobación no trazable |
| G5 | one-way merge condicionado a plan, parity, impacto, docs y Git promoted, clean snapshot ZIP | conflict unresolved, tests FAIL, target MP no lineage, STOP premature |

## Evidencia mínima cada run
Fecha UTC+local, phase/run/owner, HEAD/tree/upstream/remote de ambos tracks cuando aplique, identidad Pilot A, inputs/hashes, first-attempt inmutable, resultado PASS/BLOCK y causa, ids de receipts/approval, cambios exactos, jobs/test logs, `operator_project_writes`, conteo Full, estados persistidos antes/después, UI únicamente para verificación de estados decisivos, hallazgos ledger+disposition, artifacts con hash, firma Owner donde sea de decisión. Los logs de consola TXT sustituyen capturas redundantes de consola.

## Seguridad
- Nunca autorizar source/file mutación basándose en el hecho de poseer un ZIP o este programa.
- STOP MP conservado en P0/P1/P2/P3-A/P3-B; P3-C lo levanta solo tras SYNC1/PASS y autorización posterior.
- Trabajo experimental de conflictos en copias/worktrees aislados, no en pilot source.
- No reset-hard/clean destructivo/rebase de commits sellados/push forzado. Cambios finales Git vía autorización humana y comprobación de hash/path; revertible mediante plan aprobado y evidence.
- Probar sin comparar bytes de LF/CRLF cuando contrato es equivalencia semántica de Git; sí verificar hashes crudos donde hashes forman autoridad contractual.

## Reglas Full Regression
Misma política del backlog transversal: 0 durante micro-sprints no finales; cierre único P3-C si autorizada por el plan de impacto aprobado, con un solo receipt persistido y sin duplicación; excepciones estrictamente aprobadas por riesgo. La D06 revisada NO ejecuta full.
