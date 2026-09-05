import { DevPilotApiClient, DevPilotApiError } from '../api/client';
import type { AuthSessionContext, RoadmapProposalRequest, RoadmapWorkbenchProjection } from '../api/types';
import { renderStepActionAdvisor } from '../components/StepActionAdvisor';

const ROUTE_ID = 'ui.planning-roadmap';

const DEFAULT_ROADMAP = { roadmap_id:'planning-roadmap-001',version:'1.0.0',milestones:[{id:'mil-foundation',version:'1.0.0',title:'Foundation',owner_role:'product-owner',outcome:'Validated planning foundation',exit_criteria:['Required scope covered'],trace_links:[{kind:'requirement',target_id:'REQ-001'},{kind:'requirement',target_id:'REQ-002'},{kind:'risk',target_id:'RISK-001'}]}],dependencies:[] };
const DEFAULT_BACKLOG = { backlog_id:'planning-backlog-001',version:'1.0.0',epics:[{id:'epic-foundation',version:'1.0.0',title:'Foundation',owner_role:'product-owner',milestone_id:'mil-foundation',trace_links:[{kind:'requirement',target_id:'REQ-001'}],priority:{level:'P0',value_score:5,risk_score:4,rationale:'Core business foundation',source:'MANUAL'}}],stories:[{id:'story-first',version:'1.0.0',title:'First story',owner_role:'developer',epic_id:'epic-foundation',acceptance_criteria:['REQ-001 accepted'],trace_links:[{kind:'requirement',target_id:'REQ-001'},{kind:'adr',target_id:'ADR-001'},{kind:'risk',target_id:'RISK-001'},{kind:'test-intent',target_id:'TEST-001'}],priority:{level:'P0',value_score:5,risk_score:4,rationale:'Required first',source:'MANUAL'}},{id:'story-second',version:'1.0.0',title:'Second story',owner_role:'developer',epic_id:'epic-foundation',acceptance_criteria:['REQ-002 accepted'],trace_links:[{kind:'requirement',target_id:'REQ-002'}],priority:{level:'P1',value_score:4,risk_score:3,rationale:'Required second',source:'MANUAL'}}],dependencies:[{id:'dep-first-second',predecessor_id:'story-first',successor_id:'story-second',kind:'requires',rationale:'Second depends on first'}] };
const DEFAULT_SPRINT = { schema_id:'SCHEMA-DEVPL-PLANNING-SPRINT-PLAN-V1',schema_version:'1.0.0',sprint_plan_id:'sprint-plan-001',version:'1.0.0',title:'Sprint 1',owner_role:'product-owner',lifecycle:'DRAFT',backlog_reference:{backlog_id:'planning-backlog-001',version:'1.0.0',lifecycle:'FROZEN',content_sha256:'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'},capacity:{unit:'points',limit:8},selected_stories:[{story_id:'story-first',estimate:3,readiness:'READY',blocking_reasons:[]},{story_id:'story-second',estimate:5,readiness:'READY',blocking_reasons:[]}],completed_story_ids:[],definition_of_ready:['acceptance criteria approved','dependencies known'],definition_of_done:['tests PASS','evidence stored'],test_intent_ids:['TEST-001'],risk_focus_ids:['RISK-001'] };

