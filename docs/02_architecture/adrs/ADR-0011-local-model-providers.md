---
title: "ADR-0011 — Proveedores locales de modelos gobernados"
doc_id: "DEVPL-ADR-0011"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
standard: "MIPSoftware"
extension: "MIASI"
phase: "FUNC-SPRINT-45"
updated: "2026-06-12"
accepted_by: "Ordóñez"
accepted_at: "2026-06-12"
acceptance_scope: "FUNC-SPRINT-45 ADR y contratos de proveedores locales"
approval: "approved_by_owner"
---
# ADR-0011 — Proveedores locales de modelos gobernados

## Estado

Accepted.

## Contexto

Después del cierre de Fase C, DevPilot tiene gates determinísticos, PolicyEngine, SecretGuard, CostGuard, Approval Workflow, ejecución controlada, MIASI registries y `repo engineering-gate`. El informe de avance 0–18 ya identificaba que existía `ModelAdapter` mock y `ProviderRegistry`, pero que aún faltaban clientes reales Ollama/LM Studio y agentes LLM-driven.

La Fase D debe introducir IA local real sin perder el principio local-first, sin costos de API por defecto y sin habilitar agentes autónomos. Por eso el primer paso no es conectar Ollama o LM Studio directamente, sino formalizar contratos, configuración, estados y límites de activación.

## Decisión

DevPilot adoptará un modelo de proveedores de IA local gobernada con estas reglas:

1. `mock` es proveedor obligatorio, habilitado por defecto y usado por pruebas base.
2. `ollama` y `lmstudio` son proveedores locales opcionales, deshabilitados por defecto en `FUNC-SPRINT-45`.
3. Los endpoints locales deben ser `http://localhost`, `http://127.0.0.1` o `http://[::1]`.
4. Proveedores externos como OpenAI/Gemini siguen declarados únicamente como placeholders `disabled`.
5. Ningún provider config puede contener API keys crudas, tokens o secretos; solo nombres de variables de entorno como `OPENAI_API_KEY`.
6. Toda llamada futura debe pasar por `ModelAdapterRouter`, `ProviderRegistry`, `PolicyEngine`, `SecretGuard` y `CostGuard`.
7. `FUNC-SPRINT-45` no implementa adaptadores reales ni contacta servidores locales o APIs externas.

## Alternativas consideradas

| Alternativa | Evaluación |
|---|---|
| Implementar OllamaAdapter directamente | Acelera demo, pero introduce riesgo antes de cerrar contratos, schemas y política. |
| Permitir cualquier OpenAI-compatible base_url | Flexible, pero inseguro porque puede apuntar a red externa. |
| Mantener solo mock hasta agentes | Seguro, pero bloquea preparación real de Fase D. |
| Crear contrato primero | Decisión adoptada: permite avanzar con seguridad y pruebas herméticas. |

## Consecuencias positivas

- La Fase D inicia con una frontera clara entre `mock`, `local` y `api`.
- La suite base no depende de Ollama, LM Studio ni internet.
- CostGuard y PolicyEngine siguen bloqueando proveedores externos.
- Los adapters locales futuros tendrán contrato estable.
- Los operadores pueden editar `.devpilot/providers.yaml` sin versionar secretos.

## Consecuencias negativas

- Ollama/LM Studio aún no generan respuestas reales en este sprint.
- El contrato provider config se vuelve más estricto y puede bloquear configuraciones ambiguas.
- Hay que mantener sincronizados schema, parser narrow YAML, ProviderRegistry y documentación.

## Funcionamiento esperado

`ProviderRegistry` carga, en orden:

1. `.devpilot/providers.yaml`, si existe;
2. `.devpilot/providers.yaml.example`, si no existe configuración local;
3. defaults internos seguros.

Luego ejecuta controles semánticos:

- mock habilitado;
- ids únicos;
- proveedores locales localhost-only;
- proveedores locales sin API keys;
- proveedores externos disabled;
- valores secretos bloqueados.

`python -m devpilot_core model providers --json` debe mostrar el estado de los proveedores y bloquear si la configuración viola estos contratos.

## Criterios PASS

- Existe esta ADR aprobada.
- `.devpilot/providers.yaml.example` valida contra `provider_config.schema.json`.
- `ProviderRegistry` carga configuración versionada y mantiene defaults seguros.
- `mock` sigue generando, clasificando y embebiendo sin red.
- Ollama/LM Studio quedan deshabilitados por defecto.
- APIs externas quedan deshabilitadas y bloqueadas.
- MIASI declara herramientas/políticas de modelo local controlado.

## Criterios BLOCK

- Proveedor local requerido para que pase `pytest -q`.
- API externa habilitada por defecto.
- API key cruda versionada en YAML.
- Local provider con endpoint remoto.
- Agentes llamando adapters directamente sin router.

## Riesgos

- El schema cubre estructura y parte de seguridad, pero las reglas semánticas deben seguir en Python.
- Los endpoints de Ollama/LM Studio pueden cambiar; los adapters futuros deben encapsular compatibilidad.
- Un usuario puede crear `.devpilot/providers.yaml` local inválido; DevPilot debe fallar cerrado.

## Relación con DevPilot

Esta ADR implementa el nivel FD-L0 de Fase D. Es prerrequisito para `FUNC-SPRINT-46 — OllamaAdapter local opcional` y `FUNC-SPRINT-47 — LMStudioAdapter local OpenAI-compatible`.
