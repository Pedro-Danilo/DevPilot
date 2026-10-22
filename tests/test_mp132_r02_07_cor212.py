"""Focal tests for COR212, without real Ollama/network or user workspace writes."""
from __future__ import annotations
import json
from pathlib import Path
from types import SimpleNamespace
import pytest
from devpilot_core.application import r02_07_segmented as seg

SCOPE='''## MVP
| ID | Capacidad | Prioridad | Límite |
|---|---|---|---|
| SC-IN-01 | Reservar salas | P0 | No duplicar |
## Criterios
| ID | Nombre | Escenario |
|---|---|---|
| SC-AC-01 | Reservar salas | Dada una sala disponible, cuando la solicita un usuario autorizado, entonces se registra la reserva sin duplicar asignación |
## MVP+
| ID | Detalle |
| SC-DE-01 | Integración futura |
'''
VISION='## Visión\nRegistro gobernado de reservas.'


def fields(exception_label='Excepción', exception_value='Si la sala no está disponible, rechazar la solicitud sin duplicarla.'):
    return (f"### RF-001 — Reserva\n- Tipo: funcional\n"
        "- Justificación: La reserva debe persistirse sin duplicaciones.\n"
        "- Prioridad: P0\n"
        "- Método de verificación: Ejecutar prueba positiva y negativa contra el registro.\n"
        "- Comportamiento: Registrar Reservar salas y permitir verificar la reserva cuando la sala esté disponible.\n"
        "- Precondiciones: La sala debe estar disponible y el solicitante autorizado.\n"
        "- Regla de negocio: No duplicar asignación de salas.\n"
        f"- {exception_label}: {exception_value}\n"
        "- Criterio de aceptación: Dado el estado disponible de la sala, cuando se solicita una reserva autorizada, entonces se registra sin duplicar asignación.\n")


def test_exception_alias_substantive_and_short_rejected():
    unit=seg.plan_from_scope(SCOPE,VISION)[0]
    singular=fields()
    plural=fields('Excepciones')
    assert seg.validate_unit(singular,unit)==[]
    assert seg.validate_unit(plural,unit)==[]
    for value,reason in [('No aplica','TOO_SHORT'),('TODO','PLACEHOLDER'),('', 'MISSING_OR_EMPTY')]:
        body=fields(exception_value=value)
        problems=seg.validate_unit(body,unit)
        assert 'EXCEPTION' in problems
        assert seg.safe_field_diagnostics(body,problems)=={'EXCEPTION':reason}
    absent=fields().replace('- Excepción: Si la sala no está disponible, rechazar la solicitud sin duplicarla.\n','')
    assert 'EXCEPTION' in seg.validate_unit(absent,unit)
    assert seg.safe_field_diagnostics(absent,['EXCEPTION'])=={'EXCEPTION':'MISSING_OR_EMPTY'}


def test_retry_prompt_directed_and_no_scope_mutation():
    unit=seg.plan_from_scope(SCOPE,VISION)[0]
    prompt=seg.prompt_for_unit(unit,VISION,'b'*64)
    assert "'- Excepción:'" in prompt
    assert 'No aplica' in prompt
    assert 'Reservar salas' in prompt
    assert 'No inventes' in prompt or 'NO inventes' in prompt
    assert seg.PROFILE_VERSION=='r0207-acceptance-units-mip-v2'


def test_safe_receipt_only_classification_and_second_attempt(tmp_path):
    unit=seg.plan_from_scope(SCOPE,VISION)[0]
    folder=tmp_path/'plan'
    folder.mkdir()
    seg._failure_receipt(folder,unit,'a'*64,'gemma3:4b','R0207_SEGMENT_NOT_CONFORMANT',
                         ['EXCEPTION'],3.4,{'done_reason':'stop'},
                         {'EXCEPTION':'TOO_SHORT','OTHER':'leak'})
    data=json.loads(next((folder/'diagnostics').iterdir()).read_text(encoding='utf8'))
    assert data['attempt']==1 and data['finding_codes']==['EXCEPTION']
    assert data['field_diagnostics']=={'EXCEPTION':'TOO_SHORT'}
    assert data['raw_response_stored'] is False
    assert not any('leak' in str(v) for v in data.values())


