---
doc_id: "DEVPL-GSDLC-13-GREENFIELD-PILOT-PROJECT-BRIEF"
title: "DEVPL-GSDLC-13 — Greenfield pilot project brief"
status: "approved"
version: "1.1.0"
owner: "Ordóñez"
updated: "2026-09-21"
supersedes: "DEVPL_GSDLC_13_GREENFIELD_PILOT_PROJECT_BRIEF_v1_0_0_APPROVED.md"
pilot_workspace: 'D:\Projects\DevPilot_Workspaces\inventory-sales-local-greenfield'
operator_project_writes: 0
---

# Greenfield pilot project brief

## Business idea — único input funcional predefinido

El Owner expresará, en lenguaje de necesidad y no de diseño oracle, una aplicación local para una pequeña empresa que permita administrar productos, controlar existencias, registrar ventas, actualizar automáticamente el inventario, consultar información básica de ventas e identificar productos con poco stock.

DevPilot debe ayudar a convertir esa necesidad en Vision/Scope/Requirements/Architecture/Test Strategy/ADRs/plan/stories. Los ejemplos del User Journey Runbook son ilustrativos y no deben copiarse como artifacts preconstruidos.

## Constraints

- workspace nuevo: `D:\Projects\DevPilot_Workspaces\inventory-sales-local-greenfield`;
- Git creado por DevPilot;
- no copy desde `inventory-sales-local`;
- local-first;
- no cloud obligatorio;
- mock/no API baseline;
- modelo local opcional; external API solo aprobada/provenanced;
- stack se decide dentro del Guided SDLC, no por ChatGPT externo;
- operator project writes=0;
- mandatory terminal escapes=0.

## Resultado mínimo

Aplicación local instalable/reproducible con al menos un flujo completo de inventario y venta, pruebas, Git gobernado, package/checksum/SBOM cuando corresponda, clean install y rollback.
