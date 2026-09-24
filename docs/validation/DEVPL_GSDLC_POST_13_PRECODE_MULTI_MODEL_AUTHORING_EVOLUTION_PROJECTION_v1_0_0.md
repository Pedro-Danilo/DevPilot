---
doc_id: "DEVPL-GSDLC-POST-13-PRECODE-MULTI-MODEL-AUTHORING-EVOLUTION-PROJECTION"
title: "Post-GSDLC-13 — Multi-model agentic authoring over the governed Pre-code lifecycle"
status: "proposed/backlog-candidate/owner-prioritization"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-09-24"
approval: "pending-future-prioritization"
source_finding: "CAP-13C01-AI-001 / DEVPL_UX_P1_FINDINGS_LEDGER_13_B_v1_9_0_ES.md"
implementation_gate: "after-DEVPL-GSDLC-13-greenfield-E2E-closure-before-historical-POST-H-EVAL-002-adoption"
---

# Proyección — Multi-model agentic Pre-code authoring

## 1. Origen

El ledger `DEVPL_UX_P1_FINDINGS_LEDGER_13_B_v1_9_0_ES.md` ya registra `CAP-13C01-AI-001 — Agent/RAG no están integrados como authoring route real de Pre-code` y dispone `BACKLOG / ADR / OWNER-PRIORITIZATION`.

Este documento **desarrolla ese hallazgo existente**. No crea un finding duplicado y no modifica el ledger histórico v1.9.0.

## 2. Arquitectura objetivo

```text
                    Pre-code governed lifecycle
                              │
             ┌────────────────┼────────────────┐
             │                │                │
    DEVPL deterministic   Local Agent     External Agent
    baseline              Ollama/LM       API opt-in
             │                │                │
             └────────────────┼────────────────┘
                              ↓
                      propuesta DRAFT
                              ↓
                       Owner review
                              ↓
                     validate / diff
                              ↓
                        approval
                              ↓
                          apply
                              ↓
                         FROZEN
```

Las tres rutas son productores de propuestas. Ninguna adquiere autoridad para bypass de review, diff, approval, apply o FROZEN.

## 3. Momento adecuado

### 3.1 Diseñar ahora

La arquitectura puede documentarse desde C-01 porque el baseline determinístico ya fija el contrato al que las rutas agentic deberán adaptarse.

### 3.2 No implementar dentro de C-01/C-02/C-03/C-04

Introducir modelos durante el Greenfield acceptance impediría distinguir un defecto del control plane de variabilidad del modelo, prompt, provider o retrieval. Además ampliaría el corrective actual con provider governance, presupuesto, RAG, evaluación y nuevas superficies de seguridad.

### 3.3 Gate recomendado de implementación

Implementar **después de cerrar integralmente `DEVPL-GSDLC-13` Greenfield E2E, incluidos Sprints C, D y E, con baseline determinístico PASS y sin S0/S1 abiertos**, y **antes de reanudar la adopción/migración del `POST-H-EVAL-002` histórico `inventory-sales-local`**.

Ese punto permite usar la evolución agentic sobre un control plane ya probado end-to-end y, a continuación, medir su valor en el piloto histórico real sin confundir estabilización del producto con capacidad del modelo.

Nombre de programa sugerido:

`DEVPL-GSDLC-14 — Multi-model governed agentic authoring and grounded RAG`

El número/nombre definitivo queda sujeto a la planificación post-13.

## 4. Prerrequisitos

Antes de implementation kickoff deben estar PASS:

1. `DEVPL-GSDLC-13` completo;
2. deterministic Pre-code v2 aceptado por C-01;
3. C-02 architecture/ADR flow aceptado;
4. C-03 MIASI/Pre-code readiness aceptado;
5. C-04 planning/stories aceptado;
6. Sprints D/E coding/quality/release flow aceptados;
7. Model Gateway/provider governance de GSDLC-06 vigente;
8. agent-assisted/RAG governance de GSDLC-07 reconciliada con el baseline actual;
9. budgets, provider policy, approval, traces y secrets handling activos;
10. evaluación reproducible disponible.

## 5. Rutas de authoring

### 5.1 Deterministic baseline

- siempre disponible;
- sin API key;
- costo 0;
- reproducible;
- acceptance/fallback/reference oracle contractual, no oracle semántico perfecto.

### 5.2 Local Agent

Providers objetivo iniciales:

- Ollama;
- LM Studio/OpenAI-compatible local endpoint;
- otros adapters locales solo mediante ModelAdapter.

Reglas:

- local-first;
- secrets mínimos;
- timeout y token budget;
- bounded tool loop;
- sin arbitrary shell;
- DRAFT-only.

### 5.3 External Agent

- opt-in explícito;
- provider allowlist;
- API key por secret store/env, nunca logs;
- preflight de costo;
- token/cost ceilings;
- data egress policy;
- no fallback silencioso de local a cloud;
- DRAFT-only.

