---
doc_id: "DEVPL-GSDLC-PROGRAM-CHARTER"
title: "DEVPL-GSDLC — Program Charter"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-08-14"
approval: "approved_by_owner_scope_DEVPL-GSDLC-00-A"
program_id: "DEVPL-GSDLC"
micro_sprint: "DEVPL-GSDLC-00-A"
local_first: true
dry_run_default: true
---
# DEVPL-GSDLC — Program Charter

## 1. Decisión de activación

DEVPL-GSDLC queda **activado administrativamente** por el owner para evolucionar DevPilot desde repo341 hacia un Guided SDLC Engine. Esta activación no declara ninguna capability runtime nueva ni sustituye el parent histórico.

Estado después de DEVPL-GSDLC-00-A:

```text
program_id = DEVPL-GSDLC
program_status = active/00-a
current_backlog = DEVPL-GSDLC-00
current_micro_sprint = DEVPL-GSDLC-00-A
next_micro_sprint = DEVPL-GSDLC-00-B
R01-A = authorized-in-parallel
Guided SDLC runtime implemented = false
```

## 2. Visión vinculante

DevPilot evoluciona a un entorno local de desarrollo de software guiado que conduce un proyecto desde creación hasta release, ejecutando MIPSoftware y MIASI como workflows verificables, con autoría humana o agent-assisted, policies, approvals, testing, Git, traceability y evidence integrados.

El criterio de producto es **UI-complete normal journey**: los operadores externos pueden instalar, auditar y recolectar evidencia, pero no pueden sustituir la autoría normal del proyecto.

## 3. Parent immutable

| Campo | Valor |
|---|---|
| Parent ZIP | `repo_DevPilot_Local_341_POST_H_EVAL_002_PILOT_TRANSITION_REBIND.zip` |
| SHA-256 | `e28cd2bae08d099a2b62c4869c83b6e5a647f3f780ca1572727b7c80f6eeea3b` |
| Git commit | `cff43e8d992ff6139bd13bb1809ce4d497ae0952` |
| Adopción | `2026-08-14` |
| Sucesor | `DEVPL-GSDLC` |

El parent y toda evidencia anterior se conservan sin reescritura.

## 4. Alcance de programa

Incluye, por olas gobernadas: engineering state, local identity/RBAC, project wizard, artifact authoring, executable MIPSoftware/MIASI, model gateway, agent/RAG assistance, planning, coding, quality/Git/evidence, release y hardening.

DEVPL-GSDLC-00-A **solo** activa gobernanza y pausa el piloto. No implementa ninguna de esas capacidades.

## 5. No-go gates persistentes

Permanecen bloqueados salvo ADR/backlog posterior explícito:

- arbitrary shell;
- force push;
- `reset --hard`/rebase automáticos;
- public/non-local API;
- enterprise IAM/tenancy/SSO;
- connector write genérico;
- plugin arbitrary execution;
- remote execution/cloud deploy;
- secrets en source/evidence;
- browser scraping/cookie piggyback de aplicaciones LLM;
- agent self-approval;
- loops/costo ilimitados.

## 6. Roles de programa

- **owner:** aprueba roadmap, backlogs, ADRs y decisiones de promoción.
- **operator:** ejecuta procedimientos locales reproducibles y recolecta evidencia.
- **engineering/reviewer roles:** se diseñan aquí, pero autenticación/RBAC runtime pertenece a GSDLC-02.
- **agent-supervisor:** rol objetivo futuro; no existe como autoridad autenticada en 00-A.

## 7. Métricas del programa

- porcentaje del normal journey UI-complete;
- CLI bridges requeridos por etapa;
- PowerShell requerido por usuario normal;
- mutaciones del proyecto hechas por harness externo;
- cobertura requisito→planning→story→test→commit;
- S0/S1;
- costo/tokens por artifact/story cuando aplique.

## 8. Política de pausa/reanudación del piloto

POST-H-EVAL-002 no se cancela. Queda `paused-before-02-b`. Los cierres 01-A→01-D y 02-A se preservan. El workspace `inventory-sales-local` y su commit `a10d97f425c31300860de7ef5a3c9fd82d6d6f59` no se modifican en GSDLC-00. La reanudación se prevé únicamente en GSDLC-13.

## 9. Seguridad de 00-A

`network_used=false`, `external_api_used=false`, `source_runtime_changed=false`, `pilot_workspace_mutated=false`.

## 10. Gate

00-A solo puede cerrar con parent exacto, pausa explícita y reversible, contratos canónicos sincronizados, pruebas focales PASS y `S0=0/S1=0`.
