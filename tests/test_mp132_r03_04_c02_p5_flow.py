"""One scoped Owner path: Technology -> selection -> ADR -> Architecture DRAFT.

The model response is controlled, but the service and its durable local
candidate writer run normally. No real model, external API or project mutation.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

from devpilot_core.application import pre_code_wizard_service as pre
from devpilot_core.application.r03_04_local_authoring import R0304LocalAuthoring
from devpilot_core.modeling.contracts import ModelCallResult, ModelTask


TECH = """# Technology Options
## Drivers y restricciones
Ventas a domicilio, stock consistente y aprobación humana de promociones.
## Opción T1 — SQLite local
- **Stack:** Python, SQLite, interfaz web móvil.
- **Costo y licencias:** Licencias abiertas; hosting no necesario para el MVP.
- **Soporte:** Comunidad y documentación disponibles.
- **Seguridad:** Auth y aprobación humana para cambios sensibles.
- **Operación:** Respaldos y uso local-first.
- **Riesgos:** Sincronización futura entre dispositivos.
## Opción T2 — PostgreSQL remoto
- **Stack:** Python, PostgreSQL e interfaz web.
- **Costo y licencias:** Licencias abiertas; hosting por cotizar.
- **Soporte:** Comunidad madura y administrador requerido.
- **Seguridad:** Roles y cifrado en tránsito.
- **Operación:** Backups y mantenimiento del servidor.
- **Riesgos:** Sobrecarga para un operador unipersonal.
## Recomendación razonada
T1 reduce mantenimiento inicial; revisar sincronización antes de ampliar.
"""

ADR = """# ADR-001 — Persistencia local del MVP
## Contexto
El Owner requiere inventario consistente, ventas y bajo costo operativo.
## Decisión
Se propone la opción T1 elegida por Owner: SQLite transaccional local-first.
## Alternativas
T2, PostgreSQL remoto, incrementa complejidad operativa en el MVP.
## Consecuencias
Menos costo ahora, pero sincronización posterior deberá diseñarse aparte.
## Riesgos y mitigaciones
Copias de seguridad, pruebas de consistencia y aprobación humana sensible.
"""

ARCH = """---
doc_id: PILOT_B_ARCHITECTURE
status: draft
---
# Architecture
## Contexto
Ventas locales de bienestar a domicilio.
## Tecnología y alternativas
Propuesta inicial por reconciliar.
## ADRs materiales
Todavía no reconciliadas.
## Riesgos
Integridad de inventario y aprobación previa para efectos sensibles.
"""


class LocalModel:
    def __init__(self, content: str):
        self.content=content

    def generate(self, request):
        assert request.provider=='ollama' and request.model=='gemma3:4b'
        return ModelCallResult(ok=True,provider='ollama',model='gemma3:4b',task=ModelTask.GENERATE,
                               content=self.content,external_api_used=False,tokens_estimated=350)


def test_owner_complete_path_and_non_owner_cannot_start_it(tmp_path:Path,monkeypatch):
    project=tmp_path/'pilot-b'; (project/'.devpilot').mkdir(parents=True)
    (project/'.devpilot/project.yaml').write_text('project_name: Pilot B\n',encoding='utf-8')
    row={'mode':'LOCAL_MODEL','status':'DRAFT','approval_id':None,'content':ARCH,
         'content_sha256':hashlib.sha256(ARCH.encode()).hexdigest(),
         'derivation':{'model':'gemma3:4b'}}
    state={'stages':{'architecture':row},'r03_04_authoring':{}}
    service=object.__new__(pre.PreCodeWizardApplicationService)
    service.root=tmp_path
    service.technology_authoring=R0304LocalAuthoring(tmp_path)
    monkeypatch.setattr(pre.PreCodeWizardApplicationService,'_context',lambda self:('pilot-b',project))
    monkeypatch.setattr(pre.PreCodeWizardApplicationService,'_load_state',lambda self,workspace_id:state)
    monkeypatch.setattr(pre.PreCodeWizardApplicationService,'_write_state',lambda self,workspace_id,body:state.update(body))
    monkeypatch.setattr(pre.PreCodeWizardApplicationService,'_current_stage',lambda self,body:{'stage_id':'architecture'})
    monkeypatch.setattr(pre.PreCodeWizardApplicationService,'_stage_state',lambda self,body,stage_id:body['stages'][stage_id])
    monkeypatch.setattr(pre.PreCodeWizardApplicationService,'_r0304_frozen_context',
                        lambda self,body,workspace_root:{'product-vision':'Visión aprobada',
                            'scope':'Inventario y ventas', 'requirements':'Aprobación humana'})
    monkeypatch.setattr(pre,'parse_project_yaml_metadata',lambda path:{'project_name':'Pilot B'})
    monkeypatch.setattr(pre.PreCodeWizardApplicationService,'_append_trace',lambda self,*args,**kwargs:None)
    def save_draft(self,**kwargs):
        assert kwargs['stage_id']=='architecture' and kwargs['mode']=='LOCAL_MODEL'
        row['content']=kwargs['content']
        row['content_sha256']=hashlib.sha256(kwargs['content'].encode()).hexdigest()
        return self._pass('save draft','R0304_DRAFT_PASS','DRAFT reconciliado',{'plan_invalidated':True})
    monkeypatch.setattr(pre.PreCodeWizardApplicationService,'save_draft',save_draft)
    responses=iter([TECH,ADR])
    actual_calls=[]
    def manual_adapter(self,adapter,model,*,explicit_owner_action=False):
        assert explicit_owner_action is True
        actual_calls.append(model)
        return LocalModel(next(responses))
    monkeypatch.setattr(R0304LocalAuthoring,'_local_adapter',manual_adapter)

    common=dict(actor='owner-pilot-b',session_principal='owner-pilot-b',
                workspace_scopes=['pilot-b'],model='gemma3:4b')
    denied=service.technology_action(action='generate_options',actor_role='viewer',
                                     effective_roles=['viewer'],**common)
    assert not denied.ok and not actual_calls
    authorized=dict(common,actor_role='owner',effective_roles=['owner'])
    for action,option in [('generate_options',''),('select_option','T1'),
                          ('generate_adr',''),('reconcile','')]:
        result=service.technology_action(action=action,option_id=option,**authorized)
        assert result.ok,(action,result.message)
    assert actual_calls==['gemma3:4b','gemma3:4b']
    assert state['r03_04_authoring']['selected_option_id']=='T1'
    assert state['r03_04_authoring']['status']=='ARCHITECTURE_REVIEW_REQUIRED'
    assert 'SQLite' in row['content'] and 'ADR-001' in row['content']
    assert 'Integridad de inventario' in row['content']
    binding=row['derivation']['technology_selection']
    assert binding['technology_sha256']==state['r03_04_authoring']['technology']['candidate_sha256']
    assert binding['adr_sha256']==state['r03_04_authoring']['adr']['candidate_sha256']
    assert state['r03_04_authoring']['reconciled_architecture_sha256']==row['content_sha256']
    assert not (project/'docs').exists()  # approval and materialization are separate.
