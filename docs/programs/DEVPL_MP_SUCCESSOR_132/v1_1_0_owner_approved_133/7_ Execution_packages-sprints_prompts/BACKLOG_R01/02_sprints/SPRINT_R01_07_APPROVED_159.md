---
doc_id: MP132-R01-07-SPRINT
title: "Publicación humana Markdown y Source Registry"
version: "1.0.0-PROPOSED"
status: "SPRINT_EXECUTION_APPROVED"
owner: "DevPilot Owner"
baseline_reference_at_planning: "66ab2e6227072c951b5bd2ac9160e8515b1b9fc0"
execution_baseline: "13e7b46c2edd63576a4ab9693fc0b056d3fecb9d"
execution_authority: true
approval_scope: "INDIVIDUAL_R01_07_ONLY"
source_backlog: "BACKLOG_R01_132.md"
---

# R01-07 — Publicación humana Markdown y Source Registry

## Objetivo y alcance
Publicar documentos aprobados en ruta gobernada y reconciliar referencias canónicas/Source Registry con control de drift semántico.

- **Ítems estables cubiertos:** MP132-R1-10.
- **Dependencia de entrada:** R01-06 evidencia focal PASS; HEAD rebindeado antes de implementar.
- **Fuentes a auditar antes de decidir la allowlist:** `src/devpilot_core/application/workspace_documents_service.py`; `src/devpilot_core/interfaces/api/routers/workspace_documents.py`; `.devpilot/docs_governance/`.
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
- Publicación y relectura human-readable, hashes y source graph sincronizados; rechazo de rutas inseguras.
- Ningún cambio fuera de la allowlist aprobada y todos los reportes citan el HEAD/resultados reales.
- Sin falsa equivalencia por LF/CRLF: comparar blobs Git o texto canónico únicamente cuando el contrato sea textual; binarios por SHA exacto.
- **Riesgos / límites:** No sobrescribir FROZEN; LF/CRLF no causan falsos BLOCK.

## Entregables y validación Windows
Bundle independiente ZIP de nombre corto con `GUIA_UNICA_WINDOWS.md`, operador Python, patches/diffs, tests, receipts y manifest SHA. Descarga a `C:\Users\Pedro\Downloads`; evidencia fuera del repo; comandos PowerShell en una sola línea con `PASS` verde / `BLOCK` rojo. No copiar toda la documentación histórica al operador.

## Permisos, costo y control
- Ruta base: mock/D sin API key ni costo. L local sólo cuando sea necesario y con autorización; E/external siempre DENY hasta R8.
- No realizar `reset --hard`, `force push`, borrados ni sobreescritura sin consentimiento específico. Evitar autorizaciones para lecturas o verificaciones triviales.
- **Estado inicial:** `DRAFT_EXECUTION_GATED`; el programa Owner-133 autoriza planificar, **no ejecutar** este sprint.

## Criterio de STOP
Bloquear solamente por discrepancia material de autoridad, seguridad, source real, defectos funcionales S0/S1 o pruebas exigidas incumplidas. Hallazgos cosméticos `OBSERVE_ONLY`; documentar sin encadenar microcorrectivos.

## Rebind aprobado para ejecución R01-07 / 159
- Baseline Windows de entrada: `13e7b46c2edd63576a4ab9693fc0b056d3fecb9d`, rama `evolution/multiprovider-v2`, repo `D:\Projects\DevPilot_Local`.
- R01-06: cierre Windows acreditado, 120/120 pruebas PASS, commit `13e7b46c2edd63576a4ab9693fc0b056d3fecb9d`; contrato R01-07 vigente.
- Delta: servicio `GovernedMarkdownPublisher` independiente del visor de documentos **read-only**. Preview por defecto; ejecución requiere documento aprobado.
- Publicación gobernada limitada a `docs/published/` con identidad, frontmatter, required_tests y cuatro superficies reconciliadas: Markdown, Source Registry, authority graph, overlay de conteo.
- Allowlist Git de implementación: `src/devpilot_core/docs_governance/markdown_publication.py`, `src/devpilot_core/docs_governance/__init__.py`, `tests/test_mp132_r01_07_markdown_publication.py`.
- No publicar documentos de producción automáticamente durante la validación Windows; pruebas usan raíces temporales. El registro existente permanece con 1.752 entradas hasta aprobación de un documento real.
- ADR nueva: sí; sincronización de cuatro superficies bajo bloqueo de exclusión y compensación ante fallo, sin segundo publicador/UI.
- En R01-07 no se cubre integración UI ni generación por LLM. R01-08 no autorizado.
