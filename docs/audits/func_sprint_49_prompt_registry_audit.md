---
title: "Auditoría FUNC-SPRINT-49 — Prompt Registry y contratos de prompt seguro"
doc_id: "DEVPL-AUDIT-FUNC-SPRINT-49-001"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-06-12"
standard: "MIPSoftware"
extension: "MIASI"
sprint: "FUNC-SPRINT-49"
approval: "approved_by_owner_direction"
---

# Auditoría FUNC-SPRINT-49 — Prompt Registry y contratos de prompt seguro

## Propósito

Validar que DevPilot incorpora un Prompt Registry versionado, auditable y local-first, evitando prompts sueltos embebidos sin trazabilidad y sin exponer secretos en stdout, reportes o budget ledger.

## Estado

`implemented-initial`. La implementación agrega `PromptRegistry`, `PromptSafetyChecker`, `docs/schemas/prompt.schema.json`, prompts versionados en `docs/prompts/`, comandos CLI read-only y soporte de `model generate --prompt-id` con registro de `prompt_id/version`.

## Funcionamiento

El flujo operativo es:

```text
docs/prompts/*.json
→ docs/schemas/prompt.schema.json
→ PromptRegistry
→ PromptSafetyChecker
→ CLI prompt list/show/validate
→ model generate --prompt-id
→ ModelAdapterRouter
→ BudgetLedger con prompt_id/version y sin prompt crudo
```

`prompt list` lista contratos. `prompt validate` combina schema, semántica, placeholders e inspección básica de seguridad. `prompt show` devuelve una plantilla redacted. `model generate --prompt-id` renderiza únicamente inputs declarados y adjunta `prompt_reference` al resultado.

## Integración dentro de DevPilot

- `src/devpilot_core/prompts/registry.py`: carga, valida, muestra y renderiza prompts versionados.
- `src/devpilot_core/prompts/safety.py`: compone SecretGuard y PromptInjectionGuard para hallazgos básicos.
- `docs/prompts/`: almacena prompts aprobados iniciales.
- `docs/schemas/prompt.schema.json`: contrato estructural de prompts.
- `src/devpilot_core/cli.py`: expone comandos `prompt list/show/validate` y `model generate --prompt-id`.
- `src/devpilot_core/modeling/budget.py`: registra `prompt_id/version` sin prompts crudos.
- `src/devpilot_core/validation/gateway.py`: agrega prompt contracts al scope `contracts`.
- `.devpilot/miasi/*`: registra herramientas y reglas de prompts.

## Criterios PASS

- Prompts tienen `id`, `version`, `status`, `template`, `input_variables`, `safety` y `usage`.
- `prompt validate` pasa para prompts válidos y bloquea contratos incompletos.
- `PromptSafetyChecker` produce findings para secretos e inyección básica.
- `prompt show` no expone secretos crudos.
- `model generate --prompt-id` registra `prompt_id/version` sin guardar prompts crudos en `cost_events`.
- No se habilita red ni API externa.

## Criterios BLOCK

- Prompt sin `id/version` o schema inválido.
- Placeholder usado pero no declarado en `input_variables`.
- `store_raw_prompt=true` o `store_raw_completion=true`.
- Plantilla o render con secreto crudo.
- Prompt injection blocking sin hallazgo estructurado.
- Uso de prompt no versionado por agentes o model calls gobernadas.

## Riesgos

- Los checks de prompt injection son determinísticos y básicos; no reemplazan evaluación adversarial avanzada.
- El registry no implementa herencia de prompt packs ni composición avanzada.
- El render usa sustitución simple de placeholders, no un motor de plantillas completo.
- El sistema registra referencia de prompt, pero no evalúa todavía calidad comparativa por modelo; queda para `FUNC-SPRINT-50`.

## Veredicto

El sprint queda implementado como primera versión gobernada y local-first. Es suficiente para avanzar hacia `FUNC-SPRINT-50 — Model evaluation matrix local`, donde la evaluación deberá usar prompts versionados en vez de instrucciones embebidas sin trazabilidad.
