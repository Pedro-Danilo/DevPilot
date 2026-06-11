---
title: "Auditoría FUNC-SPRINT-35 — GitAdapter v2 read-only"
doc_id: "DEVPL-AUDIT-FUNC-SPRINT-35-001"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-06-11"
approval: "approved_by_owner_direction"
---

# Auditoría FUNC-SPRINT-35 — GitAdapter v2 read-only

## 1. Propósito

Registrar la implementación de `FUNC-SPRINT-35 — GitAdapter v2 read-only: ramas, tags, log y diff-report` como primer sprint de Fase C.

## 2. Estado

Implementado en estado `implemented-initial`. La capacidad es local-first, read-only y no habilita operaciones destructivas.

## 3. Funcionamiento técnico

`GitAdapter` amplía su allowlist con comandos seguros para leer ramas, tags, commits recientes y diferencias estructuradas. Los comandos se ejecutan con `subprocess.run` usando lista de argumentos y `shell=False`.

La ejecución se limita a:

- `git branch --all --format=...`;
- `git tag --list --format=...`;
- `git log --date=iso-strict --pretty=... -n <limit>` con límite validado;
- `git diff --name-status`;
- `git diff --numstat`;
- `git diff --cached --name-status`;
- `git diff --cached --numstat`;
- `git status --short` para detectar untracked.

## 4. Integración con DevPilot

Los nuevos comandos CLI son:

```powershell
python -m devpilot_core git branches --json
python -m devpilot_core git tags --json
python -m devpilot_core git log --limit 20 --json
python -m devpilot_core git diff-report --json --write-report
```

Todos devuelven `CommandResult`, soportan `--json`, y `diff-report` soporta `--write-report` mediante `ReportEngine`.

## 5. Rol dentro de DevPilot

Esta capacidad habilita FC-L0 de Fase C: Git read-only ampliado. Es insumo para DependencyGraph, RepoAnalyzer, drift, review rule packs y quality gates posteriores.

## 6. Criterios PASS

- Branches, tags y log se consultan sin modificar el repositorio.
- `git diff-report` reporta archivos, tipo de cambio, scope, inserciones, eliminaciones y riesgo básico.
- Comandos Git write quedan bloqueados por allowlist.
- Repositorios no Git devuelven resultado controlado, no crash.
- MIASI declara las nuevas tools read-only.
- `pytest -q` pasa.

## 7. Criterios BLOCK

- Cualquier comando usa `shell=True`.
- Se permite `git add`, `git commit`, `git checkout`, `git reset`, `git push`, merge o rebase.
- Un repositorio no Git provoca excepción no controlada.
- La documentación presenta la capacidad como sandbox, patch apply o Git write.

## 8. Riesgos

- `diff-report` es heurístico y no sustituye revisión manual, SAST/SCA ni secret scanning industrial.
- Repositorios con muchos cambios pueden requerir límites más sofisticados.
- No se inspeccionan remotos, firmas, submódulos, LFS ni integridad profunda del repositorio.

## 9. Veredicto

`FUNC-SPRINT-35` queda implementado como GitAdapter v2 read-only inicial y listo para alimentar `FUNC-SPRINT-36 — DependencyGraph e import graph Python`.
