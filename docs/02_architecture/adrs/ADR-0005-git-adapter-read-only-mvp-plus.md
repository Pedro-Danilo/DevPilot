---
title: "ADR-0005 — Git Adapter read-only en MVP+"
doc_id: "DEVPL-ADR-0005"
status: "accepted"
version: "1.1.0"
owner: "Ordóñez"
standard: "MIPSoftware"
phase: "SPRINT-PRECODE-03"
updated: "2026-06-08"
accepted_by: "Ordóñez"
accepted_at: "2026-06-04"
acceptance_scope: "SPRINT-PRECODE-03 architecture baseline"
---
# ADR-0005 — Git Adapter read-only en MVP+

## Contexto

DevPilot debe operar sobre repos reales. Git es central para trazabilidad, cambios, ramas y commits. Sin embargo, modificar repos automáticamente introduce riesgo.

## Decisión

El primer Git Adapter será read-only. Debe consultar branch, commit, dirty state y diff summary sin modificar el repo. Cualquier acción posterior de commit, branch, patch o reset requerirá policy gate y human approval.

## Consecuencias

- Se obtiene valor de trazabilidad sin riesgo destructivo inicial.
- El futuro patch/refactor flow queda preparado.
- Se evita automatización peligrosa prematura.


## Actualización 2026-06-08 — FUNC-SPRINT-14

Estado de implementación: `implemented-initial`.

Sprint 14 materializa esta ADR con `GitAdapter` y `RepoInventory`:

```text
src/devpilot_core/repo/git_adapter.py
src/devpilot_core/repo/inventory.py
python -m devpilot_core git-status --json
python -m devpilot_core repo-inventory --json
```

La implementación preserva la decisión original: solo lectura, sin comandos de escritura y sin modificación de ramas, commits, staging area ni archivos. `GitAdapter` usa una allowlist cerrada y `subprocess.run` sin shell. `RepoInventory` complementa la visibilidad del repo con clasificación por tipo/tamaño/riesgo y detección de secretos sintéticos sin emitir contenido crudo.

Riesgo residual: no hay análisis semántico de código, SCA/SAST industrial, auditoría de licencias, submódulos, LFS, ramas remotas ni patch review. Es base para `FUNC-SPRINT-15`.


## Actualización FUNC-SPRINT-15

La decisión read-only se extiende con `PatchReviewEngine` y `CodeReviewEngine` en modo dry-run. La implementación permite revisar patches y código sin ejecutar comandos destructivos, sin aplicar cambios y sin escribir fuera de `outputs/reports` cuando se solicita evidencia. Esto mantiene la línea arquitectónica original: cualquier aplicación real de patch, commit, reset, branch, push o refactor automático sigue fuera de alcance y requerirá policy gate, human approval y sandbox controlado.

Riesgo residual: el review es determinístico y preliminar; no sustituye SAST/SCA, linters, análisis semántico, sandbox de aplicación ni aprobación humana persistente.
