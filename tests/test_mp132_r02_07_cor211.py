"""COR211: canonical RF identity + one evidence-bound recovery, no real LLM/network."""
from __future__ import annotations
import json
from types import SimpleNamespace

import pytest
from devpilot_core.application import r02_07_segmented as seg

SCOPE = '''## MVP
| ID | Capacidad | Prioridad | Límite |
|---|---|---|---|
| SC-IN-01 | Catálogo de productos | P0 | Gestión registrada |
| SC-IN-02 | Reservas de salas | P0 | Sin duplicación |
## Criterios
| ID | Nombre | Escenario |
|---|---|---|
| SC-AC-01 | Catálogo | Dado un producto válido, cuando se registra el catálogo, entonces se puede consultar |
| SC-AC-02 | Reservas | Dada una sala disponible, cuando se reserva, entonces queda registrada la reserva |
## MVP+
| SC-DE-01 | Integración futura | P2 | Diferida |
'''
VISION = '## Visión\nControlar catálogo y reserva desde una aplicación bajo Owner.'


def content(unit, rf='RF-099', header=True):
    target = unit['source_row'].split(' | ', 1)[0]
    fields = f'''- Tipo: funcional
- Justificación: El propietario requiere resultados consistentes para {target} con trazabilidad.
- Prioridad: P0
- Método de verificación: Ejecutar prueba de {target} y comprobar el estado persistido.
- Comportamiento: El sistema registra {target} al recibir solicitud autorizada y permite consultar resultado.
- Precondiciones: Existe solicitud válida de {target} y autorización del operador humano.
- Regla de negocio: Las operaciones de {target} deben respetar el Scope aprobado.
- Excepción: Ante autorización insuficiente, no se registra ningún cambio.
- Criterio de aceptación: Dado un {target} válido, cuando se registra y confirma, entonces se consulta {target} persistido.
'''
    return (f'### {rf} — Modelo confundió el identificador\n' if header else '') + fields


def inputs():
    return {'upstream': {'scope': SCOPE, 'product-vision': VISION},
            'upstream_hashes': {'scope': seg.sha(SCOPE), 'product-vision': seg.sha(VISION)},
            'source_sha256': 'source:' + 'a'*64, 'predecessor_sha256': ''}


def invoke(root, adapter, name='cualquiera'):
    return seg.execute_one(root, name, inputs(), adapter, None, 'gemma3:4b', None,
                           lambda text: (text, {'content_safety': 'PASS'}),
                           lambda *args: None)


def test_rebinds_only_structure_not_semantics():
    unit = seg.plan_from_scope(SCOPE, VISION)[0]
    bound, metadata, issues = seg.bind_rf_identity(content(unit, 'RF-019'), unit)
    assert issues == []
    assert bound.startswith('### RF-001 — Catálogo de productos\n')
    assert metadata['model_heading_id'] == 'RF-019'
    assert metadata['rf_id'] == 'RF-001'
    assert seg.validate_unit(bound, unit) == []
    headerless, _, issues = seg.bind_rf_identity(content(unit, header=False), unit)
    assert issues == [] and seg.validate_unit(headerless, unit) == []
    bad_content = content(unit, header=False).replace('Catálogo de productos', 'integración ajena')
    bad_bound, _, _ = seg.bind_rf_identity(bad_content, unit)
    assert 'CAPABILITY_BEHAVIOR_MISMATCH' in seg.validate_unit(bad_bound, unit)


def test_ambiguous_or_cross_referenced_ids_rejected():
    unit = seg.plan_from_scope(SCOPE, VISION)[0]
    for text in (content(unit) + '\nVéase RF-042 para la misma operación.',
                 content(unit) + '\n### RF-008 — Otra sección\n',
                 '### Respuesta alternativa\n' + content(unit, header=False)):
        _, _, issues = seg.bind_rf_identity(text, unit)
        assert any(code.startswith('RF_IDENTITY_') for code in issues)
    assert seg.bind_rf_identity('## Requisitos no funcionales', {'kind': 'global'})[0] == '## Requisitos no funcionales'


