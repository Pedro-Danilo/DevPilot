---
doc_id: ADR-MP132-R02-04-LOCAL-MODEL-LAB
status: accepted-for-implementation-only
baseline: f2f7bf817e45b38feeb7bb64e638d3df626f825e
scope: R02-04
---
# ADR — Separación Configuración / Laboratorio de modelos

**Contexto:** el panel Providers era un `<details>` cerrado y su reconstrucción tras cada acción volvía a plegarlo; las inferencias reales aparecían bajo Configuración. El contrato R02-04 añade el segundo runtime local opcional.

**Decisión:** mantener proveedores/health/plan-only en `/settings` (sección activa siempre visible) y mover las inferencias sintéticas one-shot a `/model-lab` bajo el grupo IA. Mantener el endpoint Ollama existente por compatibilidad; añadir solo el endpoint LM Studio con RBAC Owner, sesión humana/CSRF, loopback, fixture/JSON validados, timeout, request-id idempotente y recibos runtime-only. Ningún write FROZEN ni global provider enablement.

**Consecuencias:** los candidatos son trazables y comparables por caso/fixture; no son ni quality pass ni approval. Si LM Studio no está instalado el estado es DEFERRED_WITH_REASON/NOT_TESTED. No forzar su instalación ni usar claves de API externa. Los runtime adapters existentes mantienen una sola autoridad de endpoint policy.

**Límites:** no se implementa automatic model selection, eval judge, RAG semántico ni integración Pilot B; requieren scopes posteriores. Se mantiene la ruta determinista offline.
