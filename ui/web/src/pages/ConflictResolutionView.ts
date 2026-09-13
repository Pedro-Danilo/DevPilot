import { DevPilotApiClient, DevPilotApiError } from '../api/client';
import type { ReconciliationReport, ReconciliationStatusData } from '../api/types';
import { renderAccessibleError, renderContextualHelp } from '../components/ContextualHelp';

const ROUTE_ID = 'ui.reconciliation';

function panel(title: string): HTMLElement {
  const el = document.createElement('article');
  el.className = 'panel reconciliation-card';
  const heading = document.createElement('h3');
  heading.textContent = title;
  el.append(heading);
  return el;
}

function fact(label: string, value: unknown): HTMLElement {
  const row = document.createElement('div');
  row.className = 'recovery-fact';
  const key = document.createElement('strong');
  key.textContent = label;
  const text = document.createElement('span');
  text.textContent = String(value ?? '—');
  row.append(key, text);
  return row;
}

function renderError(error: unknown): HTMLElement {
  const status=error instanceof DevPilotApiError?error.status:undefined;
  return renderAccessibleError({
    title:'Reconciliación bloqueada',
    plain:'DevPilot no pudo confirmar el drift actual. No se adoptó ninguna autoridad y no se ejecutó Git destructivo.',
    status,
    nextAction:'Actualice la vista una vez. Si el bloqueo continúa, preserve la evidencia y revise Recovery / Resume antes de mutar el workspace.',
    evidenceRef:'ui.reconciliation.error',
  });
}

export function renderReconciliationSummary(report: ReconciliationReport): HTMLElement {
  const wrap = document.createElement('article');
  wrap.className = 'panel reconciliation-card';
  wrap.dataset.classification = String(report.classification ?? 'READ_ONLY_BLOCK');
  const heading = document.createElement('div');
  heading.className = 'project-status-card__heading';
  const title = document.createElement('h3');
  title.textContent = 'Branch / external edits';
  const badge = document.createElement('span');
  badge.className = 'project-status-state';
  badge.textContent = String(report.classification ?? 'READ_ONLY_BLOCK');
  heading.append(title, badge);
  wrap.append(
    heading,
    fact('Causa', (report.reason_codes ?? []).join(' · ') || '—'),
    fact('Riesgo', report.risk),
    fact('HEAD relation', report.snapshot?.head_relation),
    fact('Branch', report.snapshot?.current?.branch),
    fact('Dirty', report.snapshot?.worktree_dirty === true ? 'YES' : 'NO'),
    fact('Cambios', report.snapshot?.changes?.length ?? 0),
    fact('Next action', report.recommended_next_action),
  );
  const detail = document.createElement('p');
  detail.className = 'project-status-muted';
  detail.textContent = 'DevPilot observa el drift y conserva la gobernanza; no sobrescribe archivos ni ejecuta operaciones Git destructivas automáticamente.';
  wrap.append(detail);
  const link = document.createElement('a');
  link.href = '/reconciliation';
  link.className = 'button-link';
  link.textContent = 'Abrir Conflict Resolution';
  wrap.append(link);
  const expert=document.createElement('details');expert.className='expert-only expert-authority-trace';const summary=document.createElement('summary');summary.textContent='Snapshot / authority trace';const trace=document.createElement('p');trace.textContent=`snapshot=${String(report.snapshot?.snapshot_sha256??'n/a')} · report=${String(report.report_sha256??'n/a')} · authority-invalidations=${String(report.authority_invalidations?.length??0)}`;expert.append(summary,trace);wrap.append(expert);
  return wrap;
}

function renderReport(data: ReconciliationStatusData): HTMLElement {
  const report = data.reconciliation;
  const wrap = document.createElement('div');
  wrap.className = 'recovery-grid reconciliation-grid';
  wrap.append(renderReconciliationSummary(report));

  const files = panel('Cambios observados');
  const changes = Array.isArray(report.snapshot?.changes) ? report.snapshot.changes : [];
  if (!changes.length) {
    const empty = document.createElement('p');
    empty.textContent = 'No hay cambios externos respecto del baseline actual.';
    files.append(empty);
  } else {
    const list = document.createElement('ul');
    for (const change of changes) {
      const row = document.createElement('li');
      const rename = change.old_path ? ` ← ${change.old_path}` : '';
      row.textContent = `${change.kind} · ${change.path}${rename} · authority=${change.linked_to_engineering_authority === true ? 'YES' : 'NO'}`;
      list.append(row);
    }
    files.append(list);
  }

  const authority = panel('Authority / drafts');
  const invalidations = Array.isArray(report.authority_invalidations) ? report.authority_invalidations : [];
  authority.append(
    fact('Invalidaciones', invalidations.length ? invalidations.map((row) => `${row.authority}:${row.state}`).join(', ') : 'NONE'),
    fact('Drafts preservados', report.draft_recovery?.drafts_preserved === true ? 'YES' : 'BLOCK'),
    fact('Draft refs', (report.draft_recovery?.draft_refs ?? []).join(', ') || '—'),
  );

  const plan = panel('Plan seguro');
  const ul = document.createElement('ol');
  for (const step of report.safe_recovery_plan ?? []) {
    const li = document.createElement('li');
    li.textContent = String(step);
    ul.append(li);
  }
  plan.append(ul);
  const prohibited = document.createElement('p');
  prohibited.className = 'project-status-muted';
  prohibited.textContent = `Operaciones automáticas prohibidas: ${(report.forbidden_automatic_git_operations ?? []).join(', ')}`;
  plan.append(prohibited);
  wrap.append(files, authority, plan);
  return wrap;
}