def test_exact_two_rf_id_failures_allow_single_remediation_and_reuse_checkpoint(tmp_path):
    units = seg.plan_from_scope(SCOPE, VISION)
    class Adapter:
        calls = 0
        def _post_json(self, *_args, **kwargs):
            self.calls += 1
            unit = units[0] if self.calls == 1 else units[1]
            return SimpleNamespace(ok=True, metadata={'response': content(unit), 'done_reason': 'stop'})
    adapter = Adapter()
    first = invoke(tmp_path, adapter)
    assert first['partial'] and first['progress']['completed'] == 1
    root = tmp_path / 'outputs/mp132_r02_07/cualquiera/requirements_segments'
    plan = next(root.iterdir())
    first_checkpoint = (plan/'SC-AC-01.json').read_bytes()
    for _ in range(2):
        seg._failure_receipt(plan, units[1], plan.name, 'gemma3:4b',
                             'R0207_SEGMENT_NOT_CONFORMANT', ['RF_ID'], 50, {'done_reason': 'stop'})
    assert len(list((plan/'diagnostics').glob('*.json'))) == 2
    result = invoke(tmp_path, adapter)
    assert result['progress']['completed'] == 2
    assert (plan/'SC-AC-01.json').read_bytes() == first_checkpoint
    second = json.loads((plan/'SC-AC-02.json').read_text())
    assert second['identity_binding']['rf_id'] == 'RF-002'
    assert second['identity_binding']['model_heading_id'] == 'RF-099'
    assert seg.validate_unit(second['body'], units[1]) == []
    assert adapter.calls == 2
    assert (plan/'manifest.json').exists()


def test_third_failed_attempt_is_final_and_preserves_previous_checkpoint(tmp_path):
    units = seg.plan_from_scope(SCOPE, VISION)
    class Adapter:
        calls = 0
        def _post_json(self, *args, **kwargs):
            self.calls += 1
            if self.calls == 1:
                return SimpleNamespace(ok=True, metadata={'response': content(units[0]),'done_reason':'stop'})
            return SimpleNamespace(ok=True,metadata={'response': 'Respuesta inválida', 'done_reason':'stop'})
    adapter = Adapter()
    invoke(tmp_path,adapter)
    root=tmp_path/'outputs/mp132_r02_07/cualquiera/requirements_segments'
    plan=next(root.iterdir())
    first=(plan/'SC-AC-01.json').read_bytes()
    for _ in range(2):
        seg._failure_receipt(plan, units[1], plan.name, 'gemma3:4b', 'R0207_SEGMENT_NOT_CONFORMANT', ['RF_ID'], 40)
    with pytest.raises(ValueError, match='SEGMENT_NOT_CONFORMANT'):
        invoke(tmp_path,adapter)
    assert len(list((plan/'diagnostics').glob('*.json')))==3
    assert not (plan/'SC-AC-02.json').exists()
    with pytest.raises(ValueError,match='RETRY_BUDGET_EXHAUSTED'):
        invoke(tmp_path,adapter)
    assert adapter.calls==2 and (plan/'SC-AC-01.json').read_bytes()==first


def test_ineligible_or_tampered_receipts_block_without_call(tmp_path):
    unit=seg.plan_from_scope(SCOPE,VISION)[0]
    assert not seg.is_identity_repair_allowed([],unit,'a'*64,'gemma3:4b')
    folder=tmp_path/'diagnostics';folder.mkdir()
    first=folder/(unit['id']+'.attempt-01.json')
    second=folder/(unit['id']+'.attempt-02.json')
    blob={'schema':'R0210.unit_failure.v1','plan_hash':'a'*64,'unit_id':unit['id'],
          'rf_id':unit['rf_id'],'source_id':unit['source_id'],
          'criterion_id':unit['criterion_id'],'model':'gemma3:4b',
          'code':'R0207_SEGMENT_NOT_CONFORMANT','finding_codes':['RF_ID'],'attempt':1}
    first.write_text(json.dumps(blob));second.write_text(json.dumps({**blob,'attempt':2}))
    assert seg.is_identity_repair_allowed([first,second],unit,'a'*64,'gemma3:4b')
    second.write_text(json.dumps({**blob,'attempt':2,'plan_hash':'b'*64}))
    assert not seg.is_identity_repair_allowed([first,second],unit,'a'*64,'gemma3:4b')
    # Portable on standard Windows accounts without symlink-creation rights.
    # Simulate a symlink at the filesystem guard, without altering receipt bytes.
    # This verifies fail-closed path validation, not OS symlink privileges.
    original_is_symlink = type(second).is_symlink
    def is_symlink_forbidden(path):
        return path == second or original_is_symlink(path)
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(type(second), 'is_symlink', is_symlink_forbidden)
        with pytest.raises(ValueError, match='STATE_UNAVAILABLE'):
            seg.is_identity_repair_allowed([first,second],unit,'a'*64,'gemma3:4b')
    # No monkeypatch remains installed; the valid unmodified receipt still works.
    second.write_text(json.dumps({**blob,'attempt':2}), encoding='utf-8')
    assert seg.is_identity_repair_allowed([first,second],unit,'a'*64,'gemma3:4b')
