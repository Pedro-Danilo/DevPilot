---
doc_id: "ADR-DEVPL-GSDLC-13-C-01-DRAFT-FIRST-SEMANTIC-REVIEW"
title: "Draft-first UX over governed internal Semantic Model"
status: "accepted"
version: "1.0.0"
date: "2026-09-25"
decision_owner: "Owner"
source_authority: "repo443 / 7a5afa2c28fc30240ee6e347dde345231134384a"
---

# ADR — Draft-first UX sobre Semantic Model gobernado

## Contexto

Repo443 introdujo un Semantic Model determinístico que corrigió la derivación semántica de Vision/Scope/Requirements. En `13-C-01-retest-03`, la experiencia obligó al Owner a microconfirmar actores, outcomes, capabilities, constraints y preguntas antes de ver el documento completo. Una fila opcional vacía pudo bloquear la operación y el bloqueo de contenido se presentó como HTTP 403.

## Decisión

1. El Semantic Model continúa como representación interna, persistente, trazable y determinística.
2. La ruta normal es **Draft-first**: DevPilot genera primero el documento completo.
3. El Owner revisa el artefacto, no la matriz interna.
4. Las decisiones estrictamente necesarias aparecen en una **Decision Inbox** compacta y stage-aware.
5. El Semantic Model completo queda accesible solo como detalle avanzado/auditoría.
6. El Owner puede editar el DRAFT conservando `DEVPL_MOCK` provenance.
7. Una edición invalida cualquier plan/diff/approval basado en el DRAFT anterior.
8. HTTP 403 queda reservado a autorización; los problemas semánticos de contenido usan una respuesta de validación accionable.
9. Vision/Scope no deben resolver anticipadamente decisiones que solo son necesarias para Requirements.

## Razones

- reduce carga cognitiva;
- preserva determinismo y auditabilidad;
- evita transformar gobernanza en burocracia;
- mantiene human-in-the-loop donde aporta valor;
- permite futura sustitución del provider semántico sin cambiar lifecycle/diff/approval;
- conserva el beneficio diferencial de DevPilot frente a pegar manualmente un documento generado externamente.

## Consecuencias

### Positivas

- experiencia centrada en artefactos comprensibles;
- menos decisiones innecesarias;
- menor probabilidad de errores de formulario;
- provenance y quality gates siguen intactos;
- mejor base para providers locales/externos futuros.

### Costes

- el generador debe tolerar semántica de alto nivel en etapas tempranas;
- Requirements debe gestionar decisiones diferidas;
- UI necesita edición DRAFT y Decision Inbox;
- tests deben cubrir stage-aware validation y replan tras edición.

## Alternativas descartadas

- conservar microconfirmación y añadir un botón `Aceptar todo`: oculta complejidad sin corregirla;
- eliminar Semantic Model: pierde trazabilidad y vuelve al defecto de derivación anterior;
- introducir un LLM ahora: amplía alcance y elimina una baseline determinística estable;
- cambiar todo error de `BLOCK` globalmente: riesgo transversal innecesario; la corrección se limita a la ruta pre-code afectada.