def test_resume_after_six_units_is_single_call_and_existing_checkpoints_immutable(tmp_path):
    unit=seg.plan_from_scope(SCOPE,VISION)[0]
    class Reply:
        calls=0
        def _post_json(self, _endpoint, payload, task):
            self.calls+=1
            assert 'EXCEPTION' in payload['prompt'] if self.calls==2 else True
            if self.calls==1:
                return SimpleNamespace(ok=True, metadata={'response':fields(exception_value='No aplica'), 'done_reason':'stop'})
            return SimpleNamespace(ok=True, metadata={'response':fields('Excepciones'), 'done_reason':'stop'})
    adapter=Reply()
    ctx={'upstream':{'scope':SCOPE,'product-vision':VISION},
         'upstream_hashes':{'scope':seg.sha(SCOPE),'product-vision':seg.sha(VISION)},
         'source_sha256':'q'*64,'predecessor_sha256':''}
    def run():
        return seg.execute_one(tmp_path,'demo',ctx,adapter,None,'gemma3:4b',None,
                        lambda x:(x,{'content_safety':'PASS'}),lambda *args:None)
    with pytest.raises(ValueError,match='R0207_SEGMENT_NOT_CONFORMANT'):
        run()
    path=next((tmp_path/'outputs/mp132_r02_07/demo/requirements_segments').iterdir())
    assert not list(path.glob('SC-AC-01.json'))
    assert json.loads((path/'diagnostics/SC-AC-01.attempt-01.json').read_text())['field_diagnostics']=={'EXCEPTION':'TOO_SHORT'}
    r=run()
    assert r['progress']['completed']==1 and adapter.calls==2
    obj=json.loads((path/'SC-AC-01.json').read_text())
    assert seg.validate_unit(obj['body'],unit)==[]
    assert json.loads((path/'manifest.json').read_text())['plan_hash']==path.name


def test_assembly_failure_is_safe_receipt_and_no_extra_model_call(tmp_path, monkeypatch):
    # One functional unit plus GLOBAL; force final assembly failure, not a retry.
    units=seg.plan_from_scope(SCOPE,VISION)
    assert len(units)==2
    def fake_assemble(_units,_segments):
        raise ValueError('R0209_DUPLICATE_BEHAVIOR_BLOCK')
    monkeypatch.setattr(seg,'assemble',fake_assemble)
    class Adapter:
        calls=0
        def _post_json(self, _endpoint, payload, task):
            self.calls+=1
            resp=fields() if self.calls==1 else ('## Requisitos no funcionales\n'
               +'- RNF-001 — Preservar el control de acceso autorizado a los registros de reserva; Verificación: prueba negativa de acceso no autorizado.\n'
               +'- RNF-002 — Mantener consistencia al procesar múltiples reservas concurrentes; Verificación: prueba de consistencia de registros.\n'
               +'- RNF-003 — Conservar eventos auditables de solicitud y aprobación de reservas; Verificación: inspección de trazas asociadas.\n'
               +'## Restricciones\n'+'Política vigente de restricción verificable.\n'*4
               +'## Decisiones pendientes\n'+'Se determinará método de verificación del despliegue.\n'*4)
            return SimpleNamespace(ok=True,metadata={'response':resp,'done_reason':'stop'})
    a=Adapter()
    ctx={'upstream':{'scope':SCOPE,'product-vision':VISION},
         'upstream_hashes':{'scope':seg.sha(SCOPE),'product-vision':seg.sha(VISION)},
         'source_sha256':'q'*64,'predecessor_sha256':''}
    def run():return seg.execute_one(tmp_path,'demo',ctx,a,None,'gemma3:4b',None,
                                   lambda x:(x,{'content_safety':'PASS'}),lambda *args:None)
    run()
    with pytest.raises(ValueError, match='R0209_DUPLICATE_BEHAVIOR_BLOCK'):
        run()
    folder=next((tmp_path/'outputs/mp132_r02_07/demo/requirements_segments').iterdir())
    issue=json.loads((folder/'assembly_status.json').read_text())
    assert issue['code']=='R0209_DUPLICATE_BEHAVIOR_BLOCK'
    assert issue['raw_response_stored'] is False
    assert a.calls==2
