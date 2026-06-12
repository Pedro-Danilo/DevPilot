---
title: "Auditoría FUNC-SPRINT-47 — LMStudioAdapter local OpenAI-compatible"
doc_id: "DEVPL-AUDIT-FUNC-SPRINT-47-001"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-06-12"
standard: "MIPSoftware"
extension: "MIASI"
sprint: "FUNC-SPRINT-47"
approval: "approved_by_owner_direction"
---

# Auditoría FUNC-SPRINT-47 — LMStudioAdapter local OpenAI-compatible

## Propósito

Validar que DevPilot incorpora un adaptador LM Studio local OpenAI-compatible sin activar OpenAI externo, sin requerir servidor LM Studio para la suite base y sin relajar los controles local-first de Fase D.

## Estado

`implemented-initial`. La implementación introduce `LMStudioAdapter`, `model health --provider lmstudio`, timeouts cortos, manejo estructurado de indisponibilidad, pruebas con fake server OpenAI-compatible y bloqueo de endpoints no-locales.

## Funcionamiento

El flujo de ejecución es:

```text
CLI model generate/classify/embed
→ ModelAdapterRouter
→ ProviderRegistry
→ SecretGuard / PromptInjectionGuard / ToolInjectionGuard
→ PolicyEngine / CostGuard
→ LMStudioAdapter si provider=lmstudio y enabled=true
→ CommandResult normalizado
```

`model health --provider lmstudio` consulta `/v1/models` en `localhost` con timeout para reportar `available` o `unavailable` sin traceback. Las llamadas de generación usan `/v1/chat/completions` y los embeddings usan `/v1/embeddings`.

## Integración dentro de DevPilot

- `src/devpilot_core/modeling/lmstudio_adapter.py`: adapter local OpenAI-compatible.
- `src/devpilot_core/modeling/router.py`: ruteo hacia LM Studio solo si el provider está habilitado.
- `src/devpilot_core/cli.py`: `model health --provider lmstudio` y timeouts reutilizados.
- `.devpilot/providers.yaml.example`: LM Studio `implemented-initial`, `enabled: false` por defecto.
- `.devpilot/miasi/tool_registry.json`: `model.call.local` y `model.health.local` cubren Ollama/LM Studio.

## Criterios PASS

- La suite base no requiere LM Studio real.
- Health unavailable es controlado.
- Fake server cubre generate/classify/embed.
- Provider disabled bloquea llamadas sin contactar servidor.
- Endpoint remoto queda bloqueado por ProviderRegistry.
- SecretGuard bloquea prompts sensibles antes del provider.
- No hay API externa ni API key.

## Criterios BLOCK

- LM Studio real requerido para tests.
- Base URL remota permitida.
- Prompt con secreto enviado al provider.
- Indisponibilidad produce traceback.
- OpenAI externo queda habilitado o confundido con LM Studio local.

## Riesgos

- Compatibilidad parcial entre versiones de LM Studio y endpoints OpenAI-compatible.
- No hay streaming en esta primera versión.
- No hay retries avanzados ni budget ledger persistente todavía.
- No hay AgentRuntime model-aware todavía.

## Veredicto

El sprint queda implementado como primera versión segura y opcional. Es suficiente para continuar con `FUNC-SPRINT-48 — Model governance: health, capability matrix y budget ledger`.
