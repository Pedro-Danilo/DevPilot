---
title: "POST-H-004-B — Agent/tool/policy semantic rules report"
doc_id: "POST-H-004-B-AUDIT"
status: "implemented-initial"
version: "0.1.0"
owner: "Ordóñez"
updated: "2026-06-24"
phase: "POST-FASE-H"
local_first: true
dry_run: true
---

# POST-H-004-B — Agent/tool/policy semantic rules report

## Propósito

Documentar la primera implementación real del validador semántico Policy/MIASI. Esta entrega convierte el contrato `MiasiSemanticReport` de `POST-H-004-A` en un comando operativo local: `python -m devpilot_core miasi semantic-validate --json`.

## Alcance implementado

```text
- Carga declarativa del bundle MIASI actual.
- Reglas agent/tool para allowed_tools existentes.
- Reglas agent/tool/policy para policy_rule_ids existentes.
- Reglas de status para detectar posible ejecutabilidad prematura.
- Detección de tools sensibles sin approval explícito.
- Detección de contradicciones allow/deny/block por domain/action.
- Detección de no-go gates remote/plugin/connector execute en allow.
```

## Criterios PASS

```text
PASS si el bundle vigente produce ok=true sin findings block/error.
PASS si el reporte valida contra MiasiSemanticReport.
PASS si fixtures inseguros producen BLOCK.
PASS si no se ejecuta runtime agent/tool/test/subprocess/network/API.
```

## Criterios BLOCK

```text
BLOCK si un agente referencia una tool inexistente.
BLOCK si agent/tool referencia policy_rule_ids inexistentes.
BLOCK si high-risk controlled_execution/network_cost implementado no requiere approval.
BLOCK si una policy rule no-go de remote/plugin/connector execute queda allow.
BLOCK si existen contradicciones allow/deny/block para el mismo domain/action.
```

## Riesgos residuales

El bundle vigente produce warnings para herramientas `controlled_write` high-risk que no declaran approval explícito a nivel de tool, pero que actualmente están gobernadas por gates locales/sandbox/registry/rollback. Esta deuda queda deliberadamente para `POST-H-004-C`, donde debe cruzarse con approval, RBAC y security guards.

## No-go gates preservados

```text
No remote execution.
No connector write.
No plugin execution.
No tool execution genérico.
No modificación de PolicyEngine para pasar tests.
No declaración production-ready-local para POST-H-004-B.
```
