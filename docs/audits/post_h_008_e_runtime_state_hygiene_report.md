# POST-H-008-E — Runtime state hygiene and release archive report

Estado: `implemented-initial`.

## Propósito

`POST-H-008-E` agrega un gate local, determinista y read-only para bloquear repositorios o paquetes fuente que mezclen runtime state con source-of-truth. El gate consolida la policy `.devpilot/runtime_state_policy.json`, el inventario `RuntimeStateInventory` y una verificación de archive:

```text
- Si `.git` existe: inspecciona `git archive HEAD` en memoria, sin escribir ZIP/TAR.
- Si `.git` no existe: evalúa un plan determinista de source archive para permitir verificar ZIPs limpios entregados sin metadata Git.
```

## Artefactos implementados

```text
src/devpilot_core/runtime_state/hygiene.py
docs/schemas/runtime_state_hygiene_report.schema.json
tests/test_runtime_state_hygiene.py
```

## Integraciones

```text
- CLI: python -m devpilot_core runtime-state hygiene --json
- CLI: python -m devpilot_core runtime-state hygiene --write-report --json
- Quality gate: subgate runtime-state-hygiene en perfiles hardening e industrial.
- Schema catalog: RuntimeStateHygieneReport.
- TCR v1/v2: post-h-008-runtime-state-hygiene.
```

## Controles de seguridad

```text
- read_only=true
- dry_run=true
- network_used=false
- external_api_used=false
- mutations_performed=false
- source_mutations_performed=false
- destructive_cleanup_performed=false
- cleanup_execution_enabled=false
- export_execution_enabled=false
- remote_execution_enabled=false
```

## Criterios PASS cubiertos

```text
PASS si quality-gate detecta runtime artifacts versionados.
PASS si git archive basado en HEAD queda limpio cuando .git está disponible.
PASS si el plan determinista de source archive queda limpio cuando .git no está disponible.
PASS si test-contracts validate pasa.
```

## Criterios BLOCK cubiertos

```text
BLOCK si `outputs/`, `.devpilot/devpilot.db`, `.devpilot/agent_sessions/`, caches o build artifacts entran al archive.
BLOCK si un runtime artifact no versionable aparece rastreado por Git.
BLOCK si la policy deja de exigir exclusiones críticas o permite runtime artifacts en release ZIP.
```

## Límites de esta versión

```text
- No firma ni cifra archives.
- No crea release ZIPs; inspecciona/valida higiene de archive como gate read-only.
- No reemplaza scanning DLP industrial completo.
- En ZIPs sin `.git`, la comprobación `git archive HEAD` se sustituye por un plan determinista equivalente; en un checkout Git real sí se inspecciona `git archive HEAD`.
```

## Verificación recomendada

```powershell
python -m pytest tests/test_runtime_state_hygiene.py tests/test_runtime_state_inventory.py tests/test_runtime_state_policy_schema.py tests/test_post_h_008_runtime_state_lifecycle.py -q
python -m devpilot_core runtime-state hygiene --write-report --json
python -m devpilot_core schema validate --schema-id RuntimeStateHygieneReport --instance outputs/reports/runtime_state_hygiene_report.json --json
python -m devpilot_core quality-gate run --profile hardening --json
python -m devpilot_core test-contracts validate --json
python -m devpilot_core test-contracts validate-v2 --json
```

## Conclusión

`POST-H-008-E` cierra el ciclo mínimo de `POST-H-008`: policy, inventario, cleanup plan, export redactado y gate de higiene runtime/release archive quedan implementados como baseline industrial local-first.
