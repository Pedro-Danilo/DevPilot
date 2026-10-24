"""C04 focal provider/transport tests without requiring live Ollama or Pilot B."""
from __future__ import annotations

from pathlib import Path
import unittest
from unittest.mock import patch

from devpilot_core.modeling.contracts import (
    ModelCallRequest, ModelCallResult, ModelProviderConfig, ModelProviderKind, ModelTask,
)
from devpilot_core.modeling.ollama_adapter import OllamaAdapter


class BoundedArchitectureAdapterTest(unittest.TestCase):
    def setUp(self):
        provider=ModelProviderConfig(provider_id='ollama',kind=ModelProviderKind.LOCAL,
            enabled=True,default_model='gemma3:4b',endpoint='http://127.0.0.1:11434')
        self.adapter=OllamaAdapter(provider_config=provider,timeout_seconds=165)

    def test_ollama_num_predict_is_explicit_and_bounded(self):
        result=ModelCallResult(ok=True,provider='ollama',model='gemma3:4b',task=ModelTask.GENERATE,
            metadata={'response':'## Propósito\nPropuesta revisable.'})
        with patch.object(OllamaAdapter,'_post_json',return_value=result) as send:
            reply=self.adapter.generate(ModelCallRequest(task=ModelTask.GENERATE,
                provider='ollama',model='gemma3:4b',prompt='## Propósito',dry_run=False,
                metadata={'ollama_options':{'num_predict':256}}))
        self.assertTrue(reply.ok)
        payload=send.call_args.args[1]
        self.assertEqual(payload['options'],{'num_predict':256})
        self.assertFalse(payload['stream'])

    def test_other_model_calls_do_not_inherit_c04_options(self):
        result=ModelCallResult(ok=True,provider='ollama',model='gemma3:4b',task=ModelTask.GENERATE,
            metadata={'response':'contenido'})
        with patch.object(OllamaAdapter,'_post_json',return_value=result) as send:
            self.adapter.generate(ModelCallRequest(task=ModelTask.GENERATE,
                provider='ollama',model='gemma3:4b',prompt='Prueba',dry_run=False))
        self.assertNotIn('options',send.call_args.args[1])

    def test_invalid_output_budget_rejected_before_network(self):
        with patch.object(OllamaAdapter,'_post_json') as send:
            for bad in (-1,0,False,513,'999'):
                with self.assertRaisesRegex(ValueError,'OLLAMA_BOUNDED_GENERATION_OPTIONS_INVALID'):
                    self.adapter.generate(ModelCallRequest(task=ModelTask.GENERATE,
                        provider='ollama',model='gemma3:4b',prompt='Prueba',dry_run=False,
                        metadata={'ollama_options':{'num_predict':bad}}))
            send.assert_not_called()

    def test_ui_architecture_timeout_has_margin_and_no_retry_advice(self):
        source=(Path(__file__).resolve().parents[1]/'ui/web/src/api/client.ts').read_text(encoding='utf8')
        self.assertIn("stageId === 'architecture' ? 225000",source)
        self.assertIn("action: uncertainDraft ? 'reconcile_before_retry'",source)
        self.assertIn('NO REINTENTES',source)


if __name__=='__main__':
    unittest.main()
