---
doc_id: "POST-H-019-A-PLUGIN-SANDBOX-DESIGN-REPORT"
title: "POST-H-019-A — Plugin sandbox threat model and design report"
status: "approved"
version: "0.1.0"
owner: "Ordóñez"
updated: "2026-06-30"
approval: "approved_by_owner"
phase: "POST-FASE-H"
source_of_truth: true
preliminary: true
---

# POST-H-019-A — Plugin sandbox threat model and design report

## Resultado

Estado: `implemented-initial`.

POST-H-019-A aprueba el backlog POST-H-019 para implementación y agrega el threat model y el diseño del sandbox de plugins sin habilitar ejecución arbitraria. El alcance es metadata-only y validator-only.

## Implementado

```text
docs/03_security/plugin_sandbox_threat_model.md
docs/02_architecture/plugin_sandbox_design.md
docs/POST-H-019_plugin_sandbox_design.md
tests/test_post_h_019_plugin_sandbox_design.py
```

## Criterios PASS cubiertos

```text
PASS si threat model cubre al menos 10 amenazas: cubre 15 amenazas identificadas.
PASS si el diseño declara plugin_execution_allowed=false.
PASS si se documentan no-go gates.
PASS si los documentos tienen frontmatter aprobado según convención.
```

## Criterios BLOCK preservados

```text
No se habilita plugin execution.
No se propone import dinámico de plugins.
No se propone subprocess/shell.
No se habilita red, APIs externas, marketplace, pip install ni remote execution.
No se omiten amenazas de secretos, red o filesystem.
```

## Límites

POST-H-019-A no implementa permission model ejecutable, manifest v2, static validator ampliado, install dry-run nuevo, exposure report ni quality gate. Esos elementos quedan para POST-H-019-B/C/D/E.
