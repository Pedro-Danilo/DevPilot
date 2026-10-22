"""COR217: format-insensitive RF assembly, unchanged model/Scope authority."""
from __future__ import annotations
import re
import pytest
from devpilot_core.application import r02_07_segmented as seg
from devpilot_core.application import r02_07_semantic as sem
from test_mp132_r02_07_segmented import SCOPE, VISION, args


def produce(tmp_path):
    ctx, adapter, calls, failures, record = args(tmp_path)
    units = seg.plan_from_scope(SCOPE, VISION)
    for _ in units:
        result = seg.execute_one(tmp_path, 'project-X', ctx, adapter, None,
                                 'gemma3:4b', None, lambda c: (c, {'content_safety':'PASS'}), record)
    return result['body'], units, calls, tmp_path


def test_replay_is_valid_without_model_calls(tmp_path):
    document, units, calls, root = produce(tmp_path)
    assert not sem.requirements_output_findings(document, SCOPE)
    folder = next((root/'outputs/mp132_r02_07/project-X/requirements_segments').iterdir())
    raw = {u['id']:seg.read_json(folder/(u['id']+'.json'))['body'] for u in units}
    assert seg.assemble(units, raw) == document
    assert len(calls) == len(units)
    for u in units:
        if u['kind']=='functional':
            published=seg._published_rf(u,raw[u['id']])
            assert '- Origen: ' in published
            for key in ('Tipo:', 'Justificación:', 'Prioridad:', 'Método de verificación:',
                        'Comportamiento:', 'Precondiciones:', 'Regla de negocio:', 'Excepción:',
                        'Criterio de aceptación:'):
                assert '- '+key in published


def test_canonicalizes_plural_exceptions_and_internal_headings_without_laundering(tmp_path):
    document, units, _, root = produce(tmp_path)
    folder = next((root/'outputs/mp132_r02_07/project-X/requirements_segments').iterdir())
    raw = {u['id']:seg.read_json(folder/(u['id']+'.json'))['body'] for u in units}
    one=units[0]
    original=raw[one['id']]
    assert '- Excepción:' in original
    alternate=original.replace('- Excepción:', '- Excepciones:',1)
    alternate=alternate.replace('- Regla de negocio:', '## Regla de negocio — subtítulo accesorio\n- Regla de negocio:',1)
    # Unit validator is still required to accept the model's unchanged fields.
    assert not seg.validate_unit(alternate,one)
    raw[one['id']]=alternate
    revised=seg.assemble(units,raw)
    assert not sem.requirements_output_findings(revised,SCOPE)
    assert '## Regla de negocio — subtítulo accesorio' not in revised
    assert '- Excepción:' in revised
    assert raw[one['id']]==alternate


def test_missing_model_authored_fields_block_instead_of_fabricating(tmp_path):
    _,units,_,root=produce(tmp_path)
    folder=next((root/'outputs/mp132_r02_07/project-X/requirements_segments').iterdir())
    raw={u['id']:seg.read_json(folder/(u['id']+'.json'))['body'] for u in units}
    one=units[0]
    raw[one['id']]=re.sub(r'(?im)^- Excepción:.*$', '- Excepción: TODO', raw[one['id']], count=1)
    with pytest.raises(ValueError,match='R0209_GLOBAL_QUALITY_BLOCK|R0217_MODEL_AUTHORED_FIELD_MISSING'):
        seg.assemble(units,raw)


def test_missing_authoritative_source_blocks():
    text=('### RF-001 — Registrar solicitud\n' +
          '\n'.join('- '+label+': '+value for label,value in [
              ('Tipo','Funcional'),('Justificación','Permite registrar una solicitud verificable.'),
              ('Prioridad','P0'),('Método de verificación','Prueba de creación de solicitud.'),
              ('Comportamiento','Registra la solicitud válida y devuelve identificador.'),
              ('Precondiciones','Usuario autenticado con autorización vigente.'),
              ('Regla de negocio','No admite duplicados ni solicitudes incompletas.'),
              ('Excepción','Solicitud incorrecta no cambia registros persistidos.'),
              ('Criterio de aceptación','Dado un usuario autorizado, cuando registra, entonces recibe ID.')]))
    u={'id':'SC-AC-03','kind':'functional','rf_id':'RF-001','source_id':'UNRESOLVED','criterion_id':''}
    with pytest.raises(ValueError,match='SOURCE_AUTHORITY_MISSING'):
        seg._published_rf(u,text)


def test_scope_transverse_is_authoritative_not_fabricated():
    text='### RF-007 — Permisos\n'+'\n'.join('- '+key+': '+value for key,value in [
        ('Tipo','Funcional'), ('Justificación','Limitar acciones administrativas.'),
        ('Prioridad','P0'), ('Método de verificación','Prueba sin sesión válida.'),
        ('Comportamiento','Bloquea operación a sujetos no autorizados.'),
        ('Precondiciones','Solicitud identificada y control de permisos activo.'),
        ('Regla de negocio','Solo usuario autorizado puede ejecutar acciones.'),
        ('Excepción','Si no hay autorización se rechaza sin alterar datos.'),
        ('Criterio de aceptación','Dado sujeto no autorizado cuando intenta cambiar datos entonces se bloquea.')])
    u={'id':'SC-AC-04','kind':'functional','rf_id':'RF-007','source_id':'TRANSVERSAL','criterion_id':'SC-AC-04'}
    published=seg._published_rf(u,text)
    assert 'Origen: TRANSVERSAL / SC-AC-04' in published
    assert 'SC-IN-' not in published


def test_frozen_checkpoint_keeps_hash_and_assembly_changes_only_view(tmp_path):
    _,units,_,root=produce(tmp_path)
    folder=next((root/'outputs/mp132_r02_07/project-X/requirements_segments').iterdir())
    before={u['id']:seg.read_json(folder/(u['id']+'.json'))['sha256'] for u in units}
    raw={u['id']:seg.read_json(folder/(u['id']+'.json'))['body'] for u in units}
    seg.assemble(units,raw)
    after={u['id']:seg.read_json(folder/(u['id']+'.json'))['sha256'] for u in units}
    assert before==after
