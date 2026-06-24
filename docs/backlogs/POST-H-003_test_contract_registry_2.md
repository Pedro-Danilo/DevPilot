---
doc_id: "POST-H-003-BACKLOG"
id: "POST-H-003"
title: "POST-H-003 — Test Contract Registry 2.0"
status: "approved"
version: "0.2.0"
owner: "Ordóñez"
approval: "internal"
updated: "2026-06-24"
phase: "POST-FASE-H"
priority: "P0"
roadmap_source: "docs/backlogs/post_h_prioritized_roadmap.md"
adr_source: "docs/adr/ADR-POSTH-002-test-contract-registry-2.md"
local_first: true
dry_run: true
no_remote_execution_enabled: true
---

# POST-H-003 — Test Contract Registry 2.0

## 1. Objetivo

Evolucionar el `Test Contract Registry` desde su versión actual `implemented-initial` hacia un registro de contratos de prueba por **dominio, criticidad, riesgo, costo, trigger, impacto y tipo de ejecución**, sin perder compatibilidad con los 87 contratos vigentes.

El propósito es evitar el falso supuesto de que “muchos tests” equivalen automáticamente a cobertura industrial. La nueva versión debe permitir decidir qué pruebas correr siempre, por impacto, por release, por seguridad o por cambios en arquitectura/agentes/políticas.

## 2. Contexto

El registry actual valida estructura y semántica básica, con 87 contratos después del cierre de POST-H-002. Sin embargo, predominan contratos históricos/documentales. Para avanzar hacia `production-ready-local`, DevPilot necesita una clasificación operacional más fuerte.

## 3. Alcance

Incluye:

```text
- Schema v2 del Test Contract Registry.
- Migrador v1 → v2 en dry-run.
- Validator v2 con compatibilidad temporal v1.
- Campos por dominio, criticidad, riesgo, costo, trigger e impacto.
- Integración con test-impact analyzer.
- Perfiles de ejecución P0/P1/P2/P3.
- Tests focales y documentación.
```

No incluye:

```text
- Reescritura total de la suite.
- Eliminación abrupta del registry v1.
- Ejecución remota de tests.
- APIs externas.
- Scheduler distribuido.
```

## 4. Entregables

```text
docs/schemas/test_contract_registry_v2.schema.json
.devpilot/testing/test_contract_registry_v2.json
src/devpilot_core/testing/contracts_v2.py
src/devpilot_core/testing/migration.py
src/devpilot_core/testing/profiles_v2.py
src/devpilot_core/testing/impact_v2.py
tests/test_test_contract_registry_v2.py
tests/test_test_contract_registry_migration.py
tests/test_test_impact_v2.py
docs/04_quality/test_contract_registry_2_design.md
```

Actualizaciones controladas:

```text
docs/schemas/schema_catalog.json
.devpilot/testing/test_contract_registry.json       # solo si se agrega referencia/migration note
docs/05_operations/runbook.md
```

## 5. Modelo v2 mínimo

Cada contrato v2 debe incluir:

```json
{
  "contract_id": "policy-engine-critical",
  "schema_version": "2.0",
  "domain": "governance.policy",
  "capability": "PolicyEngine",
  "criticality": "P0",
  "risk_level": "high",
  "test_type": "unit|integration|contract|ui-smoke|security|release|documentation",
  "execution_profile": "always|impact|release|manual|nightly-local",
  "cost_class": "low|medium|high",
  "expected_duration_seconds": 0,
  "test_files": ["tests/test_policy_engine.py"],
  "watched_paths": ["src/devpilot_core/policy/"],
  "validates": ["PolicyEngine blocks unsafe actions"],
  "required_for_release": true,
  "required_for_security_gate": true,
  "network_allowed": false,
  "external_api_allowed": false,
  "mutations_allowed": false,
  "owner": "POST-H-003",
  "recommended_commands": ["python -m pytest tests/test_policy_engine.py -q"]
}
```

## 6. Micro-sprints propuestos

### POST-H-003-A — Diseño de schema v2 y compatibilidad

Tareas:

```text
1. Crear schema v2.
2. Registrar schema en schema_catalog.
3. Documentar compatibilidad v1/v2.
4. Definir enums: domain, criticality, risk_level, cost_class, execution_profile, test_type.
5. Crear fixtures válidos e inválidos.
```

PASS:

```text
PASS si schema v2 valida contratos mínimos.
PASS si schema rechaza red/API/mutaciones no declaradas.
PASS si v1 sigue validando durante transición.
```

BLOCK:

```text
BLOCK si se rompe test-contracts validate actual.
BLOCK si no se diferencia criticidad de riesgo.
```

### POST-H-003-B — Migrador v1 → v2 dry-run

Tareas:

```text
1. Implementar migración determinística desde registry v1.
2. Mapear historical-sprint a test_type=documentation, risk=low/medium según criticidad.
3. Mapear quality-gate/global-state a P0/P1.
4. Generar reporte de gaps de clasificación.
5. No sobrescribir v1 por defecto.
```

Comando propuesto:

```powershell
python -m devpilot_core test-contracts migrate-v2 --dry-run --json
python -m devpilot_core test-contracts migrate-v2 --write-output .devpilot/testing/test_contract_registry_v2.json --json
```

PASS:

```text
PASS si todo contrato v1 tiene representación v2.
PASS si gaps quedan explícitos como findings.
PASS si no hay mutaciones salvo write-output explícito.
```

### POST-H-003-C — Validator v2 y perfiles de ejecución

Tareas:

```text
1. Implementar TestContractRegistryV2Validator.
2. Validar paths existentes.
3. Validar comandos recomendados.
4. Validar restricciones de network/external_api/mutations.
5. Implementar perfiles: p0-critical, security, release, impact, docs-historical.
```

Comandos propuestos:

```powershell
python -m devpilot_core test-contracts validate-v2 --json
python -m devpilot_core test-contracts profile --profile p0-critical --json
python -m devpilot_core test-contracts profile --profile security --json
```

### POST-H-003-D — Integración con Test Impact Analyzer

Tareas:

```text
1. Crear impact_v2 que cruce changed_paths con watched_paths v2.
2. Priorizar tests P0/P1 cuando haya cambios en policy, schemas, agents, CLI, API o release.
3. Emitir plan de pruebas recomendado.
4. No ejecutar tests automáticamente salvo flag explícito futuro.
```

Comando propuesto:

```powershell
python -m devpilot_core test-impact analyze-v2 --changed-paths src/devpilot_core/policy --json
```

PASS:

```text
PASS si cambios en policy recomiendan tests P0 de policy/security.
PASS si cambios en docs solo recomiendan tests documentales relevantes.
PASS si cambios en cli.py recomiendan CLI/command registry tests.
```

### POST-H-003-E — Quality gate y documentación

Tareas:

```text
1. Agregar subgate opcional o señal en quality-gate hardening para TCR v2.
2. Documentar uso en runbook.
3. Actualizar ADR-POSTH-002 si se requiere addendum.
4. Agregar contract de POST-H-003.
```

PASS:

```text
PASS si test-contracts validate y validate-v2 pasan.
PASS si quality-gate hardening sigue PASS.
PASS si v1 no queda roto.
```

## 7. Comandos de validación final

```powershell
$env:PYTHONPATH="src"

python -m pytest tests/test_test_contract_registry.py tests/test_test_contract_registry_v2.py -q
python -m pytest tests/test_test_contract_registry_migration.py tests/test_test_impact_v2.py -q
python -m devpilot_core test-contracts validate --json
python -m devpilot_core test-contracts validate-v2 --json
python -m devpilot_core test-impact analyze-v2 --changed-paths src/devpilot_core/policy --json
python -m devpilot_core quality-gate run --profile hardening --json
```

## 8. Riesgos

| Riesgo | Severidad | Mitigación |
|---|---:|---|
| Romper contratos v1 | Alta | Compatibilidad temporal obligatoria. |
| Clasificación artificial | Media-alta | Findings para gaps, no inventar criticidad. |
| Complejidad excesiva | Media | Schema v2 mínimo pero extensible. |
| Costos altos de test | Media | cost_class y profiles. |
| Falso PASS por tests históricos | Alta | Separar historical/documentation de P0 security/core. |

## 9. No-go gates

```text
NO-GO si se elimina registry v1 sin migración.
NO-GO si se asume que historical-sprint equivale a cobertura funcional.
NO-GO si perfiles permiten network/external_api sin declaración.
NO-GO si se ejecutan tests destructivos o remotos.
```

## 10. Entregable verificable

```text
Schema v2 registrado.
Registry v2 generado o migrable.
Validator v2 ejecutable.
Impact analyzer v2 recomienda pruebas por cambio.
Suite focal PASS.
Quality gate hardening PASS.
```


## 11. Avance de implementación — POST-H-003-A

Estado: `implemented-initial`.

`POST-H-003-A — Diseño de schema v2 y compatibilidad` queda implementado como primera base contractual de Test Contract Registry 2.0. Se agregó el schema `SCHEMA-DEVPL-TEST-CONTRACT-REGISTRY-V2`, fixtures válidos e inválidos, helper `TestContractRegistryV2Design`, pruebas focales y documentación de diseño.

Alcance implementado:

```text
docs/schemas/test_contract_registry_v2.schema.json
docs/04_quality/test_contract_registry_2_design.md
src/devpilot_core/testing/contracts_v2.py
tests/fixtures/test_contract_registry_v2/*.json
tests/test_test_contract_registry_v2.py
docs/post_h_003_a_manifest.json
docs/audits/post_h_003_a_test_contract_registry_v2_schema_report.md
```

Compatibilidad:

```text
El registry v1 continúa siendo la fuente operativa.
El comando test-contracts validate sigue validando v1.
No se migra ni sobrescribe .devpilot/testing/test_contract_registry.json.
No se agrega todavía CLI validate-v2.
```

Siguiente micro-sprint:

```text
POST-H-003-B — Migrador v1 → v2 dry-run
```
