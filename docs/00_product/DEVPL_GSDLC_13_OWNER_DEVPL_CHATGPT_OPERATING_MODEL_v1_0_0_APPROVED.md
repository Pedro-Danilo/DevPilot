---
doc_id: "DEVPL-GSDLC-13-OWNER-DEVPL-CHATGPT-OPERATING-MODEL"
title: "DEVPL-GSDLC-13 — Owner / DevPilot / ChatGPT operating model"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-09-21"
execution_model: "owner-driven/devpilot-executed/chatgpt-adjudicated"
source_repo: "repo_DevPilot_Local_436_DEVPL_UX_P0_E_PRE_PILOT_PRODUCTIZATION_RC_WINDOWS_VALIDATED_CANDIDATE.zip"
source_git_commit: "423e99fa38df3114328b555aff8f859740a49a01"
---

# Owner / DevPilot / ChatGPT operating model

## 1. Propósito

Evitar que la metodología usada para **construir DevPilot** contamine la prueba en la que DevPilot debe ser usado **como producto**.

## 2. Roles

| Actor | Responsabilidad | No debe hacer |
|---|---|---|
| Owner | operar UI, expresar necesidades reales, revisar planes/diffs, aprobar/rechazar, reportar experiencia | editar el proyecto externamente para desbloquear acceptance |
| DevPilot | guiar el SDLC, materializar workspace/Git/docs/code/tests/commits/release, producir provenance/evidence | depender de ayuda externa no declarada para una tarea normal |
| ChatGPT | preparar Run Cards, analizar evidencia, adjudicar PASS/BLOCK/findings, diseñar correctives de DevPilot | escribir contenido/código del greenfield para que el Owner lo copie y así pase |
| Operador Windows | instalar/iniciar/detener/auditar/capturar/validar DevPilot | actuar como autor del proyecto greenfield |

## 3. Cuatro modos de trabajo

### Modo A — Implementation/Validation (13-A)

Metodología histórica. ChatGPT puede modificar DevPilot y entregar bundle Windows porque 13-A es rebaseline/current-authority hygiene, no aceptación del proyecto greenfield.

### Modo B — Acceptance (13-B..13-D)

1. ChatGPT entrega **una Run Card** del checkpoint actual.
2. El Owner ejecuta la misión dentro de DevPilot.
3. DevPilot debe indicar el siguiente paso mediante su propio producto.
4. El Owner se detiene en el stop point o ante un BLOCK.
5. El Owner adjunta un **Run Packet incremental**.
6. ChatGPT devuelve `PASS`, `PASS+FINDING` o `BLOCK`, más el siguiente Run Card si procede.

Un PASS normal **no produce bundle**.

### Modo C — Corrective de DevPilot

Solo se activa ante un defecto real de DevPilot que impida o degrade materialmente la acceptance.

1. congelar el estado del proyecto/checkpoint;
2. preservar evidencia first-attempt;
3. clasificar defecto y severidad;
4. ChatGPT puede desarrollar un patch **de DevPilot**;
5. Owner valida el bundle Windows;
6. promover successor DevPilot por fast-forward y sincronizar remoto;
7. retestar solo el segmento afectado;
8. reanudar el piloto desde el checkpoint exacto.

El corrective **no puede** introducir archivos, respuestas, código o artefactos normales dentro del proyecto greenfield para fabricar éxito.

### Modo D — Independent Adjudication (13-E)

ChatGPT audita evidencia consolidada. No rellena huecos retroactivamente. Un requisito no probado queda pendiente/BLOCK según DoD.

## 4. Asistencia externa permitida durante Acceptance

Permitido preguntar a ChatGPT:

- qué significa una pantalla o concepto;
- qué efecto implica una approval;
- si una conducta observada parece un blocker;
- cómo preservar o adjuntar evidencia;
- cómo interpretar un receipt ya producido por DevPilot.

No permitido en baseline acceptance:

- “escribe requirements.md para pegarlo”;
- “dame la arquitectura exacta que debo responder”;
- “genera el código de la story para copiarlo”;
- “dime qué archivos crear manualmente para seguir”.

Si una tarea solo puede completarse de esa forma, eso es evidencia de una brecha del producto.

## 5. Terminal y operador

`terminal para operar/auditar DevPilot` es permitido: instalar, iniciar/detener servicios, comprobar puertos, leer Git/evidence sin mutar el proyecto.

`terminal escape` es BLOCK cuando el usuario necesita PowerShell/Git/editor externo para completar una etapa que debería ser normal UI journey: crear el repo, escribir project docs, aplicar código, hacer un commit gobernado o producir el release saltándose DevPilot.

Ambos se registran por separado.

## 6. Authority Pack y Run Packet

### Authority Pack estable

No se readjunta en cada checkpoint salvo cambio de authority:

- último DevPilot Windows-validado;
- charter/rebaseline/roadmap/backlog/sprint activos;
- Operating Model;
- User Journey Runbook;
- UX-P1 policy.

### Run Packet incremental

Solo contiene evidencia nueva del checkpoint: receipts/logs, screenshots decisivos, Git/evidence IDs, observación del Owner y métricas UX. Esto reduce contexto redundante y mantiene trazabilidad.

## 7. Regla de neutralidad del acceptance

Las Run Cards son **intent-first, no click-script**. Deben especificar objetivo, límites, start/stop y evidencia, pero no dirigir cada clic si la UI debería ser capaz de guiar al usuario. Dar instrucciones demasiado detalladas podría ocultar una falla de discoverability que el piloto pretende medir.
