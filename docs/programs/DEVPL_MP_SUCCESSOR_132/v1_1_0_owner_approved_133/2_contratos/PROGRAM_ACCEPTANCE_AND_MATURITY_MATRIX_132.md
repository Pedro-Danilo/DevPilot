---
doc_id: DEVPL-MP-SUCCESSOR-132-PROGRAM_ACCEPTANCE_AND_MATURITY_MATRIX_132
title: "Gates y niveles de madurez de DevPilot por alcance demostrado"
version: "1.1.0"
status: "OWNER_APPROVED_PROGRAM"
baseline_commit: "8db5b44694abcced3231183e05731e732f5b8f24"
owner: "Owner DevPilot"
supersedes_program: "DEVPL_MP_SUCCESSOR_131 v1.0.0"
execution_authority: false
approval_revision: 1
approval_date: "2026-10-13"
approved_by: "Owner Ordóñez (instrucción explícita en conversación)"
approval_scope: "PROGRAMMATIC_PLANNING_ONLY"
owner_decision_ref: "DEVPL-MP-132-OWNER-APPROVAL-133"
---

# Gates y niveles de madurez de DevPilot por alcance demostrado

## Distinción de niveles

| Estado | Prueba necesaria | Lo que NO significa |
|---|---|---|
| `FOUNDATION_PRESENT` | Símbolo/servicio/contrato existente y test focal | Vertical completo |
| `VERTICAL_INTEGRATED` | UI→API→service→candidate→policy→review→apply/quality/git de tarea real | Producto instalable |
| `LOCAL_MODEL_ACCEPTED` | Modelo L real con dataset/version/hardware y candidate validado en Owner UI | Agente autónomo ni API externa |
| `LOCAL_FIRST_PROFESSIONAL` | Pilot B B0–B5 E2E, code/quality/git/release/rollback, seguridad y docs portables | External habilitado |
| `AGENT_ASSISTED` | MIASI policy, bounded handoffs/tools, Pilot B B6, adversarial evals | Tool unrestricted / multiuser enterprise |
| `EXTERNAL_ENABLED` | ADR externa, CostGuard, egress, privacy, Pilot C external real, neg suites | Gratis/siempre encendido |
| `INDUSTRIAL_ACCEPTANCE` | B0–B7, segundo dominio, independent security/ops/evals, Owner acceptance, 0 S0/S1 critical path | Certificación regulatoria o escalabilidad enterprise automática |

## Gates por ola y validación

M0 program authority + Git; M1 kernel/policy/profiles básicos y neg suites; M2 Product Definition L real; M3 Technical Design FROZEN, tech approved, scaffold; M4 Planning trazable; M5 Story arbitraria con source real, Quality/Git; M6 release/restore; M7 agentes evaluados; M8 external o `NOT_ENABLED`; M9 fault injection/UX/perf/launcher; M10 E2E y dictamen independiente. Cada gate conserva si se probó fixture, service-only, full UI o real deployment; nunca usar `PASS` sin alcance.

## Evidencia de salida

`acceptance_id`, `milestone`, `baseline`, `scope`, `test_dataset`, `environment`, `artifacts`, `functional_scenarios`, `negative_scenarios`, `security`, `usability`, `operation`, `known_limits`, `owners`, `status PASS|PASS_WITH_FINDINGS|PARTIAL|BLOCK|NOT_APPLICABLE`, `decision_ref` y SHA. Medidas cuantitativas se calibran con hardware y dataset explícitos, no por intuición.

## Condición de producto profesional

No bastan 144 unit tests de integración, build Vite ni nuevo Git merge. Es indispensable demostrar un proyecto desde necesidad hasta release y recuperación por UI normal, sin escribir source del piloto mediante scripts de operador.
