---
doc_id: "ADR-DEVPL-GSDLC-13-C-02-ADR-COMPANION"
title: "GSDLC-13-C-02 — Governed standalone ADR companion after Architecture freeze"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-09-27"
approval: "corrective C02_ADR_101 design authority"
---

# Contexto

El selective retest `13-C-02` sobre repo448 demostró que el provider determinístico genera Architecture con ADR-001..ADR-004 embebidos y que el lifecycle principal puede completar `DRAFT → review/diff → approval → apply → FROZEN`. Sin embargo, el contrato de acceptance exige ADRs gobernados bajo `docs/02_architecture/adrs/` y la implementación repo448 no materializa esos artefactos standalone.

El directorio ADR forma parte del Project Shell neutral y no debe ser poblado por scripts del operador, edición externa ni ChatGPT como oracle.

# Decisión

Introducir un **Architecture ADR companion gate** entre `Architecture FROZEN` y el inicio de `Security`.

El Architecture Document FROZEN permanece como autoridad semántica de las decisiones ya aprobadas. El companion gate:

1. lee el Architecture exacto y verifica su SHA FROZEN;
2. extrae únicamente ADRs ya presentes, sin reinterpretarlos;
3. proyecta paths y contenido standalone determinísticamente;
4. crea un plan multiarchivo inmutable sin writes de project source;
5. liga un approval Owner al plan, hashes y exact path allowlist;
6. aplica todos los ADRs de forma atómica/all-or-nothing;
7. emite receipt runtime con plan/approval/execution/provenance;
8. bloquea Security y etapas posteriores mientras el gate no esté PASS.

# Alternativas consideradas

## Mantener ADRs solo embebidos

Rechazada porque contradice el contrato aprobado de `13-C-02`, que exige materialización bajo `docs/02_architecture/adrs/`.

## Volver a abrir Architecture y regenerar el DRAFT

Rechazada. Architecture ya fue revisada, aprobada, aplicada y congelada correctamente. Reabrirla aumentaría superficie de regresión y podría reinterpretar decisiones ya autorizadas.

## Escribir ADRs mediante operador Windows

Rechazada. Convertiría al operador en autor del proyecto, violando `operator_project_writes=0` y el journey UI-first.

# Consecuencias

- Se añade un companion state runtime separado del lifecycle principal de Architecture.
- El approval de Architecture conserva autoridad sobre la decisión semántica; el approval companion autoriza únicamente su materialización standalone.
- Un source exacto sin receipt/estado approval-bound no se acepta como PASS solo por igualdad de contenido.
- Security no puede comenzar hasta que el bundle ADR esté materializado de forma gobernada.
- El corrective no requiere LLM, Agent, red ni API externa.
- La implementación queda preparada para reanudación idempotente desde el estado sobreviviente actual: Architecture FROZEN + ADR directory vacío.

# Riesgos

- Riesgo de drift entre Architecture y ADR standalone: mitigado con Architecture SHA y proyección determinística.
- Riesgo de apply parcial: mitigado con preparación previa, replace atómico por archivo y compensating rollback del allowlist completo.
- Riesgo de inferir approval por presencia física: mitigado exigiendo estado/receipt approval-bound además de postimage parity.
- Riesgo UX de duplicar decisiones: el companion materializa decisiones existentes; no abre un segundo Decision Inbox.

# PASS / BLOCK

PASS si Architecture FROZEN produce un plan ADR sin source writes, approval exacto, apply atómico, cuatro ADRs esperados con hashes exactos, receipt runtime válido y Security queda habilitada solo después del companion gate.

BLOCK ante drift de Architecture, target ADR desconocido, path fuera del root gobernado, falta de approval exacto, apply parcial, postimage mismatch o ausencia de receipt confiable.

# Comandos de verificación

```text
PYTHONPATH=src pytest -q tests/test_devpl_gsdlc_13_c_02_adr_companion.py
PYTHONPATH=src pytest -q tests/test_devpl_gsdlc_13_c_02_technical_design_bridge.py
python -m devpilot_core schema validate --schema-id SensitiveActionCatalog --instance .devpilot/approval/sensitive_action_catalog.json --json
npm --prefix ui/web run build
```

No se autoriza Full Regression para este corrective intermedio.