## 6. ModelAdapter

La capa agentic no debe acoplar Pre-code a un proveedor concreto.

Contrato mínimo sugerido:

- provider/model identity;
- capabilities;
- structured input;
- tool policy;
- timeout;
- token/cost budget;
- response schema;
- usage/cost metadata;
- trace/provenance;
- cancellation;
- normalized error taxonomy.

DevPilot decide policies; el adapter traduce al provider.

## 7. RAG grounded

RAG debe recuperar únicamente fuentes autorizadas:

- Project Context;
- artifacts FROZEN del proyecto;
- standards MIPSoftware/MIASI;
- documentos importados y aprobados;
- otras fuentes explícitamente allowlisted.

Provenance mínima:

- query/retrieval id;
- source refs;
- source hashes/version;
- chunks usados;
- retrieval policy;
- model/provider;
- prompt/instruction version;
- generated proposal hash.

Evals obligatorios:

- groundedness;
- source coverage;
- unsupported-claim rate;
- deterministic baseline comparison cuando aplique.

## 8. Lifecycle común

Todas las rutas producen una propuesta runtime-only:

`producer → DRAFT → Owner review → validate/diff → approval → apply → FROZEN`

No habrá una ruta “agent apply” paralela.

Agent/RAG no pueden:

- autoaprobar;
- escribir source directamente;
- ampliar workspace scopes;
- crear provider credentials;
- elevar budgets;
- seleccionar cloud provider por fallback silencioso.

## 9. Evaluación

Comparar al menos:

- deterministic baseline;
- local model seleccionado;
- external model opt-in cuando se autorice.

Dimensiones:

- contract validity;
- semantic coverage;
- traceability;
- groundedness;
- edit distance/rework del Owner;
- latency;
- tokens/cost;
- failure recovery;
- reproducibility de provenance.

No se adjudica superioridad por fluidez textual.

## 10. Seguridad y operación

- dry-run por defecto;
- loops limitados;
- explicit tool allowlist;
- no destructive actions;
- secrets redactados;
- timeout/cancellation;
- budget gate;
- provider/data-egress disclosure;
- audit log;
- fail closed en approval/authority ambiguity.

## 11. Posible descomposición futura

- 14-A: ModelAdapter + capability/provider contract;
- 14-B: Local Agent authoring sobre Product Vision/Scope/Requirements;
- 14-C: External API opt-in + budget/data-egress governance;
- 14-D: grounded RAG + provenance;
- 14-E: evals, UX comparison y bounded fallback;
- 14-F: integration acceptance sobre piloto histórico.

La descomposición definitiva debe hacerse después del cierre de GSDLC-13 para usar evidencia real de Sprints C-E.

## 12. PASS para iniciar implementación futura

- baseline Greenfield E2E cerrado;
- no S0/S1 abiertos que afecten artifact lifecycle/model gateway/RAG;
- determinismo y provenance v2 estables;
- MIASI applicability resuelta;
- secrets/budget/provider governance activos;
- ADR de lifecycle común aprobada.

## 13. BLOCK

No iniciar si:

- GSDLC-13 sigue corrigiendo el control plane;
- se pretende sustituir el baseline determinístico;
- Agent/Provider puede escribir source antes de approval;
- se requiere una API externa para que DevPilot complete el flujo básico;
- RAG no puede probar sus fuentes;
- no existen límites de costo/loops/timeout.

## 14. Riesgos

- contaminar el baseline E2E con variabilidad de provider/modelo antes de cerrar el control plane;
- introducir fallback silencioso a cloud o costos no autorizados;
- crear una vía de source write/approval paralela al lifecycle gobernado;
- RAG no grounded o con fuentes no autorizadas;
- acoplar Pre-code a un proveedor concreto y dificultar evaluación/fallback;
- loops agentic sin límites de tiempo, tools o presupuesto.

## 15. Comandos de verificación del gate futuro

Mientras la evolución permanezca diferida, solo debe verificarse que el finding fuente y esta proyección existan; no hay runtime que ejecutar. Ejemplo PowerShell de inspección documental:

```powershell
Set-Location 'D:\Projects\DevPilot_Local'; Select-String -LiteralPath '.\docs\validation\DEVPL_GSDLC_POST_13_PRECODE_MULTI_MODEL_AUTHORING_EVOLUTION_PROJECTION_v1_0_0.md' -Pattern 'DEFERRED UNTIL POST-GSDLC-13 GATE','DRAFT','Owner review','approval','FROZEN'
```

Cuando se abra el futuro programa, los comandos operacionales deberán definirse en su sprint aprobado; no se reutiliza el operador C-01.

## 16. Estado

`PROPOSED / DEFERRED UNTIL POST-GSDLC-13 GATE`.

Este documento es una proyección para planificación futura; no autoriza implementación durante el corrective actual.
