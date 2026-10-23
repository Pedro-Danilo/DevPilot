---
doc_id: MP132-R01-04-IMPLEMENTATION-PROMPT
version: "1.0.1-APPROVED-156"
status: "OWNER_APPROVED"
linked_sprint: "SPRINT_R01_04_APPROVED_156.md"
execution_authority: true
approved_execution_baseline: "0815106cf57444609a20e1b537e88c96d8787dbb"
---

# Prompt R01-04 — Policy/budget y GenerationRoutePolicy D/L/E

Actúa como ingeniero responsable de DevPilot Local. Implementa **únicamente** el sprint `R01_04_ROUTE_POLICY_SPRINT.md` y los ítems MP131-R1-04, MP132-R1-12, cuando el Owner autorice individualmente este incremento. Antes de cualquier mutación Git, rebindea a `D:\Projects\DevPilot_Local`, rama `evolution/multiprovider-v2`, HEAD vivo, y comprueba que el sprint predecesor está aceptado según evidencia (para R01-01, cierre M0 COR-151).

## Trabajo solicitado

Combinar routing actual con política default-deny, presupuesto, decisiones por tipo de tarea y fallback EQUIVALENT/REDUCED/MODEL_REQUIRED auditable.

1. Consulta literalmente el sprint, `BACKLOG_R01_132.md`, los contratos programáticos pertinentes, la fuente viva y las pruebas existentes. No adivines API, paths ni estado de ejecución.
2. Produce un `Reuse/Delta Map` verificable. Evalúa `REUSE_AS_IS`, `NO_OP_ACCEPTED`, delta mínimo y riesgos. No abras cambios ajenos a este sprint.
3. Especifica la allowlist exacta a partir de inspección, endpoints/contratos afectados, pruebas positivas y negativas, idempotencia y rollback; crear ADR únicamente si existe decisión nueva.
4. Implementa un candidato local sobre copia aislada, sin APIs externas ni herramientas de borrado. Diseña operator Python focal, con estado reanudable basado en Git real; no crear dependencia de carpetas hermanas externas al ZIP.
5. Ejecuta pruebas unitarias/servicio y browser cuando lo exija el sprint; registra el nivel real de evidencia. Validación exigida: Prueba deny antes de invocar provider; timeout y presupuesto negativos; MODEL_REQUIRED no false PASS.
6. Prepara un solo bundle Windows con `GUIA_UNICA_WINDOWS.md` totalmente consecutiva (ningún volver/saltar paso), comandos PowerShell cada uno en una línea con estados PASS/BLOCK, evidencias exactas y rollback explícito.
7. No aplicar/cerrar automáticamente: informar `LOCAL_PASS/WINDOWS_PENDING` hasta recibir evidencia Windows y adjudicarla según el contrato del sprint. Evitar FULL REGRESSION salvo excepción justificada.

## Prohibiciones y controles
E siempre DENIED; D/mock disponible; sin fallback oculto ni costes reales. Ninguna API key por defecto, egress DENY, sin proveedor de pago, sin cambio de rama/worktree ni habilitar MP-1B. Comparar **contenido de Git**, no bytes de checkout CRLF/LF, excepto cuando el contrato exige bytes exactos. El operador debe aceptar reejecución idempotente y detenerse ante source drift real.

## Salida requerida
1. Resumen técnico del delta y rationale arquitectónico.
2. Paquete ZIP descargable con guía única y manifest SHA; Python modular + pruebas completas relevantes.
3. Checkpoints `aprendido/implementado/probado/pendiente` y errores reales.
4. Identificación expresa del sprint siguiente R01-05 (si aplica).

**Aprobación Owner individual formalizada exclusivamente para R01-04. La publicación Git requiere su autorización material separada.**


## Addendum ejecutivo COR-156 — rebind y alcance

- **HEAD de entrada comprobado por evidencia COR-155:** `0815106cf57444609a20e1b537e88c96d8787dbb`; rama `evolution/multiprovider-v2`, repo `D:\Projects\DevPilot_Local`.
- **Fuentes de verdad:** Git archive R01-03 COR-155, backlog Owner R01 y contratos `GenerationRouteResolver`, `ProviderSelectionPolicy`, `ModelRouterV2`, `CostGuard`, `GenerationRequest`, `OfflineCapabilityNegotiator`.
- **Reuse:** gateway, control de tokens y costos, provenance/fallback de MP-0D conservados; ningún provider adapter ni infraestructura UI se modifica.
- **Delta:** `GenerationRoutePolicy` de planificación offline para tareas explícitas, costos y timeout, fallback EQUIVALENT/REDUCED/MODEL_REQUIRED con consentimiento y trazas; nunca ejecuta una inferencia L/E.
- **Allowlist Git:** `src/devpilot_core/generation/route_policy.py`, `src/devpilot_core/generation/__init__.py`, `tests/test_mp132_r01_04_route_policy.py`.
- **Egress E:** `DENIED` incluso ante configuraciones permisivas. L puede ser planificado sin elegibilidad ejecutiva; D/mock único caso ejecutable desde el contrato de planificación.
- **Pruebas:** 116 pruebas focales PASS sobre copia aislada; 5 pruebas focales de operador Git (la ejecución Windows sigue pendiente).
- **Límites:** no se implementan R01-05, provider health real, rutas externas, modelos ejecutables, UI, ni MP-1B. ADR técnica incluida en el bundle para incorporación documental gobernada posterior.
