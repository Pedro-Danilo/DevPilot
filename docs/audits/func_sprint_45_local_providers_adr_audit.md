---
title: "Auditoría FUNC-SPRINT-45 — ADR y contratos de proveedores locales"
doc_id: "DEVPL-AUDIT-FUNC-SPRINT-45-001"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-06-12"
phase: "FASE-D-IA-LOCAL-GOBERNADA"
sprint: "FUNC-SPRINT-45"
approval: "approved_by_owner"
---
# Auditoría FUNC-SPRINT-45 — ADR y contratos de proveedores locales

## 1. Propósito

Verificar que `FUNC-SPRINT-45` formaliza proveedores locales antes de implementar adapters reales. El sprint crea la ADR, endurece el schema provider config, ajusta `ProviderRegistry`, actualiza MIASI y deja evidencia documental de que DevPilot mantiene operación local-first.

## 2. Estado

Estado: `implemented-initial`.

Este sprint no implementa OllamaAdapter ni LMStudioAdapter. Solo deja contratos y gates previos para que los sprints 46 y 47 puedan implementar proveedores locales opcionales sin romper pruebas base.

## 3. Artefactos principales

| Artefacto | Rol |
|---|---|
| `docs/02_architecture/adrs/ADR-0011-local-model-providers.md` | Decisión arquitectónica sobre proveedores locales gobernados. |
| `docs/schemas/provider_config.schema.json` | Contrato estructural y de seguridad para providers YAML. |
| `.devpilot/providers.yaml.example` | Configuración segura de referencia. |
| `src/devpilot_core/modeling/providers.py` | Carga, parseo y validación semántica de proveedores. |
| `tests/test_provider_config_schema.py` | Pruebas de contrato provider config y mock baseline. |
| `docs/functional_sprint_45_manifest.json` | Manifest ejecutable del sprint. |

## 4. Funcionamiento

`ProviderRegistry` carga provider metadata desde `.devpilot/providers.yaml`, `.devpilot/providers.yaml.example` o defaults seguros. Luego valida reglas que no conviene delegar solo a JSON Schema: `mock` obligatorio, ids únicos, proveedores locales localhost-only, API providers disabled y bloqueo de secretos crudos.

El comando `model providers` expone `semantic_valid`, conteos por tipo, proveedor de origen y notas de seguridad. Si el registry falla controles semánticos, las llamadas `model generate/classify/embed` se bloquean antes de enrutar al adapter.

## 5. Integración con MIASI

MIASI queda sincronizado con:

- `model.call.mock` implementado y seguro;
- `model.call.local` como placeholder controlado;
- `model.call.external` disabled y approval-gated;
- regla `MODEL_LOCAL_PROVIDER_CONTROLLED` para proveedores locales antes de adapters reales.

## 6. Criterios PASS

- ADR aprobada.
- Provider config schema validado.
- `.devpilot/providers.yaml.example` declara mock enabled y locales disabled.
- APIs externas disabled.
- Mock generate/classify/embed sigue PASS.
- No hay red ni APIs externas en pruebas.
- README, runbook, backlog y MIASI actualizados.

## 7. Criterios BLOCK

- Proveedor local requerido para tests.
- Endpoint local remoto o externo permitido por defecto.
- Raw API key en provider config.
- API externa habilitada por defecto.
- ProviderRegistry permite configuración insegura sin findings.

## 8. Riesgos y límites

- `FUNC-SPRINT-45` es una primera versión contractual, no una integración real de modelos locales.
- El parser YAML sigue siendo narrow/dependency-free; no reemplaza un parser YAML completo.
- La validación de endpoints locales es intencionalmente conservadora.
- Los adapters reales deben implementar timeouts, health checks y fake-server tests en sprints posteriores.

## 9. Veredicto

`FUNC-SPRINT-45` deja a DevPilot listo para iniciar integración opcional de Ollama en `FUNC-SPRINT-46` sin romper la arquitectura local-first ni habilitar proveedores externos.
