---
doc_id: "ADR-DEVPL-GSDLC-13-C-01-SEMANTIC-MODEL-DETERMINISTIC-BASELINE"
title: "ADR — Semantic Model como contrato intermedio del baseline determinístico Pre-code"
status: "accepted"
version: "1.0.0"
owner: "Ordóñez / DevPilot"
updated: "2026-09-24"
---

# ADR — Semantic Model como contrato intermedio del baseline determinístico Pre-code

## Context

El retest `13-C-01-retest-02` demostró que la derivación determinística v2 mantenía provenance y dependencia upstream, pero convertía fragmentos descriptivos del `business_need` en pseudo-capabilities y requisitos no verificables. Aumentar reglas lingüísticas sobre texto libre no ofrece una garantía profesional generalizable.

## Decision

Adoptar `PreCode Semantic Model v1` como representación intermedia gobernada para C-01.

- La extracción determinística es conservadora y produce candidatos/evidencia, no verdad semántica universal.
- El Owner resuelve ambigüedad crítica dentro de la UI.
- `deterministic-semantic-model-template-v3` compila el modelo confirmado a Vision/Scope/Requirements.
- Quality gates determinísticos verifican invariantes observables antes de review/approval.
- Markdown no es la autoridad primaria de edición semántica.
- El runtime lifecycle sigue siendo la autoridad de estado; no se mutan bytes después de approval para cambiar frontmatter.

## Consequences

### Positive

- reproducibilidad y baseline offline/costo cero;
- trazabilidad explícita de interpretación;
- fail-closed en vez de contenido aparentemente profesional inventado;
- contrato estable para futuros Local/External model providers;
- testabilidad por fixtures sin overfitting al piloto.

### Trade-offs

- el Owner debe confirmar decisiones semánticas cuando la fuente es ambigua;
- el baseline determinístico no pretende equivaler a un analista senior;
- el model schema pasa a ser un contrato interno que debe versionarse.

## Future compatibility

Futuros `LocalModelProvider`/`ExternalModelProvider` podrán proponer el mismo Semantic Model, pero no forman parte de este corrective. Todos deberán pasar los mismos gates y el mismo lifecycle gobernado.
