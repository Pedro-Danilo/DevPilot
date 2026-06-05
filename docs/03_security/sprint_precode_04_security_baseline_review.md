---
title: "SPRINT-PRECODE-04 Review — Seguridad, privacidad y threat model"
doc_id: "DEVPL-PRECODE-04-REVIEW"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
standard: "MIPSoftware"
extension: "MIASI"
phase: "SPRINT-PRECODE-04"
updated: "2026-06-05"
approval: "approved_by_owner_direction"
source_baseline: "00_product approved + 01_requirements approved + 02_architecture approved"
---

# SPRINT-PRECODE-04 Review — Seguridad, privacidad y threat model

## 1. Objetivo

Definir amenazas, controles, gestión de secretos, protección de datos, riesgos de filesystem, riesgos agentic, políticas de `dry-run` y criterios bloqueantes de seguridad para DevPilot Local.

## 2. Documentos producidos/actualizados

| Documento | Estado | Versión |
|---|---|---:|
| `security_threat_model.md` | reviewed | 0.4.0 |
| `privacy_assessment.md` | reviewed | 0.4.0 |
| `precode_coordination_audit_sprint04_entry.md` | reviewed | 0.4.0 |
| `02_architecture/sprint_precode_03_architecture_approval_audit.md` | approved | 1.0.0 |

## 3. Decisiones de seguridad incorporadas

| Decisión | Estado |
|---|---|
| Deny by default | Adoptada |
| Dry-run por defecto | Adoptada |
| Path sandbox por workspace | Adoptada |
| SecretGuard obligatorio | Adoptada |
| CostGuard para APIs externas | Adoptada |
| Human approval para acciones críticas | Adoptada |
| Tool Registry con permisos y side effects | Adoptada |
| Git Adapter read-only inicial | Adoptada |
| No aplicación automática de patches | Adoptada |
| Separación entre recomendación agentic y gate determinístico | Adoptada |
| Redacción de reportes, logs y trazas | Adoptada |

## 4. Riesgos cubiertos

| Categoría | Cobertura |
|---|---|
| Filesystem | Escritura fuera de workspace, overwrite, path traversal |
| Secretos | `.env`, API keys, tokens, connection strings |
| Agentes | Excessive agency, tool misuse, hallucinated compliance |
| LLM | Prompt injection, output inseguro, data leakage, costos |
| Git | Commit indebido, patches inseguros, diffs sensibles |
| Persistencia | SQLite, JSONL, reportes y retención |
| Privacidad | Datos sensibles, APIs externas, prompts y trazas |
| Supply chain | Dependencias y riesgos futuros |
| Desktop/Web futura | Riesgos de auth/session para diseño posterior |

## 5. Criterios de aprobación

El sprint puede promoverse a `approved` cuando el owner acepte:

1. la matriz de amenazas;
2. la política de privacidad;
3. los security gates;
4. los criterios de bloqueo;
5. la política de APIs externas con CostGuard y SecretGuard;
6. la regla de no aplicar cambios destructivos sin aprobación humana.

## 6. Pendientes para sprints posteriores

| Sprint | Pendiente |
|---|---|
| SPRINT-PRECODE-05 | Incorporar pruebas de seguridad, logs, reportes y operación. |
| SPRINT-PRECODE-06 | Completar Agent Card, Tool Card, Policy Card, Eval Card, Human Approval Card y Observability Card. |
| Sprint funcional futuro | Implementar secret scanner, path sandbox, policy engine y cost guard. |

## 7. Veredicto

SPRINT-PRECODE-04 queda en `reviewed`, listo para revisión del owner. No se marca como `approved` automáticamente porque seguridad y privacidad son decisiones sensibles que deben ser aceptadas explícitamente.
