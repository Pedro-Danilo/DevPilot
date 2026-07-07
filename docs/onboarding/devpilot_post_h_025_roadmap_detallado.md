# DevPilot - Roadmap detallado posterior a POST-H-025

## 1. Verificacion de fuentes

Fuentes consultadas:

- `Log_consola_validacion_testeo_general_no-regresion_POST-H-025-E.txt`
- `repo_DevPilot_Local_262_POST_H_025_E.zip`
- `docs/onboarding/devpilot_onboarding_report_final_compilado.md`
- `docs/onboarding/devpilot_onboarding_report_compilation_manifest.json`

Resultado de verificacion:

- Testeo general reportado: `1536 passed, 0 failed, 0 errors, 0 skipped`.
- Repo 262 incorporado desde commit archivado `d020bb4`.
- Informe versionado en `docs/onboarding/devpilot_onboarding_report_final_compilado.md`.
- Cobertura del informe: preguntas `1-260`, `260` unicas, `0` faltantes, `0` duplicadas.
- Manifest de compilacion: `status=compiled`, `source_markdown_files_total=18`, `blocks=18`.

## 2. Diagnostico ejecutivo

DevPilot puede considerarse en una posicion industrialmente consistente para cerrar POST-H-025 como declaracion `production-ready-local`, siempre entendida como claim acotado:

- Local-first.
- Evidencia antes de claim.
- PASS/BLOCK deterministico.
- No remote execution.
- No connector write.
- No plugin execution.
- No SaaS-ready.
- No enterprise-ready.
- No compliance-certified.

El informe compilado es suficientemente detallado para derivar roadmap porque contiene:

- identidad y vision de producto;
- estado real frente a planeado;
- arquitectura real y objetivo;
- DDD y runtime execution;
- workspace/onboarding;
- capacidades funcionales;
- schemas, validators y evidence model;
- MIASI, policies, approvals y agentes;
- seguridad, no-go gates y threat model;
- testing, TCR y quality gates;
- observabilidad y operacion;
- release, reproducibilidad y distribucion;
- UI/API local;
- gap analysis;
- guia de operador y caso piloto;
- sintesis y recomendaciones finales.

La limitacion principal del informe no es falta de cobertura. La limitacion es que aun mezcla contenido de diagnostico, guia operativa y roadmap en un documento muy extenso. Para ejecucion industrial conviene derivar documentos posteriores mas compactos: backlogs ejecutables, decision records, matriz de riesgos viva y plan de release candidate.

## 3. Evaluacion de los seis ejes propuestos

Los seis puntos propuestos son adecuados como roadmap de alto nivel, pero requieren ajustes de orden y granularidad para convertirse en backlogs implementables.

### 3.1 Estabilizar release candidate local

Adecuado y debe ser el primer eje.

Justificacion:

- POST-H-025 declara `production-ready-local`, pero el siguiente nivel practico es demostrar instalacion, ejecucion y verificacion en condiciones de release candidate.
- Debe incluir freshness de evidencia, regeneracion de reportes y perfil de verificacion RC.

Ajuste recomendado:

- Formularlo como `POST-H-026 - Local release candidate stabilization and operator verification`.
- Incluir explicitamente evidencia fresh/stale/missing, install smoke, UI/API smoke, packaging limpio y reporte RC PASS/BLOCK.

### 3.2 Endurecer UI/API con pruebas visuales y auth local

Adecuado, pero debe separarse en dos lineas: hardening funcional/visual y hardening de seguridad local.

Justificacion:

- La UI/API existe como `implemented-initial`.
- El riesgo no es solo visual; tambien hay riesgo de contrato, errores de estados, CORS, token local, exposicion de localhost y divergencia entre API/UI/ApplicationService.

Ajuste recomendado:

- Incluir Playwright o smoke visual equivalente.
- Verificar estados `loading`, `empty`, `error`, `BLOCK`, `401`, `403`.
- Mantener auth local como proteccion de localhost, no como IAM enterprise.

### 3.3 Reducir deuda de `cli.py` y modulos de alta concentracion

Adecuado, pero no debe ejecutarse como refactor masivo.

Justificacion:

- `cli.py` es un hotspot transversal.
- Refactorizarlo de una vez puede introducir regresion amplia.

Ajuste recomendado:

