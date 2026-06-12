---
title: "Auditoría FUNC-SPRINT-48 — Model governance: health, capability matrix y budget ledger"
doc_id: "DEVPL-AUDIT-FUNC-SPRINT-48-001"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-06-12"
standard: "MIPSoftware"
extension: "MIASI"
sprint: "FUNC-SPRINT-48"
approval: "approved_by_owner_direction"
---

# Auditoría FUNC-SPRINT-48 — Model governance: health, capability matrix y budget ledger

## Propósito

Validar que DevPilot incorpora gobierno operativo inicial para modelos locales sin habilitar APIs externas, sin requerir Ollama/LM Studio para la suite base y sin almacenar prompts o secretos crudos en el budget ledger.

## Estado

`implemented-initial`. La implementación agrega `ModelHealthService`, `CapabilityMatrix`, `BudgetLedger`, CLI de health/capabilities/budget y fallback explícito a `mock` cuando un provider local habilitado no está disponible.

## Funcionamiento

El flujo de gobierno es:

```text
ProviderRegistry
→ ModelHealthService / CapabilityMatrix / BudgetLedger
→ ModelAdapterRouter para llamadas reales
→ PolicyEngine + SecretGuard + CostGuard
→ LocalStore cost_events redacted
```

`model health --json` consolida todos los providers. `model capabilities --json` reporta capacidades sin llamar servidores. `model budget status --json` consulta `cost_events` de SQLite runtime y no expone prompts ni completions.

## Integración dentro de DevPilot

- `src/devpilot_core/modeling/health.py`: health consolidado de todos los providers.
- `src/devpilot_core/modeling/capabilities.py`: matriz de capacidades estática y auditable.
- `src/devpilot_core/modeling/budget.py`: budget ledger local sobre `LocalStore.cost_events`.
- `src/devpilot_core/store/local_store.py`: lectura y agregación de `cost_events`.
- `src/devpilot_core/cli.py`: comandos `model health`, `model capabilities`, `model budget status` y `--fallback-to-mock`.
- `.devpilot/miasi/*`: herramientas y políticas de governance declaradas.

## Criterios PASS

- Health/capabilities reportan `mock`, providers locales y providers externos bloqueados.
- Budget ledger registra eventos con costo monetario y compute estimate sin payloads crudos.
- Fallback a `mock` es explícito, configurable y visible en findings.
- La suite base no requiere Ollama, LM Studio ni APIs externas.
- No hay llamadas a OpenAI/Gemini/Mistral/Hugging Face.

## Criterios BLOCK

- `cost_events` contiene prompts, completions, API keys o secretos crudos.
- Provider local unavailable produce traceback.
- Budget permite gasto externo por defecto.
- Fallback a `mock` ocurre de forma silenciosa o no auditable.
- Providers externos quedan habilitados por defecto.

## Riesgos

- El budget ledger inicial mide estimaciones, no uso real de CPU/GPU.
- La capability matrix es estática y debe evolucionar con health dinámico y model evals.
- No hay enforcement monetario avanzado para APIs externas porque siguen bloqueadas.
- No hay prompt registry todavía; queda para el siguiente sprint.

## Veredicto

El sprint queda implementado como primera versión gobernada y local-first. Es suficiente para continuar con `FUNC-SPRINT-49 — Prompt Registry y Prompt Packs gobernados`.
