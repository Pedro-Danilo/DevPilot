import { DevPilotApiClient, DevPilotApiError } from '../api/client';
import type { ReconciliationReport, ReconciliationStatusData } from '../api/types';

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
  const el = panel('Reconciliación bloqueada');
  const p = document.createElement('p');
  p.textContent = error instanceof DevPilotApiError ? error.message : error instanceof Error ? error.message : String(error);
  el.append(p);
  return el;
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
  root.setAttribute('aria-live', 'polite');
  const title = document.createElement('h2');
  title.textContent = 'Conflict Resolution';
  const intro = document.createElement('p');
  intro.textContent = 'Revisa branch, HEAD y cambios externos antes de continuar. Las adopciones son dry-run por defecto y solo actualizan metadata de autoridad después de una confirmación humana explícita.';
  const legend = document.createElement('p');
  legend.className = 'project-status-muted';
  legend.textContent = 'Estados: NO_CONFLICT · REVALIDATE · REPLAN_REQUIRED · MANUAL_RECONCILIATION_REQUIRED · READ_ONLY_BLOCK.';
  const controls = document.createElement('div');
  controls.className = 'recovery-controls';
  const refresh = document.createElement('button');
  refresh.textContent = 'Actualizar drift';
  const baselineDry = document.createElement('button');
  baselineDry.textContent = 'Dry-run baseline';
  const baselineApply = document.createElement('button');
  baselineApply.textContent = 'Capturar baseline revisado';
  const adoptDry = document.createElement('button');
  adoptDry.textContent = 'Dry-run adopción';
  const adoptApply = document.createElement('button');
  adoptApply.textContent = 'Adoptar autoridad revisada';
  controls.append(refresh, baselineDry, baselineApply, adoptDry, adoptApply);
  const content = document.createElement('div');
  root.append(title, intro, legend, controls, content);
  const api = () => new DevPilotApiClient({ token: tokenProvider() });
  const load = async () => {
    try {
      const response = await api().reconciliationStatus();
      content.replaceChildren(renderReport(response.data));
    } catch (error) {
      content.replaceChildren(renderError(error));
    }
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
