"""COR220 tests: rejects noun-phrase features; preserves quality controls."""
from pathlib import Path
import importlib.util
import pytest

SRC=Path(__file__).resolve().parents[1]/'src/devpilot_core/application/r02_07_quality.py'
spec=importlib.util.spec_from_file_location('cor220_quality',SRC)
quality=importlib.util.module_from_spec(spec)
spec.loader.exec_module(quality)


def doc(rows):
    return '\n'.join(f'- {i} — {c}; Verificación: {v}' for i,c,v in rows)


def test_nominal_functions_not_misclassified():
    text=doc([('RNF-001','Detección de stock bajo y notificación al propietario',
            'Se realizará una prueba que verifique las alertas generadas.'),
           ('RNF-002','Asistencia de IA para generación de informes',
            'Se realizará una prueba para comprobar la generación de borradores.')])
    pairs={(f['id'],f['target']) for f in quality.inspect_requirements(text)}
    assert ('R0218_NFR_FUNCTIONAL_MASQUERADE','RNF-001') in pairs
    assert ('R0218_NFR_FUNCTIONAL_MASQUERADE','RNF-002') in pairs


def test_deferred_capability_is_blocked_from_scope():
    scope='MVP+ capacidades diferidas SC-DEF-01 — agentes consultivos.'
    text=doc([('RNF-004','Asistencia de IA para generación de informes',
             'Se realizará una prueba de generación de informes.')])
    codes={f['id'] for f in quality.inspect_requirements(text,scope) if f['severity']=='BLOCK'}
    assert 'R0218_DEFERRED_CAPABILITY_COMMITTED' in codes


def test_legitimate_quality_about_notifications_not_blocked():
    text=doc([('RNF-001','Disponibilidad de notificaciones ante fallas de red',
             'Prueba de desconexión: comprobar que se conservan los avisos pendientes y su reenvío.')])
    assert not [f for f in quality.inspect_requirements(text) if f['severity']=='BLOCK']


def test_integrity_without_reconciled_expected_balance_requires_review():
    text=doc([('RNF-001','Integridad de datos de venta y actualización de inventario',
        'Se realizará una prueba de aceptación para comprobar los datos del formulario y el acceso del usuario.')])
    ids={f['id'] for f in quality.inspect_requirements(text)}
    assert 'R0218_NFR_INTEGRITY_PROOF_WEAK' in ids


def test_integrity_with_balance_evidence_no_weakness_hint():
    text=doc([('RNF-001','Consistencia del inventario tras una venta',
         'Prueba integrada: saldo anterior, movimiento asociado y saldo posterior esperado.')])
    ids={f['id'] for f in quality.inspect_requirements(text)}
    assert 'R0218_NFR_INTEGRITY_PROOF_WEAK' not in ids


def test_independent_domain_feature():
    text=doc([('RNF-001','Generación de citas para pacientes',
       'Se realizará una prueba de que las citas se almacenan.')])
    ids={f['id'] for f in quality.inspect_requirements(text)}
    assert 'R0218_NFR_FUNCTIONAL_MASQUERADE' in ids


def test_new_detection_limits_repair_to_actual_blocking_targets():
    scope='MVP+ diferidos SC-DEF-01 — agentes consultivos.'
    text=doc([('RNF-001','Integridad de datos de venta y actualización de inventario',
                'Se realizará una prueba de interfaz y acceso al sistema.'),
              ('RNF-003','Detección de stock bajo y notificación al propietario',
                'Se realizará una prueba de alerta de stock bajo.'),
              ('RNF-004','Asistencia de IA para generación de informes',
                'Se realizará una prueba de que el asistente genera informes.')])
    targets=quality.repair_targets(quality.inspect_requirements(text,scope))
    assert sorted(targets)==['RNF-003','RNF-004']
