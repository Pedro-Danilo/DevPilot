---
title: "Auditoría FUNC-SPRINT-46 — OllamaAdapter local opcional"
doc_id: "DEVPL-AUDIT-FUNC-SPRINT-46-001"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-06-12"
standard: "MIPSoftware"
extension: "MIASI"
sprint: "FUNC-SPRINT-46"
approval: "approved_by_owner_direction"
---

# Auditoría FUNC-SPRINT-46 — OllamaAdapter local opcional

## Propósito

Validar que DevPilot incorpora un adaptador Ollama local opcional sin romper la arquitectura local-first, sin requerir servidor Ollama para la suite base y sin habilitar APIs externas.

## Estado

`implemented-initial`. La implementación introduce `OllamaAdapter`, `model health`, timeouts cortos, manejo estructurado de indisponibilidad y pruebas con fake server. Ollama sigue deshabilitado por defecto en `.devpilot/providers.yaml.example`.

## Funcionamiento

El flujo de ejecución es:

```text
CLI model generate/classify/embed
→ ModelAdapterRouter
→ ProviderRegistry
→ SecretGuard / PromptInjectionGuard / ToolInjectionGuard
→ PolicyEngine / CostGuard
→ OllamaAdapter si provider=ollama y enabled=true
→ CommandResult normalizado
```

`model health --provider ollama` puede consultar `/api/tags` en `localhost` con timeout para reportar `available` o `unavailable` sin traceback.

## Integración dentro de DevPilot

- `src/devpilot_core/modeling/ollama_adapter.py`: adapter local.
- `src/devpilot_core/modeling/router.py`: ruteo hacia Ollama solo si el provider está habilitado.
- `src/devpilot_core/cli.py`: comando `model health` y timeouts en comandos model.
- `.devpilot/miasi/tool_registry.json`: `model.health.local` y `model.call.local`.
- `.devpilot/miasi/policy_matrix.json`: `MODEL_LOCAL_HEALTH_ALLOW`.

## Criterios PASS

- La suite base no requiere Ollama real.
- Health unavailable es controlado.
- Fake server cubre generate/classify/embed.
- Provider disabled bloquea llamadas sin contactar servidor.
- SecretGuard bloquea prompts sensibles antes del provider.
- No hay API externa ni API key.

## Criterios BLOCK

- Ollama real requerido para tests.
- Endpoint remoto permitido.
- Prompt con secreto enviado al provider.
- Indisponibilidad produce traceback.
- APIs externas habilitadas.

## Riesgos

- Compatibilidad parcial entre versiones de Ollama.
- No hay streaming en esta primera versión.
- No hay budget ledger persistente todavía.
- No hay AgentRuntime model-aware todavía.

## Veredicto

El sprint queda implementado como primera versión segura y opcional. Es suficiente para continuar con `FUNC-SPRINT-47 — LMStudioAdapter local OpenAI-compatible`.
