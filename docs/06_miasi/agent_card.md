---
title: "Agent Card — DevPilot Local"
doc_id: "DEVPL-MIASI-AGENT"
status: "reviewed"
version: "0.6.0"
owner: "Ordóñez"
standard: "MIASI"
parent_standard: "MIPSoftware"
phase: "SPRINT-PRECODE-06"
updated: "2026-06-05"
approval: "ready_for_owner_approval"
source_baseline: "00_product approved + 01_requirements approved + 02_architecture approved + 03_security approved + 04_quality approved + 05_operations approved"
change_policy: "controlled_changes_allowed_until_precode_baseline"
---

# Agent Card — DevPilot Local

## 1. Propósito

Este documento formaliza los agentes previstos para **DevPilot Local / Agent-assisted SDLC personal** y activa MIASI para el proyecto. La plataforma no se limita a validadores documentales; su evolución comprometida incluye agentes especializados para asistir el ciclo de vida completo del software: planeación, documentación pre-code, requerimientos, arquitectura, seguridad, pruebas, análisis de repositorios, revisión de código, validación de patches, refactor seguro, release y operación.

La regla central es:

> Los agentes de DevPilot asisten, recomiendan, auditan y preparan acciones; los gates determinísticos, las políticas y la aprobación humana controlan la ejecución.

## 2. Alcance por etapa

| Etapa | Agentes permitidos | Nivel de autonomía máximo | Estado |
|---|---|---:|---|
| MVP | PreCodeDocumentationAgent, DocumentationAuditAgent | A2 — agente con herramientas en dry-run | Obligatorio |
| MVP+ | RequirementsAgent, ArchitectureAgent, SecurityAgent, TestPlannerAgent, RepoAnalysisAgent, CodeReviewAgent, PatchReviewAgent, SafeRefactorAgent | A4 — agente con aprobación humana | Planeado |
| Post-MVP | ReleaseAgent, OperationsAgent, DeploymentAssistantAgent, DocumentationAgent, CostOptimizationAgent, MultiAgentCoordinator | A5/A6 controlado | Futuro |
| Producción industrial | Agentes integrados a workflows con observabilidad, evaluación, policy-as-code, approvals y rollback | A6/A7 controlado | No en MVP |

## 3. Taxonomía de agentes

| Agente | Propósito | Entradas principales | Salidas | Herramientas | Riesgo | Fase |
|---|---|---|---|---|---:|---|
| PreCodeDocumentationAgent | Construir borradores de documentos MIPSoftware/MIASI desde una idea inicial. | idea, contexto, estándar, plantillas | propuesta Markdown, brechas, preguntas | read templates, generate draft, report | Medio | MVP |
| DocumentationAuditAgent | Auditar documentos pre-code contra MIPSoftware/MIASI. | docs, checklist, estándares | hallazgos, recomendaciones, PASS/FAIL | read docs, validate structure, report | Medio | MVP |
| RequirementsAgent | Transformar visión en requerimientos verificables. | product docs, stakeholders, MVP scope | RF/RNF, historias, criterios | read docs, generate requirements, traceability | Medio | MVP+ |
| ArchitectureAgent | Proponer arquitectura, C4 y ADRs. | requerimientos, restricciones, riesgos | arquitectura, ADRs, riesgos | read docs, C4 draft, ADR draft | Medio/Alto | MVP+ |
| SecurityAgent | Revisar amenazas, privacidad, secretos, políticas y controles. | arquitectura, tools, agentes, datos | threat findings, policies, gates | scan docs, secret check, policy validate | Alto | MVP+ |
| TestPlannerAgent | Generar estrategia de pruebas y quality gates. | requisitos, aceptación, arquitectura | test plan, eval plan, traceability | read docs, generate tests | Medio | MVP+ |
| RepoAnalysisAgent | Analizar repos reales sin modificar archivos. | repo path, git status, config | inventario, riesgos, estructura | git status, read tree, repo scan | Medio | MVP+ |
| CodeReviewAgent | Revisar código y proponer ajustes sin aplicar cambios. | diff, archivos, reglas | review report, risks, suggestions | read files, diff parse, static checks | Alto | MVP+ |
| PatchReviewAgent | Validar patches antes de aplicarlos. | patch, target repo, policy | verdict, riesgos, rollback notes | patch parse, dry-run apply, tests plan | Alto | MVP+ |
| SafeRefactorAgent | Proponer refactor seguro, reversible y testeable. | code, tests, goals | plan de refactor, patch candidate | code read, tests, patch draft | Alto | MVP+ |
| ReleaseAgent | Asistir release notes, gates, rollback y despliegue. | version, tests, changelog | release checklist, rollback plan | git tags, reports | Alto | Post-MVP |
| OperationsAgent | Asistir operación, incidentes, runbooks y postmortems. | logs, events, incidents | diagnóstico, runbook update | logs read, incident report | Alto | Post-MVP |

