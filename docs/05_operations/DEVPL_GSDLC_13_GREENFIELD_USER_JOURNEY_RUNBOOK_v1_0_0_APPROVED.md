---
doc_id: "DEVPL-GSDLC-13-GREENFIELD-USER-JOURNEY-RUNBOOK"
title: "DEVPL-GSDLC-13 — Greenfield user journey runbook"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-09-21"
source_user_journey: "Cómo se desarrollaría una app con DevPilot.docx"
project_workspace: 'D:\Projects\DevPilot_Workspaces\inventory-sales-local-greenfield'
---

# Greenfield user journey runbook

Este documento convierte la explicación del Owner en una secuencia de acceptance. Los ejemplos funcionales son **ilustrativos**, no oracle design. DevPilot debe derivar el detalle dentro del Guided SDLC.

## Mapa maestro

| Pasos | Sprint | Propósito |
|---|---|---|
| 1–8 | 13-B | instalar/arrancar, login, crear proyecto, idea/constraints, plan/approval, bootstrap, Project Status |
| 9–17 | 13-C | Vision, Scope, Requirements, Architecture/Security/Tests/ADRs, readiness, Roadmap/Backlog/Sprint/Stories |
| 18–32 | 13-D | Story/Coding cycle, tests, quality, Git, repetición hasta MVP, recovery scenarios |
| 33 | UX-P1 transversal | observar/medir/clasificar/corrective bounded/resume |
| 34–38 | 13-D | Release Readiness, package/checksum/SBOM, clean install, rollback, local release |
| 39 | 13-E | adjudicación independiente |

## 13-B — Bootstrap (pasos 1–8)

1. **Instalar y arrancar DevPilot.** Terminal solo para operar DevPilot; todavía no existe la app greenfield.
2. **Ingresar y autenticarse.** Login local → Home; debe ser comprensible si existe proyecto activo y cuál es la acción principal.
3. **Elegir Crear proyecto.** Workspace nuevo `inventory-sales-local-greenfield`; no copiar artifacts, DB, código, Git history, configuración ni evidencia del piloto histórico.
4. **Expresar la idea, no la solución.** El Owner describe una app local de inventario/ventas; no entrega tablas/endpoints/arquitectura preconstruidos.
5. **Definir ubicación y restricciones.** Nombre/workspace, restricciones, tipo de aplicación, ejecución y model policy; local-first, mock/no-API baseline.
6. **Revisar antes de ejecutar.** Propuesta → plan → dry-run → efectos → approval; ninguna mutación relevante debe materializarse antes.
7. **Bootstrap gobernado.** DevPilot crea carpeta, estructura inicial, Git, entorno/configuración y Project Context. `git init` manual o project writes externos = BLOCK.
8. **Project Status como centro operacional.** Debe mostrar proyecto, etapa, completado/pendiente, blocker/causa y next valid action.

## 13-C — Engineering + planning (pasos 9–17)

9. **Product Vision.** DevPilot ayuda a formalizar qué problema se resuelve.
10. **Scope.** Delimitar qué entra y qué queda fuera del MVP.
11. **Requirements.** Convertir necesidades en requisitos verificables.
12. **Diseño técnico.** Architecture, Security, Test Strategy, ADRs y traceability; decisiones justificadas, no impuestas por oracle externo.
13. **Pre-code readiness.** MIASI/MIPSoftware y readiness deben revelar faltantes y next action.
14. **Roadmap.** Organizar capacidades/etapas sin bajar todavía a implementación por archivo.
15. **Backlog.** Convertir capacidades en trabajo priorizable y trazable.
16. **Sprint.** Seleccionar trabajo coherente para una iteración.
17. **Stories ejecutables.** Stories con acceptance criteria y readiness suficiente para pasar a implementación.

## 13-D — Story loop, quality, Git, recovery y release (pasos 18–38)

18. **Story/Coding Workbench.** DevPilot reúne requirement, objetivo, architecture, constraints, acceptance criteria, código y tests relacionados en context pack.
19. **Ruta de implementación.** Manual o agent-assisted dentro de DevPilot. Mock/no API es baseline; local/external model solo con policy/provenance.
20. **Change Plan.** Qué archivos cambiar/crear y qué tests ejecutar.
21. **Diff.** Revisar archivos, diferencias y posibles efectos.
22. **Dry-run.** Validar antes de materializar cuando corresponda.
23. **Approval.** Approve/Reject humano con autoridad real.
24. **Apply.** DevPilot ejecuta solo el plan autorizado y registra evidence.
25. **Pruebas pertinentes.** Test Impact → targeted tests → evaluación.
26. **Remediation loop.** fallo → entender → propuesta → review → approval → apply → retest.
27. **Quality Gate.** Evidencia de qué se hizo, qué tests pasaron y qué criteria se cumplen.
28. **Git review/stage.** Revisar qué entra en commit.
29. **Commit gobernado.** Unidad coherente ligada a story/evidence.
30. **Volver a Project Status.** Next Action conduce a la siguiente story/tarea.
31. **Repetir hasta MVP.** Story loop hasta obtener el flujo mínimo coherente de inventario/ventas.
32. **Recovery scenarios.** Probar controladamente restart, interrupted safe work, external edit, dirty worktree, branch/divergence/conflict y stale lock; recuperación no destructiva.
33. **UX-P1 transversal.** usar → detectar fricción → medir → clasificar → corrective bounded si aplica → selective retest → resume exact segment.
34. **Release Readiness.** Stories/quality/Git/blockers/version/evidence listos.
35. **Package.** Artefacto distribuible + checksum + SBOM cuando corresponda + version/release notes.
36. **Clean install.** Probar fuera del workspace de desarrollo.
37. **Rollback.** Demostrar release → install/upgrade → rollback seguro.
38. **Local release.** Aplicación identificable, probada y reproducible alcanzada mediante DevPilot.

## 13-E — Adjudicación (paso 39)

39. **Independent adjudication.** Verificar que el proyecto nació desde cero, `operator_project_writes=0`, mandatory terminal escapes=0, approvals/provenance/recovery/release son reproducibles, S0/S1=0 y la instalación limpia es real.

## Rutina diaria central

`Project Status → Next Action → Story/Task → Context → Plan → Diff → Dry-run → Approval → Apply → Tests → Quality → Git Review/Commit → Project Status`.

## Rutina macro

`IDEA → Create Project → Vision → Scope → Requirements → Architecture/Security/Tests/ADRs → Roadmap → Backlog → Sprint → Story → Context/Plan/Diff/Dry-run/Approval/Apply → Tests/Quality/Remediation → Git Commit → siguientes stories → Release Readiness → Package/Checksum/SBOM → Clean Install → Rollback → LOCAL RELEASE`.

## Regla de aceptación

No intervenir para hacer que DevPilot parezca funcionar. Si una etapa normal exige escribir manualmente archivos, inicializar Git por fuera, modificar código desde PowerShell o fabricar artefactos externos para desbloquear el journey, preservar el evento como evidencia y adjudicarlo; no ocultarlo.
