---
doc_id: "DEVPL-GSDLC-06-E-EVIDENCE-ERRATUM"
title: "DEVPL-GSDLC-06-E — Evidence erratum for RBAC browser case"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-08-29"
approval: "approved_by_owner"
---

# DEVPL-GSDLC-06-E — Erratum de evidencia browser RBAC

## 1. Objeto

Registrar sin reescritura el defecto de fidelidad de `05-rbac-negative.png` detectado después del sellado de la evidencia Windows de GSDLC-06-E.

## 2. Evidencia sellada preservada

- caso: `05-rbac-negative`;
- screenshot: `05-rbac-negative.png`;
- SHA-256 inspeccionado: `0d55d878e30d48c7e4ea9c0a658608d5a8a6a63ce95144e00582fbfcec661da4`;
- observación histórica declarada: bloqueo `403/RBAC`;
- contenido visual real: `API local down o inaccesible`.

La captura original queda preservada como evidencia histórica defectuosa. No se reemplaza, no se reetiqueta y no se usa como prueba del claim RBAC.

## 3. Clasificación

`S2-EVIDENCE-06E-001 / evidence-fidelity`. No se clasifica como bypass de RBAC. El defecto está en la evidencia visual, no en el enforcement.

## 4. Resolución mínima autorizada

La resolución **no requiere repetir navegador** porque el activation rebind no modifica runtime UI, RBAC ni Provider Settings. La prueba funcional se apoya en contratos determinísticos ya versionados:

- `tests/test_devpl_gsdlc_06_c_external_provider_enablement.py::test_disable_and_revoke_are_owner_only_audited_kill_switches` — demuestra que un `developer` no puede ejecutar los kill-switches owner-only;
- `tests/test_devpl_gsdlc_06_e_provider_settings.py::test_controlled_evaluation_application_boundary_requires_authorized_human_role` — demuestra enforcement RBAC en el boundary de evaluación de Model Gateway.

El activation rebind debe ejecutar esos tests de forma focal y conservar su log. No se crea identidad runtime, no se inicia API/UI y no se genera una nueva captura para corregir retrospectivamente el browser run histórico.

## 5. PASS/BLOCK

**PASS:** captura original preservada + erratum versionado + ambos contratos focales PASS + `S0=0/S1=0`.  
**BLOCK:** editar la evidencia original, seguir describiéndola como `403/RBAC`, o encontrar un fallo real en cualquiera de los contratos RBAC focales.