export function renderRoadmapWorkbenchView(tokenProvider:()=>string|null, session:AuthSessionContext):HTMLElement{
  const host=document.createElement('section'); host.className='roadmap-workbench'; host.dataset.routeId=ROUTE_ID; host.dataset.gsdlc08e='planning-workbench'; host.setAttribute('aria-labelledby','planning-workbench-title');
  const intro=panel('Planning Workbench','Roadmap → backlog → sprint → trazabilidad. DevPilot mantiene una única experiencia gobernada desde PRE_CODE_READY hasta IMPLEMENTING_READY.');
  intro.querySelector('h3')!.id='planning-workbench-title'; const safe=document.createElement('p'); safe.className='muted'; safe.textContent='Local-first · runtime planning only · sin ejecución de código · approval/freeze humano · agent suggestions nunca auto-aprueban.'; intro.append(safe); host.append(intro);
  const status=document.createElement('div'); status.className='notice'; status.setAttribute('role','status'); status.setAttribute('aria-live','polite'); host.append(status);
  const advisorMount=document.createElement('div'); advisorMount.dataset.planningAdvisor='true'; host.append(advisorMount);
  const journey=document.createElement('div'); host.append(journey);
  const client=()=>new DevPilotApiClient({token:tokenProvider()});

  const roadmapArea=jsonArea('Roadmap JSON',DEFAULT_ROADMAP,16); const backlogArea=jsonArea('Backlog JSON',DEFAULT_BACKLOG,18); const sprintArea=jsonArea('SprintPlan JSON',DEFAULT_SPRINT,18);
  const roadmapMode=selectField('Ruta roadmap',[['MANUAL','Manual'],['IMPORT','Import'],['AGENT','Agent-assisted']],new URLSearchParams(location.search).get('mode')||'MANUAL');
  const backlogMode=selectField('Ruta backlog',[['MANUAL','Manual'],['DERIVED','Derivada'],['AGENT','Agent-assisted']],'MANUAL');

  const roadmap=section('1 · Roadmap','Manual, import y agente producen DRAFT bajo el mismo schema.', roadmapMode, roadmapArea);
  actions(roadmap,[['Guardar DRAFT',()=>client().roadmapPropose({mode:roadmapMode.value as RoadmapProposalRequest['mode'],roadmap:JSON.parse(roadmapArea.value),required_requirement_ids:['REQ-001','REQ-002'],required_risk_ids:['RISK-001'],source_label:roadmapMode.value.toLowerCase()})],['Review',()=>client().roadmapReview()],['Approve humano',()=>client().roadmapApprove(),true],['Freeze',()=>client().roadmapFreeze(),true]],session,refresh);

  const backlog=section('2 · Backlog','Derivación explicable con coverage requirement→story, acceptance criteria y prioridad con rationale.', backlogMode, backlogArea);
  actions(backlog,[['Guardar DRAFT',()=>client().backlogPropose({mode:backlogMode.value as any,backlog:JSON.parse(backlogArea.value),required_requirement_ids:['REQ-001','REQ-002'],roadmap_milestone_ids:['mil-foundation'],known_adr_ids:['ADR-001'],known_risk_ids:['RISK-001'],known_test_intent_ids:['TEST-001'],source_label:backlogMode.value.toLowerCase()})],['Review',()=>client().backlogReview()],['Approve humano',()=>client().backlogApprove(),true],['Freeze',()=>client().backlogFreeze(),true]],session,refresh);

  const sprint=section('3 · Sprint','Solo stories READY; capacidad, prerequisites, DoR/DoD, test intent y risk focus deben permanecer válidos.', null, sprintArea);
  actions(sprint,[['Guardar DRAFT',async()=>{const b=(await client().backlogStatus()).data.backlog_workbench as any; const rec=b?.backlog??{}; const body=rec.backlog??DEFAULT_BACKLOG; const plan=JSON.parse(sprintArea.value); if(rec.content_sha256) plan.backlog_reference={backlog_id:body.backlog_id,version:body.version,lifecycle:rec.lifecycle,content_sha256:rec.content_sha256}; return client().sprintPropose({sprint_plan:plan,backlog:body,dependencies:body.dependencies??[]});}],['Review',()=>client().sprintReview()],['Approve humano',()=>client().sprintApprove(),true],['Freeze',()=>client().sprintFreeze(),true]],session,refresh);

  host.append(roadmap,backlog,sprint);

  async function refresh(message=''):Promise<void>{
    status.className='notice notice--loading'; status.textContent=message||'Actualizando estado planning…';
    try{
      const [r,b,s,c]=await Promise.all([client().roadmapStatus(),client().backlogStatus(),client().sprintStatus(),client().planningClosure()]);
      const rw=(r.data.roadmap_workbench??{}) as RoadmapWorkbenchProjection; advisorMount.replaceChildren(); if(rw.advisor) advisorMount.append(renderStepActionAdvisor({ui_state:'READY',workspace_id:rw.workspace_id,current_step:'PLANNING_ROADMAP',advisor:rw.advisor,read_only:false,actor_neutral:false,server_authoritative:true,network_used:false,external_api_used:false,mutations_performed:false,source_mutations_performed:false}));
      journey.replaceChildren(renderJourney(c.data.planning_closure as any, b.data.backlog_workbench as any, s.data.sprint_planner as any));
      status.className='notice notice--pass'; status.textContent=message||`Planning listo · ${(c.data.planning_closure as any)?.journey_state??'UNKNOWN'}`;
    }catch(e){status.className='notice notice--block';status.textContent=errorText(e);}
  }
  void refresh(); return host;
}

