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


## Adenda de estado operativo — R02-03/COR-176 (sucesora, no retroactiva)

- **Predecesores acreditados:** R02-01 `CLOSED/WINDOWS_PASS` en `4a4443f1631acdbfcd19e1e2fca4be36f707daf9`; R02-02 `CLOSED/WINDOWS_PASS` en `8a9b1cf915f8cfb9d08b35d6d1c13467d0bd08fc`. Las adendas R02-01 anteriores se conservan como historia, no son la autoridad de ejecución actual.
- **Autorización individual vigente:** únicamente `R02_03_OLLAMA_REAL_CANDIDATE_SPRINT.md` = `SPRINT_EXECUTION_APPROVED` y su prompt = `OWNER_APPROVED`; baseline R02-02 acreditado y rama `evolution/multiprovider-v2`. Este bloque NO constituye recepción Windows de R02-03.
- **Gate de salida R02-03:** al menos tres candidatas sintéticas generadas mediante invocación **real** a Ollama en loopback, con procedencia, hashes, recibos JSON, revisión browser, negativas y ninguna publicación FROZEN ni cambio de enabled global. Hasta observarlo, `LOCAL_PASS/WINDOWS_PENDING`; `EVALUATED`/`ELIGIBLE` NO se conceden automáticamente.
- **Límites:** R02-04 a R02-10 = `DRAFT/NOT_AUTHORIZED`; proveedores externos y MP-1B = `DENIED/NOT_AUTHORIZED`; M2 no declarado. Se conservan todos los `doc_id`, el status histórico `OWNER_APPROVED_PROGRAM` y los 1.752 registros del Source Registry.


## Adenda R02-04 — ejecución individual 2026-10-16

- R02-03 acreditado en Windows: `f2f7bf817e45b38feeb7bb64e638d3df626f825e`, `146/146` pruebas, tres candidatas Ollama reales, cinco capturas, push normal. La **generación** está validada; calidad semántica, aprobación y FROZEN permanecen pendientes.
- R02-04: `SPRINT_EXECUTION_APPROVED` exclusivamente para paridad opcional LM Studio, `OWNER_APPROVED` para su prompt, ejecución sobre el HEAD R02-03 indicado; no supone habilitación global ni requerimiento de instalación de LM Studio.
- LM Studio ausente → `DEFERRED_WITH_REASON`, nunca `REAL_PASS` ni bloqueo del futuro M2 con Ollama. Laboratorio de inferencia separado de Configuración por UX; sin activar R02-05.
- R02-05 y posteriores: `NOT_AUTHORIZED`. Mantener históricos y 1.752 entradas Source Registry inmutables.

## Actualización de ejecución R02-05 — COR178 (Owner individual)

- Entrada canónica: `735ecfd82e9604a4755fd7d4e7c386976984ed71` (R02-04 Windows PASS_WITH_FINDINGS; LM Studio `DEFERRED_WITH_REASON`).
- `R02-05/PILOT-B-ENTRY-RESUME`: `SPRINT_EXECUTION_APPROVED`, solo la unidad B0. `R02-06`: `NOT_AUTHORIZED`.
- Se reutilizan los mecanismos existentes de `CREATE_NEW` neutral, PathGuard, dry-run, revalidación, aprobación, bootstrap y runtime registry persistente.
- El cambio R02-05 es la evidencia/control de entrada de Pilot B por la interfaz y la identidad clara del proyecto activo en Home; no inicia B1 ni establece RF, stack, scaffold o proveedor por defecto.
- El baseline de planificación histórico no se reescribe. El sucesor Git solo se acredita cuando Windows apruebe browser, B0 creado por UI y Git normal.
- Los defectos de select de modelo y espaciado del Laboratorio de modelos (`R02-04`) permanecen findings UX; no se introducen modificaciones de modelo en esta unidad.

## Adenda Owner UI-first 179 — UI_FIRST_PILOT_B_V1


**Norma Owner 179:** leer primero `0_program/11_ADDENDA_UI_FIRST_179.md` y `1_arquitectura/ADR-MP-132-012.md` junto a los contratos vivos. R02-05 se continúa por COR-179, no con la guía COR-178 que pide ID/ruta por consola. R00–R02-04 siguen históricamente inmutables.
