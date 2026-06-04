---
title: "Política de waiver y excepciones MIASI"
version: "1.0.0"
status: "approved"
owner: "AI_agents"
scope: "engineering-model/checklists"
updated: "2026-05-31"
doc_type: "checklist"
---
# Política de waiver y excepciones MIASI

## 1. Propósito

Definir cómo registrar excepciones temporales cuando un control o checklist no puede cumplirse inmediatamente.

## 2. Regla central

Un waiver no elimina el riesgo. Solo permite avanzar temporalmente con justificación, responsable, mitigación y fecha de expiración.

## 3. Campos obligatorios

| Campo | Obligatorio | Descripción |
|---|---:|---|
| `waiver_id` | Sí | ID único. |
| `control_id` | Sí | Control MIASI afectado. |
| `reason` | Sí | Motivo de excepción. |
| `risk` | Sí | Riesgo aceptado. |
| `mitigation` | Sí | Mitigación temporal. |
| `owner` | Sí | Responsable. |
| `approved_by` | Sí | Aprobador. |
| `expires_at` | Sí | Fecha de expiración. |
| `review_date` | Sí | Fecha de revisión. |

## 4. Ejemplo

```yaml
waiver_id: "WAIVER-2026-001"
control_id: "MIASI-CICD-002"
reason: "Firma de artefactos no disponible en MVP local."
risk: "Artefactos sin firma criptográfica."
mitigation: "Usar hashes SHA256 y CI local reproducible."
owner: "AI_agents"
approved_by: "project_owner"
expires_at: "2026-07-30"
review_date: "2026-06-30"
```

## 5. Criterios PASS/FAIL

| Ítem | Obligatorio | Evidencia requerida | Responsable | PASS | FAIL |
|---|---:|---|---|---|---|
| Waiver tiene responsable | Sí | `owner` | Project Owner | Responsable definido | Responsable ausente |
| Waiver tiene expiración | Sí | `expires_at` | Project Owner | Fecha válida | Sin expiración |
| Riesgo documentado | Sí | `risk` | Security Reviewer | Riesgo claro | Riesgo omitido |
| Mitigación definida | Sí | `mitigation` | Tech Lead | Mitigación viable | Sin mitigación |

## 6. Criterios de bloqueo

- Waiver sin expiración se considera `FAIL`.
- Waiver de secreto expuesto no permite release.
- Waiver de acción destructiva sin human approval no permite operación.
