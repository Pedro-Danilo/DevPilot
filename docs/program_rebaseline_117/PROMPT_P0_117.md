---
doc_id: "DEVPL-REB-117-PROMPT-P0"
title: "Prompt de ejecución P0 — Formalización contractual y publicación de successors"
version: "1.0.0"
status: "APPROVED / EXECUTION-GATED"
date: "2026-10-11"
owner_decision: "OWNER-APPROVAL-2026-10-11-REBASELINE-116"
implementation_authority: false
multiprovider_stop_lifted: false
---

# Prompt de ejecución P0 — Formalización contractual y publicación de successors

## Instrucción para ejecutar en el siguiente hilo
Implementa **exclusivamente** el micro-sprint `P0` de `SPRINT_P0_117.md` con entrada `G0 PASS; documentación fuente y baseline íntegros; STOP MP activo` y salida `G1 DOCUMENTARY_AUTHORITY_PASS`. El programa rector es `PROPUESTA_REBASELINE_116_APPROVED.md`, el roadmap `ROADMAP_P0_P3_117.md`, el backlog `BACKLOG_P0_P3_117.md`, los controles `GATES_EVIDENCIA_117.md` y los successors aplicables. Usa el contrato vigente registrado en P0, no un histórico desfasado.

## Lectura y preflight obligatorios
1. Descomprimir y consultar literalmente los paquetes Greenfield, Multiprovider, `repo_465` o su sucesor, Pilot A y evidence pertinentes, `gen113_status.json`, decisiones posteriores y últimos receipts. No asumir que archivos de otro hilo siguen presentes.
2. Verificar SHA/CRC, identidades de worktrees, Git 3 estados y STOP. Si falta fuente obligatoria, solicitarla al Owner y detener; no inferir ni reconstruir contrato por memoria.
3. Identificar diferencias entre lo requerido y lo ya persistido: reanudar desde checkpoint, no duplicar commits, approvals, jobs o acciones mutativas. No crear Full Regression intermedia ni false FAIL por LF/CRLF.

## Encargo y entregables

**Trabajo:** identificar autoridad canónica del paquete y registros, reconciliar Greenfield Charter/Brief/roadmap/backlog y 13-D sprint/protocol/runbook/prompt/evidence con `BRIDGE_GREENFIELD_117`; reconciliar MP STOP, synchronization protocol, ADR-008, piloto, dependencia e índices con `BRIDGE_MP_STOP_SYNC_117`. **No** reprogramar todavía olas MP-1B..MP-8. Implementar P0 como sucesores documentales mínimos, con publicación en el índice puente para ambos programas y rebind únicamente del Source Registry determinístico; el MP Source Registry permanece congelado hasta P3-C.

**Validación:** antes/después lista de paths, doc_id/version/lifecycle/supersedes, tests de gobernanza documental, lint de links/indices, coherencia de `STOP ACTIVE`, upstream parity de worktree modificado, 0 mutaciones Pilot A y 0 MP source mutation. Si los archivos MP congelados deben incorporar nuevas cláusulas, solo preparar paquete sucesor documental fuera del MP worktree: **no levantar STOP ni escribir en él hasta gate SYNC-1**. El contrato puente aprobado se publicará en authority neutral/track determinístico con receipt que MP pueda importar cuando sea autorizado; no hacer push de documentación MP en MP congelada.

**Estado de programa:** G0 queda registrado como PASS. G1 exige publicación coherente y accesible de los successors en índice documental puente externo versionado con SHA, más rebind determinístico; `MP Source Registry=PENDING_MP_IMPORT` constituye un estado explícito controlado hasta P3-C. Si no se logra un soporte canónico seguro y accesible para el índice puente, G1 sigue BLOCK. Nunca declarar ficticiamente que MP fue modificado.

**Evidencia:** manifest del successor pack, pruebas focales docs, logs TXT, Git commits (solo track permitido), ZIP limpio+SHA por modificación de plataforma, tabla de reglas sustituidas, decision receipt G1. No dejar un README histórico como autoridad activa.


**Resultado:** emitir informe PASS/BLOCK con razones y evidence hashes, artefactos específicos y, cuando haya intervención Windows, **una sola guía `.md` secuencial de nivel beginner-medio**, sin referencias a ejecutar otra guía, incluyendo nombres reales de superficies/secciones/botones, momentos de capturas, qué verificar, resultados esperados y archivos a devolver. Los comandos PowerShell se entregan siempre en una única línea y se prefiere operador Python minimalista; no ejecutar como Owner en un entorno al que no tienes acceso.

## Límites no negociables
Si los contratos puente no pueden ser materializados y auditados sin violar STOP, detener el sprint y solicitar una decisión de publicación neutral; nunca editar MP congelada.
Nota: publicar bridge MP sin mutar la branch congelada; si hay conflicto de autoridad para el registro neutral, informar y detener. No inventar G1.
No generar un correctivo preventivo grande ni nuevos providers RF00N para facilitar el avance. Cualquier decisión arquitectónica nueva exige ADR successor. Registrar hallazgos UX S0–S3 y no reinterpretar `OBSERVE_ONLY` como permiso de modificación.
