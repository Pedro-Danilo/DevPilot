---
doc_id: MP132-R01-03-IMPLEMENTATION-PROMPT
version: "1.0.1-OWNER-APPROVED-155"
status: "OWNER_APPROVED"
linked_sprint: "SPRINT_R01_03_APPROVED_155.md"
execution_authority: true
planning_baseline: "0505ab2ee0711561d3c2e68511ce05aea8c857b1"
---

# Prompt R01-03 — ModelAdapter y negotiation por capacidades

Actúa como ingeniero responsable de DevPilot Local. Implementa **únicamente** el sprint `SPRINT_R01_03_APPROVED_155.md` y los ítems MP131-R1-03, cuando el Owner autorice individualmente este incremento. Antes de cualquier mutación Git, rebindea a `D:\Projects\DevPilot_Local`, rama `evolution/multiprovider-v2`, HEAD vivo, y comprueba que el sprint predecesor está aceptado según evidencia (para R01-01, cierre M0 COR-151).

## Trabajo solicitado

Definir puerto mínimo proveedor-independiente y adapters mock/local; separar SUPPORTED, CONFIGURED, HEALTHY, EVALUATED, ELIGIBLE, tool/stream/timeout.

1. Consulta literalmente el sprint, `BACKLOG_R01_132.md`, los contratos programáticos pertinentes, la fuente viva y las pruebas existentes. No adivines API, paths ni estado de ejecución.
2. Produce un `Reuse/Delta Map` verificable. Evalúa `REUSE_AS_IS`, `NO_OP_ACCEPTED`, delta mínimo y riesgos. No abras cambios ajenos a este sprint.
3. Especifica la allowlist exacta a partir de inspección, endpoints/contratos afectados, pruebas positivas y negativas, idempotencia y rollback; crear ADR únicamente si existe decisión nueva.
4. Implementa un candidato local sobre copia aislada, sin APIs externas ni herramientas de borrado. Diseña operator Python focal, con estado reanudable basado en Git real; no crear dependencia de carpetas hermanas externas al ZIP.
5. Ejecuta pruebas unitarias/servicio y browser cuando lo exija el sprint; registra el nivel real de evidencia. Validación exigida: Contrato con mock y adapter local stub sin servidor; falla de proveedor no habilita otro silenciosamente.
6. Prepara un solo bundle Windows con `GUIA_UNICA_WINDOWS.md` totalmente consecutiva (ningún volver/saltar paso), comandos PowerShell cada uno en una línea con estados PASS/BLOCK, evidencias exactas y rollback explícito.
7. No aplicar/cerrar automáticamente: informar `LOCAL_PASS/WINDOWS_PENDING` hasta recibir evidencia Windows y adjudicarla según el contrato del sprint. Evitar FULL REGRESSION salvo excepción justificada.

## Prohibiciones y controles
Sin API key, sin iniciar Ollama/LM Studio, sin instalar modelos; E deshabilitado. Ninguna API key por defecto, egress DENY, sin proveedor de pago, sin cambio de rama/worktree ni habilitar MP-1B. Comparar **contenido de Git**, no bytes de checkout CRLF/LF, excepto cuando el contrato exige bytes exactos. El operador debe aceptar reejecución idempotente y detenerse ante source drift real.

## Salida requerida
1. Resumen técnico del delta y rationale arquitectónico.
2. Paquete ZIP descargable con guía única y manifest SHA; Python modular + pruebas completas relevantes.
3. Checkpoints `aprendido/implementado/probado/pendiente` y errores reales.
4. Identificación expresa del sprint siguiente R01-04 (si aplica).

**Aprobación Owner individual para ejecutar únicamente R01-03, otorgada mediante el prompt del usuario. No autoriza R01-04, R2, MP-1B ni proveedor externo.**

## Rebind y alcance de ejecución COR-155 (15-10-2026)

- Baseline fuente: `0505ab2ee0711561d3c2e68511ce05aea8c857b1`, rama `evolution/multiprovider-v2`, raíz `D:\Projects\DevPilot_Local`.
- Prerrequisito R01-02: HEAD `0505ab2ee0711561d3c2e68511ce05aea8c857b1`, focal 29/29 y remoto confirmado según evidencia Windows.
- Allowlist exacta: `src/devpilot_core/modeling/__init__.py`, `src/devpilot_core/modeling/negotiation.py`, `tests/test_mp132_r01_03_negotiation.py`.
- Cambios: puerto `ModelAdapter` preexistente reutilizado; negociación offline, mock y stub local sin servidor.
- Estados explícitos SUPPORTED, CONFIGURED, HEALTHY, EVALUATED, ELIGIBLE; sin fallback silencioso ni egress.
- No activa Ollama, LM Studio, APIs externas, routers de ejecución ni MP-1B.
- Validación local: tests mock/stub + gateway; Windows pendiente.
- Autoridad del Owner: solo R01-03; la publicación Git requiere autorización de commit/push en guía.