- Extraer por dominios y comandos, con compatibility tests.
- Congelar crecimiento directo en `cli.py`.
- Priorizar comandos con mayor cambio futuro: industrial-readiness, quality-gate, release, workspace, API/UI, testing.

### 3.4 Mejorar tiers de testing e impacto

Adecuado y debe correr en paralelo con estabilizacion RC.

Justificacion:

- La suite general ya pasa, pero es costosa.
- El proyecto necesita perfiles `always`, `impact`, `release-candidate`, `full`, `security`, `ui-api`, `docs-contracts`.

Ajuste recomendado:

- Reforzar TCR v2 como fuente machine-readable para seleccionar pruebas.
- Reducir dependencia de `pytest -q` completo para cada micro-sprint.
- Mantener full suite para cierres mayores, RC y regresion acumulativa.

### 3.5 Formalizar ADRs antes de remote/connectors/plugins

Adecuado y obligatorio.

Justificacion:

- Remote execution, connector write y plugin execution son capacidades sensibles.
- El repo tiene design-only y no-go gates; habilitar ejecucion sin ADR romperia el modelo de seguridad.

Ajuste recomendado:

- Tratarlo como carril de arquitectura y seguridad, no como feature inmediata.
- Cada capacidad sensible requiere ADR, threat model, policy, approvals, sandbox, observability, tests adversariales y rollback.

### 3.6 Preparar packaging reproducible para instalacion local

Adecuado, pero debe adelantarse: no debe quedar despues de todo lo demas.

Justificacion:

- Sin instalacion reproducible, `production-ready-local` queda mas cerca de "repo verificable" que de "producto local instalable".

Ajuste recomendado:

- Integrarlo en POST-H-026 como release candidate local.
- Luego expandirlo en backlog propio para packaging, wheel/sdist, source ZIP, checksums, install smoke, rollback y matriz OS.

## 4. Ajustes propuestos al roadmap de alto nivel

Roadmap ajustado:

1. Estabilizar release candidate local con evidencia fresca, install smoke y RC PASS/BLOCK.
2. Preparar packaging reproducible para instalacion local y validacion post-install.
3. Endurecer UI/API local con pruebas visuales, contratos, auth local, CORS y estados de error.
4. Mejorar tiers de testing, TCR v2 e impacto para reducir costo de regresion.
5. Reducir deuda de `cli.py` y hotspots mediante extraccion incremental con contratos de compatibilidad.
6. Consolidar observabilidad/evidence graph/operator console para que el operador entienda salud, gaps, claims y riesgos.
7. Formalizar ADRs antes de remote, connector write, plugin execution, multiusuario, enterprise o SaaS.

La diferencia principal frente a la lista original es que packaging y evidencia fresca deben entrar antes, porque son precondiciones de release candidate. La formalizacion ADR debe existir como carril paralelo, pero sin habilitar ejecucion sensible hasta cerrar estabilizacion local.

## 5. Roadmap detallado por olas

### Ola 1 - POST-H-026: Release candidate local y verificacion de operador

Objetivo:

Convertir la declaracion `production-ready-local` en un release candidate local verificable por un operador, con evidencia fresca, instalacion reproducible, pruebas focales y reporte RC PASS/BLOCK.

Backlogs/micro-sprints sugeridos:

- `POST-H-026-A - Evidence freshness model`
- `POST-H-026-B - Release candidate verification profile`
- `POST-H-026-C - Install smoke local`
- `POST-H-026-D - UI/API local smoke under RC`
- `POST-H-026-E - RC PASS/BLOCK report`

Criterios de cierre:

- Evidencia clasificada como `fresh`, `stale`, `missing` o `not_applicable`.
- RC profile ejecuta validaciones focales deterministicas.
- Install smoke pasa en entorno limpio.
- UI/API local levanta bajo localhost y pasa smoke basico.
- No-go gates permanecen cerrados.
- Reporte `release_candidate_local_report.json/.md` emitido y validado por schema.

### Ola 2 - POST-H-027: Packaging reproducible e instalacion local

Objetivo:

Convertir el repo verificable en artefactos locales distribuibles y auditables.

Backlogs/micro-sprints sugeridos:

- `POST-H-027-A - Source ZIP release policy hardening`
- `POST-H-027-B - Wheel/sdist install verification`
- `POST-H-027-C - Artifact manifest and checksums`
- `POST-H-027-D - Windows install guide and smoke`
- `POST-H-027-E - Upgrade/rollback dry-run`

