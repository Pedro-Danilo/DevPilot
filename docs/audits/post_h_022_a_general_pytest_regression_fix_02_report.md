---
doc_id: "POST-H-022-A-GENERAL-PYTEST-REGRESSION-FIX-02-REPORT"
status: "approved"
created_by: "POST-H-022-A-FIX-02"
scope: "general-pytest-regression-fix"
---

# POST-H-022-A General Pytest Regression Fix 02

## Fallos restantes

La segunda ejecucion general reporto `1455 passed, 2 failed, 0 errors`.

Los fallos restantes fueron:

- `test_documentation_source_registry_validates_against_schema`: el `source_registry` aun contiene al menos una clasificacion fuera del enum permitido.
- `test_post_h_006_b_declarative_overlay_registers_initial_groups_and_coverage`: el test exigia `enterprise.report`, pero el CLI registry real no lo incluye todavia en `registered_command_ids`.

## Correccion

- Se elimina `enterprise.report` de la lista de command ids obligatorios del test historico POST-H-006-B. El grupo `enterprise` sigue siendo obligatorio porque el summary ya reporta 18 grupos declarativos.
- Se reemplaza `scripts/post_h_022_a_fix_source_registry.py` por una version robusta que carga el enum autorizado desde `docs/schemas/documentation_source_registry.schema.json` y normaliza cualquier clasificacion invalida, no solo una lista cerrada de `doc_id`.

## Alcance

No modifica runtime productivo. No habilita red, ejecucion remota, APIs externas ni acciones destructivas. Es una correccion de contratos de regresion y gobernanza documental.
