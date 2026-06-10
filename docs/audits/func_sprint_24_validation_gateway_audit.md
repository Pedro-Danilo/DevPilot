---
title: "FUNC-SPRINT-24 — Artifact Profiles data-driven y ValidationGateway inicial"
doc_id: "DEVPL-AUDIT-FUNC-SPRINT-24-001"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
standard: "MIPSoftware"
extension: "MIASI"
phase: "FUNC-SPRINT-24"
updated: "2026-06-10"
approval: "approved_by_owner"
---

# FUNC-SPRINT-24 — Artifact Profiles data-driven y ValidationGateway inicial

## 1. Propósito

Este artefacto audita la implementación de `FUNC-SPRINT-24`. El sprint reduce hardcoding de perfiles documentales y crea una fachada común para ejecutar validaciones determinísticas sin reemplazar los validadores existentes.

El resultado es una primera versión **implemented-initial** de `ValidationGateway` y un catálogo `docs/validation/artifact_profiles.json` gobernado por schema.

## 2. Alcance implementado

Se implementó:

- catálogo data-driven de perfiles documentales;
- schema `ArtifactProfiles`;
- `ArtifactProfileRegistry` con fallback Python;
- `ValidationGateway` para scopes `docs`, `contracts` y `all`;
- comandos CLI `validate docs`, `validate contracts` y `validate all`;
- pruebas de compatibilidad de perfiles y gateway;
- sincronización de README, runbook y backlog Fase A.

No se implementó:

- trazabilidad SDLC;
- reglas semánticas nuevas;
- UI;
- APIs externas;
- ejecución de agentes;
- acciones destructivas;
- parser YAML general;
- cambios de política MIASI.

## 3. Funcionamiento técnico

`ArtifactProfileRegistry` carga `docs/validation/artifact_profiles.json`, lo valida contra `docs/schemas/artifact_profiles.schema.json` y compara su cobertura frente a los perfiles Python históricos. Si el catálogo JSON no está disponible, los validadores documentales conservan fallback a `src/devpilot_core/validators/artifact_profiles.py`.

`ValidationGateway` no duplica reglas. Compone resultados de validadores existentes:

- `validate docs`: `ArtifactProfileRegistry.status()` + `build_strict_readiness_result()`;
- `validate contracts`: `schema list`, `schema validate-miasi`, `schema validate-workspace`, `schema validate-providers` y manifests funcionales 19+;
- `validate all`: combina `docs` y `contracts`.

Cada comando devuelve `CommandResult`, preserva findings de origen y soporta `--json` y `--write-report`.

## 4. Integración y rol dentro de DevPilot

Sprint 24 ubica una nueva capa en `src/devpilot_core/validation/`. Esta capa es una fachada de orquestación, no una fuente de reglas nueva. Su rol es preparar la transición hacia trazabilidad y baseline industrial sin romper validadores ya estabilizados.

Relación con componentes existentes:

| Componente | Relación |
|---|---|
| `validators.artifact` | Usa selección de perfiles data-driven con fallback. |
| `validators.readiness` | Sigue siendo gate documental semántico principal. |
| `schemas.SchemaValidator` | Valida el nuevo catálogo de perfiles y contratos. |
| `schemas.BuiltinContractValidator` | Se reutiliza para validar contratos críticos. |
| `ReportEngine` | Persiste evidencia cuando el CLI recibe `--write-report`. |
| `LocalStore` y `EventLogger` | Mantienen historial y trazas best-effort desde CLI. |

## 5. Comandos de uso

```powershell
$env:PYTHONPATH="src"
python -m devpilot_core validate docs --json
python -m devpilot_core validate contracts --json
python -m devpilot_core validate all --json --write-report
python -m devpilot_core schema validate --schema ArtifactProfiles --instance docs/validation/artifact_profiles.json --json
python -m pytest tests/test_artifact_profile_registry.py tests/test_validation_gateway.py -q
python -m pytest -q
```

## 6. Criterios PASS

- `artifact_profiles.json` existe y pasa schema.
- Los perfiles JSON cubren todos los perfiles Python actuales.
- `ArtifactProfileRegistry` selecciona perfiles equivalentes a `artifact_profiles.py`.
- `validate docs` pasa y conserva warnings no bloqueantes.
- `validate contracts` pasa y valida contratos estructurales críticos.
- `validate all` consolida ambos grupos.
- Los findings de validadores internos no se ocultan.
- No se realizan mutaciones destructivas.
- `pytest -q` pasa.

## 7. Criterios BLOCK

- Un perfil Python actual falta en JSON.
- El catálogo JSON inválido se usa como si fuera válido.
- `ValidationGateway` cambia semántica de validators existentes.
- Un finding interno desaparece del resultado consolidado.
- Se elimina fallback Python antes de estabilizar el catálogo JSON.
- Se agrega una dependencia externa sin ADR.

## 8. Riesgos

- El catálogo JSON puede divergir si futuros perfiles se agregan solo en Python o solo en JSON.
- `ValidationGateway` puede crecer demasiado si futuros sprints lo convierten en fuente de reglas en lugar de fachada.
- `validate all` produce salidas grandes porque preserva detalles y findings de origen.
- La validación sigue siendo documental/contractual; no cubre trazabilidad SDLC, drift arquitectura-código ni cobertura de requisitos.

## 9. ADR

No se creó ADR nueva porque Sprint 24 no introduce dependencia externa, proveedor, política runtime, almacenamiento nuevo ni acción destructiva. Se reutiliza la dependencia `jsonschema` ya justificada por `ADR-0010`.

## 10. Pruebas implementadas

- `tests/test_artifact_profile_registry.py`
- `tests/test_validation_gateway.py`
- ajustes de compatibilidad en `tests/test_schema_registry.py`, `tests/test_sprint_22_documentation.py` y `tests/test_sprint_23_documentation.py`.

## 11. Evolución recomendada

El siguiente paso es `FUNC-SPRINT-25 — Traceability Model y extracción de entidades SDLC`. La integración de trazabilidad debe consumir el gateway sin duplicar reglas ni modificar artefactos.
