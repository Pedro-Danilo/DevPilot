---
title: Registro de excepciones — MIPSoftware
doc_id: MIPS-REF-002
doc_type: reference
version: 0.1.0
status: reviewed
owner: AI_agents / MIPSoftware
scope: software-engineering-model
created: '2026-05-31'
updated: '2026-05-31'
---

# Registro de excepciones — MIPSoftware

| ID | Categoría | Severidad | Excepción | Riesgo | Mitigación | Responsable | Estado |
|---|---|---:|---|---|---|---|---|
| EXC-001 | Schemas | Media | No todas las plantillas tienen schema JSON. | Automatización parcial. | Priorizar schemas según uso en DevPilot. | Technical Lead | Abierta |
| EXC-002 | Automatización | Media | Aún no hay validadores CLI. | Validación manual. | Crear comandos `devpilot validate-*`. | DevPilot Owner | Abierta |
| EXC-003 | Documentación pedagógica | Baja | `tutorials/`, `how_to/`, `explanations/` tienen contenido mínimo. | Curva de adopción mayor. | Agregar guías conforme avance el primer proyecto. | Documentation Owner | Abierta |
| EXC-004 | Validación empírica | Media | MIPSoftware no ha sido aplicado end-to-end. | Brechas prácticas no observadas. | Usar DevPilot Local como piloto. | Product/Engineering Lead | Abierta |
| EXC-005 | Compliance regional | Media | No se incorporan anexos legales por país/sector. | Cumplimiento incompleto en dominios regulados. | Crear anexos por proyecto. | Security/Legal Owner | Abierta |
