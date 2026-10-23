---
doc_id: PROMPT-MP132-R00-04-134
version: 1.0.1
status: OWNER_APPROVED
linked_sprint: SPRINT-MP132-R00-04-134
execution_authority: true
---
# PROMPT R00-04 — Auditoría focal Settings/UI y baseline de métricas

## Tarea precisa

Implementa solo el alcance de `SPRINT_MP132_R00_04_SETTINGS_METRICS_AUDIT_134.md`, **después** de verificar nuevo baseline R00-03 Windows PASS. No crear refactor de Settings, no habilitar modelos, no instalar librerías ni alterar Git. Consulta literalmente el paquete Owner-133, ADR-007/011, `CONFIGURATION_AUTHORITY_MATRIX_132.md`, contratos PESP, capacidades de modelo, `ledger_v1_32_MP0F_REB117_INTEGRADO.md`, source real del HEAD promovido y evidencia de UX histórica. Los findings son históricos hasta su reproducción actual; no false S1.

## Implementación de instrumento/auditoría

1. Crear utilería Python stdlib opcional **read-only** `mp132_r00_04_audit.py`, fases `inspect|inventory|verify|package`, con `--repo --ledger --program-zip --evidence` y comprobación de HEAD/upstream; inspeccionar `SettingsView.ts`, `settings_service.py`, routes/API, `.devpilot/project.yaml`, policy/providers y runtime records **solo con permiso**.
2. Elaborar `SETTINGS_AUTHORITY_MATRIX.md`: origen, valor efectivo, persistencia, scope, permiso, default, autorización, restart, rollback, efecto y ruta UI/API/store; evidenciar la prioridad de políticas globales deny. Catalogar controles runtime (disable/revoke) fuera de edición de preferencias.
3. Contrastar ledger por IDs: `UX-P1-02-B01-004`, `UX-P1-02-B01-006`, `CAP-13B01-SETTINGS-001`, `UX-P1-MP0F-001` y otros riesgos relacionados de B03; corroborar progressive disclosure MP-0F, no reimplementarlo. Clasificar `REPRODUCED|RESOLVED_EVIDENCED|NOT_TESTED|NO_OP|OPEN`; fuente, screenshot solo si necesario, sin exigir capturas gigantes.
4. Obtener información ambiental **sin ejecutar inferencia ni descargar dependencias**: SO, Python, Node, RAM/CPU/GPU si disponible y consentido, Ollama/LM Studio instalados/configurados de forma pasiva, dataset de evaluación disponible o `NOT_AVAILABLE`. Pruebas focales read-only y build UI únicamente en worktree *desechable*, sin ensuciar el repositorio canónico, si el contrato los necesita.
5. Proponer `REUSE_DELTA_MAP` para R1/R2 sobre Configuración, settings persistentes, Model Gateway y estado UX; registrar límites de presupuesto y costos como `NOT_MEASURED` si no se midieron. Priorizar S2 que afecten approvals y acciones críticas, no dispersar refactor estético.
6. Emitir reportes versionados/checkpoint, gate `AUDITED/PENDING_REVIEW` o `BLOCK`; empaquetar evidencia con SHA sin secretos. Si un S0/S1 funcional comprobado bloquea, **no aplicar parche en R00-04**: proponer corrective y detener.

## Pruebas y entrega

Suite del auditor que compruebe inputs inexistentes, ZIP/HEAD drift, lectura que requiere network/credenciales, ledger repetido, configuración inexistente y idempotencia de packaging. Entregar reporte Markdown útil a ingenieros y Owner, utilería, una guía única Windows secuencial, ZIP+SHA y recibo. Demostrar `operator_project_writes=0`, `model_calls=0`, `egress=0`. No configurar la interfaz ni declarar L E2E aceptado.

---
## Rebind de ejecución COR-146 (siguiente al G-R00-03)

- Aprobación individual Owner otorgada explícitamente en el prompt del 14-10-2026; limita ejecución a la auditoría focal, sin source writes.
- Baseline exacto acreditado: `77cdf9af323decc09e33cebad2169863e3b86e1a`, `evolution/multiprovider-v2`, `D:\Projects\DevPilot_Local`.
- `G-R00-03 AUTHORITY_REBOUND_WINDOWS_PASS` precede R00-04; validación incluye evidencia COR-145 y los ZIP/SHA.
- Configuración y ADR-007/011 de Owner-133 permanecen contratos de diseño; la auditoría no los convierte en funciones implementadas.
- `ledger_v1_32_MP0F_REB117_INTEGRADO.md` no fue identificado por esa ruta en el Git archive R00-03; se usan los IDs y el ledger 13-B presentes y se declara fuente histórica pendiente de localización, sin inventar contenido.
- Implementación de R00-04: auditor `audit146.py` en carpeta externa, fases inspect/inventory/verify/package, validación focal, evidencia fuera del repositorio; no se hacen commits/push.
- Windows valida estado Git vivo y revisiones humanas cuando sean posibles; si UI no está disponible, registrar NOT_TESTED, nunca PASS de UX.
- Gate de salida sigue pendiente de evaluación Owner de la evidencia Windows.
