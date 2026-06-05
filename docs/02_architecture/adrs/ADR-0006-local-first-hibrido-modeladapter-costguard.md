---
title: "ADR-0006 — Local-first híbrido con ModelAdapter y CostGuard"
doc_id: "DEVPL-ADR-0006"
status: "accepted"
version: "1.0.0"
owner: "Ordóñez"
standard: "MIPSoftware"
extension: "MIASI"
phase: "SPRINT-PRECODE-03"
updated: "2026-06-04"
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
