"""R03-04 scoped ADR/Technology decisions; no model, network or project writes."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest


# Load the pure projector without triggering ApplicationService's unrelated
# optional FastAPI/GUI dependencies; pytest can discover these tests normally.
ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('r0304_decision_test_unit', ROOT/'src/devpilot_core/application/r03_04_tech_decision.py')
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
inspect = module.inspect_technology_decisions


REFS = [{'stage':s,'sha256':d*64} for s,d in [('product-vision','1'),('scope','2'),('requirements','3')]]
SOURCE = '''# Architecture
## Tecnología y alternativas
Se propone PostgreSQL como motor relacional, por consistencia de ventas; alternativa SQLite.
Costo: licencias y operación por evaluar. Soporte, seguridad y continuidad son drivers.
## ADRs materiales
### ADR-101 — Almacenamiento transaccional
- **Contexto:** operaciones de ventas con consistencia obligatoria.
- **Decisión:** considerar motor relacional con transacciones.
- **Alternativas:** SQLite frente a PostgreSQL según despliegue y soporte.
- **Consecuencias:** operación local y migraciones; cambios posteriores se revisan.
- **Costo:** NOT_AVAILABLE.
- **Soporte:** evaluar experiencia del equipo.
- **Seguridad:** configuración con mínimos privilegios.
'''


class R0304TechnologyTests(unittest.TestCase):
    def test_material_adr_remains_proposed_in_draft(self):
        result=inspect(SOURCE,source_refs=REFS,lifecycle='APPROVAL_REQUIRED',architecture_approval_id='approval-pending')
        self.assertEqual(result['status'],'REVIEW_REQUIRED')
        self.assertFalse(result['semantic_quality_certified'])
        self.assertEqual(result['material_adr_count'],1)
        self.assertEqual(result['approval_lineage']['state'],'NOT_APPROVED')
        self.assertTrue(result['adrs'][0]['relative_path'].endswith('almacenamiento-transaccional.md'))

    def test_approved_lineage_requires_frozen_source_receipt(self):
        refused=inspect(SOURCE,source_refs=REFS,lifecycle='FROZEN',architecture_approval_id='A-2',frozen_sha256='4'*64,source_sha256_verified=False)
        self.assertEqual(refused['approval_lineage']['state'],'NOT_APPROVED')
        proved=inspect(SOURCE,source_refs=REFS,lifecycle='FROZEN',architecture_approval_id='A-2',frozen_sha256='4'*64,source_sha256_verified=True)
        self.assertEqual(proved['approval_lineage']['state'],'APPROVED_WITH_ARCHITECTURE')
        self.assertEqual(proved['adrs'][0]['disposition'],'APPROVED_WITH_ARCHITECTURE')
        self.assertFalse(proved['separate_technology_approval_required'])

    def test_unsupported_tech_approval_claim_is_material_block(self):
        bad=SOURCE.replace('Se propone PostgreSQL','El perfil tecnológico ya aprobado por el Owner es PostgreSQL')
        report=inspect(bad,source_refs=REFS)
        self.assertEqual(report['status'],'BLOCK')
        self.assertIn('TECH_UNGROUNDED_APPROVAL',[f['rule_id'] for f in report['findings']])

    def test_auto_install_prohibited_without_second_approval(self):
        bad=SOURCE.replace('Se propone PostgreSQL','Instalar automáticamente PostgreSQL sin aprobación. Se propone PostgreSQL')
        report=inspect(bad,source_refs=REFS)
        self.assertEqual(report['status'],'BLOCK')
        self.assertIn('TECH_AUTOINSTALL_DENY',[f['rule_id'] for f in report['findings']])
        self.assertFalse(report['dependency_installation_performed'])

    def test_explicit_prohibition_is_not_a_false_auto_install_block(self):
        text=SOURCE.replace('Se propone PostgreSQL', 'No instalar automáticamente PostgreSQL. Se propone PostgreSQL')
        result=inspect(text,source_refs=REFS)
        self.assertNotIn('TECH_AUTOINSTALL_DENY',[x['rule_id'] for x in result['findings']])

    def test_incomplete_material_adr_does_not_fake_approval(self):
        report=inspect(SOURCE.replace('- **Consecuencias:** operación local y migraciones; cambios posteriores se revisan.',''),source_refs=REFS)
        self.assertEqual(report['status'],'BLOCK')
        self.assertIn('TECH_ADR_INCOMPLETE',[x['rule_id'] for x in report['findings']])

    def test_unstructured_historical_c07_is_review_not_false_pass(self):
        report=inspect('# Architecture\n## Tecnología y alternativas\nPostgreSQL frente a NoSQL.\n## ADRs materiales\nLa decisión queda pendiente.',source_refs=REFS)
        self.assertEqual(report['status'],'REVIEW_REQUIRED')
        self.assertEqual(report['material_adr_count'],0)
        self.assertFalse(report['semantic_quality_certified'])

    def test_second_domain_and_conditional_non_applicability(self):
        sample='''# Architecture
## Tecnología y alternativas
Biblioteca educativa local; usar archivos versionados o SQLite; evaluar costo y soporte.
## ADRs materiales
No hay decisiones materiales ADR porque ninguna tecnología queda vinculada antes del prototipo.
'''
        report=inspect(sample,source_refs=REFS)
        self.assertEqual(report['material_adr_applicability'],'NOT_APPLICABLE_REPORTED')
        self.assertEqual(report['status'],'REVIEW_REQUIRED')
        self.assertNotIn('admon_empresa_unipersonal',str(report))


if __name__=='__main__':
    unittest.main()
