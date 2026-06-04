---
title: "Estándares internos versionados — MIPSoftware y MIASI"
doc_id: "DEVPL-STANDARDS-README"
status: "reviewed"
version: "0.1.0"
owner: "Ordóñez"
standard: "MIPSoftware"
extension: "MIASI"
phase: "PRECODE"
updated: "2026-06-04"
approval: "ready_for_owner_approval"
---

# Estándares internos versionados

## 1. Propósito

Esta carpeta contiene una copia versionada de los estándares internos que gobiernan DevPilot Local:

```text
estándares/
  mipsoftware/
  miasi/
```

Su presencia dentro de `docs/` permite que la documentación del proyecto, los validadores futuros y los agentes de DevPilot consulten una referencia local de los estándares aplicables.

## 2. Decisión

La inclusión de MIPSoftware y MIASI dentro del repositorio de DevPilot Local es pertinente porque:

- preserva trazabilidad entre estándar y artefactos del proyecto;
- permite revisión por Git y pull request;
- habilita validadores locales sin depender de red;
- facilita que los agentes consulten el estándar de forma controlada;
- refuerza el enfoque local-first.

## 3. Regla de sincronización

MIPSoftware y MIASI no deben editarse ad hoc dentro de un proyecto aplicado sin registrar decisión. Si se detecta una mejora del estándar, debe abrirse una tarea explícita para actualizar el estándar fuente y luego sincronizar la copia local.

