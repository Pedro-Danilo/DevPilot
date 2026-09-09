import { DevPilotApiClient, readQualityStoryContext, writeQualityStoryContext } from '../api/client';
import type { StoryQualityFinding, StoryQualityRemediationTrace, StoryQualityReport } from '../api/types';

export function renderStoryQualityGatePanel(tokenProvider:()=>string): HTMLElement {
  const host=document.createElement('article'); host.className='viewer-card story-quality-gate'; host.dataset.gsdlc10c='story-quality-gate';
  let context=readQualityStoryContext();
  let report:StoryQualityReport|null=null;
  let trace:StoryQualityRemediationTrace|null=null;
  let busy=false;
  let notice='';
  let noticeKind:'pass'|'block'|'info'='info';
  let successorId=''; let successorHash='';
  let findingMessage='Revisión manual detectó una condición que requiere remediación y retest impactado.';
  let findingSeverity:'S0'|'S1'|'S2'|'S3'='S2';
  let waiverReason='';
  let agentSourceId='';
  const client=()=>new DevPilotApiClient({token:tokenProvider()});

  async function evaluate():Promise<void>{
    if(!context){setNotice('BLOCK · No hay StoryTestPlan en contexto. Vuelve a Story Code Workbench, planifica los jobs o carga el contexto preparado por la validación.', 'block');return;}
    busy=true;draw();try{const r=await client().storyQualityEvaluate(context.test_plan_id,context.test_plan_hash);report=(r.data as any).story_quality_report as StoryQualityReport;setNotice(report.decision==='PASS'?'PASS · Quality Gate determinista; COMMIT_READY=true.':`BLOCK · ${report.findings.filter(x=>x.blocking).length} blocker(s); COMMIT_READY=false.`,report.decision==='PASS'?'pass':'block');}catch(e){setNotice(errorText(e),'block');}busy=false;draw();
  }

  async function recordFinding():Promise<void>{
    if(!context)return; busy=true;draw();try{await client().storyQualityRecordFinding({test_plan_id:context.test_plan_id,test_plan_hash:context.test_plan_hash,origin:'review',severity:findingSeverity,message:findingMessage,source_ref:'ui.quality/story-review'});setNotice('PASS · finding de revisión registrado como input fail-closed.','pass');await evaluate();return;}catch(e){setNotice(errorText(e),'block');}busy=false;draw();
  }

  async function remediate(finding:StoryQualityFinding,mode:'manual'|'agent'):Promise<void>{
    if(!report)return;if(mode==='agent'&&!agentSourceId.trim()){setNotice('BLOCK · indica el Source ID exacto que el agente debe inspeccionar. La propuesta no puede elegir archivos implícitamente.','block');return;}busy=true;draw();try{const r=await client().storyQualityPlanRemediation(report.report_id,{report_hash:report.report_hash,finding_id:finding.finding_id,mode,instruction:mode==='agent'?`Propón una corrección bounded para ${finding.finding_id}. No apliques cambios.`:'',source_id:mode==='agent'?agentSourceId.trim():undefined,agent_mode:'mock'});trace=(r.data as any).remediation_trace as StoryQualityRemediationTrace;setNotice(mode==='manual'?'PASS · handoff de remediación manual preparado; source sigue gobernado por GSDLC-09.':'PASS · propuesta agentic proposal-only preparada; ToolIntent no concedió autoridad.','pass');}catch(e){setNotice(errorText(e),'block');}busy=false;draw();
  }

  async function requestWaiver(finding:StoryQualityFinding):Promise<void>{
    if(!report)return;if(!waiverReason.trim()){setNotice('BLOCK · escribe una razón para solicitar waiver.','block');return;}busy=true;draw();try{await client().storyQualityRequestWaiver(report.report_id,{report_hash:report.report_hash,finding_id:finding.finding_id,reason:waiverReason,ttl_minutes:60});setNotice('PASS · solicitud de waiver creada. Debe aprobarla un owner diferente del requester; no hay auto-approval.','pass');}catch(e){setNotice(errorText(e),'block');}busy=false;draw();
  }

  async function planRetest():Promise<void>{
    if(!trace||!successorId.trim()||!successorHash.match(/^[0-9a-f]{64}$/)){setNotice('BLOCK · indica StoryTestPlan successor APPROVED (id + hash) preparado después de la remediación.','block');return;}busy=true;draw();try{const r=await client().storyQualityPlanRetest(trace.trace_id,successorId.trim(),successorHash.trim());trace=(r.data as any).remediation_trace as StoryQualityRemediationTrace;setNotice('PASS · retest impactado planificado desde Test Impact del StoryTestPlan successor; rerun-everything=false; Full=0.','pass');}catch(e){setNotice(errorText(e),'block');}busy=false;draw();
  }

  async function completeRetest():Promise<void>{
    if(!trace)return;busy=true;draw();try{const r=await client().storyQualityCompleteRetest(trace.trace_id);trace=(r.data as any).remediation_trace as StoryQualityRemediationTrace;setNotice('PASS · retest impactado confirmado; provenance finding→remediation→retest quedó RESOLVED.','pass');}catch(e){setNotice(errorText(e),'block');}busy=false;draw();
  }

  function useSuccessor():void{
    if(!successorId.trim()||!successorHash.match(/^[0-9a-f]{64}$/))return;
    writeQualityStoryContext({test_plan_id:successorId.trim(),test_plan_hash:successorHash.trim()}); context=readQualityStoryContext(); report=null; trace=null; setNotice('PASS · StoryTestPlan successor ahora es el contexto Quality. Evalúa nuevamente para una decisión fresca.','pass'); draw();
  }

  function draw():void{
    host.replaceChildren();
    const title=document.createElement('div'); title.innerHTML='<h3>Story Quality Gate · GSDLC-10-C</h3><p>Agrega validaciones, findings, traceability y waivers en una decisión determinista. <strong>COMMIT_READY nunca se infiere de un modelo</strong>.</p>';host.append(title);
    const safety=document.createElement('div');safety.className='code-safety-strip';safety.textContent='QUALITY AUTHORITY · SERVER-SIDE · S0/S1 NO WAIVER · AGENT PROPOSAL-ONLY · IMPACTED RETEST · FULL=0';host.append(safety);
    if(notice){const n=document.createElement('div');n.className=`ui-state ui-state--${noticeKind==='block'?'block':noticeKind==='pass'?'pass':'loading'}`;n.textContent=notice;host.append(n);}
    const ctx=document.createElement('section');ctx.className='story-quality-context';ctx.innerHTML='<h4>Contexto StoryTestPlan</h4>';const cp=document.createElement('p');cp.dataset.qualityContext='true';cp.textContent=context?`${context.test_plan_id} · ${context.test_plan_hash.slice(0,12)}…`:'Sin contexto. Planifica StoryValidationJobs desde Story Code Workbench.';ctx.append(cp);const evalBtn=button('Evaluar Quality Gate');evalBtn.dataset.evaluateStoryQuality='true';evalBtn.disabled=busy||!context;evalBtn.addEventListener('click',()=>void evaluate());ctx.append(evalBtn);host.append(ctx);

    const inject=document.createElement('details');inject.className='story-quality-review-input';const summary=document.createElement('summary');summary.textContent='Registrar finding de revisión / seguridad (input adicional, solo endurece el gate)';inject.append(summary);const sev=document.createElement('select');sev.setAttribute('aria-label','Severidad Quality finding');for(const value of ['S0','S1','S2','S3'] as const){const o=document.createElement('option');o.value=value;o.textContent=value;o.selected=value===findingSeverity;sev.append(o);}sev.addEventListener('change',()=>findingSeverity=sev.value as any);const msg=document.createElement('input');msg.value=findingMessage;msg.maxLength=1000;msg.setAttribute('aria-label','Mensaje Quality finding');msg.addEventListener('input',()=>findingMessage=msg.value);const add=button('Registrar finding');add.disabled=busy||!context;add.addEventListener('click',()=>void recordFinding());inject.append(sev,msg,add);host.append(inject);

    if(report){
      const decision=document.createElement('section');decision.className=`story-quality-decision story-quality-decision--${report.decision.toLowerCase()}`;decision.dataset.qualityDecision=report.decision;decision.innerHTML=`<h4>${report.decision} · ${report.commit_ready?'COMMIT_READY':'COMMIT_BLOCKED'}</h4><p>report ${escapeHtml(report.report_id)} · inputs ${escapeHtml(report.inputs_hash.slice(0,12))}… · S0=${report.severity_counts.S0??0} S1=${report.severity_counts.S1??0} S2=${report.severity_counts.S2??0} S3=${report.severity_counts.S3??0}</p>`;host.append(decision);
      const agentScope=document.createElement('div');agentScope.className='story-quality-agent-scope';const asl=document.createElement('label');asl.textContent='Source ID para propuesta agentic (scope explícito)';const asi=document.createElement('input');asi.placeholder='source-id exacto desde Story Code Workbench';asi.value=agentSourceId;asi.setAttribute('aria-label','Source ID para remediación agentic');asi.addEventListener('input',()=>agentSourceId=asi.value);asl.append(asi);agentScope.append(asl);host.append(agentScope);
      const list=document.createElement('div');list.className='story-quality-findings';for(const finding of report.findings){const card=document.createElement('div');card.className=`story-quality-finding ${finding.blocking?'story-quality-finding--block':'story-quality-finding--resolved'}`;card.dataset.qualityFinding=finding.finding_id;const p=document.createElement('p');p.innerHTML=`<strong>${escapeHtml(finding.severity)} · ${escapeHtml(finding.origin)}</strong> · ${escapeHtml(finding.message)}<br><code>${escapeHtml(finding.finding_id)}</code> · ${finding.waived?'WAIVED':finding.status}`;card.append(p);if(finding.blocking){const actions=document.createElement('div');actions.className='viewer-controls';const manual=button('Remediación manual');manual.dataset.remediateManual='true';manual.addEventListener('click',()=>void remediate(finding,'manual'));const agent=button('Propuesta agentic');agent.className='button-secondary';agent.dataset.remediateAgent='true';agent.addEventListener('click',()=>void remediate(finding,'agent'));actions.append(manual,agent);if(finding.waivable){const reason=document.createElement('input');reason.placeholder='Razón waiver';reason.maxLength=500;reason.addEventListener('input',()=>waiverReason=reason.value);const waiver=button('Solicitar waiver');waiver.className='button-secondary';waiver.addEventListener('click',()=>void requestWaiver(finding));actions.append(reason,waiver);}card.append(actions);}list.append(card);}host.append(list);
    }
    if(trace){const tr=document.createElement('section');tr.className='story-quality-remediation';tr.dataset.remediationTrace=trace.trace_id;tr.innerHTML=`<h4>Remediation trace · ${escapeHtml(trace.status)}</h4><p>${escapeHtml(trace.trace_id)} · finding ${escapeHtml(trace.finding_id)} · mode=${escapeHtml(trace.mode)}</p><p>Source write authority: GSDLC-09; model/agent no concede waiver ni ejecución.</p>`;const sid=document.createElement('input');sid.placeholder='StoryTestPlan successor ID';sid.value=successorId;sid.setAttribute('aria-label','StoryTestPlan successor ID');sid.addEventListener('input',()=>successorId=sid.value);const sh=document.createElement('input');sh.placeholder='StoryTestPlan successor hash (64 hex)';sh.value=successorHash;sh.setAttribute('aria-label','StoryTestPlan successor hash');sh.addEventListener('input',()=>successorHash=sh.value);const controls=document.createElement('div');controls.className='viewer-controls';const plan=button('Planificar retest impactado');plan.dataset.planImpactedRetest='true';plan.addEventListener('click',()=>void planRetest());const complete=button('Confirmar retest PASS');complete.dataset.completeImpactedRetest='true';complete.addEventListener('click',()=>void completeRetest());const use=button('Usar successor para Quality');use.className='button-secondary';use.addEventListener('click',useSuccessor);controls.append(plan,complete,use);tr.append(sid,sh,controls);const pre=document.createElement('pre');pre.className='viewer-pre';pre.textContent=JSON.stringify({tool_authority:trace.tool_authority,retest:trace.retest},null,2);tr.append(pre);host.append(tr);}
  }
  function setNotice(text:string,kind:'pass'|'block'|'info'):void{notice=text;noticeKind=kind;}
  function button(label:string):HTMLButtonElement{const b=document.createElement('button');b.type='button';b.textContent=label;return b;}
  function errorText(error:unknown):string{return error instanceof Error?error.message:String(error);}
  function escapeHtml(value:string):string{return value.replace(/[&<>"']/g,ch=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]??ch));}
  draw();return host;
}
