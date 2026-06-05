---
title: Plantilla — Backup Restore Plan
doc_id: MIPS-TPL-BACKUP-RESTORE
doc_type: template
version: 0.1.0
status: draft
owner: AI_agents / MIPSoftware
scope: observability-operations-sre
created: '2026-05-31'
updated: '2026-05-31'
related_standard: MIPS-DOC-012 — Observabilidad, operación, SRE e incidentes
---

# Plantilla — Backup Restore Plan

## 1. Propósito

Definir cómo se protegen, restauran y verifican datos persistentes.

## 2. Campos obligatorios

| Campo | Descripción |
|---|---|
| Datos cubiertos | Bases, storage, archivos, configuraciones. |
| Frecuencia | Horaria, diaria, semanal. |
| Retención | Tiempo de conservación. |
| Ubicación | Local, offsite, cloud, cifrado. |
| RPO | Pérdida máxima aceptable de datos. |
| RTO | Tiempo máximo de recuperación. |
| Prueba de restore | Frecuencia y evidencia. |
| Seguridad | Cifrado, acceso, auditoría. |
| Eliminación | Procedimiento al retiro. |

## 3. Ejemplo

```yaml
system: "inventory-db"
backup:
  frequency: "daily"
  retention: "30d"
  encryption: true
rpo: "24h"
rto: "4h"
restore_test:
  frequency: "monthly"
  last_test: "2026-05-30"
```

## 4. Criterios de rechazo

- Hay datos persistentes sin backup.
- El restore nunca se ha probado.
- Los backups no están protegidos.
