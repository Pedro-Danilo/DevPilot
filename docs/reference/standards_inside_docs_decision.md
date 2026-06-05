---
title: "Decisión — Incluir MIPSoftware y MIASI dentro de docs/"
doc_id: "DEVPL-REF-002"
status: "reviewed"
version: "0.2.0"
owner: "Ordóñez"
standard: "MIPSoftware"
extension: "MIASI"
phase: "PRECODE"
updated: "2026-06-04"
approval: "ready_for_owner_approval"
decision_type: "documentation-architecture"
---
# Decisión — Incluir MIPSoftware y MIASI dentro de `docs/`

## 1. Contexto

DevPilot Local se está construyendo bajo un enfoque **docs-as-code**. El proyecto usa MIPSoftware como estándar general de ingeniería profesional de software y MIASI como extensión especializada para sistemas con IA y agentes.

Durante la fase pre-code se decidió incorporar copias versionadas de ambos estándares dentro de:

```text
docs/standars/
  mipsoftware/
  miasi/
```

## 2. Decisión

Se acepta incluir MIPSoftware y MIASI dentro de `docs/` como **referencia normativa local versionada del proyecto**.

Esta decisión no convierte a DevPilot Local en propietario único de los estándares. Los estándares siguen siendo activos transversales del emprendimiento. La copia dentro del proyecto funciona como baseline aplicable, auditable y consumible por los validadores y agentes de DevPilot.

## 3. Justificación

La decisión es pertinente porque:

1. **Docs-as-code real**: los estándares quedan versionados junto con los artefactos que deben cumplirlos.
2. **Local-first**: DevPilot puede validar sin red ni servicios externos.
3. **Trazabilidad**: cada requisito, ADR, checklist o gate puede referenciar el estándar local.
4. **Automatización futura**: los validadores y agentes pueden consultar reglas, plantillas y checklists del estándar.
5. **Reproducibilidad**: una revisión futura puede reconstruir qué versión del estándar aplicaba a cada decisión.

## 4. Riesgos

| Riesgo | Impacto | Mitigación |
|---|---|---|
| Duplicación de estándares entre proyectos | Divergencia documental | Mantener manifiesto de versión y política de sincronización. |
| Edición accidental de estándares locales | Pérdida de coherencia | Cambios al estándar requieren tarea/ADR explícito. |
| Ruta `estándares/` con caracteres no ASCII | Posibles problemas de tooling | Validar UTF-8 y evaluar alias `standards/` si aparece fricción. |
| Confusión entre docs del proyecto y docs normativos | Lectura incorrecta | Mantener `docs/README.md` y este documento de decisión. |

## 5. Política

- Los documentos en `00_product`, `01_requirements`, `02_architecture`, etc. son artefactos del proyecto.
- Los documentos en `docs/estándares/` son referencia normativa.
- Los documentos en `docs/06_miasi/` son aplicación de MIASI al proyecto, no el estándar MIASI completo.
- Si MIPSoftware o MIASI cambian, debe registrarse una sincronización explícita.

## 6. Estado

```yaml
decision: accepted_for_project_baseline
status: reviewed
pending: owner approval
```



## 8. Nota de ruta heredada

En el ZIP fuente vigente la carpeta aparece como:

```text
docs/standars/
```

Se identifica como una ruta heredada con grafía no ideal. No se renombra en este sprint para evitar duplicidad de carpetas o pérdida de trazabilidad al aplicar patches por `Expand-Archive`. La política adoptada es:

1. Tratar `docs/standars/` como ruta canónica temporal.
2. No crear una segunda carpeta `docs/standards/` sin migración controlada.
3. Programar una tarea técnica futura para migrar la ruta si el tooling lo exige.
4. Mientras tanto, todo documento nuevo debe referenciar la ruta física real.
