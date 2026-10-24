"""C03 corrective tests, unittest/stdlib: source budgets and resumable Architecture."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
from devpilot_core.application.r03_03_architecture import HEADINGS, generate_local_architecture
from devpilot_core.application.r03_03_segments import progress, LEGACY_REVISION, PREVIOUS_REVISION, BLOCKED_REVISION, REVISION, MAX_OUTPUT_TOKENS
from devpilot_core.modeling.contracts import ModelCallResult, ModelTask


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def _facts(domain: str = 'tienda') -> dict[str, str]:
    core = ('Registrar venta bajo aprobación humana.' if domain == 'tienda'
            else 'Inscribir estudiantes con consentimiento.')
    requirements = ('# Requisitos\n## RF-001 — Registro\n'+core+
                    '\n## RNF-001 — Auditabilidad\nRegistrar eventos verificables.\n')
    # More than R03-02's per-source selection cap. Full FROZEN remains verified.
    requirements += ('Nota no normativa de alcance.\n' * 1250)
    return {'product-vision':'Visión FROZEN: '+core,'scope':'Scope FROZEN: '+core,
            'requirements':requirements}


def _context(facts: dict[str,str]) -> dict:
    refs = [{'stage':stage,'path':'docs/'+stage+'.md','sha256':_sha(text)}
            for stage,text in facts.items()]
    return {'status':'REVIEW_REQUIRED','truncated_stages':['requirements'],
            'sources':[{'stage':x['stage'],'text':facts[x['stage']][:28000],'required':True} for x in refs],
            'source_refs':refs,'project_context_sha256':'1'*64,'context_sha256':'2'*64}


class DummyAdapter:
    def __init__(self, *, omit: bool = False, fail: bool = False):
        self.calls = 0
        self.prompts = []
        self.options = []
        self.omit = omit
        self.fail = fail

    def generate(self, request):
        self.calls += 1
        self.prompts.append(request.prompt)
        self.options.append(request.metadata.get('ollama_options'))
        assert request.task == ModelTask.GENERATE and request.provider == 'ollama' and request.dry_run is False
        assert '[FUENTES FROZEN ORIGINALES: EXTRACTOS' in request.prompt
        assert len(request.prompt) < 13000
        if self.fail:
            raise ValueError('SIMULATED_PROVIDER_INTERRUPTION')
        headings = [] if self.omit else [
            title for title in HEADINGS if ('## '+title) in request.prompt.split('FUENTES VERIFICADAS')[0]
        ]
        body = ('La solución contempla RF-001 y RNF-001; opciones y riesgos sujetos a revisión Owner.')
        content = ('\n\n'.join(f'## {heading}\n{body}' for heading in headings)
                   if headings else 'Propuesta sin estructura, revisión Owner necesaria.')
        return ModelCallResult(ok=True,provider='ollama',model=str(request.model),task=ModelTask.GENERATE,
                               content=content,tokens_estimated=350,cost_estimate_usd=0.0,external_api_used=False)


class C03SegmentsTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        path = self.root/'.devpilot/gsdlc/architecture_authoring_profile.json'
        path.parent.mkdir(parents=True)
        shutil.copy2(ROOT/'.devpilot/gsdlc/architecture_authoring_profile.json', path)

    def run_one(self, facts, adapter, workspace='domain_local'):
        return generate_local_architecture(self.root,workspace_id=workspace,project_name='Dominio local',
            context=_context(facts),upstream=facts,model='gemma3:4b',adapter=adapter)

    def test_long_requirements_segmented_one_call_per_unit_and_idempotent(self):
        facts = _facts()
        llm = DummyAdapter()
        for expected in range(1,10):
            partial = self.run_one(facts,llm)
            self.assertTrue(partial['partial'])
            self.assertEqual(partial['progress']['completed'],expected)
            self.assertEqual(llm.calls,expected)
        final = self.run_one(facts,llm)
        self.assertIn('## Upstream trace',final['content'])
        self.assertEqual(llm.calls,10)
        self.assertEqual(final['provenance']['segmented_units'],10)
        self.assertIn('requirements',final['provenance']['context_truncated_stages'])
        self.assertEqual(final['provenance']['quality_receipt']['disposition'],'REVIEW_REQUIRED')
        self.assertEqual(progress(self.root,'domain_local')['status'],'COMPLETE')
        repeat = self.run_one(facts,llm)
        self.assertEqual(final,repeat)
        self.assertEqual(llm.calls,10)

    def test_failed_uncertain_unit_is_not_replayed(self):
        facts = _facts('educacion')
        failed = DummyAdapter(fail=True)
        with self.assertRaisesRegex(ValueError,'SIMULATED_PROVIDER_INTERRUPTION'):
            self.run_one(facts,failed)
        self.assertEqual(failed.calls,1)
        new = DummyAdapter()
        with self.assertRaisesRegex(ValueError,'PREVIOUS_BLOCK_NO_RETRY'):
            self.run_one(facts,new)
        self.assertEqual(new.calls,0)
        self.assertEqual(progress(self.root,'domain_local')['status'],'BLOCK')

    def test_completed_c04_is_never_replayed_by_c05(self):
        folder=self.root/'outputs/mp132_r03_03/domain_local'
        folder.mkdir(parents=True)
        (folder/'active_segment_plan.json').write_text(json.dumps({
            'revision':PREVIOUS_REVISION,'plan_key':'a'*64,
            'status':'COMPLETE','completed':10,'model':'gemma3:4b'}),encoding='utf8')
        self.assertEqual(progress(self.root,'domain_local')['status'],'LEGACY_COMPLETE_REVIEW')
        llm=DummyAdapter()
        with self.assertRaisesRegex(ValueError,'OLDER_COMPLETE_CANDIDATE_REVIEW_REQUIRED'):
            self.run_one(_facts(),llm)
        self.assertEqual(llm.calls,0)

    def test_explicit_c05_alternative_preserves_completed_c04_receipts(self):
        facts=_facts()
        folder=self.root/'outputs/mp132_r03_03/domain_local'
        plan=folder/('seg-'+'a'*24)
        plan.mkdir(parents=True)
        old=[]
        for number in range(1,11):
            content=f'## {HEADINGS[number-1]}\nDecisión anterior C04.'
            # The receipt hashes UTF-8 bytes, not platform-translated text.
            # write_text() changes LF to CRLF on Windows and creates a false drift.
            (plan/f'unit-{number}.md').write_bytes(content.encode('utf-8'))
            descriptor={'status':'COMPLETE','plan_key':'a'*64,'unit':number,
                        'output_sha256':_sha(content)}
            (plan/f'unit-{number}.json').write_text(json.dumps(descriptor),encoding='utf8')
            old.append((plan/f'unit-{number}.md').read_bytes())
        (folder/'active_segment_plan.json').write_text(json.dumps({
            'revision':PREVIOUS_REVISION,'plan_key':'a'*64,
            'status':'COMPLETE','completed':10,'model':'gemma3:4b'}),encoding='utf8')
        llm=DummyAdapter()
        result=generate_local_architecture(self.root,workspace_id='domain_local',
            project_name='Dominio local',context=_context(facts),upstream=facts,
            model='gemma3:4b',adapter=llm,allow_successor=True)
        self.assertEqual(result['progress']['completed'],1)
        self.assertEqual(llm.calls,1)
        self.assertTrue((folder/('legacy-c04-'+'a'*24+'.json')).is_file())
        self.assertEqual([(plan/f'unit-{n}.md').read_bytes() for n in range(1,11)],old)
        self.assertEqual(progress(self.root,'domain_local')['status'],'IN_PROGRESS')

    def test_explicit_successor_rejects_missing_c04_unit(self):
        folder=self.root/'outputs/mp132_r03_03/domain_local'
        folder.mkdir(parents=True)
        (folder/'active_segment_plan.json').write_text(json.dumps({
            'revision':PREVIOUS_REVISION,'plan_key':'a'*64,
            'status':'COMPLETE','completed':10,'model':'gemma3:4b'}),encoding='utf8')
        llm=DummyAdapter()
        with self.assertRaisesRegex(ValueError,'C04_COMPLETED_RECEIPT_MISSING'):
            generate_local_architecture(self.root,workspace_id='domain_local',
                project_name='Dominio local',context=_context(_facts()),upstream=_facts(),
                model='gemma3:4b',adapter=llm,allow_successor=True)
        self.assertEqual(llm.calls,0)

    def test_missing_model_sections_create_editable_draft_but_not_quality_pass(self):
        facts = _facts('educacion')
        llm = DummyAdapter(omit=True)
        for _ in range(9):
            self.run_one(facts,llm)
        final = self.run_one(facts,llm)
        self.assertIn('R0303_PENDING_OWNER_REVIEW',final['content'])
        self.assertEqual(final['provenance']['quality_receipt']['disposition'],'BLOCK')
        self.assertTrue(final['provenance']['missing_model_sections'])
        self.assertTrue(final['provenance']['owner_review_required'])

    def test_source_change_does_not_reuse_old_plan(self):
        facts = _facts()
        llm = DummyAdapter()
        self.run_one(facts,llm)
        altered = dict(facts)
        altered['requirements'] += '\n## RF-002\nNueva regla verificada.'
        with self.assertRaisesRegex(ValueError,'PLAN_OR_MODEL_DRIFT'):
            self.run_one(altered,llm)
        self.assertEqual(llm.calls,1)

    def test_large_requirement_id_index_kept_complete_and_bounded(self):
        facts = _facts()
        facts['requirements'] += ''.join(f'\n## RF-{n:03d} — Detalle gobernado' for n in range(2,140))
        llm = DummyAdapter()
        partial = self.run_one(facts,llm)
        self.assertEqual(partial['progress']['completed'],1)
        self.assertIn('RF-139',llm.prompts[0])
        self.assertIn('índice íntegro',llm.prompts[0])
        self.assertLess(len(llm.prompts[0]),13000)

    def _legacy(self, *, status='BLOCK', completed=0, receipt_status='BLOCK', lock=False):
        folder=self.root/'outputs/mp132_r03_03/domain_local'
        key='f'*64
        plan=folder/('seg-'+key[:24]);plan.mkdir(parents=True)
        (folder/'active_segment_plan.json').write_text(json.dumps({
            'revision':LEGACY_REVISION,'plan_key':key,'model':'gemma3:4b',
            'status':status,'completed':completed}),encoding='utf8')
        (plan/'unit-1.json').write_text(json.dumps({'status':receipt_status,
            'plan_key':key,'unit':1,'calls_started':1}),encoding='utf8')
        if lock:(plan/'plan.lock').write_text('stale',encoding='utf8')
        return folder,plan

    def test_legacy_timeout_preserved_as_immutable_older_plan(self):
        folder,plan=self._legacy()
        before=(plan/'unit-1.json').read_bytes()
        self.assertEqual(progress(self.root,'domain_local')['status'],'LEGACY_REQUIRES_RECONCILIATION')
        result=self.run_one(_facts(),DummyAdapter())
        self.assertTrue(result['partial'])
        self.assertEqual(result['progress']['total'],10)
        self.assertEqual((plan/'unit-1.json').read_bytes(),before)
        self.assertTrue((folder/('legacy-c03-'+'f'*24+'.json')).is_file())

    def test_legacy_completed_work_must_be_reconciled_not_recomputed(self):
        self._legacy(status='IN_PROGRESS',completed=1,receipt_status='COMPLETE')
        adapter=DummyAdapter()
        with self.assertRaisesRegex(ValueError,'LEGACY_COMPLETED_WORK_REQUIRES_REVIEW'):
            self.run_one(_facts(),adapter)
        self.assertEqual(adapter.calls,0)

    def test_legacy_active_lock_must_not_be_bypassed(self):
        self._legacy(status='IN_PROGRESS',lock=True)
        with self.assertRaisesRegex(ValueError,'LEGACY_ACTIVE_LOCK_REQUIRES_REVIEW'):
            self.run_one(_facts(),DummyAdapter())

    def test_segments_request_bounded_provider_options(self):
        adapter=DummyAdapter()
        self.run_one(_facts(),adapter)
        # The concrete C04 route requests a finite output budget; generic
        # adapters remain unchanged for non-Architecture callers.
        self.assertEqual(MAX_OUTPUT_TOKENS,448)
        self.assertEqual(adapter.options[0],{'num_predict':448})

    def _c06_block_fixture(self, facts=None, *, tamper=False, failed=True):
        from devpilot_core.application.r03_03_architecture import _json_sha
        facts = facts or _facts()
        ctx = _context(facts)
        profile=json.loads((ROOT/'.devpilot/gsdlc/architecture_authoring_profile.json').read_text(encoding='utf-8'))
        request={'profile_version':profile['profile_version'],
                 'context_sha256':ctx['context_sha256'],
                 'project_context_hash':ctx['project_context_sha256'],
                 'upstream_refs':ctx['source_refs'],'model':'gemma3:4b',
                 'provider':'ollama','prompt_revision':BLOCKED_REVISION}
        key=_json_sha(request)
        base=self.root/'outputs/mp132_r03_03/domain_local'
        old=base/('seg-'+key[:24]);old.mkdir(parents=True)
        saved=[]
        for number in (1,2):
            blob=(f'## {HEADINGS[number-1]}\nRequisito RF-001 con revisión Owner.').encode('utf-8')
            (old/f'unit-{number}.md').write_bytes(blob)
            (old/f'unit-{number}.json').write_text(json.dumps({
                'status':'COMPLETE','plan_key':key,'unit':number,
                'model':'gemma3:4b','output_sha256':hashlib.sha256(blob).hexdigest(),
                'calls_started':1,'missing_headings':[]}),encoding='utf-8')
            saved.append(blob)
        if tamper:(old/'unit-2.md').write_bytes(b'altered-source-receipt')
        if failed:(old/'unit-3.json').write_text(json.dumps({
            'status':'BLOCK','plan_key':key,'unit':3,'calls_started':1,
            'model':'gemma3:4b'}),encoding='utf-8')
        (base/'active_segment_plan.json').write_text(json.dumps({
            'status':'BLOCK','revision':BLOCKED_REVISION,'plan_key':key,
            'model':'gemma3:4b','completed':2}),encoding='utf-8')
        return base,old,key,saved,facts

    def test_c07_explicit_successor_inherits_c06_one_and_two_without_model_replay(self):
        from devpilot_core.application.r03_03_architecture import generate_local_architecture
        base,old,key,saved,facts=self._c06_block_fixture()
        llm=DummyAdapter()
        with self.assertRaisesRegex(ValueError,'REQUIRES_EXPLICIT_SUCCESSOR'):
            self.run_one(facts,llm)
        self.assertEqual(llm.calls,0)
        result=generate_local_architecture(self.root,workspace_id='domain_local',
            project_name='Dominio local',context=_context(facts),upstream=facts,
            model='gemma3:4b',adapter=llm,allow_successor=True)
        self.assertEqual(result['progress']['completed'],3)
        self.assertEqual(llm.calls,1)
        self.assertIn('## Requisitos y trazabilidad',llm.prompts[0])
        pointer=json.loads((base/'active_segment_plan.json').read_text(encoding='utf-8'))
        self.assertEqual(pointer['revision'],REVISION)
        self.assertEqual(pointer['status'],'IN_PROGRESS')
        current=base/('seg-'+pointer['plan_key'][:24])
        self.assertEqual([(old/f'unit-{n}.md').read_bytes() for n in (1,2)],saved)
        self.assertEqual([(current/f'unit-{n}.md').read_bytes() for n in (1,2)],saved)
        self.assertEqual(json.loads((current/'unit-2.json').read_text())['model_calls_on_successor'],0)
        self.assertTrue((base/('legacy-c06-'+key[:24]+'.json')).exists())

    def test_c07_bad_c06_digest_never_starts_inference_or_changes_pointer(self):
        from devpilot_core.application.r03_03_architecture import generate_local_architecture
        base,_,key,_,facts=self._c06_block_fixture(tamper=True)
        llm=DummyAdapter()
        with self.assertRaisesRegex(ValueError,'C06_COMPLETED_UNIT_DRIFT'):
            generate_local_architecture(self.root,workspace_id='domain_local',
                project_name='Dominio local',context=_context(facts),upstream=facts,
                model='gemma3:4b',adapter=llm,allow_successor=True)
        self.assertEqual(llm.calls,0)
        self.assertEqual(json.loads((base/'active_segment_plan.json').read_text())['plan_key'],key)

    def test_c07_incomplete_c06_block_receipt_stops_before_model(self):
        from devpilot_core.application.r03_03_architecture import generate_local_architecture
        _,_,_,_,facts=self._c06_block_fixture(failed=False)
        llm=DummyAdapter()
        with self.assertRaisesRegex(ValueError,'C06_BLOCK_RECEIPT_INVENTORY_DRIFT'):
            generate_local_architecture(self.root,workspace_id='domain_local',
                project_name='Dominio local',context=_context(facts),upstream=facts,
                model='gemma3:4b',adapter=llm,allow_successor=True)
        self.assertEqual(llm.calls,0)

    def test_c07_length_signal_with_complete_markdown_can_be_reviewed(self):
        class CompleteAtLimit(DummyAdapter):
            def generate(self,request):
                response=super().generate(request)
                response.metadata['stop_reason']='length'
                return response
        llm=CompleteAtLimit()
        result=self.run_one(_facts(),llm)
        self.assertEqual(result['progress']['completed'],1)
        base=self.root/'outputs/mp132_r03_03/domain_local'
        pointer=json.loads((base/'active_segment_plan.json').read_text())
        receipt=json.loads((base/('seg-'+pointer['plan_key'][:24])/'unit-1.json').read_text())
        self.assertTrue(receipt['output_limit_hit'])
        self.assertEqual(receipt['status'],'COMPLETE')

    def test_c07_length_signal_with_cut_sentence_remains_block_no_retry(self):
        class CutAtLimit(DummyAdapter):
            def generate(self,request):
                from dataclasses import replace
                response=super().generate(request)
                response.metadata['stop_reason']='length'
                return replace(response,content='## Propósito\nEl sistema debe cumplir con')
        llm=CutAtLimit()
        with self.assertRaisesRegex(ValueError,'OUTPUT_INCOMPLETE_AT_LIMIT'):
            self.run_one(_facts(),llm)
        self.assertEqual(llm.calls,1)
        self.assertEqual(progress(self.root,'domain_local')['status'],'BLOCK')
        with self.assertRaisesRegex(ValueError,'PREVIOUS_BLOCK_NO_RETRY'):
            self.run_one(_facts(),llm)
        self.assertEqual(llm.calls,1)

    def test_c07_copied_units_remain_complete_through_final_assembly(self):
        from devpilot_core.application.r03_03_architecture import generate_local_architecture
        base,old,_,saved,facts=self._c06_block_fixture()
        llm=DummyAdapter()
        for expected in range(3,10):
            result=generate_local_architecture(self.root,workspace_id='domain_local',
                project_name='Dominio local',context=_context(facts),upstream=facts,
                model='gemma3:4b',adapter=llm,allow_successor=True)
            self.assertEqual(result['progress']['completed'],expected)
        final=generate_local_architecture(self.root,workspace_id='domain_local',
            project_name='Dominio local',context=_context(facts),upstream=facts,
            model='gemma3:4b',adapter=llm,allow_successor=True)
        self.assertEqual(llm.calls,8)
        self.assertIn('## Upstream trace',final['content'])
        self.assertTrue(final['provenance']['prior_block_preserved'])
        self.assertEqual(progress(self.root,'domain_local')['status'],'COMPLETE')
        self.assertEqual([(old/f'unit-{n}.md').read_bytes() for n in (1,2)],saved)

    def test_c07_partial_migration_bytes_reconciled_without_overwrite(self):
        from devpilot_core.application.r03_03_architecture import generate_local_architecture, _json_sha
        base,_,_,saved,facts=self._c06_block_fixture()
        ctx=_context(facts)
        profile=json.loads((ROOT/'.devpilot/gsdlc/architecture_authoring_profile.json').read_text(encoding='utf-8'))
        request={'profile_version':profile['profile_version'],
                 'context_sha256':ctx['context_sha256'],
                 'project_context_hash':ctx['project_context_sha256'],
                 'upstream_refs':ctx['source_refs'],'model':'gemma3:4b',
                 'provider':'ollama','prompt_revision':REVISION}
        key=_json_sha(request)
        successor=base/('seg-'+key[:24]);successor.mkdir()
        (successor/'unit-1.md').write_bytes(saved[0])
        llm=DummyAdapter()
        result=generate_local_architecture(self.root,workspace_id='domain_local',
            project_name='Dominio local',context=ctx,upstream=facts,
            model='gemma3:4b',adapter=llm,allow_successor=True)
        self.assertEqual(result['progress']['completed'],3)
        self.assertEqual(llm.calls,1)
        self.assertEqual((successor/'unit-1.md').read_bytes(),saved[0])


if __name__ == '__main__':
    unittest.main()
