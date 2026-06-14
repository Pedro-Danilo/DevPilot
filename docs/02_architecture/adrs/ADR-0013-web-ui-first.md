---
title: "ADR-0013 — Estrategia visual Web UI first"
doc_id: "DEVPL-ADR-0013"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
standard: "MIPSoftware"
extension: "MIASI"
phase: "FASE-F-PRODUCTO-VISUAL"
updated: "2026-06-14"
source_repo: "repo_DevPilot_Local_77.zip"
decision_scope: "phase_f_visual_product_strategy"
change_policy: "controlled_changes_allowed_via_docs_as_code"
---

# ADR-0013 — Estrategia visual Web UI first

## Contexto

DevPilot Local llega a Fase F después de cerrar Fase E con AgentOps, trazas, métricas, reportes y `agentops status`. El producto necesita una experiencia visual para consultar estado del workspace, readiness, MIASI, reportes, trazas, aprobaciones y configuración sin obligar al usuario a leer JSON crudo.

La discusión arquitectónica previa evaluó tres rutas visuales:

1. Web UI local como primera interfaz visual.
2. Web UI real como evolución posterior.
3. UI Desktop o shell nativo como posibilidad futura.

Construir dos interfaces independientes incrementaría costo, pruebas, riesgo de divergencia y superficie de seguridad. Desktop agrega además packaging, auto-update, permisos nativos, IPC, firma, instaladores y compatibilidad por sistema operativo.

## Decisión

DevPilot adopta una estrategia **Web UI first**:

```text
CLI técnica
  ↓
ApplicationService / Core
  ↓
API local segura en 127.0.0.1
  ↓
Web UI local canónica de Fase F
  ↓
Web UI real futura cuando existan contratos, seguridad y operación suficientes
```

La **UI Desktop queda diferida** fuera de Fase F. No se elimina como posibilidad de producto, pero solo podrá reabrirse mediante ADR posterior si existe justificación explícita de distribución, permisos nativos, experiencia de usuario, empaquetado y costo de mantenimiento.

Fase F no debe construir Web UI y Desktop UI independientes. Si en una fase futura se aprueba Desktop, deberá reutilizar la Web UI/API/ApplicationService o actuar como shell liviano, sin duplicar lógica de negocio.

## Consecuencias

### Positivas

- Reduce complejidad de Fase F.
- Evita duplicar frontend web y desktop.
- Permite validar dashboard, report viewer, trace viewer, approval center y settings sobre API local.
- Facilita evolución a Web UI real usando contratos API y componentes reutilizables.
- Mantiene CLI como interfaz técnica estable.
- Reduce riesgos de packaging, actualización, permisos nativos e IPC.

### Negativas o trade-offs

- No habrá aplicación desktop instalable en Fase F.
- Usuarios no técnicos deberán abrir navegador local durante el MVP visual.
- El ciclo de vida de API local y frontend deberá documentarse cuidadosamente.
- La futura Web UI real requerirá endurecimiento adicional de autenticación, autorización, sesiones, CORS, CSRF y despliegue.

## Alternativas consideradas

| Alternativa | Veredicto | Razón |
|---|---|---|
| Solo CLI | Rechazada como destino visual | Mantiene potencia técnica, pero no resuelve dashboard ni UX visual. |
| Web UI local first | Aprobada | Mejor balance entre velocidad, seguridad local, contratos y evolución. |
| Web UI real inmediata | Rechazada para Fase F | Requiere auth, despliegue, multiusuario y hardening prematuro. |
| Desktop UI nativa directa | Rechazada para Fase F | Mayor costo y superficie de riesgo. |
| Web UI + Desktop UI independientes | Rechazada | Duplica lógica, UX, testing y mantenimiento. |
| Desktop shell futuro sobre Web UI | Diferida | Posible solo si una ADR posterior demuestra conveniencia. |

## Reglas de implementación

1. La Web UI local consume API local; no importa módulos internos del core.
2. La API local escucha por defecto solo en `127.0.0.1`.
3. La UI inicial es read-only/dry-run para operaciones sensibles.
4. Toda operación write/execute requiere `PolicyEngine` y Approval Workflow.
5. Las respuestas visuales preservan `CommandResult`/`ApplicationResponse` y findings.
6. No se exponen secretos, prompts, completions, stdout/stderr ni patches crudos.
7. CORS wildcard queda bloqueado por defecto.
8. Desktop queda fuera de Fase F.

## Criterios PASS

```text
Backlog Fase F declara Web UI local como interfaz canónica.
C4 Container muestra API local y Web UI local como planned-fase-f.
Desktop aparece como deferred.
Runbook documenta criterios PASS/BLOCK de la estrategia visual.
Internal Application Contract menciona CLI/API/Web UI como rutas principales.
No se implementa servidor ni frontend en este ajuste documental.
```

## Criterios BLOCK

```text
Implementar Desktop en Fase F sin ADR posterior.
Crear dos UI independientes.
Permitir que la UI consuma el core directamente.
Exponer API fuera de localhost por defecto.
Permitir operaciones destructivas sin approval.
Asumir Web UI local como SaaS o Web real productiva.
```

## Relación con Sprint 64

`FUNC-SPRINT-64` debe usar esta ADR como decisión base y completar el threat model de interfaz/API local. No debe codificar servidor ni frontend hasta cerrar las restricciones de localhost, token, CORS, CSRF/local origin, secrets, aprobación humana y acciones críticas.
