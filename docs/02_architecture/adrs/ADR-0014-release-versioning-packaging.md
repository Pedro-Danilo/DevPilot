---
title: "ADR-0014 — Release, versionado y productización"
doc_id: "DEVPL-ADR-0014"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
standard: "MIPSoftware"
extension: "MIASI"
phase: "FUNC-SPRINT-74"
updated: "2026-06-17"
source_repo: "repo_DevPilot_Local_95.zip"
source_backlog: "docs/devpilot_backlog_fase_G_productizacion_release.md"
decision_scope: "phase_g_release_versioning_packaging_productization"
change_policy: "controlled_changes_allowed_via_docs_as_code"
approval: "approved_by_func_sprint_74"
operationalized_by: "FUNC-SPRINT-74"
---

# ADR-0014 — Release, versionado y productización

## Estado

`approved` y operacionalizada por `FUNC-SPRINT-74 — ADR de release, versionado y productización`.

Esta ADR es una **decisión arquitectónica de primera versión**. No implementa todavía comandos de build, publicación, `quality-gate`, SBOM, checksums ni installer. Su función es fijar la estrategia que deben respetar los sprints 75-84 antes de automatizar release.

## Contexto

DevPilot Local llega a Fase G después de cerrar Fase F con Web UI local MVP, API local segura y `ApplicationService v2`. El informe de avance Sprint 0-18 ya identificaba como brechas la falta de CI/CD local, release manifest, packaging formal, changelog automático, tagging, rollback release y operación industrial. La Fase F resolvió la experiencia visual local, pero no convirtió el repositorio en un producto distribuible.

El backlog Fase G define el objetivo de pasar desde un repositorio funcional con pruebas y comandos manuales hacia un release reproducible, con quality gate, paquete limpio, manifiesto, SBOM, checksums, smoke tests, instalación y estrategia de actualización.

La decisión debe proteger principios ya consolidados:

- local-first;
- dry-run-first;
- policy-first;
- no publicación externa por defecto;
- no despliegue remoto por defecto;
- evidencia reproducible;
- exclusión de estado runtime, caches y secretos;
- trazabilidad entre sprint, manifest, changelog, package y verificación.

## Decisión

DevPilot adopta una estrategia de release **local-first, staged y evidence-driven**:

```text
source repo limpio
  -> quality gate local
  -> version metadata
  -> release manifest
  -> changelog
  -> package build local
  -> SBOM/checksums
  -> smoke test de release
  -> release report
  -> ReleaseAgent dry-run
```

### Decisiones vinculantes

1. **Versionado interno**: DevPilot usará SemVer interno. Mientras siga en madurez MVP/productización temprana, se mantiene dentro de `0.y.z`. El primer release liberable local de Fase G será de línea `0.1.x`, salvo ADR posterior.
2. **Fuente de verdad de versión**: `pyproject.toml` sigue siendo la fuente técnica de versión del paquete Python hasta que Sprint 77 introduzca metadata formal de release. Los manifests de sprint documentan estado funcional, no sustituyen el versionado de producto.
3. **Release interno por defecto**: el tipo de release permitido por Fase G es release local interno. Publicación pública en PyPI, GitHub Releases, GitLab Releases, contenedores o instaladores firmados queda fuera de alcance hasta ADR posterior.
4. **Artefactos liberables**: la estrategia contempla cuatro familias: ZIP limpio del repo, wheel/sdist Python, manifest/changelog/evidencia y artefactos de verificación como SBOM/checksums. Sprint 74 solo define la matriz; sprints posteriores automatizan.
5. **Paquete limpio obligatorio**: todo release package debe excluir `outputs/`, `.pytest_cache/`, `__pycache__/`, `.venv/`, `.git/`, `node_modules/`, `.devpilot/devpilot.db`, logs runtime, archivos `.pyc` y secretos locales.
6. **No runtime state en release**: `.devpilot/project.yaml` y `.devpilot/providers.yaml.example` pueden ser parte del source package si no contienen secretos; `.devpilot/devpilot.db` y outputs generados no forman parte del release source.
7. **Quality gate antes de package**: ningún package debe considerarse liberable sin evidencia de `pytest`, validadores documentales, schema/manifest validation y checks específicos de release.
8. **SBOM/checksums**: SBOM y checksums serán obligatorios antes de declarar una versión release-ready al cierre de Fase G. Sprint 74 solo fija la obligación.
9. **Installer y Desktop**: desktop installer se mantiene como estrategia futura documentada, no como entregable de Sprint 74. Cualquier installer real requiere threat model y smoke test propio.
10. **ReleaseAgent**: el asistente de release solo podrá operar en dry-run durante Fase G. No podrá publicar, etiquetar ni desplegar sin aprobación humana y ADR posterior.

## Alternativas consideradas

