---
doc_id: "ADR-FRX-001"
title: "FRX — Git-semantic bounded source guard and end-to-end wall-clock accounting"
status: "accepted"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-09-02"
approval: "corrective-engineering-decision"
---
# ADR-FRX-001 — Git-semantic bounded source guard and end-to-end wall-clock accounting

## Contexto
La única full de FRX-v2.2-D ejecutó 72 shards y alcanzó 100% de accounting, pero el wall-clock observado entre el primer shard y el último fue ~10,28 h. La suma de los procesos pytest fue ~4,60 h. El runner v1.0.3 recalculaba antes y después de cada shard un fingerprint fuerte de todo el worktree y ejecutaba `git hash-object` individualmente para cada archivo. Con ~3.530 archivos, el orden de magnitud es ~508.320 procesos Git para 72 shards.

El cronómetro de `duration_seconds` comenzaba después del fingerprint previo y terminaba antes del fingerprint posterior. Por tanto el benchmark omitía el mayor costo de orquestación y podía declarar mejora de max/p95/CV mientras empeoraba el tiempo end-to-end.

## Decisión
1. El fingerprint fuerte sigue sellándose en el límite de sesión/colección.
2. Entre shards se usa un guard Git-semántico acotado: mismo `HEAD`, sin staged/unstaged/untracked relevantes, ignorando solo runtime explícitamente excluido.
3. La verificación usa Git content semantics; no compara bytes físicos CRLF/LF.
4. Si el guard barato no está disponible o detecta drift, se degrada al fingerprint fuerte para adjudicar con seguridad.
5. Cada receipt registra por separado tiempo de proceso pytest y tiempo de lifecycle/orquestación.
6. El benchmark de adopción incorpora wall-clock end-to-end y ratio de overhead oculto. `PASS/ENABLED` queda prohibido si el tiempo total no mejora o si el overhead oculto excede el umbral.
7. En v2.2, `target_shard_seconds` pasa de 300 s a 900 s como default correctivo para reducir fragmentación secuencial. La capacidad temporal permanece `AVAILABLE-NOT-DEFAULT` hasta evidencia posterior válida.

## Consecuencias
- Se elimina el patrón O(shards × files) de procesos Git del hot path.
- Se conserva detección de source mutation con semántica Git.
- Los receipts antiguos siguen siendo legibles; los campos nuevos son opcionales en schema.
- v2.3 no puede usar el benchmark v2.2 anterior como baseline de velocidad sin la corrección analítica de wall-clock.

## PASS/BLOCK
PASS: mismo HEAD, worktree Git-semánticamente limpio, 0 source drift, instrumentación de lifecycle disponible en ejecuciones nuevas y benchmark end-to-end calculable.  
BLOCK: hash físico LF/CRLF como guard, `git hash-object` por archivo en cada shard, métricas que excluyan el tiempo de orquestación o adopción default basada solo en max/p95/CV.

## Riesgos
El guard barato depende de que la sesión se selle desde un worktree limpio. Si esa precondición no se cumple, el runner debe usar el fingerprint fuerte; nunca asumir equivalencia.
