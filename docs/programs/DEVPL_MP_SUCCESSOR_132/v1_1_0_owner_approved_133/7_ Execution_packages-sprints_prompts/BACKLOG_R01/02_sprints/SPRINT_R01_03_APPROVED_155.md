---
doc_id: MP132-R01-03-SPRINT
title: "ModelAdapter y negotiation por capacidades"
version: "1.0.1-EXECUTION-APPROVED-155"
status: "SPRINT_EXECUTION_APPROVED"
owner: "DevPilot Owner"
baseline_reference_at_planning: "0505ab2ee0711561d3c2e68511ce05aea8c857b1"
execution_authority: true
approval_scope: "R01_03_ONLY"
source_backlog: "BACKLOG_R01_132.md"
---

# R01-03 — ModelAdapter y negotiation por capacidades

## Objetivo y alcance
Definir puerto mínimo proveedor-independiente y adapters mock/local; separar SUPPORTED, CONFIGURED, HEALTHY, EVALUATED, ELIGIBLE, tool/stream/timeout.

- **Ítems estables cubiertos:** MP131-R1-03.
- **Dependencia de entrada:** R01-02 evidencia focal PASS; HEAD rebindeado antes de implementar.
- **Fuentes a auditar antes de decidir la allowlist:** `src/devpilot_core/modeling/providers.py`; `src/devpilot_core/modeling/local_provider_discovery.py`; `src/devpilot_core/generation/`.
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
- Contrato con mock y adapter local stub sin servidor; falla de proveedor no habilita otro silenciosamente.
- Ningún cambio fuera de la allowlist aprobada y todos los reportes citan el HEAD/resultados reales.
- Sin falsa equivalencia por LF/CRLF: comparar blobs Git o texto canónico únicamente cuando el contrato sea textual; binarios por SHA exacto.
- **Riesgos / límites:** Sin API key, sin iniciar Ollama/LM Studio, sin instalar modelos; E deshabilitado.

## Entregables y validación Windows
Bundle independiente ZIP de nombre corto con `GUIA_UNICA_WINDOWS.md`, operador Python, patches/diffs, tests, receipts y manifest SHA. Descarga a `C:\Users\Pedro\Downloads`; evidencia fuera del repo; comandos PowerShell en una sola línea con `PASS` verde / `BLOCK` rojo. No copiar toda la documentación histórica al operador.

## Permisos, costo y control
- Ruta base: mock/D sin API key ni costo. L local sólo cuando sea necesario y con autorización; E/external siempre DENY hasta R8.
- No realizar `reset --hard`, `force push`, borrados ni sobreescritura sin consentimiento específico. Evitar autorizaciones para lecturas o verificaciones triviales.
- **Estado inicial:** `DRAFT_EXECUTION_GATED`; el programa Owner-133 autoriza planificar, **no ejecutar** este sprint.

## Criterio de STOP
Bloquear solamente por discrepancia material de autoridad, seguridad, source real, defectos funcionales S0/S1 o pruebas exigidas incumplidas. Hallazgos cosméticos `OBSERVE_ONLY`; documentar sin encadenar microcorrectivos.

## Rebind y alcance de ejecución COR-155 (15-10-2026)

- Baseline fuente: `0505ab2ee0711561d3c2e68511ce05aea8c857b1`, rama `evolution/multiprovider-v2`, raíz `D:\Projects\DevPilot_Local`.
- Prerrequisito R01-02: HEAD `0505ab2ee0711561d3c2e68511ce05aea8c857b1`, focal 29/29 y remoto confirmado según evidencia Windows.
- Allowlist exacta: `src/devpilot_core/modeling/__init__.py`, `src/devpilot_core/modeling/negotiation.py`, `tests/test_mp132_r01_03_negotiation.py`.
- Cambios: puerto `ModelAdapter` preexistente reutilizado; negociación offline, mock y stub local sin servidor.
- Estados explícitos SUPPORTED, CONFIGURED, HEALTHY, EVALUATED, ELIGIBLE; sin fallback silencioso ni egress.
- No activa Ollama, LM Studio, APIs externas, routers de ejecución ni MP-1B.
- Validación local: tests mock/stub + gateway; Windows pendiente.
- Autoridad del Owner: solo R01-03; la publicación Git requiere autorización de commit/push en guía.
