"""COR213 isolated GLOBAL contract: local/mock, no Ollama/API, no workspace writes."""
import importlib.util
from pathlib import Path

import pytest

# Runtime normally resolves source under PYTHONPATH. This file is also runnable
# on a candidate isolated from the whole DevPilot repo.
try:
    from devpilot_core.application import r02_07_segmented as seg
except ImportError:
    module=Path(__file__).resolve().parents[1]/'src/devpilot_core/application/r02_07_segmented.py'
    spec=importlib.util.spec_from_file_location('seg_cor213',module)
    seg=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(seg)

UNIT={'kind':'global','id':'GLOBAL','rf_id':'','source_id':'',
      'transverse_ids':'SC-AC-07,SC-AC-08',
      'criteria':'SC-AC-07 | control de acceso | evidencia; SC-AC-08 | autorización agentes | decisión'}

VALID='''## Requisitos no funcionales
- RNF-001 — Acceso a información según autorización del titular y contexto FROZEN; Verificación: prueba negativa del control de acceso.
- RNF-002 — Registro auditable de operaciones sensibles con identidad autorizada; Verificación: inspección de registros de auditoría.
- RNF-003 — Integridad de cambios transaccionales autorizados sin escritura parcial; Verificación: prueba de reversión ante fallo.
## Restricciones
- SC-AC-07: control de acceso sujeto a restricciones FROZEN y evidencia de verificación mediante prueba de intento no autorizado.
## Decisiones pendientes
- SC-AC-08: decisión pendiente de política para acciones de agentes, sin autorizar ejecución de acciones sensibles; verificación mediante inspección de decisión.
'''

def test_global_grounded_format_passes():
    assert seg.validate_unit(VALID,UNIT)==[]

def test_global_missing_transverse_mapping_blocks():
    broken=VALID.replace('- SC-AC-08:', '- Referencia omitida:')
    assert 'GLOBAL_ACCEPTANCE_NOT_COVERED' in seg.validate_unit(broken,UNIT)

def test_global_mention_in_narrative_not_a_control_mapping():
    broken=VALID.replace('- SC-AC-08:', '- Otra decisión: SC-AC-08')
    assert 'GLOBAL_ACCEPTANCE_NOT_COVERED' in seg.validate_unit(broken,UNIT)

def test_global_verification_required_per_nfr():
    broken=VALID.replace('Verificación: inspección de registros de auditoría.', 'Evidencia a definir.')
    assert 'NFR_VERIFICATION_MISSING' in seg.validate_unit(broken,UNIT)

def test_global_nfr_ids_required_and_unique():
    broken=VALID.replace('RNF-003','RNF-001')
    assert 'NFR_IDS_MISSING' in seg.validate_unit(broken,UNIT)

def test_bind_only_sufficient_model_authored_nfr():
    unnumbered=VALID.replace('RNF-001 — ', '').replace('RNF-002 — ', '').replace('RNF-003 — ', '')
    bound,metadata,errors=seg.bind_global_nfr_ids(unnumbered,UNIT)
    assert errors==[] and metadata['renumbered_model_rows']==3
    assert seg.validate_unit(bound,UNIT)==[]

def test_bind_does_not_invent_nfr_or_proofs():
    unnumbered=VALID.replace('- RNF-003 — Integridad de cambios transaccionales autorizados sin escritura parcial; Verificación: prueba de reversión ante fallo.', '- Integridad de cambios transaccionales.')
    bound,_,errors=seg.bind_global_nfr_ids(unnumbered,UNIT)
    assert errors==[]
    assert 'NFR_IDS_MISSING' in seg.validate_unit(bound,UNIT)

def test_bind_conflicting_nfr_sequence_blocks():
    broken=VALID.replace('RNF-003','RNF-004')
    _,_,errors=seg.bind_global_nfr_ids(broken,UNIT)
    assert errors==['NFR_IDENTITY_CONFLICT']

def test_prompt_contains_all_mandatory_ids_and_sections():
    prompt=seg.prompt_for_unit(UNIT,'Vision aprobada', 'a'*64)
    assert 'SC-AC-07' in prompt and 'SC-AC-08' in prompt
    assert all(k in prompt for k in ('RNF-001','RNF-002','RNF-003','Verificación','## Restricciones'))


def test_functional_parser_not_changed_by_global_binder():
    text='### RF-001 — Crear registro\n- Tipo: funcional\n'
    candidate,_,errors=seg.bind_global_nfr_ids(text,{'kind':'functional'})
    assert candidate==text and errors==[]
