---
doc_id: MP132-R01-06-SPRINT
title: "Catalog/Coverage ejecutable"
version: "1.0.0-PROPOSED"
status: "SPRINT_EXECUTION_APPROVED"
owner: "DevPilot Owner"
baseline_reference_at_planning: "154e5eb20fffce2e884dd8f2bc3c4ae46e7d73b7"
execution_authority: true
approval_scope: "OWNER_INCREMENT_R01_06_ONLY"
source_backlog: "BACKLOG_R01_132.md"
---

# R01-06 — Catalog/Coverage ejecutable

## Objetivo y alcance
Registrar requeridos/condicionales/recomendados/N-A y dependencias por etapa, con gate que distingue archivo existente de contenido aceptable.

- **Ítems estables cubiertos:** MP132-R1-09.
- **Dependencia de entrada:** R01-05 evidencia focal PASS; HEAD rebindeado antes de implementar.
- **Fuentes a auditar antes de decidir la allowlist:** `src/devpilot_core/validators/artifact_profiles.py`; `docs/schemas/artifact_profiles.schema.json`; `.devpilot/`.
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
- Required ausente BLOCK; recommended WARN; conditional sin evidencia REVIEW_REQUIRED.
- Ningún cambio fuera de la allowlist aprobada y todos los reportes citan el HEAD/resultados reales.
- Sin falsa equivalencia por LF/CRLF: comparar blobs Git o texto canónico únicamente cuando el contrato sea textual; binarios por SHA exacto.
- **Riesgos / límites:** No templates vacíos; no cobertura global artificial.

## Entregables y validación Windows
Bundle independiente ZIP de nombre corto con `GUIA_UNICA_WINDOWS.md`, operador Python, patches/diffs, tests, receipts y manifest SHA. Descarga a `C:\Users\Pedro\Downloads`; evidencia fuera del repo; comandos PowerShell en una sola línea con `PASS` verde / `BLOCK` rojo. No copiar toda la documentación histórica al operador.

## Permisos, costo y control
- Ruta base: mock/D sin API key ni costo. L local sólo cuando sea necesario y con autorización; E/external siempre DENY hasta R8.
- No realizar `reset --hard`, `force push`, borrados ni sobreescritura sin consentimiento específico. Evitar autorizaciones para lecturas o verificaciones triviales.
- **Estado inicial:** `DRAFT_EXECUTION_GATED`; el programa Owner-133 autoriza planificar, **no ejecutar** este sprint.

## Criterio de STOP
Bloquear solamente por discrepancia material de autoridad, seguridad, source real, defectos funcionales S0/S1 o pruebas exigidas incumplidas. Hallazgos cosméticos `OBSERVE_ONLY`; documentar sin encadenar microcorrectivos.

## Rebind de ejecución R01-06 / 158

- Aprobación Owner individual: sprint y prompt R01-06 únicamente, instrucción expresa de este turno; sin aprobación de R01-07.
- Baseline vivo: `154e5eb20fffce2e884dd8f2bc3c4ae46e7d73b7`, rama `evolution/multiprovider-v2`, worktree `D:\Projects\DevPilot_Local`.
- Estado de R01-05: CLOSED / WINDOWS_PASS; evidencia SHA/CRC, 90 pruebas, cinco rutas y promoción.
- Reuse/Delta: `ArtifactProfileRegistry` fuente única; evaluador independiente `ArtifactCoverageGate`, sin catálogo paralelo.
- Alcance Git exacto: `src/devpilot_core/validation/artifact_coverage_gate.py`, `src/devpilot_core/validation/artifact_profile_registry.py`, `tests/test_mp132_r01_06_coverage_gate.py`.
- Niveles probatorios: código/servicio mock + pruebas focales; sin aceptación semántica por automatismo, browser no exigido, sin modelos.
- Sólo dos aprobaciones materiales: commit local y push normal. Sin full regression ni egress.
