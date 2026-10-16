---
doc_id: DEVPL-MP-SUCCESSOR-132-00_LEEME_INDICE_Y_ORDEN_132
title: "DEVPL-MP-SUCCESSOR-132 — Índice, estado y lectura guiada"
version: "1.1.0"
status: "OWNER_APPROVED_PROGRAM"
baseline_commit: "8db5b44694abcced3231183e05731e732f5b8f24"
owner: "Owner DevPilot"
supersedes_program: "DEVPL_MP_SUCCESSOR_131 v1.0.0"
execution_authority: false
approval_revision: 1
approval_date: "2026-10-13"
approved_by: "Owner Ordóñez (instrucción explícita en conversación)"
approval_scope: "PROGRAMMATIC_PLANNING_ONLY"
owner_decision_ref: "DEVPL-MP-132-OWNER-APPROVAL-133"
---

# DEVPL-MP-SUCCESSOR-132 — Índice, estado y lectura guiada

## 1. Cómo interpretar este paquete

**En lenguaje llano.** Esta es la propuesta sucesora completa del programa de desarrollo de DevPilot. Explica qué producto construiremos, qué partes existentes reutilizaremos, cómo se comprobará cada avance y qué autoriza exactamente el Owner. No es un operador: abrir este ZIP **no modifica repositorios ni concede autorización de ejecutar código**.

- **Producto objetivo:** una plataforma local-first y agent-assisted para desarrollar aplicaciones profesionales de propósito general desde la necesidad hasta operaciones, mantenimiento y evolución, con MIPSoftware general y MIASI cuando aplique.
- **Punto de partida:** HEAD `8db5b44694abcced3231183e05731e732f5b8f24`, rama `evolution/multiprovider-v2` tras SYNC-1 y COR-130; no equivale a producto industrial aceptado.
- **Estado:** `OWNER_APPROVED_PROGRAM` mediante acta separada 133. Ratificación administrativa G5 y COR-130 `OWNER_RATIFIED`; STOP global `OWNER_LIFTED` a nivel de programa. Los antiguos prompts MP-1B siguen **no ejecutables** hasta auditoría y autorización sucesora. El repositorio conserva sus metadatos hasta publicación gobernada.
- **Supersession:** los **12 artefactos de v131** quedan reemplazados en planificación por la versión 132 Owner-approved; v131 conserva únicamente valor histórico. La aprobación no es autorización de source mutation ni de ejecutar un sprint.

## 2. Carpetas y función

| Carpeta | Qué contiene | Lectura |
|---|---|---|
| `0_program` | Propósito, autoridad, roadmap, matriz de cobertura, gates y orden de lectura | Comenzar aquí |
| `1_arquitectura` | Decisiones de arquitectura (ADRs) propuestas y límites no negociables | Antes de aprobar contratos |
| `2_contratos` | Diez contratos solicitados y matrices de cumplimiento | Regulan comportamientos futuros; necesitan implementación gradual |
| `3_gobernanza` | Audit-first, riesgos, Git, ledger y controles transversales | Vincula decisión con evidencia |
| `4_backlogs` | Índice y **11 backlogs R0–R10**; 66 IDs heredados íntegros + nuevas capacidades | Referencia de trabajo progresivo |
| `5_pilotos` | Pilot B continuo, Pilot C opcional externo, condiciones E2E | Prueba real del producto |
| `6_trazabilidad` | Inventario de fuentes, mapa de supersession y matriz de decisiones recientes | Comprobar que nada quedó omitido |

## 3. Prioridad documental

1. Baseline Git y estándares/versiones realmente aprobados del repositorio prevalecen frente a ejemplos de este paquete.
2. Decisiones Owner firmadas/aprobadas por ID + SHA, políticas de seguridad y ADRs **ya aprobados** mantienen autoridad mientras no exista sucesor explícitamente aprobado.
3. Al aprobarse 132, este programa reemplaza íntegramente a 131 en planeación. Los viejos prompts MP v2.1 se conservan **no ejecutables**.
4. Dentro de 132: `0_program/01` da visión; los ADRs deciden trade-offs; los contratos precisan obligaciones; los backlogs ordenan capacidades. Si hay contradicción, **BLOCK y decisión Owner**, no prevalencia implícita de un documento genérico.
5. Los hallazgos UX del ledger son `working-ledger`, no autorizan cambios sin audit-first ni aprobaciones.

## 4. Orden de lectura recomendado

Ver `0_program/06_GUIA_LECTURA_132.md`: recorre visión → límites → decisiones → contratos → Pilot B → roadmap → backlogs → riesgos → preparación operativa. Reservar los documentos más detallados para después del mapa mental general.

## 5. Lo que todavía no está autorizado

**Autorizado y ratificado ahora:** programa 132 para planeación, ADRs para arquitectura, cierre administrativo G5/COR-130 y levantamiento del STOP **global** por decisión Owner. **No autorizado sin nuevo gate:** sprint, cambio de HEAD, publicación al Source Registry, migración Git efectiva, proveedor externo, gasto API, habilitación de agente o cambio al Pilot B. Cada incremento exige audit-first, alcance, límites y aprobación; `GLOBAL_STOP_LIFTED` no implica `EXECUTE_ALL`.

## Actualización operativa MP132 post-M1 — R02-01

**Índice activo y jerarquía post-M1.** R01 CLOSED/PASS_WITH_FINDINGS; R02-01 ONLY SPRINT_EXECUTION_APPROVED; R02-02..10 DRAFT/NOT_AUTHORIZED. Ver el programa sucesor documental `DEVPL_MP_132_POST_M1_R02_172.zip`; éste no es un sello Git por sí mismo.

**Autoridad:** esta sección actualiza el *estado operativo*, no modifica el `status: OWNER_APPROVED_PROGRAM` de la aprobación histórica Owner-133, ni autoriza R02-02. Source Registry mantiene el `doc_id` y `path` originales.