export function renderConflictResolutionView(tokenProvider: () => string | null): HTMLElement {
  const root = document.createElement('section');
  root.className = 'reconciliation-view';
  root.dataset.uiRouteId = ROUTE_ID;
  const title = document.createElement('h2');
  title.textContent = 'Conflict Resolution';
  const intro = document.createElement('p');
  intro.textContent = 'Revisa branch, HEAD y cambios externos antes de continuar. Las adopciones son dry-run por defecto y solo actualizan metadata de autoridad después de una confirmación humana explícita.';
  const legend = document.createElement('p');
  legend.className = 'project-status-muted';
  legend.textContent = 'Estados: NO_CONFLICT · REVALIDATE · REPLAN_REQUIRED · MANUAL_RECONCILIATION_REQUIRED · READ_ONLY_BLOCK.';
  const help=renderContextualHelp({
    title:'Ayuda para conflictos externos',
    plain:'Esta vista explica qué cambió fuera de DevPilot y si puede revalidarse o necesita reconciliación manual.',
    technical:'La observación Git/filesystem es read-only. Guided/Expert comparten el mismo servicio, locks y policy; Expert solo expone hashes/IDs adicionales.',
    nextAction:'Revise causa, riesgo y archivos observados. Use primero dry-run y nunca resuelva un conflicto ocultándolo.',
    evidenceRef:'ui.reconciliation',
  });
  const controls = document.createElement('div');
  controls.className = 'recovery-controls';
  controls.setAttribute('aria-label','Controles de reconciliación');
  const refresh = document.createElement('button'); refresh.type='button'; refresh.textContent = 'Actualizar drift';
  const baselineDry = document.createElement('button'); baselineDry.type='button'; baselineDry.textContent = 'Dry-run baseline';
  const baselineApply = document.createElement('button'); baselineApply.type='button'; baselineApply.textContent = 'Capturar baseline revisado';
  const adoptDry = document.createElement('button'); adoptDry.type='button'; adoptDry.textContent = 'Dry-run adopción';
  const adoptApply = document.createElement('button'); adoptApply.type='button'; adoptApply.textContent = 'Adoptar autoridad revisada';
  controls.append(refresh, baselineDry, baselineApply, adoptDry, adoptApply);
  const content = document.createElement('div');
  content.className='reconciliation-content';
  content.setAttribute('role','status');
  content.setAttribute('aria-live','polite');
  content.setAttribute('aria-atomic','false');
  root.append(title, intro, legend, help, controls, content);
  const api = () => new DevPilotApiClient({ token: tokenProvider() });
  const load = async () => {
    content.setAttribute('aria-busy','true');
    try {
      const response = await api().reconciliationStatus();
      content.replaceChildren(renderReport(response.data));
    } catch (error) {
      content.replaceChildren(renderError(error));
    } finally { content.setAttribute('aria-busy','false'); }
  };
  const mutation = async (kind: 'baseline'|'adopt', execute: boolean) => {
    try {
      if (kind === 'baseline') await api().reconciliationBaseline(execute, execute ? 'CAPTURE_RECONCILIATION_BASELINE' : '');
      else await api().reconciliationAdopt(execute, execute ? 'ADOPT_RECONCILIATION_BASELINE' : '');
      await load();
    } catch (error) {
      content.replaceChildren(renderError(error));
    }
  };
  refresh.onclick = () => void load();
  baselineDry.onclick = () => void mutation('baseline', false);
  baselineApply.onclick = () => void mutation('baseline', true);
  adoptDry.onclick = () => void mutation('adopt', false);
  adoptApply.onclick = () => void mutation('adopt', true);
  void load();
  return root;
}
