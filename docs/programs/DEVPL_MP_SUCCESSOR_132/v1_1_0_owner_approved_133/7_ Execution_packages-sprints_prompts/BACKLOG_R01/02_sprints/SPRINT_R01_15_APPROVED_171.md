---
doc_id: MP132-R01-15-SPRINT
title: "Madurez M1 y cierre de la primera vertical"
version: "1.0.0-PROPOSED"
status: "SPRINT_EXECUTION_APPROVED"
owner: "DevPilot Owner"
baseline_reference_at_planning: "66ab2e6227072c951b5bd2ac9160e8515b1b9fc0"
execution_baseline: "feaac2723c1f8a467f5cdb7d456e4e7679dd0f82"
execution_authority: true
approval_scope: "R01_15_INDIVIDUAL_OWNER_APPROVAL"
source_backlog: "BACKLOG_R01_132.md"
---

# R01-15 — Madurez M1 y cierre de la primera vertical

## Objetivo y alcance
Consolidar nivel FOUNDATION_PRESENT vs VERTICAL_INTEGRATED; evidencia API/UI/negative tests y transferencia concreta a R2; cierre M1 solo si criterios reales.

- **Ítems estables cubiertos:** MP132-R1-16.
- **Dependencia de entrada:** R01-14 evidencia focal PASS; HEAD rebindeado antes de implementar.
- **Fuentes a auditar antes de decidir la allowlist:** `src/devpilot_core/`; `tests/`; `ui/web/`.
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
- Pruebas integradas de candidate→policy→docs→Settings según vertical ejecutada; report PASS_WITH_FINDINGS/PARTIAL honesto.
- Ningún cambio fuera de la allowlist aprobada y todos los reportes citan el HEAD/resultados reales.
- Sin falsa equivalencia por LF/CRLF: comparar blobs Git o texto canónico únicamente cuando el contrato sea textual; binarios por SHA exacto.
- **Riesgos / límites:** Full regression solo por riesgo documentado o gate final; no habilita R2, L real, E, MP-1B.

## Entregables y validación Windows
Bundle independiente ZIP de nombre corto con `GUIA_UNICA_WINDOWS.md`, operador Python, patches/diffs, tests, receipts y manifest SHA. Descarga a `C:\Users\Pedro\Downloads`; evidencia fuera del repo; comandos PowerShell en una sola línea con `PASS` verde / `BLOCK` rojo. No copiar toda la documentación histórica al operador.

## Permisos, costo y control
- Ruta base: mock/D sin API key ni costo. L local sólo cuando sea necesario y con autorización; E/external siempre DENY hasta R8.
- No realizar `reset --hard`, `force push`, borrados ni sobreescritura sin consentimiento específico. Evitar autorizaciones para lecturas o verificaciones triviales.
- **Estado inicial:** `DRAFT_EXECUTION_GATED`; el programa Owner-133 autoriza planificar, **no ejecutar** este sprint.

## Criterio de STOP
Bloquear solamente por discrepancia material de autoridad, seguridad, source real, defectos funcionales S0/S1 o pruebas exigidas incumplidas. Hallazgos cosméticos `OBSERVE_ONLY`; documentar sin encadenar microcorrectivos.

## Rebind de ejecución / delta aprobado 171

La autorización individual procede de la orden Owner de 15-10-2026. Baseline de entrada feaac2723c1f8a467f5cdb7d456e4e7679dd0f82. Alcance exacto: seis rutas Git según `05_inputs/manifest.json`. Estado final M1 = PASS_WITH_FINDINGS únicamente para vertical determinista/UI previamente verificada; real L/E y R2 no autorizados. Pruebas positivas/negativas y evidencia de los 14 receipts adjuntados al ledger. No se ejecuta full regression por ausencia de excepción de riesgo.
