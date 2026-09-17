export type OperationSemanticState =
  | 'loading' | 'empty' | 'ready' | 'pending' | 'running'
  | 'success' | 'pass' | 'warn' | 'block' | 'error'
  | 'recovery' | 'stale' | 'revalidation';

export interface OperationStateOptions {
  state: OperationSemanticState;
  title: string;
  detail?: string;
  reasonCode?: string;
}

export interface PrimaryActionOptions {
  label: string;
  hierarchy?: 'primary' | 'secondary' | 'destructive' | 'blocked';
  detail?: string;
  href?: string;
}

export interface GateSummaryOptions {
  label: string;
  state: 'PASS' | 'WARN' | 'BLOCK' | 'PENDING';
  detail?: string;
}

export interface ApprovalSummaryOptions {
  required: boolean;
  status?: string;
  role?: string;
  effect?: string;
}

export interface DiffSummaryOptions {
  changedPaths?: number;
  risk?: string;
  detail?: string;
}

export interface LongRunningOperationOptions {
  state: 'idle' | 'queued' | 'running' | 'pass' | 'block' | 'error' | 'cancelled';
  label: string;
  heartbeat?: string;
  detail?: string;
}

export interface OperationalSurfaceSummaryOptions {
  eyebrow: string;
  title: string;
  state: OperationSemanticState;
  stateDetail: string;
  primaryAction: PrimaryActionOptions;
  gate?: GateSummaryOptions;
  approval?: ApprovalSummaryOptions;
  diff?: DiffSummaryOptions;
  longRunning?: LongRunningOperationOptions;
  evidenceSummary: string;
  evidenceBody: string;
  recovery?: string;
}

const NORMALIZED_STATE: Record<OperationSemanticState, string> = {
  loading: 'LOADING', empty: 'EMPTY', ready: 'READY', pending: 'PENDING', running: 'RUNNING',
  success: 'PASS', pass: 'PASS', warn: 'WARN', block: 'BLOCK', error: 'ERROR',
  recovery: 'RECOVERY', stale: 'STALE', revalidation: 'REVALIDATION REQUIRED',
};

export function renderOperationState(options: OperationStateOptions): HTMLElement {
  const el=document.createElement('div');
  el.className=`operation-state operation-state--${options.state}`;
  el.dataset.operationState=options.state;
  el.setAttribute('role', options.state === 'block' || options.state === 'error' ? 'alert' : 'status');
  const badge=document.createElement('span'); badge.className='operation-state__badge'; badge.textContent=NORMALIZED_STATE[options.state];
  const copy=document.createElement('div');
  const title=document.createElement('strong'); title.textContent=options.title; copy.append(title);
  if(options.detail){const p=document.createElement('p');p.textContent=options.detail;copy.append(p);}
  if(options.reasonCode){const code=document.createElement('code');code.textContent=options.reasonCode;copy.append(code);}
  el.append(badge,copy); return el;
}

export function renderPrimaryAction(options: PrimaryActionOptions): HTMLElement {
  const hierarchy=options.hierarchy ?? 'primary';
  const wrap=document.createElement('div'); wrap.className=`primary-action primary-action--${hierarchy}`; wrap.dataset.actionHierarchy=hierarchy;
  const label=options.href ? document.createElement('a') : document.createElement('span');
  label.className='primary-action__label'; label.textContent=options.label;
  if(label instanceof HTMLAnchorElement) label.href=options.href!;
  wrap.append(label);
  if(options.detail){const p=document.createElement('p');p.textContent=options.detail;wrap.append(p);}
  return wrap;
}

export function renderGateSummary(options: GateSummaryOptions): HTMLElement {
  const el=document.createElement('div');el.className=`gate-summary gate-summary--${options.state.toLowerCase()}`;el.dataset.gateState=options.state;
  const label=document.createElement('strong');label.textContent=`${options.label}: ${options.state}`;el.append(label);
  if(options.detail){const p=document.createElement('p');p.textContent=options.detail;el.append(p);}return el;
}

export function renderApprovalSummary(options: ApprovalSummaryOptions): HTMLElement {
  const el=document.createElement('div');el.className='approval-summary';el.dataset.approvalRequired=String(options.required);
  const h=document.createElement('strong');h.textContent=options.required ? 'Approval requerido' : 'Approval no requerido';el.append(h);
  const p=document.createElement('p');p.textContent=[options.status && `estado=${options.status}`, options.role && `rol=${options.role}`, options.effect].filter(Boolean).join(' · ') || 'La autoridad permanece server-side.';el.append(p);return el;
}

export function renderDiffSummary(options: DiffSummaryOptions): HTMLElement {
  const el=document.createElement('div');el.className='diff-summary';const h=document.createElement('strong');h.textContent='Diff / cambio';el.append(h);
  const p=document.createElement('p');p.textContent=[options.changedPaths !== undefined ? `${options.changedPaths} paths` : undefined,options.risk ? `riesgo ${options.risk}` : undefined,options.detail].filter(Boolean).join(' · ') || 'Sin diff materializado.';el.append(p);return el;
}

export function renderLongRunningOperation(options: LongRunningOperationOptions): HTMLElement {
  const el=document.createElement('div');el.className=`long-running-operation long-running-operation--${options.state}`;el.dataset.longRunningState=options.state;
  const h=document.createElement('strong');h.textContent=`${options.label}: ${options.state.toUpperCase()}`;el.append(h);
  const p=document.createElement('p');p.textContent=[options.heartbeat && `heartbeat ${options.heartbeat}`,options.detail].filter(Boolean).join(' · ') || 'Sin operación larga activa.';el.append(p);return el;
}

export function renderProgressiveEvidence(summaryText: string, bodyText: string): HTMLElement {
  const details=document.createElement('details');details.className='progressive-evidence';details.dataset.progressiveEvidence='true';
  const summary=document.createElement('summary');summary.textContent=summaryText;const body=document.createElement('pre');body.textContent=bodyText;details.append(summary,body);return details;
}

export function renderOperationalSurfaceSummary(options: OperationalSurfaceSummaryOptions): HTMLElement {
  const section=document.createElement('section');section.className='operational-patterns panel';section.dataset.uxP0D='operational-patterns';
  const head=document.createElement('div');head.className='operational-patterns__header';
  const eyebrow=document.createElement('p');eyebrow.className='operational-patterns__eyebrow';eyebrow.textContent=options.eyebrow;
  const title=document.createElement('h3');title.textContent=options.title;head.append(eyebrow,title);section.append(head);
  section.append(renderOperationState({state:options.state,title:options.stateDetail}));
  const grid=document.createElement('div');grid.className='operational-patterns__grid';
  grid.append(renderPrimaryAction(options.primaryAction));
  if(options.gate)grid.append(renderGateSummary(options.gate));
  if(options.approval)grid.append(renderApprovalSummary(options.approval));
  if(options.diff)grid.append(renderDiffSummary(options.diff));
  if(options.longRunning)grid.append(renderLongRunningOperation(options.longRunning));
  if(options.recovery){const r=document.createElement('div');r.className='recovery-summary';const h=document.createElement('strong');h.textContent='Recovery';const p=document.createElement('p');p.textContent=options.recovery;r.append(h,p);grid.append(r);}
  section.append(grid,renderProgressiveEvidence(options.evidenceSummary,options.evidenceBody)); return section;
}
