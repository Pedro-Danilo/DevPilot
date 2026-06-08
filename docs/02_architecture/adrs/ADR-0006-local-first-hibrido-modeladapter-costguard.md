---
title: "ADR-0006 — Local-first híbrido con ModelAdapter y CostGuard"
doc_id: "DEVPL-ADR-0006"
status: "accepted"
version: "1.1.0"
owner: "Ordóñez"
standard: "MIPSoftware"
extension: "MIASI"
phase: "SPRINT-PRECODE-03"
updated: "2026-06-08"
approval: "approved_by_owner_direction"
accepted_by: "Ordóñez"
accepted_at: "2026-06-04"
acceptance_scope: "SPRINT-PRECODE-03 architecture baseline"
---
# ADR-0006 — Local-first híbrido con ModelAdapter y CostGuard

## Estado

Proposed.

## Contexto

DevPilot Local debe operar sin nube obligatoria, pero el owner ha definido que esto no debe impedir el uso de modelos locales o APIs externas cuando aporten calidad. El costo cero es deseable por defecto, pero no debe convertirse en una restricción que degrade el producto maduro.

## Decisión

Adoptar una estrategia local-first híbrida: mock/rule-based por defecto, modelos locales opcionales y APIs externas opcionales. Toda integración de proveedor pasa por ModelAdapter, SecretGuard, ProviderPolicy, CostGuard, evaluación y trazabilidad.

## Consecuencias positivas

- Evita lock-in de proveedor.
- Permite funcionar sin API keys.
- Permite mejorar calidad cuando un modelo externo lo justifique.
- Hace explícitos presupuesto, costos y consentimiento.

## Consecuencias negativas / riesgos

- Aumenta complejidad de configuración.
- Requiere gestión segura de secretos.
- Requiere métricas de calidad/costo para justificar proveedores externos.

## Controles obligatorios

- API keys opcionales, nunca requeridas para tests herméticos.
- Presupuesto por workspace/proveedor/modelo.
- Redacción de secretos y prompts sensibles.
- Fallback local/mock si falla proveedor.
- Reporte de costo por run.

## Criterios de aceptación

- El sistema funciona sin API key.
- Una llamada externa no se ejecuta sin proveedor configurado.
- Todo uso externo deja evento de costo y trazabilidad.
- Tests offline no requieren red.


## Actualización FUNC-SPRINT-17

Estado: implementación inicial materializada.

Sprint 17 introduce `src/devpilot_core/modeling/` con `ModelAdapter`, `MockModelAdapter`, `ProviderRegistry` y `ModelAdapterRouter`. La decisión local-first se mantiene: el proveedor `mock` es el único ejecutable, mientras que Ollama/LM Studio quedan como placeholders locales y OpenAI/Gemini como placeholders externos bloqueados por CostGuard.

La configuración versionada se limita a `.devpilot/providers.yaml.example`, que contiene metadata y nombres de variables de entorno, nunca valores secretos. `.devpilot/providers.yaml` queda ignorado para configuración local futura.

Criterios mantenidos:

- DevPilot funciona sin API key.
- Las pruebas son offline.
- No hay llamadas de red.
- Las APIs externas se bloquean por defecto.
- SecretGuard bloquea prompts/textos con secretos sintéticos.
- CostGuard evalúa proveedor, costo estimado y política local antes de cualquier ruta.

Riesgo residual: no existe aún integración real con proveedores locales/API, medición real de tokens, latencia, retries, rate limits ni facturación. Estos elementos requieren sprints posteriores y, si habilitan red o costo real, una actualización adicional de ADR/política.
