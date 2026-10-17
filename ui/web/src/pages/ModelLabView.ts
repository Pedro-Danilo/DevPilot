import { DevPilotApiClient } from '../api/client';
import { renderOllamaCandidatePanel, renderLmstudioCandidatePanel } from '../components/LocalReadinessView';
import { renderPilotBComparisonPanel } from '../components/PilotBComparisonPanel';

/** Bounded model experiments; configuration never triggers inference. */
export function renderModelLabView(token: () => string): HTMLElement {
  const root=document.createElement('section');root.className='panel model-lab-panel';
  root.dataset.devpilotUiContract='ui.model-lab';
  const busy: Record<string,boolean>={ollama:false,lmstudio:false};
  const notices:Record<string,string>={ollama:'',lmstudio:''};
  const receipts:Record<string,any>={ollama:null,lmstudio:null};
  const models:Record<string,string>={ollama:'qwen2.5:3b-instruct',lmstudio:''};
  const cases:Record<string,string>={ollama:'vision',lmstudio:'vision'};
  function draw():void {
    root.replaceChildren();
    const title=document.createElement('h2');title.textContent='Laboratorio de modelos locales';
    const desc=document.createElement('p');desc.textContent='Comparación de candidatos sintéticos. Los resultados no publican documentos, no habilitan providers y no sustituyen quality gates. Sin API externa.';
    const back=document.createElement('p');back.innerHTML='<a href="/settings">← Volver a Configuración</a>';
    const info=document.createElement('p');info.textContent='Ollama y LM Studio son runtimes independientes. LM Studio es opcional: si no se encuentra un servidor/modelo local, registrar DEFERRED_WITH_REASON, sin usar mocks como evidencia real.';
    const wrap=document.createElement('div');wrap.className='model-lab-grid';
    for(const provider of ['ollama','lmstudio'] as const){
      const node=provider==='ollama' ? renderOllamaCandidatePanel(busy[provider],notices[provider],receipts[provider]) : renderLmstudioCandidatePanel(busy[provider],notices[provider],receipts[provider]);
      const prefix=provider==='ollama'?'r0203':'r0204';
      const model=node.querySelector<HTMLInputElement>(`#${prefix}-model`);
      const selected=node.querySelector<HTMLSelectElement>(`#${prefix}-case`);
      if(model)model.value=models[provider];if(selected)selected.value=cases[provider];
      node.querySelector<HTMLButtonElement>(`#${prefix}-run`)?.addEventListener('click',()=>void run(provider,node));
      wrap.append(node);
    }
    root.append(title,renderPilotBComparisonPanel(token),desc,back,info,wrap);
  }
  async function run(provider:'ollama'|'lmstudio', node:HTMLElement):Promise<void>{
    if(busy[provider])return;
    const prefix=provider==='ollama'?'r0203':'r0204';
    models[provider]=(node.querySelector<HTMLInputElement>(`#${prefix}-model`)?.value||'').trim();
    cases[provider]=node.querySelector<HTMLSelectElement>(`#${prefix}-case`)?.value||'vision';
    if(!models[provider]){notices[provider]='BLOCK: indique el identificador exacto del modelo cargado en el runtime';draw();return;}
    if(!window.confirm(`Ejecutar una inferencia REAL local con ${provider}/${models[provider]} para ${cases[provider]}? Sin publicación.`))return;
    busy[provider]=true;notices[provider]='Consultando solo el runtime local…';
    const button=node.querySelector<HTMLButtonElement>(`#${prefix}-run`);if(button)button.disabled=true;
    const label=node.querySelector<HTMLElement>(`#${prefix}-result`);if(label)label.textContent=notices[provider];
    try {
      const bytes=new Uint8Array(16);crypto.getRandomValues(bytes);
      const request_id=Array.from(bytes).map(v=>v.toString(16).padStart(2,'0')).join('');
      const api=new DevPilotApiClient({token:token()});
      const payload={case_id:cases[provider],model:models[provider],request_id,execute:true};
      const resp=provider==='ollama'?await api.ollamaProductCandidate(payload):await api.lmstudioProductCandidate(payload);
      if(!resp.ok)throw new Error(String(resp.data?.reason||resp.message||'Proveedor rechazado'));
      receipts[provider]=resp.data;
      notices[provider]='PASS · Candidato real recibido, sin aprobar ni publicar. Revisar calidad por separado.';
    } catch(e){notices[provider]='BLOCK · '+(e instanceof Error?e.message:'Proveedor no disponible');}
    finally{busy[provider]=false;draw();}
  }
  draw();return root;
}
