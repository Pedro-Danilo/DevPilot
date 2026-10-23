---
doc_id: MP132-R01-12-SPRINT
title: "Trazas provider/agent y coste-origen"
version: "1.0.0-PROPOSED"
status: "SPRINT_EXECUTION_APPROVED"
owner: "DevPilot Owner"
baseline_reference_at_planning: "66ab2e6227072c951b5bd2ac9160e8515b1b9fc0"
execution_baseline: "e79601f630626eb0a2fb8572071e7f1f51742c47"
execution_authority: true
approval_scope: "INDIVIDUAL_OWNER_APPROVAL_R01_12"
source_backlog: "BACKLOG_R01_132.md"
---

# R01-12 — Trazas provider/agent y coste-origen

## Objetivo y alcance
Exponer provenance de ruta/modelo/fallback/error/costo y origen en Guided/Expert sin secretos, enlazado a recibos reales del kernel.

- **Ítems estables cubiertos:** MP131-R1-07.
- **Dependencia de entrada:** R01-11 evidencia focal PASS; HEAD rebindeado antes de implementar.
- **Fuentes a auditar antes de decidir la allowlist:** `src/devpilot_core/generation/`; `src/devpilot_core/modeling/`; `ui/web/src/`.
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
- Trazas redactadas, estados NOT_AVAILABLE honestos; UI muestra origen y coste sin claves.
- Ningún cambio fuera de la allowlist aprobada y todos los reportes citan el HEAD/resultados reales.
- Sin falsa equivalencia por LF/CRLF: comparar blobs Git o texto canónico únicamente cuando el contrato sea textual; binarios por SHA exacto.
- **Riesgos / límites:** No llamada E, no cifra inventada, no logs de prompts sensibles.

## Entregables y validación Windows
Bundle independiente ZIP de nombre corto con `GUIA_UNICA_WINDOWS.md`, operador Python, patches/diffs, tests, receipts y manifest SHA. Descarga a `C:\Users\Pedro\Downloads`; evidencia fuera del repo; comandos PowerShell en una sola línea con `PASS` verde / `BLOCK` rojo. No copiar toda la documentación histórica al operador.

## Permisos, costo y control
- Ruta base: mock/D sin API key ni costo. L local sólo cuando sea necesario y con autorización; E/external siempre DENY hasta R8.
- No realizar `reset --hard`, `force push`, borrados ni sobreescritura sin consentimiento específico. Evitar autorizaciones para lecturas o verificaciones triviales.
- **Estado sucesor:** `SPRINT_EXECUTION_APPROVED` por autorización individual Owner del 2026-10-15; únicamente R01-12, sin autorizar R01-13.

## Criterio de STOP
Bloquear solamente por discrepancia material de autoridad, seguridad, source real, defectos funcionales S0/S1 o pruebas exigidas incumplidas. Hallazgos cosméticos `OBSERVE_ONLY`; documentar sin encadenar microcorrectivos.

## Rebind e ingeniería de la ejecución 167

Fuente Git acreditada: `e79601f630626eb0a2fb8572071e7f1f51742c47` en `evolution/multiprovider-v2`. Dependencia R01-11: `CLOSED/WINDOWS_PASS_WITH_FINDINGS` mediante COR-166. Fuente de verdad del programa: `BACKLOG_R01_132.md`, sprint y prompt Owner literales.

Delta concreto: no duplicar el kernel de routing ni llamar a proveedores; proyectar únicamente campos permitidos de `runtime_provenance` y `execution_receipt`, hash de enlace y `NOT_AVAILABLE` sin medición; vistas Guided y Expert redactadas; trazas de agentes selladas con costo desconocido no igual a cero. La revisión browser Windows precede al push.