Criterios de cierre:

- Source ZIP limpio sin `outputs/`, `.git/`, `.venv/`, `node_modules/`, DB runtime ni caches.
- Wheel/sdist instalables en venv temporal.
- Checksums y manifest unificados.
- Comando post-install valida CLI, schemas, TCR, docs-governance y project-state.
- Rollback/backup documentado y probado en dry-run.

### Ola 3 - POST-H-028: UI/API local hardening

Objetivo:

Elevar la UI/API local desde shell inicial a consola operacional local robusta.

Backlogs/micro-sprints sugeridos:

- `POST-H-028-A - API contract drift guard`
- `POST-H-028-B - Local auth and CORS hardening`
- `POST-H-028-C - Visual smoke tests`
- `POST-H-028-D - Operator flows and error states`
- `POST-H-028-E - UI route registry enforcement`

Criterios de cierre:

- Playwright o equivalente cubre dashboard, reports, traces, approvals, settings y operator dashboard.
- Tests negativos cubren `401`, `403`, CORS no permitido y token faltante.
- UI muestra `PASS`, `BLOCK`, `WARN`, `ERROR` sin ocultar findings.
- API no expone operaciones write/remote/plugin.
- UI no lee filesystem directo; todo pasa por API/ApplicationService.

### Ola 4 - POST-H-029: Testing tiers, impacto y costo de regresion

Objetivo:

Hacer que el ecosistema de pruebas sea accionable para desarrollo continuo sin depender siempre de la suite completa.

Backlogs/micro-sprints sugeridos:

- `POST-H-029-A - Test profile taxonomy`
- `POST-H-029-B - TCR v2 impact rules`
- `POST-H-029-C - Test impact CLI recommendations`
- `POST-H-029-D - Release candidate test profile`
- `POST-H-029-E - Historical regression guard`

Criterios de cierre:

- Perfiles: `always`, `changed-domain`, `security`, `ui-api`, `docs-contracts`, `release-candidate`, `full`.
- TCR v2 mapea dominio, owner, criticidad, costo, triggers, outputs y riesgos.
- `test-impact analyze` recomienda comandos concretos.
- El perfil RC no sustituye full suite, pero cubre gates criticos.
- Documentacion indica cuando usar full suite.

### Ola 5 - POST-H-030: CLI hotspot reduction y boundaries de aplicacion

Objetivo:

Reducir riesgo de mantenibilidad en `cli.py` y consolidar fronteras CLI/API/UI/ApplicationService.

Backlogs/micro-sprints sugeridos:

- `POST-H-030-A - CLI command ownership matrix`
- `POST-H-030-B - Industrial readiness command extraction`
- `POST-H-030-C - Release command extraction`
- `POST-H-030-D - Workspace/onboarding command extraction`
- `POST-H-030-E - CLI compatibility contract tests`

Criterios de cierre:

- Nuevos comandos no se agregan directamente como bloques extensos en `cli.py`.
- Handlers por dominio con contratos de entrada/salida.
- Backward compatibility para comandos existentes.
- Tests por comando critico y golden outputs normalizados.
- Documentacion de CLI registry sincronizada.

### Ola 6 - POST-H-031: Observabilidad, evidence graph y operador

Objetivo:

Hacer que el operador pueda interpretar salud, evidencia, gaps, claims, riesgos y acciones recomendadas sin leer todo el repo.

Backlogs/micro-sprints sugeridos:

- `POST-H-031-A - Evidence graph model`
- `POST-H-031-B - Operator health summary`
- `POST-H-031-C - Gap-to-action mapping`
- `POST-H-031-D - Claims and no-go dashboard`
- `POST-H-031-E - Redacted evidence export UX`

Criterios de cierre:

- Vista consolidada de evidencias por dominio.
- Gaps conectados con acciones y comandos.
- Claims permitidos/prohibidos visibles.
- Export redacted de evidencia usable por auditor.
- Sin exponer prompts crudos, outputs crudos, secrets ni DB SQLite cruda.

### Ola 7 - POST-H-032: ADRs de capacidades sensibles

Objetivo:

Preparar decisiones tecnicas antes de ampliar superficie de riesgo.

