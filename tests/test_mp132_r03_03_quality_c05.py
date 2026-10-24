"""C05 guards for visibly clipped Architecture without claiming semantic PASS."""
from __future__ import annotations
import unittest

from devpilot_core.application.r03_03_architecture import HEADINGS, architecture_quality


def _document(tails=None):
    tails=tails or {}
    return '# Architecture Document\n\n'+'\n\n'.join(
        f'## {heading}\n'+tails.get(heading, 'Se propone una delimitación para RF-001 y RNF-001 bajo revisión humana.')
        for heading in HEADINGS)


def _upstream():
    return {'product-vision':'Producto de ventas y stock, Owner conserva autoridad.',
            'scope':'Catálogo, ventas, existencias y stock bajo.',
            'requirements':'### RF-001 — Catálogo\n### RNF-001 — Integridad'}


class C05ArchitectureQualityTest(unittest.TestCase):
    def test_clipped_sections_are_material_block_not_review_pass(self):
        text=_document({'Propósito':'Se propone un catálogo con atributos (definido',
            'Upstream trace':'Las fuentes ratifican operaciones que se'})
        report=architecture_quality(text,_upstream())
        self.assertEqual(report['disposition'],'BLOCK')
        self.assertEqual(sum(c['rule_id']=='TRUNCATED_SECTION' for c in report['checks']),2)

    def test_punctuation_ambiguity_is_review_only(self):
        text=_document({'Tecnología y alternativas':'Una propuesta no aprobada de PostgreSQL'})
        report=architecture_quality(text,_upstream())
        self.assertEqual(report['disposition'],'REVIEW_REQUIRED')
        self.assertTrue(any(c['rule_id']=='UNTERMINATED_PROSE' for c in report['checks']))
        self.assertFalse(any(c['status']=='BLOCK' for c in report['checks']))

    def test_complete_short_sections_are_not_falsely_blocked(self):
        report=architecture_quality(_document(),_upstream())
        self.assertEqual(report['disposition'],'REVIEW_REQUIRED')
        self.assertFalse(any(c['rule_id'] in ('TRUNCATED_SECTION','UNTERMINATED_PROSE') for c in report['checks']))

    def test_owner_approved_decision_missing_reference_is_review_only(self):
        upstream=_upstream()
        upstream['requirements'] += '\n| D-01 | Regla | saldo inferior al umbral | **APROBADA POR OWNER** |'
        report=architecture_quality(_document(),upstream)
        self.assertEqual(report['disposition'],'REVIEW_REQUIRED')
        self.assertTrue(any(c['rule_id']=='OWNER_DECISION_TRACE' and 'D-01' in c['message'] for c in report['checks']))
