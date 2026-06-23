---
doc_id: "ADR-POSTH-002"
title: "Test Contract Registry 2.0 por dominio, criticidad, riesgo e impacto"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-06-23"
approval: "accepted_by_owner"
decision_state: "accepted"
micro_sprint: "POST-H-EVAL-001-F"
---

# ADR-POSTH-002 — Test Contract Registry 2.0 por dominio, criticidad, riesgo e impacto

## Contexto

`POST-H-EVAL-001-E` identificó una suite amplia: 187 archivos `test_*.py`, 893 casos recolectables por pytest y 84 contratos en el Test Contract Registry v1. Sin embargo, 78 de 84 contratos son históricos/documentales y 103 archivos de test no están mapeados explícitamente por el registry v1.

El impact analyzer actual es conservador y seguro, pero para rutas críticas no mapeadas cae a `pytest -q` completo. Esta conducta es correcta para seguridad, pero costosa como estrategia de desarrollo diario.

## Decisión

DevPilot debe evolucionar a **Test Contract Registry 2.0** antes de depender del impact analyzer como selector industrial de regresión.

El registry v2 deberá modelar como mínimo:

```text
domain
priority P0/P1/P2/P3
risk_level
execution_tier
estimated_cost
change_triggers
security_critical
release_blocking
required_for_remote_enablement
coverage_intent
owner_role
```

## Alternativas consideradas

| Alternativa | Resultado | Motivo |
|---|---|---|
| Mantener registry v1 sin cambios | Rechazada | No representa criticidad ni costo industrial |
| Ejecutar siempre `pytest -q` | Rechazada como estrategia única | Seguro pero costoso; útil para cierre/release, no para cada cambio |
| Migrar a registry v2 incremental | Aceptada | Permite preservar v1 mientras se mapean dominios críticos |

## Consecuencias

- `POST-H-003` queda como hito P0.
- P0 debe mapear PolicyEngine, Approval, RBAC, PathGuard, SecretGuard, remote disabled, connector write denied y plugin execution denied.
- El impact analyzer no debe omitir full regression cuando no tenga contrato suficiente.
- La suite histórica/documental debe conservarse, pero no debe confundirse con cobertura de seguridad runtime.

## Criterios PASS

```text
registry v2 propuesto y versionado
P0/P1/P2/P3 definidos
execution_tier definido
rutas críticas de seguridad mapeadas
fallback a pytest completo conservado para rutas desconocidas
```

## Criterios BLOCK

```text
cantidad de tests usada como proxy de cobertura industrial
históricos documentales mezclados con tests de seguridad crítica
impact analyzer omite regresión completa en dominios no mapeados
remote enablement sin tests P0 requeridos
```

## Riesgos

Una migración demasiado agresiva puede romper validaciones existentes. La mitigación es introducir v2 con compatibilidad temporal, pruebas de schema y migración controlada.

## Comandos de verificación

```powershell
$env:PYTHONPATH="src"
python -m devpilot_core test-contracts validate --json
python -m devpilot_core test-impact analyze --path src\devpilot_core\policy\engine.py --json
python -m pytest tests	est_test_contract_registry.py tests	est_test_impact.py -q
```

## Estado

Aceptada en `POST-H-EVAL-001-F`. Debe materializarse en `POST-H-003`.
