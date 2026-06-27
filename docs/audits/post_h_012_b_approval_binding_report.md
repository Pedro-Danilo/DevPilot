---
doc_id: "POST-H-012-B-APPROVAL-BINDING-REPORT"
title: "POST-H-012-B — Approval binding fuerte"
status: "approved"
owner: "Ordóñez"
updated: "2026-06-27"
source_of_truth: "docs/backlogs/POST-H-012_approval_rbac_hardening.md"
---

# POST-H-012-B — Approval binding fuerte

## Propósito

Implementar una primera versión industrial-local del binding fuerte de approvals para impedir reutilización indebida de aprobaciones humanas. El objetivo es que un `approval_id` solo pueda autorizar el actor, rol, herramienta, acción, sujeto, comando y tool call para los cuales fue emitido.

## Artefactos implementados

```text
src/devpilot_core/approval/binding.py
tests/test_approval_binding.py
```

## Controles implementados

```text
- `ApprovalBindingRequest` como contrato de verificación exacta.
- `StrongApprovalBindingValidator` como validador determinístico local.
- `compute_subject_hash()` para binding opcional por hash de sujeto.
- Bloqueo de approval expirado.
- Bloqueo de approval revocado.
- Bloqueo de actor spoofing.
- Bloqueo de tool/action/subject mismatch.
- Bloqueo de subject_hash mismatch.
- Bloqueo de command_id/tool_call_id faltante o distinto cuando el catálogo lo exige.
- Bloqueo de scopes genéricos o wildcard para acciones sensibles.
- Integración inicial con `ApprovalPolicyChecker` para acciones presentes en `SensitiveActionCatalog`.
```

## Criterios PASS

```text
PASS si un approval solo sirve para su scope exacto.
PASS si approval expirado bloquea.
PASS si approval revocado bloquea.
PASS si subject mismatch bloquea.
PASS si tool_call_id mismatch bloquea cuando el catálogo lo requiere.
PASS si un approval genérico no puede autorizar una acción sensible.
```

## Criterios BLOCK

```text
BLOCK si actor spoofing pasa.
BLOCK si approval expirado o revocado autoriza.
BLOCK si approval sin command_id/tool_call_id autoriza una acción crítica que los requiere.
BLOCK si un approval global o wildcard puede autorizar patch/refactor/release/remote/plugin/connector.
```

## Seguridad

La implementación es local-first, determinística y de solo validación. No ejecuta herramientas, no modifica archivos de usuario, no llama red, no usa APIs externas, no habilita remote execution, no habilita connector write y no habilita plugin execution.

## Límites

POST-H-012-B es `implemented-initial`. La matriz de exposición RBAC queda para POST-H-012-C; el enforcement homogéneo de PolicyEngine queda para POST-H-012-D; el subgate integral approval-rbac-hardening queda para POST-H-012-E.
