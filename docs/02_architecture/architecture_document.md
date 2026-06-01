---
title: "Architecture Document — DevPilot Local"
doc_id: "DEVPL-ARCH-001"
status: "draft"
version: "0.1.0"
owner: "Ordóñez"
standard: "MIPSoftware"
updated: "2026-06-01"
---

# Architecture Document

## Drivers arquitectónicos

- Local-first.
- Sin API keys en MVP.
- Dry-run por defecto.
- Validación documental antes que automatización autónoma.
- Preparado para agentes, pero controlado por MIASI.

## Vista C4 — Contexto

```mermaid
flowchart LR
  User[Desarrollador / Ordóñez] --> CLI[DevPilot Local CLI]
  CLI --> Project[Workspace del proyecto]
  CLI --> Standards[MIPSoftware + MIASI]
  CLI --> Reports[Reportes JSON/Markdown]
```

## Vista C4 — Contenedores

```mermaid
flowchart TD
  CLI[CLI] --> Core[DevPilot Core]
  Core --> Validators[Validators]
  Core --> Checklists[Checklist Engine]
  Core --> Reports[Report Writer]
  Validators --> Docs[Project Docs]
  Checklists --> Docs
```

## Componentes iniciales

| Componente | Responsabilidad |
|---|---|
| CLI | Interfaz local de ejecución. |
| Artifact Validator | Validar existencia y contenido mínimo. |
| MIASI Detector | Determinar activación MIASI. |
| Readiness Evaluator | Emitir PASS/FAIL. |
| Report Writer | Guardar evidencia. |
