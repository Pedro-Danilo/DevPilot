---
doc_id: "POST-H-022-A-GENERAL-PYTEST-REGRESSION-FIX-REPORT"
status: "approved"
created_by: "POST-H-022-A-FIX-01"
scope: "general-pytest-regression-fix"
---

# POST-H-022-A General Pytest Regression Fix Report

## Diagnostico

La ejecucion general posterior a POST-H-022-A reporto 1445 pruebas en PASS y 12 fallos. Los fallos no corresponden a una regresion de runtime del threat model enterprise; corresponden a tres desincronizaciones de contratos historicos y registros:

- `DocumentationSourceRegistry` contenia clasificaciones nuevas fuera del enum permitido.
- El test de CLI registry no habia incorporado el grupo declarativo `enterprise` ni el comando `enterprise.report`.
- Tests historicos de POST-H-017, POST-H-018 y POST-H-019 seguian comparando `project_state` contra valores exactos de sprints ya cerrados, aunque el repositorio habia avanzado a POST-H-022-A.
- `test_schema_registry.py` no habia incorporado `SCHEMA-DEVPL-ENTERPRISE-THREAT-MODEL-V1`.

## Correccion

El fix actualiza las pruebas para validar invariantes estables:

- Los backlogs historicos deben seguir cerrados con su micro-sprint final documentado.
- El `project_state` acumulativo debe haber avanzado al menos hasta el hito historico correspondiente.
- El registry de schemas debe incluir el schema enterprise agregado por POST-H-022-A.
- El CLI registry debe reconocer el grupo `enterprise`.

Tambien se entrega `scripts/post_h_022_a_fix_source_registry.py`, idempotente, para corregir las clasificaciones de los documentos POST-H-022-A en `.devpilot/docs_governance/source_registry.json`.

## Riesgo

El cambio no modifica codigo productivo. Solo corrige pruebas de regresion y un artefacto de gobernanza documental. No habilita red, APIs externas, ejecucion remota ni acciones destructivas.
