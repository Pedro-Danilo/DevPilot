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

## Actualización operativa MP132 post-M1 — R02-01

**Matriz de madurez vigente.** R01 primera vertical determinista: `PASS_WITH_FINDINGS`, no E2E multi-modelo; local real / semantic judge / grounded RAG real: `NOT_TESTED`; externo `DENIED`. M2 no evaluado y R02-02..10 no autorizados.

**Autoridad:** esta sección actualiza el *estado operativo*, no modifica el `status: OWNER_APPROVED_PROGRAM` de la aprobación histórica Owner-133, ni autoriza R02-02. Source Registry mantiene el `doc_id` y `path` originales.


## Adenda de estado operativo — R02-03/COR-176 (sucesora, no retroactiva)

- **Predecesores acreditados:** R02-01 `CLOSED/WINDOWS_PASS` en `4a4443f1631acdbfcd19e1e2fca4be36f707daf9`; R02-02 `CLOSED/WINDOWS_PASS` en `8a9b1cf915f8cfb9d08b35d6d1c13467d0bd08fc`. Las adendas R02-01 anteriores se conservan como historia, no son la autoridad de ejecución actual.
- **Autorización individual vigente:** únicamente `R02_03_OLLAMA_REAL_CANDIDATE_SPRINT.md` = `SPRINT_EXECUTION_APPROVED` y su prompt = `OWNER_APPROVED`; baseline R02-02 acreditado y rama `evolution/multiprovider-v2`. Este bloque NO constituye recepción Windows de R02-03.
- **Gate de salida R02-03:** al menos tres candidatas sintéticas generadas mediante invocación **real** a Ollama en loopback, con procedencia, hashes, recibos JSON, revisión browser, negativas y ninguna publicación FROZEN ni cambio de enabled global. Hasta observarlo, `LOCAL_PASS/WINDOWS_PENDING`; `EVALUATED`/`ELIGIBLE` NO se conceden automáticamente.
- **Límites:** R02-04 a R02-10 = `DRAFT/NOT_AUTHORIZED`; proveedores externos y MP-1B = `DENIED/NOT_AUTHORIZED`; M2 no declarado. Se conservan todos los `doc_id`, el status histórico `OWNER_APPROVED_PROGRAM` y los 1.752 registros del Source Registry.


## Adenda R02-04 — ejecución individual 2026-10-16

- R02-03 acreditado en Windows: `f2f7bf817e45b38feeb7bb64e638d3df626f825e`, `146/146` pruebas, tres candidatas Ollama reales, cinco capturas, push normal. La **generación** está validada; calidad semántica, aprobación y FROZEN permanecen pendientes.
- R02-04: `SPRINT_EXECUTION_APPROVED` exclusivamente para paridad opcional LM Studio, `OWNER_APPROVED` para su prompt, ejecución sobre el HEAD R02-03 indicado; no supone habilitación global ni requerimiento de instalación de LM Studio.
- LM Studio ausente → `DEFERRED_WITH_REASON`, nunca `REAL_PASS` ni bloqueo del futuro M2 con Ollama. Laboratorio de inferencia separado de Configuración por UX; sin activar R02-05.
- R02-05 y posteriores: `NOT_AUTHORIZED`. Mantener históricos y 1.752 entradas Source Registry inmutables.
