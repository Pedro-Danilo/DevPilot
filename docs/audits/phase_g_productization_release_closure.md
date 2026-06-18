---
title: "DevPilot Local — Cierre Fase G: Productización y release"
doc_id: "DEVPL-PHASE-G-CLOSURE"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
standard: "MIPSoftware"
extension: "MIASI"
phase: "FASE-G-PRODUCTIZACION-RELEASE"
closed_by_sprint: "FUNC-SPRINT-84"
updated: "2026-06-17"
approval: "approved_by_func_sprint_84_validation"
---

# DevPilot Local — Cierre Fase G: Productización y release

## Estado

Fase G cerrada funcionalmente como `implemented-initial` industrial local-first.

## Propósito

Registrar el cierre formal de la Fase G y dejar trazabilidad del paso de DevPilot desde un repositorio funcional probado hacia un producto localmente distribuible, versionable, verificable y mantenible.

## Alcance cerrado

| Sprint | Capacidad | Estado |
|---|---|---|
| FUNC-SPRINT-74 | ADR de release, versionado y productización | Cerrado |
| FUNC-SPRINT-75 | Quality Gate local unificado | Cerrado |
| FUNC-SPRINT-76 | CI local y workflow scaffolding seguro | Cerrado |
| FUNC-SPRINT-77 | Release metadata y Release Manifest | Cerrado |
| FUNC-SPRINT-78 | Changelog generator y política de cambios | Cerrado |
| FUNC-SPRINT-79 | Packaging Python y ZIP limpio reproducible | Cerrado |
| FUNC-SPRINT-80 | SBOM y supply-chain baseline | Cerrado |
| FUNC-SPRINT-81 | Checksums, smoke tests y verificación de release | Cerrado |
| FUNC-SPRINT-82 | Estrategia de instalación e installer preliminar | Cerrado |
| FUNC-SPRINT-83 | Backup, restore y upgrade local | Cerrado |
| FUNC-SPRINT-84 | ReleaseAgent MVP dry-run y cierre Fase G | Cerrado |

## Evidencia de release local

DevPilot cuenta con la siguiente evidencia regenerable:

- pruebas `pytest -q` reportadas en PASS por validación externa del sprint;
- `quality-gate run --profile ci` y `quality-gate run --profile release`;
- Release Manifest;
- Changelog local;
- package build dry-run/execute local;
- SBOM baseline;
- checksums SHA256;
- release verify y smoke test local;
- install plan;
- backup/restore/upgrade check;
- ReleaseAgent dry-run.

## Criterios de liberabilidad local

Una versión local de DevPilot puede considerarse candidata si:

1. `pytest -q` está en PASS.
2. `quality-gate run --profile release --json` está en PASS.
3. `agent run release-assistant --dry-run --json` está en PASS.
4. El package limpio no contiene outputs, caches, runtime DB, backups, `.git`, `.venv` ni `node_modules`.
5. SBOM, checksums, changelog y manifest pueden regenerarse localmente.
6. Backup/restore/upgrade están documentados y probados en modo seguro.

## Límites explícitos

Esta fase no implementa:

- publicación pública en PyPI;
- GitHub Releases reales;
- despliegue cloud;
- firma criptográfica obligatoria;
- provenance fuerte;
- auto-update;
- remote runners;
- SaaS;
- soporte enterprise multiusuario.

## Riesgos residuales

| Riesgo | Estado | Evolución esperada |
|---|---|---|
| Firma/provenance no implementada | Aceptado | Fase futura de supply-chain hardening. |
| SBOM sin SCA externo | Aceptado | Agregar validación CycloneDX formal y scanners opcionales. |
| Instalación real todavía manual | Aceptado | Smoke install aislado y scripts controlados. |
| Backups no cifrados | Aceptado | Cifrado/firma local opcional. |
| ReleaseAgent rule-based | Aceptado | Modelo local/API opcional gobernado y evals avanzadas. |

## Relación con Fase H

La siguiente fase lógica es Fase H, iniciando en `FUNC-SPRINT-85 — ADR de arquitectura avanzada agentic/enterprise`. Fase H no debe habilitar multiagente, RAG, MCP, plugins o remote runners sin conservar PolicyEngine, MIASI, Approval, trazas, evaluación y reportes.

## Límite operacional explícito

ReleaseAgent no publica, no despliega, no firma y no etiqueta Git. Cualquier capacidad futura que haga estas acciones requerirá ADR, PolicyEngine, aprobación humana y evidencia adicional.

## Veredicto

Fase G queda cerrada como baseline de productización y release local. El resultado es suficientemente sólido para continuar hacia capacidades avanzadas, siempre que las capacidades futuras no degraden la filosofía local-first, dry-run-first y evidence-driven.