| Alternativa | Evaluación | Veredicto |
|---|---|---|
| ZIP manual ad hoc | Fácil de producir, pero no es reproducible ni auditable y puede incluir runtime artifacts. | Descartada como estrategia final; solo aceptable como intercambio temporal fuera de release. |
| ZIP limpio gobernado | Alinea local-first, facilita distribución interna y permite exclusiones verificables. | Seleccionada como artefacto base. |
| Wheel/sdist Python | Alinea instalación local y packaging estándar de Python. Requiere controles de build en sprints posteriores. | Seleccionada como artefacto Python objetivo. |
| Publicación PyPI | Útil para distribución pública, pero exige supply-chain, credenciales, ownership, seguridad y soporte. | Diferida fuera de Fase G inicial. |
| GitHub/GitLab Releases | Útil cuando exista CI/CD maduro, pero implica publicación remota. | Diferida; solo scaffolding CI dry-run en Sprint 76. |
| Desktop installer | Valioso para UX final, pero aumenta complejidad de permisos, actualización y firma. | Documentar estrategia; no implementar en Sprint 74. |
| Contenedor Docker | Puede ayudar a reproducibilidad, pero no es el canal primario local-first Windows actual. | Diferido. |

## Consecuencias

### Positivas

- Evita ambigüedad entre sprint cerrado, repo fuente y release distribuible.
- Convierte Fase G en una secuencia segura: primero decisión, luego gates, metadata, packaging y verificación.
- Reduce riesgo de publicar secretos o estado runtime.
- Mantiene compatibilidad con CLI, API local y Web UI local.
- Permite evidencia reproducible para usuarios y auditoría.

### Costos y límites

- Sprint 74 no entrega comandos de release ni paquetes instalables.
- El versionado queda definido pero no automatizado hasta Sprint 77/79.
- Publicación externa sigue bloqueada.
- SBOM/checksums quedan definidos como obligación futura, no implementados todavía.
- El Desktop installer continúa fuera del alcance inmediato.

## Modelo de release objetivo

```text
Repo de desarrollo
  -> QualityGate local
  -> ReleaseManifest
  -> Changelog
  -> PackageBuilder
  -> SBOM + checksums
  -> ReleaseSmokeTest
  -> ReleaseReport
```

## Reglas de exclusión

Los sprints de packaging y verificación deben tratar como BLOCK cualquier artefacto de release que incluya:

- `outputs/`;
- `.pytest_cache/`;
- `__pycache__/`;
- `.venv/`;
- `.git/`;
- `node_modules/`;
- `ui/web/dist/`;
- `.devpilot/devpilot.db`;
- `.pyc`;
- logs runtime;
- credenciales, tokens, API keys o secretos locales.

## Relación con Fase G

| Sprint | Uso de esta ADR |
|---|---|
| FUNC-SPRINT-75 | Implementa Quality Gate local unificado según esta estrategia. |
| FUNC-SPRINT-76 | Prepara CI local/scaffolding sin deploy ni secrets. |
| FUNC-SPRINT-77 | Formaliza metadata y release manifest. |
| FUNC-SPRINT-78 | Genera changelog trazable. |
| FUNC-SPRINT-79 | Construye ZIP limpio y package Python local. |
| FUNC-SPRINT-80 | Agrega SBOM y baseline supply-chain. |
| FUNC-SPRINT-81 | Agrega checksums, smoke tests y verification report. |
| FUNC-SPRINT-82 | Define instalación e installer preliminar. |
| FUNC-SPRINT-83 | Agrega backup/restore/upgrade local. |
| FUNC-SPRINT-84 | Crea ReleaseAgent MVP dry-run y cierre Fase G. |

## Criterios PASS

- Existe política de versionado y productización.
- La publicación externa queda fuera de alcance.
- La matriz de artefactos define qué se puede liberar y qué se excluye.
- README, runbook, backlog G y manifest Sprint 74 quedan sincronizados.
- No se agregan dependencias ni comandos destructivos.

## Criterios BLOCK

- Permitir publicación externa sin ADR posterior.
- Considerar liberable un paquete con runtime DB, outputs, caches, `.venv`, `.git` o secretos.
- Confundir manifest de sprint con release manifest final.
- Implementar comandos de release antes de cerrar la estrategia.
- Omitir actualización de runbook o política de release.

## Riesgos

| ID | Riesgo | Mitigación |
|---|---|---|
| RISK-FUNC-74-001 | Versionado inconsistente entre sprint, package y release. | SemVer interno, fuente de verdad temporal en `pyproject.toml` y manifest de sprint separado. |
| RISK-FUNC-74-002 | Paquetes contaminados con runtime state. | Matriz de exclusión y criterios BLOCK de package limpio. |
| RISK-FUNC-74-003 | Publicación prematura. | Publicación externa fuera de alcance y ReleaseAgent dry-run. |
| RISK-FUNC-74-004 | Falso sentido de producción industrial. | Documentar que Sprint 74 es estrategia inicial y que la industrialización se completa en sprints 75-84. |

## Decisión final

Se aprueba la estrategia local-first de release/versionado/productización para Fase G. Sprint 74 cierra la decisión y habilita construir los mecanismos operativos posteriores sin reabrir la arquitectura base.
