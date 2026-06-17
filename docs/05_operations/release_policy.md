---
title: "Política de release y versionado — DevPilot Local"
doc_id: "DEVPL-OPS-RELEASE-POLICY-001"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
standard: "MIPSoftware"
extension: "MIASI"
phase: "FUNC-SPRINT-74"
updated: "2026-06-17"
source_repo: "repo_DevPilot_Local_95.zip"
source_adr: "docs/02_architecture/adrs/ADR-0014-release-versioning-packaging.md"
change_policy: "controlled_changes_allowed_via_docs_as_code"
approval: "approved_by_func_sprint_74"
---

# Política de release y versionado — DevPilot Local

## 0. Estado

`approved` como primera versión de política operacional de release para Fase G.

Esta política es **preliminar e industrializable**. Define reglas, criterios y límites; no implementa todavía comandos automáticos de build, publicación, SBOM, checksums o installer. Esos mecanismos se desarrollan progresivamente en los sprints 75-84.

## 1. Propósito

Definir cómo DevPilot local-first debe versionarse, prepararse, verificarse y declararse liberable sin introducir publicación externa prematura, secretos, runtime state ni artefactos no reproducibles.

## 2. Principios

1. **Local-first**: todo release debe poder prepararse y verificarse localmente sin red externa obligatoria.
2. **Dry-run-first**: comandos de release, backup, upgrade o agente deben tener dry-run cuando puedan modificar artefactos.
3. **Evidence-driven**: ningún release es válido sin pruebas, gates, manifest, changelog y verificación documentada.
4. **Clean package**: el release no incluye estado runtime, caches, outputs, `.venv`, `.git`, `node_modules` ni secretos.
5. **No publish by default**: publicar en PyPI, GitHub Releases, GitLab Releases, contenedores o instaladores públicos requiere ADR posterior y aprobación humana.
6. **Docs-as-code**: README, runbook, backlog, ADR, manifest y auditoría deben evolucionar junto con el código.

## 3. Modelo de versionado

DevPilot adopta SemVer interno con formato:

```text
MAJOR.MINOR.PATCH[-pre-release]
```

### 3.1 Regla para línea 0.y.z

Mientras DevPilot esté en madurez de MVP/productización temprana:

- `0.MINOR.PATCH` representa versiones internas no garantizadas para compatibilidad pública estable.
- `MINOR` aumenta cuando se cierra una fase funcional o se habilita una capacidad mayor de producto.
- `PATCH` aumenta por correcciones, ajustes documentales, limpieza de packaging o mejoras compatibles.

### 3.2 Regla para 1.0.0 futuro

Solo se podrá declarar `1.0.0` cuando existan, como mínimo:

- release package reproducible;
- quality gate en PASS;
- manifest de release;
- changelog;
- SBOM baseline;
- checksums;
- smoke test de instalación;
- documentación de instalación/upgrade;
- política clara de compatibilidad;
- ausencia de runtime state en paquetes.

### 3.3 Fuente de verdad de versión

Durante Sprint 74:

- `pyproject.toml` sigue como fuente técnica de versión del paquete Python.
- `docs/functional_sprint_XX_manifest.json` describe avance funcional, no versión liberable.
- El release manifest formal se implementará en Sprint 77.

## 4. Estados de release

| Estado | Significado | Puede distribuirse |
|---|---|---|
| `development` | Repo activo de trabajo. | No como release. |
| `candidate-local` | Candidato local con gates previos. | Solo interno. |
| `verified-local` | Artefactos locales verificados. | Sí, distribución interna controlada. |
| `blocked` | Falla gate, paquete o evidencia. | No. |
| `published-external` | Publicado fuera del entorno local. | Fuera de Fase G inicial. |

## 5. Reglas para declarar un release liberable

Un release local solo puede pasar a `verified-local` si existe evidencia de:

1. `pytest -q` en PASS;
2. quality gate local en PASS;
3. release manifest generado;
4. changelog legible;
5. package limpio;
6. SBOM o inventario baseline;
7. checksums SHA256;
8. smoke test de instalación/ejecución;
9. runbook actualizado;
10. auditoría de release.

## 6. Publicación externa

Queda explícitamente fuera de alcance de Sprint 74 y de la Fase G inicial:

- PyPI;
- GitHub Releases;
- GitLab Releases;
- Docker Hub u otros registries;
- instaladores firmados públicos;
- auto-update remoto;
- despliegues cloud.

Cualquier publicación externa futura requiere:

- ADR específica;
- threat model de publicación;
- gestión de secretos;
- revisión de supply-chain;
- aprobación humana;
- evidencia de rollback.

## 7. Política de exclusión

Todo package de release debe excluir:

| Patrón | Motivo | Severidad si aparece en release |
|---|---|---|
| `outputs/` | Evidencia runtime regenerable. | BLOCK |
| `.pytest_cache/` | Cache de pruebas. | BLOCK |
| `__pycache__/` | Cache Python. | BLOCK |
| `*.pyc` | Bytecode generado. | BLOCK |
| `.venv/` | Entorno local no portable. | BLOCK |
| `.git/` | Metadata VCS no requerida en package. | BLOCK |
| `node_modules/` | Dependencias runtime frontend no versionables. | BLOCK |
| `ui/web/dist/` | Build frontend generado. | BLOCK salvo package específico futuro. |
| `.devpilot/devpilot.db` | Estado runtime local. | BLOCK |
| `.env` | Secretos/config local. | BLOCK |
| logs runtime | Evidencia local no release. | BLOCK |

## 8. Relación con changelog, manifest y SBOM

- El **changelog** explica cambios notables para humanos.
- El **release manifest** lista versión, artefactos, comandos, checks, hashes y referencias.
- El **SBOM** declara componentes y dependencias.
- Los **checksums** verifican integridad de artefactos.
- Los **manifests de sprint** documentan implementación funcional acumulativa.

Ninguno de estos artefactos reemplaza a los demás.

## 9. Comandos previstos por fase posterior

Estos comandos no se implementan en Sprint 74, pero quedan definidos como dirección:

```powershell
python -m devpilot_core quality-gate run --json
python -m devpilot_core release manifest --version 0.1.0 --json
python -m devpilot_core release changelog --version 0.1.0 --json
python -m devpilot_core package build --kind repo-zip --version 0.1.0 --json
python -m devpilot_core release sbom --json
python -m devpilot_core release verify --artifact dist/devpilot.zip --json
```

## 10. Criterios PASS

- Política define versión interna y estados de release.
- Publicación externa queda bloqueada por defecto.
- Exclusiones de package están explícitas.
- Distingue sprint manifest, release manifest, changelog, SBOM y checksums.
- Declara límites de primera versión.

## 11. Criterios BLOCK

- Declarar release sin quality gate.
- Distribuir paquetes con outputs, caches, `.venv`, `.git`, `node_modules`, `.devpilot/devpilot.db` o secretos.
- Publicar externamente sin ADR posterior.
- Usar auto-update silencioso.
- Confundir repo de trabajo con release verificado.

## 12. Riesgos

| ID | Riesgo | Mitigación |
|---|---|---|
| RISK-REL-001 | Incrementos de versión arbitrarios. | Regla SemVer interna y ReleaseManifest futuro. |
| RISK-REL-002 | Package contaminado. | Exclusion policy y PackageBuilder en Sprint 79. |
| RISK-REL-003 | Falso release industrial. | Estado `candidate-local`/`verified-local` y límites documentados. |
| RISK-REL-004 | Secretos en artefactos. | SecretGuard, exclusiones y revisión de supply-chain. |
