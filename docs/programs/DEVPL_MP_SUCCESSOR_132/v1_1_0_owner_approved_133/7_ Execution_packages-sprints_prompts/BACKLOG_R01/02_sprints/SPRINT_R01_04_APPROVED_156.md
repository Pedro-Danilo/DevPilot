---
doc_id: MP132-R01-04-SPRINT
title: "Policy/budget y GenerationRoutePolicy D/L/E"
version: "1.0.1-APPROVED-156"
status: "SPRINT_EXECUTION_APPROVED"
owner: "DevPilot Owner"
approved_execution_baseline: "0815106cf57444609a20e1b537e88c96d8787dbb"
execution_authority: true
approval_scope: "R01_04_ONLY"
source_backlog: "BACKLOG_R01_132.md"
---

# R01-04 — Policy/budget y GenerationRoutePolicy D/L/E

## Objetivo y alcance
Combinar routing actual con política default-deny, presupuesto, decisiones por tipo de tarea y fallback EQUIVALENT/REDUCED/MODEL_REQUIRED auditable.

- **Ítems estables cubiertos:** MP131-R1-04, MP132-R1-12.
- **Dependencia de entrada:** R01-03 evidencia focal PASS; HEAD rebindeado antes de implementar.
- **Fuentes a auditar antes de decidir la allowlist:** `src/devpilot_core/generation/runtime.py`; `docs/schemas/model_routing_decision_v2.schema.json`; `src/devpilot_core/modeling/`.
- **No ampliar la ola:** R01 únicamente; R2/R8/R7 no se ejecutan.

## Decisión técnica y porqué
Ningún cambio sin inspección previa del HEAD recibido del incremento anterior. Reutilizar contratos existentes; un solo owner por capacidad. Un `NO_OP_ACCEPTED` es admisible cuando la evidencia demuestra una capacidad ya existente. Separar claramente `mock`, `service`, `UI browser` y `modelo real`.

## Micro-checkpoints secuenciales (sin regresiones completas)
1. **A0/A1 – Preflight y Reuse/Delta.** Comprobar Git tres estados, rama `evolution/multiprovider-v2`, HEAD vivo, portabilidad de tests y matriz de autoridad; identificar firmas existentes y documentación actual vs histórica.
2. **A2 – Diseño focal.** Delimitar el cambio, contratos afectados, `allowlist` **exacta**, criterios negativos y ADR sucesora solamente si cambia una decisión arquitectónica; no inventar dependencias ni rutas.
3. **A3 – Dry-run controlado.** Crear parche en copia aislada; validar preimage por hash de blobs Git y compatibilidad con el baseline; no modificar source antes de aprobación del cambio material.
4. **A4 – Implementación acotada.** Aplicar exclusivamente los paths aprobados, con idempotencia y reanudación por HEAD y estado Git real; dry-run es el modo predeterminado.
5. **A5 – Validación y promoción.** Pruebas focales positivas/negativas y browser si la superficie es UI; commit y push no forzados bajo autorización conforme al impacto. No publicar sin evidencia funcional.
6. **A6 – Resultado.** Recibo técnico, límites, huellas y estado `PASS|PASS_WITH_FINDINGS|PARTIAL|BLOCK|NO_OP_ACCEPTED`, con una guía Windows única para la ejecución del incremento.

## Criterios de aceptación verificables
- Prueba deny antes de invocar provider; timeout y presupuesto negativos; MODEL_REQUIRED no false PASS.
- Ningún cambio fuera de la allowlist aprobada y todos los reportes citan el HEAD/resultados reales.
- Sin falsa equivalencia por LF/CRLF: comparar blobs Git o texto canónico únicamente cuando el contrato sea textual; binarios por SHA exacto.
- **Riesgos / límites:** E siempre DENIED; D/mock disponible; sin fallback oculto ni costes reales.

## Entregables y validación Windows
Bundle independiente ZIP de nombre corto con `GUIA_UNICA_WINDOWS.md`, operador Python, patches/diffs, tests, receipts y manifest SHA. Descarga a `C:\Users\Pedro\Downloads`; evidencia fuera del repo; comandos PowerShell en una sola línea con `PASS` verde / `BLOCK` rojo. No copiar toda la documentación histórica al operador.

## Permisos, costo y control
- Ruta base: mock/D sin API key ni costo. L local sólo cuando sea necesario y con autorización; E/external siempre DENY hasta R8.
- No realizar `reset --hard`, `force push`, borrados ni sobreescritura sin consentimiento específico. Evitar autorizaciones para lecturas o verificaciones triviales.
- **Estado actual:** `SPRINT_EXECUTION_APPROVED`, conforme a la aprobación individual del Owner en el prompt de implementación. No autoriza incrementos posteriores.

## Criterio de STOP
Bloquear solamente por discrepancia material de autoridad, seguridad, source real, defectos funcionales S0/S1 o pruebas exigidas incumplidas. Hallazgos cosméticos `OBSERVE_ONLY`; documentar sin encadenar microcorrectivos.


## Addendum ejecutivo COR-156 — rebind y alcance

- **HEAD de entrada comprobado por evidencia COR-155:** `0815106cf57444609a20e1b537e88c96d8787dbb`; rama `evolution/multiprovider-v2`, repo `D:\Projects\DevPilot_Local`.
- **Fuentes de verdad:** Git archive R01-03 COR-155, backlog Owner R01 y contratos `GenerationRouteResolver`, `ProviderSelectionPolicy`, `ModelRouterV2`, `CostGuard`, `GenerationRequest`, `OfflineCapabilityNegotiator`.
- **Reuse:** gateway, control de tokens y costos, provenance/fallback de MP-0D conservados; ningún provider adapter ni infraestructura UI se modifica.
- **Delta:** `GenerationRoutePolicy` de planificación offline para tareas explícitas, costos y timeout, fallback EQUIVALENT/REDUCED/MODEL_REQUIRED con consentimiento y trazas; nunca ejecuta una inferencia L/E.
- **Allowlist Git:** `src/devpilot_core/generation/route_policy.py`, `src/devpilot_core/generation/__init__.py`, `tests/test_mp132_r01_04_route_policy.py`.
- **Egress E:** `DENIED` incluso ante configuraciones permisivas. L puede ser planificado sin elegibilidad ejecutiva; D/mock único caso ejecutable desde el contrato de planificación.
- **Pruebas:** 116 pruebas focales PASS sobre copia aislada; 5 pruebas focales de operador Git (la ejecución Windows sigue pendiente).
- **Límites:** no se implementan R01-05, provider health real, rutas externas, modelos ejecutables, UI, ni MP-1B. ADR técnica incluida en el bundle para incorporación documental gobernada posterior.