function renderJourney(c:any,b:any,s:any):HTMLElement{
  const p=panel('Estado y trazabilidad',`Journey: ${String(c?.journey_state??'UNKNOWN')} · coverage ${String(c?.required_planning_coverage_percent??0)}%`); p.dataset.journeyState=String(c?.journey_state??'UNKNOWN');
  const facts=document.createElement('dl'); facts.className='roadmap-workbench__facts'; add(facts,'Roadmap',String(c?.roadmap?.lifecycle??'MISSING')); add(facts,'Backlog',`${String(c?.backlog?.lifecycle??'MISSING')} · coverage ${String(c?.backlog?.required_coverage_percent??0)}%`); add(facts,'Sprint',`${String(c?.sprint?.lifecycle??'MISSING')} · executable ${String(c?.sprint?.executable??false)}`); add(facts,'Blockers',String((c?.blockers??[]).length)); p.append(facts);
  const graph=c?.trace_graph??{}; const table=document.createElement('table'); table.setAttribute('aria-label','Trace graph planning'); const head=document.createElement('tr'); for(const x of ['Origen','Relación','Destino']){const th=document.createElement('th');th.textContent=x;head.append(th);} table.append(head); for(const e of graph.edges??[]){const tr=document.createElement('tr');for(const v of [e.from,e.kind,e.to]){const td=document.createElement('td');td.textContent=String(v??'');tr.append(td);}table.append(tr);} p.append(table);
  const review=document.createElement('p');review.className='muted';review.textContent=`Backlog lifecycle: ${String(b?.backlog?.lifecycle??'MISSING')} · Sprint lifecycle: ${String(s?.sprint_plan?.lifecycle??'MISSING')}`;p.append(review); return p;
}
function section(title:string,description:string,select:HTMLSelectElement|null,area:HTMLTextAreaElement):HTMLElement{const p=panel(title,description);if(select)p.append(select);p.append(area);return p;}
function actions(root:HTMLElement,defs:Array<[string,()=>Promise<any>,boolean?]>,session:AuthSessionContext,refresh:(m?:string)=>Promise<void>):void{const box=document.createElement('div');box.className='roadmap-workbench__actions';for(const [label,fn,approval] of defs){const b=document.createElement('button');b.type='button';b.textContent=label;if(approval&&!canApprove(session)){b.disabled=true;b.title='Solo owner/product-owner. El servidor también deniega la operación.';}b.addEventListener('click',()=>void (async()=>{try{await fn();await refresh(`${label}: PASS`);}catch(e){const notice=root.closest('.roadmap-workbench')?.querySelector('.notice');if(notice){notice.className='notice notice--block';notice.textContent=errorText(e);}}})());box.append(b);}root.append(box);}
function panel(title:string,description:string):HTMLElement{const p=document.createElement('section');p.className='panel';const h=document.createElement('h3');h.textContent=title;const d=document.createElement('p');d.textContent=description;p.append(h,d);return p;}
function jsonArea(label:string,value:any,rows:number):HTMLTextAreaElement{const a=document.createElement('textarea');a.rows=rows;a.value=JSON.stringify(value,null,2);a.setAttribute('aria-label',label);a.spellcheck=false;return a;}
function selectField(label:string,options:Array<[string,string]>,value:string):HTMLSelectElement{const s=document.createElement('select');s.setAttribute('aria-label',label);for(const [v,t] of options){const o=document.createElement('option');o.value=v;o.textContent=t;o.selected=v===value;s.append(o);}return s;}
function add(dl:HTMLDListElement,k:string,v:string):void{const dt=document.createElement('dt');dt.textContent=k;const dd=document.createElement('dd');dd.textContent=v;dl.append(dt,dd);}
function canApprove(session:AuthSessionContext):boolean{return session.principal.roles.some(x=>['owner','product-owner'].includes(x));}
function errorText(e:unknown):string{return e instanceof DevPilotApiError?e.message:e instanceof Error?e.message:'Error local no clasificado.';}
