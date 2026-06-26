# POST-H-008-D — Runtime state export/redaction report

Estado: `implemented-initial`.

## Alcance

`POST-H-008-D` implementa export local de evidencia runtime con redacción. La capacidad complementa `POST-H-008-B` y `POST-H-008-C`: primero se inventaría, luego se planifica limpieza, y ahora se puede exportar evidencia sanitizada antes de limpiar o auditar.

## Comandos

```powershell
python -m devpilot_core runtime-state export --dry-run --json
python -m devpilot_core runtime-state export --execute --output outputs/runtime_exports/post_h_008_d_local --json
python -m devpilot_core schema validate --schema-id RuntimeStateExportManifest --instance outputs/runtime_exports/post_h_008_d_local/runtime_state_export_manifest.json --json
```

## Controles implementados

```text
- Dry-run por defecto.
- Execute requiere --output explícito bajo outputs/runtime_exports/.
- JSON/JSONL se sanitiza eliminando raw prompts/raw outputs.
- SecretGuard redacta tokens, API keys, passwords, bearer/basic auth y connection strings conocidas.
- .devpilot/devpilot.db y binarios no redactables se exportan metadata-only.
- Manifest y checksums SHA-256 por payload exportado.
- No red, no APIs externas, no remote execution, no connector write, no plugin execution.
```

## Criterios PASS

```text
PASS si export genera manifest y checksums.
PASS si secretos conocidos se redactan.
PASS si no requiere red ni APIs externas.
PASS si raw_prompts_exported=false y raw_outputs_exported=false.
PASS si local_db_raw_exported=false.
```

## Limitaciones

```text
- implemented-initial: no es DLP completo ni redacción semántica industrial.
- No implementa signing, cifrado ni empaquetado remoto.
- No integra automáticamente con auditpack/release; deja manifest listo como fuente opcional.
- Quality-gate runtime-state-hygiene queda para POST-H-008-E.
```

## Riesgos mitigados

```text
- Filtración accidental de prompts/outputs: eliminación estructural y pruebas focales.
- Filtración de secretos obvios: SecretGuard antes de escribir payloads.
- Export de SQLite raw: metadata-only para local-db.
- Contaminación de source-of-truth: salida restringida a outputs/runtime_exports/.
```
