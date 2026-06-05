---
title: "Policy Card — DevPilot Local"
doc_id: "DEVPL-MIASI-POLICY"
status: "reviewed"
version: "0.6.0"
owner: "Ordóñez"
standard: "MIASI"
parent_standard: "MIPSoftware"
phase: "SPRINT-PRECODE-06"
updated: "2026-06-05"
approval: "ready_for_owner_approval"
source_baseline: "security approved + architecture approved + quality/operations approved"
change_policy: "controlled_changes_allowed_until_precode_baseline"
---

# Policy Card — DevPilot Local

## 1. Propósito

Este documento define las políticas de ejecución de DevPilot Local para agentes, herramientas, modelos, filesystem, Git, patches, persistencia, costos, secretos y aprobación humana.

La regla central es:

> DevPilot opera bajo deny-by-default, dry-run por defecto, privilegio mínimo, trazabilidad obligatoria y aprobación humana para acciones críticas.

## 2. Principios de política

| Principio | Regla |
|---|---|
| Local-first híbrido | Local por defecto, APIs opcionales y controladas. |
| Dry-run por defecto | Ninguna acción con side effect inicia en execute. |
| Deny-by-default | Lo no permitido explícitamente queda bloqueado. |
| Least privilege | Cada agente/tool solo accede a lo necesario. |
| Human approval | Escritura, patch, refactor, Git write y despliegue requieren aprobación. |
| Cost controlled | APIs externas requieren presupuesto, proveedor permitido y trazabilidad. |
| Secret safe | Secretos redactados, nunca impresos ni enviados sin permiso. |
| Auditable | Todo gate, tool call, aprobación y costo deja evidencia. |
| Deterministic gate first | El agente recomienda, el gate determina. |

## 3. Modos de ejecución

| Modo | Descripción | Permitido en MVP |
|---|---|---:|
| `read_only` | Solo lectura de artefactos permitidos. | Sí |
| `dry_run` | Simula acción y reporta impacto. | Sí |
| `suggest` | Propone cambios sin escribirlos. | Sí |
| `write_report` | Escribe reportes en rutas controladas. | Sí |
| `write_artifact_candidate` | Escribe borradores en zona segura. | Sí, con aprobación |
| `execute` | Aplica cambios reales. | No por defecto |
| `deploy` | Despliegue externo. | No |

## 4. Políticas por dominio

| Dominio | Política |
|---|---|
| Filesystem | Solo rutas del workspace; prohibido borrar/sobrescribir sin aprobación. |
| Git | MVP+ read-only; commit/tag/push bloqueados hasta política posterior. |
| Patches | Parse y dry-run permitidos; apply bloqueado sin aprobación. |
| Repos | Lectura controlada; secret scan antes de resumen o envío a modelo. |
| Modelos locales | Permitidos si no exponen datos fuera del equipo. |
| APIs externas | Permitidas solo con API key opcional, CostGuard, redacción y consentimiento. |
| Persistencia | SQLite/JSONL/Markdown con redacción y retención. |
| RAG/memoria | Solo fuentes permitidas; grounding y citas obligatorias. |
| MCP/API futuros | Deshabilitados por defecto; registro explícito y policy gate. |
| Agentes | No aprueban sus propias acciones críticas. |

## 5. Matriz de política

| Acción | MVP | MVP+ | Post-MVP | Requiere aprobación |
|---|---:|---:|---:|---:|
| Leer documentos pre-code | Sí | Sí | Sí | No |
| Validar documentos | Sí | Sí | Sí | No |
| Generar reporte | Sí | Sí | Sí | No si ruta segura |
| Generar borrador documental | Sí | Sí | Sí | Sí si escribe |
| Leer Git status/diff | No | Sí | Sí | No |
| Analizar repo | No | Sí | Sí | Depende |
| Revisar código | No | Sí | Sí | No si solo reporta |
| Proponer patch | No | Sí | Sí | No si no aplica |
| Aplicar patch | No | Restringido | Sí | Sí |
| Ejecutar pruebas | No | Sí | Sí | Depende del comando |
| Crear commit | No | Restringido | Sí | Sí |
| Llamar API externa LLM | Opcional controlado | Sí | Sí | Sí si envía código/datos |
| Desplegar | No | No | Sí | Sí |

## 6. CostGuard

Toda operación con costo potencial debe declarar:

- proveedor;
- modelo;
- límite de tokens/requests;
- presupuesto de ejecución;
- modo de estimación;
- confirmación humana;
- evento `devpilot.cost.event`;
- fallback local/mock.

## 7. SecretGuard

Toda operación debe:

- detectar patrones de secretos;
- redactar outputs;
- evitar imprimir tokens;
- bloquear envío de secretos a modelos;
- generar findings si detecta `.env`, API keys o credenciales;
- registrar evento seguro sin valor del secreto.

## 8. Criterios PASS

La política queda aprobada si:

- cubre filesystem, Git, tools, agents, modelos, costos, secretos y persistencia;
- define modos de ejecución;
- define bloqueos críticos;
- separa recomendación de ejecución;
- exige trazabilidad;
- exige aprobación humana para acciones críticas.

## 9. Criterios BLOCK

Bloquear avance si:

- un agente puede aplicar cambios sin policy;
- un tool puede ejecutar comandos arbitrarios;
- APIs externas pueden usarse sin CostGuard;
- secretos pueden salir en logs/reportes;
- no existe registro de aprobación;
- no hay trazas para acciones relevantes.
