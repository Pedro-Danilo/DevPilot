---
doc_id: ADR-MP132-R02-06-B0-COMPARISON
status: accepted-for-local-candidate
version: 1.0.0
owner: product-owner
updated: 2026-10-16
related_sprint: R02_06_DL_COMPARISON_AND_REVIEW_SPRINT.md
---
# ADR — Comparación D/L de Pilot B como evidencia, no autoridad documental

## Contexto

R02-03 acreditó Ollama real **sobre casos sintéticos** y R02-05 registró Pilot B B0. Un recibo sintético no está vinculado a `business_need` ni al SHA de `.devpilot/project.yaml` de Pilot B, de modo que no puede presentarse como comparación semántica de su Vision/Scope/Requirements. A su vez, el lifecycle de artefactos de Pre-code autoriza DRAFT/review/approval/apply/FROZEN de forma separada; R02-06 no debe anticipar R02-07.

## Decisión

Extender el contrato existente `GenerationRequest` + `ArtifactCandidateEnvelope` + `CandidateComparisonGroup` con una proyección de comparación R02-06 vinculada al **único B0 exacto** `admon_empresa_unipersonal_con_agentes` del runtime registry server-authoritative. Leer la necesidad desde Project Context, nunca desde texto libre del navegador. Fijar fuente e input canónico por SHA-256. Cada etapa recibe un candidato D conservador y un candidato L generado por Ollama loopback real con consentimiento explícito. La ruta D es extractiva y **no equivale a una especificación de ingeniería completa**. Validar integridad, esquema y origen de referencias antes de exponer L al Owner. El Owner decide entre `EQUIVALENT`, `REDUCED`, `MODEL_REQUIRED` con justificación visible; esta clasificación es **juicio humano, no prueba automatizada de verdad ni autorización**.

Los recibos se guardan inmutablemente bajo `outputs/mp132_r02_06/<project>/<stage>/`, en la **plataforma**, fuera de los documentos del workspace. La ruta D no llama modelos. La L exige Ollama instalado, loopback allowlisted, timeout y output acotados. No reintentar automáticamente una llamada L, no usar API externa y no hacer fallback silencioso. Los receipts deben sobrevivir al reinicio, no ser sobreescritos y bloquear ante source drift. Solo sesión humana Owner y CSRF autorizan candidate/review.

## Reutilización y límites

- `GenerationRequest`, `ArtifactCandidateEnvelope`, `CandidateComparisonGroup`: **REUSE_AS_IS**, se utiliza el mismo contrato canónico y de selección.
- `ProviderRegistry`, `OllamaAdapter`, `parse_model_json`: **REUSE_AS_IS** para la llamada local explícita y output estructurado.
- `PathGuard`, RBAC, `Settings` route security: **EXTEND** con binding de workspace, tres rutas y operaciones Owner-only.
- Pre-code/FROZEN, Approval Center, Git apply y Model Gateway external: **NO_OP**, no autorizar desde la comparación.
- Proyección D local: **NEW bounded adapter** por inexistencia de Requirements/Architecture FROZEN en B0. La degradación de calidad debe hacerse explícita.

## Seguridad y riesgos residuales

1. Un modelo puede citar el SHA correcto y producir una afirmación falsa. El esquema y el SHA **no constituyen groundedness semántica**. Se requiere revisión explícita humana y casos negativos; no emitir `EQUIVALENT` automáticamente.
2. L genera costo API `0 USD`, pero sí consume CPU/RAM y hasta 75 segundos por inferencia. `network_used=true` refleja tráfico loopback y nunca internet autorizada.
3. Las políticas de identidad y PathGuard se verifican en backend, el navegador no puede elegir workspace raíz.
4. Al cambiar Project Context, se bloquean los recibos anteriores; no se reinterpreta un candidato contra inputs nuevos.
5. R02-06 no publica ni congela documentos; R02-07 necesita su propio lifecycle y autorización posterior.
6. El operador Windows solo puede modificar la plataforma DevPilot bajo allowlist Git exacta; jamás el source de Pilot B.

## Consecuencias y validación

Se gana una comparación observable, recuperable y con provenance sin crear autoridad duplicada. La calidad D será necesariamente limitada antes de la formalización semántica. La aceptación real exige UI Owner, resultados **Ollama real** para los tres stages, reinicio y recuperación, negativos de contenido contrario, test de no-escritura, SHA/CRC del evidence bundle y Git 3-state. Hasta recibir evidencia Windows, status `LOCAL_PASS/WINDOWS_PENDING` como máximo.
