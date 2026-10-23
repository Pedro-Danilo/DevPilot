---
doc_id: MP132-R01-02-SPRINT
title: "Estado de candidatos, idempotencia y provenance"
version: "1.0.0-PROPOSED"
status: "SPRINT_EXECUTION_APPROVED"
owner: "DevPilot Owner"
baseline_reference_at_planning: "caad145436d26404875dbd800559d27a1db590ba"
execution_authority: true
approval_scope: "R01_02_ONLY"
source_backlog: "BACKLOG_R01_132.md"
---

# R01-02 — Estado de candidatos, idempotencia y provenance

## Objetivo y alcance
Reutilizar envelope/candidate store; dar persistencia terminal, lineage y hashes context/input/output/provider/prompt/version, con idempotencia de reintentos.

- **Ítems estables cubiertos:** MP131-R1-02.
- **Dependencia de entrada:** R01-01 evidencia focal PASS; HEAD rebindeado antes de implementar.
- **Fuentes a auditar antes de decidir la allowlist:** `src/devpilot_core/generation/`; `src/devpilot_core/application/`; `tests/test_mp0b_candidate_generation_kernel.py`.
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
- Reintento terminal no crea duplicado; context/version reproducibles; conflicto concurrente bloqueado.
- Ningún cambio fuera de la allowlist aprobada y todos los reportes citan el HEAD/resultados reales.
- Sin falsa equivalencia por LF/CRLF: comparar blobs Git o texto canónico únicamente cuando el contrato sea textual; binarios por SHA exacto.
- **Riesgos / límites:** Ningún segundo authority de apply; no side effects por retry.

## Entregables y validación Windows
Bundle independiente ZIP de nombre corto con `GUIA_UNICA_WINDOWS.md`, operador Python, patches/diffs, tests, receipts y manifest SHA. Descarga a `C:\Users\Pedro\Downloads`; evidencia fuera del repo; comandos PowerShell en una sola línea con `PASS` verde / `BLOCK` rojo. No copiar toda la documentación histórica al operador.

## Permisos, costo y control
- Ruta base: mock/D sin API key ni costo. L local sólo cuando sea necesario y con autorización; E/external siempre DENY hasta R8.
- No realizar `reset --hard`, `force push`, borrados ni sobreescritura sin consentimiento específico. Evitar autorizaciones para lecturas o verificaciones triviales.
- **Estado inicial:** `DRAFT_EXECUTION_GATED`; el programa Owner-133 autoriza planificar, **no ejecutar** este sprint.

## Criterio de STOP
Bloquear solamente por discrepancia material de autoridad, seguridad, source real, defectos funcionales S0/S1 o pruebas exigidas incumplidas. Hallazgos cosméticos `OBSERVE_ONLY`; documentar sin encadenar microcorrectivos.


## Addendum de ejecución y rebind — COR-154 (15-10-2026)

- **Autoridad individual:** `SPRINT_EXECUTION_APPROVED` / `OWNER_APPROVED`, exclusivamente `MP131-R1-02`. No se extiende a R01-03, R1 completo, MP-1B ni APIs externas.
- **Fuente técnica viva:** Git limpio `D:\Projects\DevPilot_Local`, rama `evolution/multiprovider-v2`, HEAD `caad145436d26404875dbd800559d27a1db590ba`, acreditado por COR-153.
- **Reuse/Delta:** contratos `GenerationRequest`, `ArtifactCandidateEnvelope`, `CandidateLineage`, `LEGAL_TRANSITIONS` reutilizados; incorporar adaptador SQLite local transaccional para persistencia, retries y CAS, y pruebas focales.
- **Allowlist Git:** `src/devpilot_core/generation/__init__.py`, `src/devpilot_core/generation/lifecycle_store.py`, `tests/test_mp132_r01_02_candidate_lifecycle.py`. La ADR de diseño se entrega como documento propuesto en el bundle, sin insertar un registro documental incompleto en Git antes de R1-10.
- **Alcance real:** store transaccional mock/servicio, SIN conexión activa al runtime Story o a UI; esa conexión necesitará aceptación de otro incremento. No afirmar capacidad production end-to-end ni equivalencia con modelo real.
- **Evidencia:** pruebas focales kernel/Story/store; Git index exacto; normal push; SHA/CRC de Git archive y paquete de evidencia.
- **Autorizaciones:** únicamente operación material apply+commit y push remoto, con confirmaciones separadas; ninguna validación Owner para lectura.
- **Gate STOP:** diferencia real de HEAD, seguridad o source, colisión de idempotencia no controlada, o pruebas funcionales focales fallidas.
