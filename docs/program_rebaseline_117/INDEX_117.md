---
doc_id: "DEVPL-REB-117-INDEX"
title: "Índice de entrega, aprobaciones y punto autorizado"
version: "1.0.0"
status: "APPROVED / EXECUTION-GATED"
date: "2026-10-11"
owner_decision: "OWNER-APPROVAL-2026-10-11-REBASELINE-116"
implementation_authority: false
multiprovider_stop_lifted: false
---

# Índice de entrega, aprobaciones y punto autorizado

## Alcance de la aprobación expresa
El Owner solicitó elevar la propuesta 116 a `approved` y derivar los artefactos P0–P3. Por tanto **G0=PASS** como resolución de estrategia; los artefactos 117 son **documentos de programa aprobados, ejecución condicionada**, sin commits, source patches, arranques de jobs o permisos Git. No se ha alterado `repo465`, Pilot A ni MP STOP por redactar este paquete.

## Lectura ordenada
1. `PROPUESTA_REBASELINE_116_APPROVED.md`: decisión con G0 aprobado y original conservado.
2. `AUTORIDAD_Y_SUPERSESSION_117.md`, `BRIDGE_GREENFIELD_117.md`, `BRIDGE_MP_STOP_SYNC_117.md`, `ADR_REBASELINE_117.md`: contratos de transición y precedencia.
3. `ROADMAP_P0_P3_117.md`, `BACKLOG_P0_P3_117.md`, `GATES_EVIDENCIA_117.md`: programa y acceptance.
4. `MATRIZ_CONTRATOS_117.md`: impacto exacto sobre ambos paquetes y cuándo publicar cada cambio.
5. `SPRINT_P0_117.md` y `PROMPT_P0_117.md` son **siguiente trabajo posible**. Los micro-sprints sucesores solo se abren después de sus gates.
6. `PROTOCOLO_AUDITORIA_SYNC1_117.md`: cláusula principal de P3: inspeccionar el final real de la rama determinística **y** las capacidades instaladas de MP para elegir estrategia, antes de cualquier sync.

## Micro-sprints aprobados (NO ejecutados)
| Orden | Sprint | Prompt | Requiere |
|---|---|---|---|
| 1 | `SPRINT_P0_117.md` | `PROMPT_P0_117.md` | G0 |
| 2 | `SPRINT_P1_117.md` | `PROMPT_P1_117.md` | G1 |
| 3 | `SPRINT_P2A_117.md` | `PROMPT_P2A_117.md` | G2 |
| 4 | `SPRINT_P2B_117.md` | `PROMPT_P2B_117.md` | P2A PASS |
| 5 | `SPRINT_P2C_117.md` | `PROMPT_P2C_117.md` | P2A+B PASS |
| 6 | `SPRINT_P3A_117.md` | `PROMPT_P3A_117.md` | G3 |
| 7 | `SPRINT_P3B_117.md` | `PROMPT_P3B_117.md` | G4A |
| 8 | `SPRINT_P3C_117.md` | `PROMPT_P3C_117.md` | G4B + Owner approval plan exacto |

## STOP
MP worktree NO debe recibir writes en P0–P3B. Autoridad puente aprobada ≠ merge ni aprobación del sync. `MP-1B` sigue prohibido. Después de P3-C/PASS se revisará el programa global MP sobre el repositorio fusionado; este paquete no pre-aprueba su implementación.

## Estado declarado al publicar el ZIP documental
`G0=APPROVED`; `G1=PENDING`; `G2=PENDING`; `G3=PENDING`; `G4A=PENDING`; `G4B=PENDING`; `G5=PENDING`; `MP-1B=BLOCKED`. Los hashes del paquete corroboran únicamente integridad documental, no la existencia de receipts operativos ni el estado del repositorio Windows.