Backlogs/micro-sprints sugeridos:

- `POST-H-032-A - Connector write ADR`
- `POST-H-032-B - Plugin execution ADR`
- `POST-H-032-C - Remote execution ADR-3`
- `POST-H-032-D - Multiuser/auth ADR`
- `POST-H-032-E - Enterprise/SaaS boundary ADR`

Criterios de cierre:

- Cada ADR incluye decision, alternativas, riesgos, no-go gates, tests, observability, approvals, rollback y criterio de no implementacion.
- Ninguna capacidad sensible queda habilitada por documentar ADR.
- Implementacion futura requiere backlog separado, threat model y quality gate propio.

### Ola 8 - POST-H-033+: Expansiones controladas

Objetivo:

Solo despues de RC local, packaging, UI/API hardening, tests e ADRs, abrir implementaciones sensibles si el owner decide ampliar alcance.

Lineas posibles:

- Connector write sandbox con conector fake y rollback.
- Plugin sandbox no ejecutor, luego ejecutor restringido si se aprueba.
- Remote runner experimental local-lab, nunca por defecto.
- Auth/RBAC local avanzado.
- Enterprise deployment design, no claim enterprise.
- Compliance evidence packs no certificantes.

Criterios de entrada:

- ADR aprobada.
- Threat model aprobado.
- Policy matrix actualizada.
- Approval/RBAC actualizado.
- Observability y audit trail definidos.
- Tests adversariales.
- No-go gates actualizados.
- Reporte PASS/BLOCK especifico.

## 6. Secuencia recomendada de ejecucion

Orden sugerido:

1. POST-H-026: RC local.
2. POST-H-027: Packaging/install.
3. POST-H-028: UI/API hardening.
4. POST-H-029: Testing tiers/impact.
5. POST-H-030: CLI hotspot reduction.
6. POST-H-031: Evidence graph/operator console.
7. POST-H-032: ADRs de capacidades sensibles.
8. POST-H-033+: Implementaciones sensibles solo si cumplen criterios de entrada.

Razon del orden:

- Primero se estabiliza lo ya declarado.
- Luego se hace instalable.
- Luego se mejora la experiencia visible.
- Luego se reduce costo de cambio.
- Luego se reduce deuda estructural.
- Luego se mejora operacion/auditoria.
- Solo despues se evalua ampliar alcance de riesgo.

## 7. Reglas para derivar backlogs

Cada backlog futuro debe incluir:

- objetivo operativo;
- alcance y no-alcance;
- claims permitidos/prohibidos;
- schemas nuevos o modificados;
- comandos CLI/API afectados;
- tests focales;
- TCR entries;
- docs sincronizados;
- quality gates;
- reportes generados;
- riesgos;
- criterios PASS/BLOCK;
- instrucciones Windows;
- ZIP limpio sin runtime artifacts.

Regla de control:

Ningun backlog debe cerrar solo por narrativa. Debe cerrar por evidencia ejecutable, contratos actualizados y verificacion reproducible.

## 8. Riesgos residuales principales

Riesgos que deben gobernar el roadmap:

- Evidencia stale usada para decisiones de release.
- UI/API interpretada como consola enterprise.
- `cli.py` creciendo como punto unico de acoplamiento.
- Suite completa costosa que inhibe validacion frecuente.
- Remote/write/plugin activados antes de ADR y threat model.
- Packaging sin install smoke real.
- Claims superiores usados en documentacion o comunicacion.
- Runtime artifacts incluidos en ZIPs limpios.
- Secrets o prompts crudos en evidencias.

## 9. Dictamen final

El roadmap de alto nivel propuesto es correcto, pero debe ajustarse para convertirlo en una progresion industrial:

- RC local y evidencia fresca primero.
- Packaging e instalacion tempranos, no tardios.
- UI/API hardening como producto visible.
- Testing tiers para sostener velocidad.
- CLI modularization incremental, no refactor masivo.
- Observabilidad/evidence graph para operacion.
- ADRs antes de capacidades sensibles.

El siguiente backlog recomendado es:

```text
POST-H-026 - Local release candidate stabilization and operator verification
```

Ese backlog debe actuar como puente entre `production-ready-local` y un release candidate local que un operador pueda instalar, levantar, verificar y auditar sin depender de conocimiento historico de la conversacion.
  