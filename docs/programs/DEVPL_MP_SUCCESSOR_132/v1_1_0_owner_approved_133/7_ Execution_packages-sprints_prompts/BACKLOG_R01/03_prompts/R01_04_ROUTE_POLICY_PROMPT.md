---
doc_id: MP132-R01-04-IMPLEMENTATION-PROMPT
version: "1.0.0-PROPOSED"
status: "DRAFT_AWAITING_OWNER_INCREMENT_APPROVAL"
linked_sprint: "R01_04_ROUTE_POLICY_SPRINT.md"
execution_authority: false
planning_baseline: "66ab2e6227072c951b5bd2ac9160e8515b1b9fc0"
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

**Este prompt es planificación propuesta; no confiere aprobación Owner de ejecución.**
