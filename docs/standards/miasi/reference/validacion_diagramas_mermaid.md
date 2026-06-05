---
title: "Política de validación de diagramas Mermaid MIASI"
version: "1.0.0"
status: "approved"
owner: "AI_agents"
scope: "engineering-model/reference"
updated: "2026-05-31"
doc_type: "reference"
---
# Política de validación de diagramas Mermaid MIASI

## 1. Propósito

Definir cómo validar diagramas Mermaid para reducir riesgo de documentación rota al publicar en HTML/PDF.

## 2. Reglas

- Todo diagrama crítico debe estar en bloque `mermaid`.
- Todo diagrama C4/Mermaid debe tener título o contexto cercano.
- Los diagramas no deben mezclar niveles C4.
- Los diagramas críticos deben tener alternativa textual.

## 3. Validación futura

Comando objetivo:

```bash
devpilot docs lint-diagrams --path docs/engineering_model
```

| Validación | Bloquea |
|---|---:|
| Bloque Mermaid mal cerrado | Sí |
| Sintaxis no renderizable | Sí |
| Diagrama sin contexto | No, warning |
| Mezcla de niveles C4 | No, warning |
| Diagrama crítico sin descripción textual | Sí para approved |

## 4. Criterios de bloqueo

- Documento `approved` no debe contener diagramas críticos sin validar.
- Publicación PDF/HTML debe bloquearse si hay Mermaid roto.
