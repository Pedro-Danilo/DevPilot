---
title: "ADR-0007 — Persistencia local con filesystem, SQLite y JSONL"
doc_id: "DEVPL-ADR-0007"
status: "proposed"
version: "0.1.0"
owner: "Ordóñez"
standard: "MIPSoftware"
extension: "MIASI"
phase: "SPRINT-PRECODE-03"
updated: "2026-06-02"
approval: "pending_owner_decision"
---
# ADR-0007 — Persistencia local con filesystem, SQLite y JSONL

## Estado

Proposed.

## Contexto

DevPilot necesita conservar documentos versionables, reportes, estado de workspaces, resultados de gates, ejecuciones, hallazgos, aprobaciones, trazas, uso de herramientas y eventos de costo. Guardarlo todo solo como Markdown sería insuficiente para operación, consultas y dashboards futuros.

## Decisión

Adoptar una arquitectura de persistencia local mixta: Markdown/YAML/JSON para artefactos versionables, SQLite para estado operativo consultable y JSONL para eventos/trazas append-only.

## Consecuencias positivas

- Mantiene local-first.
- Facilita consultas históricas.
- Prepara dashboards desktop/web.
- Permite auditoría y trazabilidad.
- SQLite no requiere servidor externo.

## Consecuencias negativas / riesgos

- Requiere migraciones de schema.
- Puede generar archivos locales no versionables.
- Necesita política clara de retención y redacción.

## Controles obligatorios

- No almacenar secretos en claro.
- Separar fuente versionable de estado generado.
- Mantener backups/migraciones.
- Definir política `.gitignore` para DB/traces cuando aplique.

## Criterios de aceptación

- Existe descriptor de workspace.
- Existe modelo lógico de DB.
- Reportes y runs quedan correlacionados.
- Trazas pueden exportarse sin secretos.
