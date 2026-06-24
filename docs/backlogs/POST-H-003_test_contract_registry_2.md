---
doc_id: "POST-H-003-BACKLOG"
id: "POST-H-003"
title: "POST-H-003 — Test Contract Registry 2.0"
status: "approved"
version: "0.5.0"
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

## 11. Avance de implementación

### POST-H-003-A — Diseño de schema v2 y compatibilidad

Estado: `implemented-initial`.

`POST-H-003-A — Diseño de schema v2 y compatibilidad` queda implementado como primera base contractual de Test Contract Registry 2.0. Se agregó el schema `SCHEMA-DEVPL-TEST-CONTRACT-REGISTRY-V2`, fixtures válidos e inválidos, helper `TestContractRegistryV2Design`, pruebas focales y documentación de diseño. El registry v1 sigue siendo la fuente operativa de `python -m devpilot_core test-contracts validate --json`.

### POST-H-003-B — Migrador v1 → v2 dry-run

Estado: `implemented-initial`.

`POST-H-003-B — Migrador v1 → v2 dry-run` implementa una migración determinística local desde `.devpilot/testing/test_contract_registry.json` hacia una representación v2 schema-backed. El migrador produce preview en memoria por defecto, genera findings explícitos para gaps de clasificación, preserva el registry v1 y solo escribe `.devpilot/testing/test_contract_registry_v2.json` cuando se usa `--write-output`.

Alcance exacto de B:

```text
- Implementa TestContractRegistryV2Migrator.
- Agrega CLI test-contracts migrate-v2.
- Genera .devpilot/testing/test_contract_registry_v2.json con 87 contratos migrados.
- Mantiene v1 validate operativo con 87 contratos.
- Marca clasificaciones como inferred o needs-review.
- No ejecuta tests desde JSON.
- No implementa validate-v2 ni perfiles ejecutables; eso queda para POST-H-003-C.
```

Criterios PASS materializados:

```text
PASS si todo contrato v1 tiene representación v2.
PASS si el output v2 cumple TestContractRegistryV2.
PASS si los gaps de clasificación quedan en findings.
PASS si v1 no se sobrescribe.
PASS si no hay red, APIs externas ni ejecución remota.
```

Criterios BLOCK materializados:

```text
BLOCK si el migrador intenta sobrescribir .devpilot/testing/test_contract_registry.json.
BLOCK si el output v2 queda fuera del workspace.
BLOCK si el payload migrado no valida contra schema v2.
BLOCK si test-contracts validate v1 deja de pasar.
```

Limitación explícita: la clasificación generada por B es una primera migración determinística para acelerar revisión industrial; no debe tratarse como matriz final de criticidad/costo/riesgo hasta `POST-H-003-C`, `POST-H-003-D` y `POST-H-003-E`.

### POST-H-003-C — Validator v2 y perfiles de ejecución

Estado: `implemented-initial`.

`POST-H-003-C — Validator v2 y perfiles de ejecución` implementa el validador semántico local de `.devpilot/testing/test_contract_registry_v2.json` y los perfiles de selección `p0-critical`, `security`, `release`, `impact` y `docs-historical`. La validación sigue siendo local-first y no ejecuta pruebas desde el registry.

Alcance exacto de C:

```text
- Implementa TestContractRegistryV2Validator.
- Agrega CLI test-contracts validate-v2.
- Agrega CLI test-contracts profile --profile <id>.
- Valida schema, paths, comandos recomendados y restricciones de seguridad.
- Selecciona contratos y comandos recomendados por perfil.
- Mantiene test-contracts validate v1 operativo con 87 contratos.
- No ejecuta pytest ni subprocesses desde JSON.
- No implementa todavía impact_v2; eso queda para POST-H-003-D.
- No agrega todavía subgate TCR v2 a quality-gate; eso queda para POST-H-003-E.
```

Criterios PASS materializados:

```text
PASS si test-contracts validate-v2 pasa contra .devpilot/testing/test_contract_registry_v2.json.
PASS si p0-critical/security/release/impact/docs-historical seleccionan contratos sin ejecutar pruebas.
PASS si se bloquean comandos recomendados inseguros o paths inexistentes.
PASS si v1 sigue validando y quality-gate hardening sigue PASS.
PASS si no hay red, APIs externas, ejecución remota ni mutaciones de código.
```

Limitación explícita: `POST-H-003-C` valida y selecciona; no ejecuta pruebas. La ejecución sigue siendo explícita por comandos del operador o por `tests.run` approval-gated. El análisis de impacto por paths se implementará en `POST-H-003-D`.

### POST-H-003-D — Integración con Test Impact Analyzer

Estado: `implemented-initial`.

`POST-H-003-D — Integración con Test Impact Analyzer` implementa `TestImpactAnalyzerV2` y el comando `test-impact analyze-v2`. La capacidad cruza rutas cambiadas con `watched_paths`, `validates` y `test_files` del registry v2, aplica reglas heurísticas explícitas para hotspots de seguridad/arquitectura y emite un plan de pruebas recomendado sin ejecutar pruebas.

Alcance exacto de D:

```text
- Implementa src/devpilot_core/testing/impact_v2.py.
- Agrega CLI test-impact analyze-v2.
- Usa .devpilot/testing/test_contract_registry_v2.json como fuente de contratos.
- Recomienda pruebas y comandos por impacto.
- Prioriza P0/P1 para cambios en policy, schemas, agents, CLI, API o release.
- Para documentación histórica, selecciona contratos documentales específicos cuando existe match exacto.
- No ejecuta pytest ni subprocesses desde JSON.
- No agrega todavía subgate TCR v2 a quality-gate; eso queda para POST-H-003-E.
```

Criterios PASS materializados:

```text
PASS si cambios en policy recomiendan pruebas de policy/security y perfiles p0-critical/security.
PASS si cambios documentales específicos recomiendan la prueba documental relevante, no toda la suite histórica.
PASS si cambios en cli.py recomiendan pruebas CLI/API/impact.
PASS si el plan declara tests_executed=false, network_used=false, external_api_used=false y mutations_performed=false.
PASS si v1 y v2 siguen validando y quality-gate hardening sigue PASS.
```

Limitación explícita: `POST-H-003-D` recomienda pruebas; no las ejecuta. La ejecución sigue siendo manual o mediante `tests.run` approval-gated. La integración como señal/subgate de quality gate y el cierre documental del hito quedan para `POST-H-003-E`.

