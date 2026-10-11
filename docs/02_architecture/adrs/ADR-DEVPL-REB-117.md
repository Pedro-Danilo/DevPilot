---
doc_id: "ADR-DEVPL-REB-117"
title: "ADR — transición de Pilot A a programa de convergencia reforzada"
version: "1.0.0"
status: "APPROVED / EXECUTION-GATED"
date: "2026-10-11"
owner_decision: "OWNER-APPROVAL-2026-10-11-REBASELINE-116"
implementation_authority: false
multiprovider_stop_lifted: false
---

# ADR — transición de Pilot A a programa de convergencia reforzada

## Contexto
Tres stories Greenfield implementadas comprueban el circuito de cambio gobernado. Extender proveedores fijos hasta ocho stories produce trabajo específico que no acredita ingeniería general. MP v2.1 ya incorpora diseño de generación por modelo y núcleo determinístico. Su STOP protege el aislamiento y requiere un successor de dependencia sin alterar historias.

## Decisión
Adoptar P0–P3 como vía formal, mantener `D05 PARTIAL_ACCEPTANCE`, exigir recuperación D06 real, auditar ambas ramas obligatoriamente antes de diseñar SYNC-1 y posponer la reprogramación global de MP hasta tener un resultado de fusión verificable. No resolver de antemano qué parte de `GeneralStoryProvider` se importará: auditar equivalencia frente a los servicios y policies existentes de MP.

## Reglas de arquitectura
- `GenerationRouteResolver/ProviderSelectionPolicy` MP conserva la responsabilidad objetivo de routing general; no mantener dos routers activos sin justificación basada en código y tests.
- Ningún motor de propuesta concede autoridad de SourceChangePlan, Quality, approval, Git, install, rollback o red.
- Pilot A es fuente de fixtures y evidencia, no release E2E de producto.
- Preserve ADR-MP-V2-007 y ADR-MP-V2-008 en sus invariantes; este ADR es successor del calendario y gates de ADR-008, no reemplazo de las reglas de integridad Git.
- Control de versiones documentales en source registry, con tests y permanencia de históricos FROZEN.

## Consecuencias
Requiere P0 documental en ambos tracks y una auditoría P3-A exhaustiva; puede diferir MP-1B hasta completar SYNC-1 pero evita duplicación y fallos de integración posteriores. Si un análisis de estado contradice el beneficio de la estrategia, la auditoría debe demostrarlo y llevar una alternativa explícita al Owner; no ejecutar un merge predeterminado.
