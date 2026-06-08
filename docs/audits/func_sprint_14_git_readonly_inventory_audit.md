---
title: "FUNC-SPRINT-14 — Git read-only y repo inventory MVP+"
doc_id: "DEVPL-AUDIT-FUNC-SPRINT-14"
status: "implemented-initial"
version: "1.0.0"
owner: "Ordóñez"
standard: "MIPSoftware"
extension: "MIASI"
updated: "2026-06-08"
---
# FUNC-SPRINT-14 — Git read-only y repo inventory MVP+

## Propósito

Implementar visibilidad segura de repositorios mediante Git read-only e inventario local del workspace, sin modificar archivos, staging area, ramas, commits ni historial.

## Componentes implementados

```text
src/devpilot_core/repo/__init__.py
src/devpilot_core/repo/git_adapter.py
src/devpilot_core/repo/inventory.py
tests/test_repo_tools.py
```

## Integración

Los nuevos comandos se integran en `src/devpilot_core/cli.py`:

```powershell
python -m devpilot_core git-status --json
python -m devpilot_core git-status --json --write-report
python -m devpilot_core repo-inventory --json
python -m devpilot_core repo-inventory --json --write-report
```

Los resultados mantienen el contrato `CommandResult`, emiten eventos JSONL, pueden generar reportes JSON/Markdown y se persisten en SQLite de forma best-effort.

## Criterios PASS

```text
pytest -q pasa.
GitAdapter solo ejecuta comandos Git allowlisted de lectura.
git-status no modifica el estado antes/después.
repo-inventory no sale del workspace.
repo-inventory detecta secretos sintéticos sin emitir valores crudos.
README y runbook quedan sincronizados.
Tool Registry refleja git.status, git.diff y repo.inventory como implemented.
```

## Criterios BLOCK

```text
git add/commit/checkout/reset/merge/rebase/tag/push.
shell=True o comandos Git no allowlisted.
Lectura fuera del workspace.
Fuga de secreto crudo.
Reportes fuera de outputs/reports.
```

## Pruebas

`tests/test_repo_tools.py` cubre:

- repositorio Git temporal con cambios modificados/no rastreados;
- invariancia de `git status --short` antes/después del adapter;
- workspace sin Git;
- inventario con secreto sintético;
- CLI `git-status`;
- CLI `repo-inventory`.

## Riesgos

Primera versión. No cubre submódulos, LFS, ramas remotas, SCA/SAST, licencias, vulnerabilidades, secret scanning por entropía ni revisión semántica de código.

## ADR

No se abrió una ADR nueva. Se actualizó `ADR-0005 — Git Adapter read-only en MVP+`, ya existente y aceptada para esta decisión arquitectónica.
