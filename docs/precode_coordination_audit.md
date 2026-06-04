---
title: "Auditoría de coordinación pre-code — DevPilot Local"
doc_id: "DEVPL-AUDIT-PRECODE-0001"
status: "reviewed"
version: "0.1.0"
owner: "Ordóñez"
standard: "MIPSoftware"
extension: "MIASI"
phase: "PRECODE"
updated: "2026-06-04"
approval: "ready_for_owner_review"
audit_scope:
  - "docs/00_product"
  - "docs/01_requirements"
  - "docs/02_architecture"
  - "docs/estándares/mipsoftware"
  - "docs/estándares/miasi"
---

# Auditoría de coordinación pre-code — DevPilot Local

## 1. Objetivo

Auditar si los artefactos de ingeniería ya desarrollados para DevPilot Local cumplen con MIPSoftware y MIASI, si existe coordinación entre `00_product`, `01_requirements` y `02_architecture`, y si la decisión de incluir los estándares dentro de `docs/` está suficientemente justificada.

## 2. Veredicto ejecutivo

| Área | Veredicto |
|---|---|
| Inclusión de MIPSoftware/MIASI dentro de `docs/` | Pertinente, con documentación adicional necesaria. |
| `00_product` | Cumple y puede mantenerse `approved`. |
| `01_requirements` | Cumple y puede mantenerse `approved`; se corrigió inconsistencia menor en documento de revisión. |
| `02_architecture` | Cumple sustancialmente, pero debe permanecer `reviewed` hasta aprobación explícita de ADR-0002 a ADR-0009. |
| Coordinación general | Alta, con brechas no críticas en estado documental y trazabilidad hacia seguridad/calidad/operación aún pendientes. |
| Preparación para SPRINT-PRECODE-04 | Adecuada. |

## 3. Decisión sobre estándares dentro de `docs/`

La decisión es pertinente para un enfoque docs-as-code y local-first porque permite validar el proyecto contra una referencia normativa local, versionada y auditable. Sin embargo, hacía falta documentar explícitamente la decisión, sus límites, riesgos y política de sincronización.

### Ajustes aplicados

Se agregaron:

```text
docs/README.md
docs/estándares/README.md
docs/reference/standards_inside_docs_decision.md
```

Se actualizó:

```text
docs/reference/mipsoftware_adoption.md
```

## 4. Auditoría de `00_product`

### Cumplimiento

`00_product` cubre correctamente:

- visión de DevPilot Local como plataforma agent-assisted SDLC;
- local-first híbrido;
- MVP, MVP+ y post-MVP;
- compromiso CLI → escritorio → web;
- workspaces;
- integración futura con Git;
- valor de negocio personal;
- alcance y fuera de alcance.

### Veredicto

```yaml
status: approved
recommendation: keep_approved
```

## 5. Auditoría de `01_requirements`

### Cumplimiento

`01_requirements` transforma la visión de producto en requerimientos, historias, casos de uso, criterios de aceptación y trazabilidad. Los requerimientos ya distinguen MVP, MVP+ y post-MVP, e incluyen agentes documentales desde el MVP y agentes especializados en MVP+.

### Hallazgo menor corregido

El documento `sprint_precode_02_requirements_baseline_review.md` permanecía en `reviewed`, aunque el bloque de requerimientos ya tenía auditoría de aprobación. Se promovió a `approved` para mantener consistencia documental.

### Veredicto

```yaml
status: approved
recommendation: keep_approved
```

## 6. Auditoría de `02_architecture`

### Cumplimiento

La arquitectura cubre:

- baseline para MVP, MVP+ y post-MVP;
- C4 context y C4 container;
- local-first híbrido;
- ModelAdapter;
- CostGuard;
- persistencia filesystem + SQLite + JSONL;
- Agent Runtime industrial bajo MIASI;
- Policy Engine;
- aprobaciones humanas;
- Git Adapter;
- Workspace Manager;
- Desktop/Web como evolución comprometida;
- ADRs críticas.

### Brecha formal

La arquitectura no debe promoverse automáticamente a `approved` porque las ADRs `ADR-0002` a `ADR-0009` siguen en estado `proposed` o con aprobación pendiente.

### Veredicto

```yaml
status: reviewed
recommendation: approve_after_owner_accepts_adrs
```

## 7. Coordinación entre producto, requerimientos y arquitectura

| Concepto | Producto | Requerimientos | Arquitectura | Estado |
|---|---|---|---|---|
| Plataforma SDLC completa | Sí | Sí | Sí | OK |
| MVP documental estricto | Sí | Sí | Sí | OK |
| Agentes desde MVP | Sí | Sí | Sí | OK |
| MVP+ con Git/repos/patches/refactor | Sí | Sí | Sí | OK |
| Local-first híbrido | Sí | Sí | Sí | OK |
| APIs externas opcionales | Sí | Sí | Sí | OK |
| Cost control | Sí | Sí | Sí | OK |
| Workspaces | Sí | Sí | Sí | OK |
| Persistencia local | Parcial | Parcial | Sí | A desarrollar más en seguridad/operación |
| Seguridad transversal | Sí | Sí | Sí | Debe profundizarse en SPRINT-PRECODE-04 |
| Observabilidad | Parcial | Parcial | Sí | Debe profundizarse en SPRINT-PRECODE-05/06 |
| MIASI aplicado | Sí | Sí | Sí | Debe formalizarse en `06_miasi` |

## 8. Hallazgos

| ID | Severidad | Hallazgo | Impacto | Recomendación |
|---|---:|---|---|---|
| AUD-PRE-001 | Media | La decisión de incluir estándares en `docs/` no estaba suficientemente documentada. | Riesgo de confusión entre estándar y artefactos del proyecto. | Corregido con decisión formal y READMEs. |
| AUD-PRE-002 | Baja | Ruta `estándares/` usa caracteres no ASCII. | Potencial fricción en scripts o CI futuros. | Mantener por ahora; evaluar alias `standards/` si aparece fricción. |
| AUD-PRE-003 | Baja | Documento de revisión de `01_requirements` estaba `reviewed` mientras el bloque figuraba aprobado. | Inconsistencia de estado. | Corregido a `approved`. |
| AUD-PRE-004 | Media | `02_architecture` tiene ADRs propuestas pendientes. | No debe promoverse aún a `approved`. | Revisar y aceptar ADR-0002..ADR-0009. |
| AUD-PRE-005 | Media | Seguridad, calidad, operación y MIASI aplicado aún están en `draft`. | Normal por fase; bloquea implementación funcional fuerte. | Continuar con SPRINT-PRECODE-04 a 06. |
| AUD-PRE-006 | Media | Falta validador automático para sincronía entre MIPSoftware/MIASI y docs del proyecto. | La revisión aún depende de auditoría manual. | Implementar en sprint funcional posterior. |

## 9. Recomendación

1. Mantener `00_product` en `approved`.
2. Mantener `01_requirements` en `approved`.
3. Mantener `02_architecture` en `reviewed`.
4. Aprobar explícitamente o ajustar ADR-0002..ADR-0009.
5. Avanzar a `SPRINT-PRECODE-04 — Seguridad, privacidad y threat model`.
6. No iniciar desarrollo funcional fuerte hasta cerrar seguridad, calidad, operación y MIASI aplicado.

## 10. Decisión final recomendada

```yaml
precode_status: "partially_approved"
approved_blocks:
  - "00_product"
  - "01_requirements"
reviewed_blocks:
  - "02_architecture"
draft_blocks:
  - "03_security"
  - "04_quality"
  - "05_operations"
  - "06_miasi"
next_action: "owner_review_adrs_then_sprint_precode_04"
```

