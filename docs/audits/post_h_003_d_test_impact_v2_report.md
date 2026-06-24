---
doc_id: "POST-H-003-D-AUDIT"
title: "POST-H-003-D — Test Impact Analyzer v2 audit"
status: "approved"
version: "0.1.0"
owner: "Ordóñez"
updated: "2026-06-24"
approval: "internal"
---

# POST-H-003-D — Test Impact Analyzer v2 audit

## Propósito

Registrar la implementación inicial de `POST-H-003-D — Integración con Test Impact Analyzer`, cuyo objetivo es recomendar planes de prueba selectivos a partir de rutas cambiadas y contratos v2 sin ejecutar pruebas automáticamente.

## Estado

Estado: `implemented-initial`.

Esta entrega complementa `POST-H-003-C`: el registry v2 ya se puede validar y seleccionar por perfil; ahora también se puede analizar por impacto de cambios locales.

## Alcance implementado

```text
- Módulo src/devpilot_core/testing/impact_v2.py.
- CLI test-impact analyze-v2.
- Pruebas focales tests/test_test_impact_v2.py.
- Sincronización de README, runbook, backlog, diseño y changelog.
- Manifest docs/post_h_003_d_manifest.json.
```

## Funcionamiento

`TestImpactAnalyzerV2` ejecuta el siguiente flujo:

```text
1. Valida .devpilot/testing/test_contract_registry_v2.json con TestContractRegistryV2Validator.
2. Lee changed_paths directos o desde archivo.
3. Cruza rutas cambiadas contra test_files, watched_paths y validates.
4. Aplica heurísticas explícitas para cambios sensibles.
5. Emite matched_contracts, heuristic_recommendations, recommended_tests y recommended_commands.
6. Declara tests_executed=false y deja la ejecución en manos del operador.
```

## Integración

La integración principal queda en CLI:

```powershell
python -m devpilot_core test-impact analyze-v2 --changed-paths src/devpilot_core/policy --json
```

El comando se integra con `CommandResult`, `ReportEngine` mediante `--write-report`, eventos locales y persistencia best-effort, igual que otros comandos DevPilot.

## Criterios PASS

```text
PASS si policy/security recomienda pruebas de policy/security y perfiles p0-critical/security.
PASS si docs/audits/func_sprint_N recomienda la prueba documental de N, no toda la historia.
PASS si cli.py recomienda pruebas CLI/Application/API e impact.
PASS si schema changes recomiendan schema registry y schema validator.
PASS si tests_executed=false.
PASS si network_used=false, external_api_used=false y mutations_performed=false.
```

## Criterios BLOCK

```text
BLOCK si no se entregan rutas cambiadas.
BLOCK si validate-v2 falla antes del análisis.
BLOCK si se intenta ejecutar pytest desde el analyzer.
BLOCK si se activa red, API externa, ejecución remota o mutación de fuentes.
```

## Riesgos

| Riesgo | Severidad | Mitigación |
|---|---:|---|
| Falso PASS por falta de contratos policy/security dedicados | Alta | Heurísticas explícitas y findings; contratos dedicados deben evolucionar después. |
| Ejecutar pruebas automáticamente desde recomendaciones | Alta | `tests_executed=false` y sin subprocesses. |
| Seleccionar demasiada documentación histórica | Media | Se evita `docs/audits/` como match broad para seleccionar todos los sprints. |
| Omitir rutas nuevas no cubiertas | Media | `unmatched_paths` genera warning y recomienda revisión/P0. |

## No-go gates

```text
NO-GO si analyze-v2 ejecuta pytest.
NO-GO si usa red, APIs externas o ejecución remota.
NO-GO si modifica .devpilot/testing/test_contract_registry.json.
NO-GO si sustituye quality-gate hardening antes de POST-H-003-E.
```

## Próximo paso

`POST-H-003-E — Quality gate y documentación` debe decidir cómo integrar `validate-v2` y `analyze-v2` como señal/gate sin romper compatibilidad v1 ni ejecutar pruebas pesadas por defecto.
