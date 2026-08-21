---
doc_id: "ADR-GSDLC-005"
title: "Runtime draft store and optimistic concurrency for governed artifact authoring"
status: "accepted/pending-windows-proof"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-08-20"
approval: "architecture_accepted_for_gsdlc_04_b"
---

# ADR-GSDLC-005 — Runtime draft store and optimistic concurrency

## Contexto

GSDLC-04-B necesita autosave y recuperación tras restart sin convertir un borrador en source aprobado. El predecessor UOC-004 conservaba propuestas en `sessionStorage`, adecuado para planning local pero insuficiente como historial gobernado y no autorizado como autoridad server-side.

## Decisión

1. Persistir drafts MANUAL en runtime bajo `outputs/drafts/gsdlc_04_b`, separados del workspace source.
2. Mantener revisiones inmutables hash-linked de forma lógica y bounded a 50 revisiones por documento.
3. Exigir `source_preimage_sha256` y `expected_revision_sha256` server-side para evitar lost updates.
4. Derivar actor/rol/session del principal autenticado; ignorar cualquier actor aportado por UI.
5. Reutilizar UOC-004/UOC-005 para plan/apply al source; no crear un segundo motor de escritura.
6. Mantener `sessionStorage` solo como UX/compatibilidad no autoritativa donde la superficie histórica YAML aún la usa.

## Alternativas descartadas

- Guardar draft directamente en el archivo aprobado: viola lifecycle y hace autosave equivalente a source mutation.
- Un archivo `.draft` junto al documento: multiplica artefactos arbitrarios dentro del workspace y dificulta higiene Git/fixtures.
- SQLite `devpilot.db`: mezcla estado de authoring con store runtime histórico y eleva el riesgo de copiar DBs efímeras a fixtures.
- Browser storage como autoridad: viola la invariante GSDLC-03 de sesión/RBAC/approval server-side y no sobrevive de forma reproducible a reinicios/sesiones.

## Consecuencias

Positivas: restart recovery, historial local verificable, aislamiento del source, fácil exclusión de packages, optimistic concurrency determinística y reuse del writer gobernado existente.

Costos: el runtime store debe validarse, limpiarse/retenerse de forma explícita en evolución futura y no puede ser usado como evidence autoritativa.

## Seguridad

No network, no external API, no free-form shell, no source writes durante draft persistence, SecretGuard, JSON Schema fail-closed y human session obligatoria.

## PASS/BLOCK

PASS si los tests de autosave/restart/conflict/recovery y browser smoke Windows demuestran el contrato. BLOCK ante source overwrite, stale update aceptado, runtime store corrupto aceptado o autoridad derivada del cliente.

## Verificación

Usar únicamente la guía Windows del micro-sprint. Full regression permanece reservada a GSDLC-04-E.
