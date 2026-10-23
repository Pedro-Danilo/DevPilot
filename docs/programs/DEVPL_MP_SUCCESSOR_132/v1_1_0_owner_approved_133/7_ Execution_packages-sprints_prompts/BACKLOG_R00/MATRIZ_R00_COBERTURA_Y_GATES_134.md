---
doc_id: DEVPL-MP-132-R00-TRACEABILITY-134
version: 1.0.0
status: DRAFT_EXECUTION_GATED
---
# R0 — Matriz de cobertura literal de BACKLOG_R00_132

Nueve ítems exactos; los estados `Owner-133 formalizado` no prueban publicación en Git ni reemplazan gates por incremento.

| ID R0 | Resultado obligatorio | Sprint responsable | Prueba decisiva | Estado al planificar |
|---|---|---|---|---|
| `MP131-R0-01` | Ratificación administrativa G5 separada | R00-03; adjudicar R00-05 | Acta `G5-RATIFICATION-133` publicada + overlay/registry current owner ratified; histórico intacto | Acto Owner ya emitido; publicación PENDING |
| `MP131-R0-02` | Programa 132 y supersession 131 publicadas | R00-01 auditoría → R00-03 publicación | 57/57 MD con hashes, Source Registry, 131 historical only, nuevo HEAD/remote | Aprobación ya emitida; publicación PENDING |
| `MP131-R0-03` | Topología Git decidida, validada | R00-01 → R00-02 | Preflight y receipt de B migrada o A retenida con Owner | Condicional B Owner-133, Windows PENDING |
| `MP131-R0-04` | Audit-first aplicado como gate | R00-01,03,04; cierre 05 | Mapas REUSE/DELTA, NO-OP y allowlists antes de cambios, receipts PASS | Política aprobada; ejecución PENDING |
| `MP131-R0-05` | Baseline riesgos/UX/métricas | R00-04 → R00-05 | Valores medidos o NOT_MEASURED/NOT_AVAILABLE, ledger por ID, Owner prioridades | PENDING |
| `MP132-R0-06` | Gate B Git con backup/rollback y alternativa A | R00-01 → R00-02 | `MIGRATED_B_PASS` o `RETAINED_A_APPROVED`, sin histórico perdido | PENDING |
| `MP132-R0-07` | Aprobación 132 + G5/COR/STOP + rebind | **R00-03** | Actas Owner-133, registros paritarios, DOC SHA, tests, primer baseline limpio | Actos emitidos; repo PENDING |
| `MP132-R0-08` | Auditoría Settings/UI/ledger | R00-04 | UI→API→stores/policy, UX-S2 y MP-0F, Reuse/Delta Map | PENDING |
| `MP132-R0-09` | Estado hardware/dataset/latencias y budgets | R00-04 | Evidencia si medible; NOT_AVAILABLE sin inventar modelo/costo | PENDING |

## Gates y decisiones

| Gate | Permite | No permite |
|---|---|---|
| `G-R00-01 AUDIT_PASS` | Proponer decisión de ubicación | Ejecutar B o publicar 132 |
| `G-R00-02 LOCATION_DECIDED` | Preparar primer cambio documental en ruta segura | Source mutation sin nueva autorización |
| `G-R00-03 AUTHORITY_REBOUND_WINDOWS_PASS` | Considerar 132 físicamente publicado en nuevo HEAD | MP-1B, llamadas E, funcionalidad R1 |
| `G-R00-04 SETTINGS_RISK_AUDITED` | Handoff informado para R1 | Refactor UI por simple preferencia |
| `M0 OWNER_ADJUDICATED` | Solicitar autorización para preparar R1 | Iniciar R1 automáticamente |

## Decisiones históricas que no se reejecutan

- `G5/P3C` y `COR-130`: PASS y ratificados. Se **registran** sus actos, no se ejecutan SYNC-1, pruebas G5 ni COR-130 de nuevo.
- `STOP GLOBAL OWNER_LIFTED`: no un `allow-all`. MP-1B viejo, Pilot A, egress externo, agentes con tools y gastos siguen sin permiso por incremento.
- `ADR-132-010`: arquitectura `OWNER_ACCEPTED`, pero egress `DEFERRED`.
- Git B: aceptación condicional, no prueba de migración ejecutada.
- R1–R10 no son scope de este paquete.


---

## Addendum operacional M0→R1 — sucesor de planificación (14-10-2026)

- **Asunto:** Matriz R00.
- **Actualización concreta:** Adjudicar 9 ítems y COR-151 con 0 blockers; diferimiento R0-09 aceptado; sin inferir R1 autorizado.
- **Evidencia vinculada:** COR-143 (migración B), R00-03/COR-145 (publicación 57 documentos), R00-04/COR-147 (auditoría Settings), COR-150 (paridad 1752), COR-151 (cierre Owner M0).
- **HEAD de autoridad técnica:** `66ab2e6227072c951b5bd2ac9160e8515b1b9fc0`. Las referencias a `8db5b44694abcced3231183e05731e732f5b8f24` y los indicadores `STOP ACTIVE` en secciones históricas no se reescriben como si fueran estados presentes.
- **Autoridad:** copia sucesora propuesta para adopción documental posterior; no constituye un commit, promoción Git, autorización de R1, de MP-1B, de modelo/API externa ni una aceptación funcional de Settings.
- **Transferencias vigentes:** `MP132-R0-09` → R2 para mediciones reales; UX Settings pendiente de reproducción y validación; egress externo DENY; no duplicar ownership entre olas.