## 4. Contrato mínimo de agente

Todo agente debe declarar:

| Campo | Obligatorio | Descripción |
|---|---:|---|
| `agent_id` | Sí | Identificador estable. |
| `name` | Sí | Nombre funcional. |
| `purpose` | Sí | Propósito único y verificable. |
| `scope` | Sí | Qué puede hacer. |
| `out_of_scope` | Sí | Qué no puede hacer. |
| `autonomy_level` | Sí | A0–A7 según MIASI. |
| `allowed_tools` | Sí | Herramientas permitidas por policy. |
| `forbidden_tools` | Sí | Herramientas prohibidas. |
| `input_contract` | Sí | Entradas esperadas. |
| `output_contract` | Sí | Salidas esperadas. |
| `memory_policy` | Sí | Qué puede recordar o persistir. |
| `rag_policy` | Sí | Fuentes permitidas, citas y grounding. |
| `cost_policy` | Sí | Presupuesto y límites si usa APIs. |
| `security_policy` | Sí | Restricciones de secretos, rutas y acciones. |
| `approval_policy` | Sí | Acciones que requieren aprobación humana. |
| `eval_policy` | Sí | Evaluaciones mínimas antes de uso. |
| `observability_policy` | Sí | Eventos y trazas requeridas. |

## 5. Niveles de autonomía permitidos

| Nivel | Uso en DevPilot | Requiere aprobación humana |
|---|---|---:|
| A0 — asistente pasivo | Resumen o explicación sin herramientas. | No |
| A1 — recomendador | Sugiere estructura, riesgos o mejoras. | No |
| A2 — tool calling dry-run | Ejecuta herramientas de lectura/validación sin cambios. | Depende del tool |
| A3 — ejecutor controlado | Genera artefactos nuevos en zona segura. | Sí para escritura |
| A4 — ejecución con aprobación humana | Propone y espera confirmación. | Sí |
| A5 — operacional local-first | Opera flujos locales con policy gates. | Sí para acciones críticas |
| A6 — producción controlada | Acciones sobre sistemas reales. | Sí y con auditoría |
| A7 — industrial | Multiagente con gobernanza completa. | Sí, con gestión formal |

## 6. Relación con MIPSoftware

| Dominio MIPSoftware | Agentes relacionados |
|---|---|
| Producto y negocio | PreCodeDocumentationAgent, DocumentationAuditAgent |
| Requerimientos | RequirementsAgent |
| Arquitectura | ArchitectureAgent |
| Seguridad | SecurityAgent |
| Calidad | TestPlannerAgent |
| Operación | OperationsAgent |
| CI/CD y release | ReleaseAgent |
| MIASI | Todos los agentes |

## 7. Criterios PASS

Un agente queda aprobado para implementación si:

- tiene contrato completo;
- está vinculado a una fase del SDLC;
- tiene herramientas permitidas y prohibidas;
- opera en dry-run por defecto;
- tiene evaluación mínima;
- emite trazas;
- respeta CostGuard y SecretGuard;
- no puede ejecutar acciones destructivas sin aprobación;
- tiene fallback ante error;
- tiene pruebas herméticas.

## 8. Criterios BLOCK

Bloquear implementación o uso del agente si:

- no tiene Agent Card;
- no tiene Tool Card asociada;
- no tiene policy;
- puede escribir/borrar/sobrescribir sin aprobación;
- puede exponer secretos;
- puede usar API externa sin CostGuard;
- no genera trazas;
- no tiene evaluación mínima;
- no separa propuesta de ejecución.
