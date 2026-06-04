---
title: ADR-0004 — Usar Diátaxis para organización documental
doc_id: ADR-0004
doc_type: adr
version: 0.1.0
status: accepted
owner: AI_agents / MIPSoftware
scope: software-engineering-model
created: '2026-05-31'
updated: '2026-05-31'
decision_status: accepted
---

# ADR-0004 — Usar Diátaxis para organización documental

## Estado

Aceptado.

## Contexto

La documentación del estándar debe servir a múltiples necesidades: aprender, ejecutar tareas, consultar referencia y entender decisiones. Mezclar todo en un único tipo de documento reduce utilidad.

## Decisión

Adoptar Diátaxis como marco de clasificación documental: tutoriales, how-to guides, referencia técnica y explicaciones.

## Consecuencias positivas

- Mejora navegabilidad.
- Evita mezclar guías prácticas con teoría.
- Permite construir documentación útil para humanos y agentes DevPilot Local.

## Consecuencias negativas o costos

- Requiere clasificar documentos con disciplina.
- Algunos documentos híbridos deberán declarar su doc_type dominante.

## Criterios de cumplimiento

- Cada documento debe declarar doc_type.
- README debe diferenciar tutorial, how-to, referencia y explicación.
- Plantillas y checklists se ubican como referencia/operación.

## Relación con MIASI

MIASI ya separa documentos rectores, templates, checklists y referencias. MIPSoftware replica y amplía esta práctica.

## Referencias

- Diátaxis.
- MIASI v1.0.0.

## Changelog

| Versión | Fecha | Cambio |
|---|---|---|
| 0.1.0 | 2026-05-31 | ADR inicial. |
