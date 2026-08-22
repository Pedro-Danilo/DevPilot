import type { AuthBootstrapStatus, AuthSessionContext, AuthSessionEnvelope, AuthSessionStatus, DevPilotApplicationResponse, GuidedSdlcProjectStatusResponseData, OperatorDashboardResponseData } from './types';

export const DEFAULT_API_BASE = 'http://127.0.0.1:8787/api/v1';
export const TOKEN_STORAGE_KEY = 'devpilot.apiToken';
export const TOKEN_STORED_AT_KEY = 'devpilot.apiTokenStoredAt';
export const TOKEN_SESSION_TTL_MS = 8 * 60 * 60 * 1000;
export const PROJECT_JOURNEY_CONTEXT_KEY = 'devpilot.gsdlc03e.projectJourneyContext.v1';
export const APPROVAL_CENTER_ENTRY_HANDOFF_KEY = 'devpilot.gsdlc03e.approvalCenterEntryHandoff.v1';
export const APPROVAL_CENTER_ENTRY_HANDOFF_TTL_MS = 30 * 60 * 1000;
export const PROJECT_ENTRY_RESUME_STATE_KEY = 'devpilot.gsdlc03e.projectEntryResumeState.v1';
export const PROJECT_ENTRY_RESUME_TTL_MS = 30 * 60 * 1000;

export type ProjectJourneyPhase = 'entry' | 'project';
export type ProjectEntryMode = 'CREATE_NEW' | 'OPEN_EXISTING' | 'IMPORT_GIT';

export interface ProjectJourneyContext {
  phase: ProjectJourneyPhase;
  entry_mode?: ProjectEntryMode;
  project_id?: string;
  target_root?: string;
  activated_at?: string;
}

export interface ProjectEntryResumeState {
  phase: 'entry';
  entry_mode: ProjectEntryMode;
  actor_id: string;
  session_created_at: string;
  intake: Record<string, unknown>;
  dry_run: Record<string, unknown>;
  bootstrap_plan: Record<string, unknown>;
  plan_hash: string;
  preimage_hash: string;
  approval_id?: string;
  created_at_ms: number;
  updated_at_ms: number;
  expires_at_ms: number;
}

interface ApprovalCenterEntryHandoff {
  phase: 'entry';
  entry_mode: ProjectEntryMode;
  approval_id: string;
  actor_id: string;
  session_created_at: string;
  created_at_ms: number;
  expires_at_ms: number;
}
export const DEFAULT_REQUEST_TIMEOUT_MS = 8000;
export const PROTECTED_WARMUP_TIMEOUT_MS = 15000;
export const REPORTS_REQUEST_TIMEOUT_MS = 15000;
export const READINESS_REQUEST_TIMEOUT_MS = 30000;
export const PROVIDER_SETTINGS_READ_TIMEOUT_MS = 45000;
export const ACTION_DRY_RUN_TIMEOUT_MS = 60000;
export const PROJECT_ENTRY_PROBE_TIMEOUT_SECONDS = 8.0;
export const PROJECT_ENTRY_PLANNING_TIMEOUT_MS = 90000;
export const PROJECT_ENTRY_EXECUTION_TIMEOUT_MS = 240000;
export const APPROVAL_CENTER_READ_TIMEOUT_MS = 30000;
export const APPROVAL_CENTER_DECISION_TIMEOUT_MS = 30000;
export const MAX_REQUEST_TIMEOUT_MS = PROJECT_ENTRY_EXECUTION_TIMEOUT_MS;
export const PROVIDER_PLAN_TIMEOUT_MS = 60000;
// Compatibility alias retained for older static contracts. New code must use the operation-specific constants above.
export const EXPENSIVE_REQUEST_TIMEOUT_MS = READINESS_REQUEST_TIMEOUT_MS;
export const TRANSIENT_NETWORK_RETRY_DELAYS_MS = [500, 1000] as const;

export class DevPilotApiError extends Error {
  readonly status: number;
  readonly payload: unknown;
  readonly endpoint: string;
  readonly durationMs: number;

  constructor(message: string, status: number, payload: unknown, endpoint = '', durationMs = 0) {
    super(message);
    this.name = 'DevPilotApiError';
    this.status = status;
    this.payload = payload;
    this.endpoint = endpoint;
    this.durationMs = durationMs;
  }
}

export interface DevPilotApiClientOptions {
  baseUrl?: string;
  token?: string;
  requestTimeoutMs?: number;
}

interface RequestPolicy {
  timeoutMs?: number;
  retryNetworkErrors?: boolean;
  retryDelaysMs?: readonly number[];
}

export class DevPilotApiClient {
  readonly baseUrl: string;
  readonly token: string;
  readonly requestTimeoutMs: number;

  constructor(options: DevPilotApiClientOptions = {}) {
    this.baseUrl = (options.baseUrl ?? DEFAULT_API_BASE).replace(/\/$/, '');
    this.token = options.token ?? readStoredToken();
    this.requestTimeoutMs = normalizeTimeout(options.requestTimeoutMs);
  }


  async authBootstrapStatus(): Promise<AuthBootstrapStatus> {
    return this.authJson<AuthBootstrapStatus>('/auth/bootstrap/status', { method: 'GET' });
  }

  async authSessionStatus(): Promise<AuthSessionStatus> {
    return this.authJson<AuthSessionStatus>('/auth/session/status', { method: 'GET' });
  }

  async authSession(): Promise<AuthSessionEnvelope> {
    return this.authJson<AuthSessionEnvelope>('/auth/session', { method: 'GET' });
  }

  async authBootstrapOwner(payload: { username: string; display_name: string; password: string }): Promise<AuthSessionEnvelope> {
    return this.authJson<AuthSessionEnvelope>('/auth/bootstrap/owner', { method: 'POST', body: JSON.stringify(payload), headers: { 'Content-Type': 'application/json' } });
  }

  async authLogin(payload: { username: string; password: string }): Promise<AuthSessionEnvelope> {
    return this.authJson<AuthSessionEnvelope>('/auth/login', { method: 'POST', body: JSON.stringify(payload), headers: { 'Content-Type': 'application/json' } });
  }

  async authLogout(): Promise<{ ok: boolean; revoked: boolean; reason?: string }> {
    return this.authJson('/auth/logout', { method: 'POST', body: '{}' });
  }

  async authRevokeCurrent(): Promise<{ ok: boolean; revoked: boolean }> {
    return this.authJson('/auth/session/revoke', { method: 'POST', body: '{}' });
  }

  async health(): Promise<DevPilotApplicationResponse> {
    return this.get('/health', { timeoutMs: 5000, retryNetworkErrors: true });
  }

  async protectedWarmup(): Promise<DevPilotApplicationResponse> {
    return this.get('/workspace/status', {
      timeoutMs: PROTECTED_WARMUP_TIMEOUT_MS,
      retryNetworkErrors: true,
    });
  }

  async workspaceStatus(): Promise<DevPilotApplicationResponse> {
    return this.get('/workspace/status', { retryNetworkErrors: true });
  }

  async applicationContract(): Promise<DevPilotApplicationResponse> {
    return this.get('/application/contract', { retryNetworkErrors: true });
  }

  async standardsStatus(): Promise<DevPilotApplicationResponse> {
    return this.get('/standards/status', { retryNetworkErrors: true });
  }

  async miasiStatus(): Promise<DevPilotApplicationResponse> {
    return this.get('/miasi/status', { retryNetworkErrors: true });
  }

  async readiness(strict = true): Promise<DevPilotApplicationResponse> {
    return this.post('/validation/readiness', {
      operation: 'validation.readiness',
      payload: { strict },
      dry_run: true,
    }, {
      timeoutMs: READINESS_REQUEST_TIMEOUT_MS,
      retryNetworkErrors: true,
    });
  }

  async listReports(filters: { limit?: number; offset?: number; severity?: string; status?: string; command?: string; query?: string; scope?: string } = {}): Promise<DevPilotApplicationResponse> {
    return this.get(`/reports${this.query(filters)}`, {
      timeoutMs: REPORTS_REQUEST_TIMEOUT_MS,
      retryNetworkErrors: true,
    });
  }

  async readReport(reportId: string, format = 'json'): Promise<DevPilotApplicationResponse> {
    return this.get(`/reports/${encodeURIComponent(reportId)}${this.query({ format })}`, { timeoutMs: REPORTS_REQUEST_TIMEOUT_MS });
  }

  async listTraces(limit = 20, scope = 'active'): Promise<DevPilotApplicationResponse> {
    return this.get(`/traces${this.query({ limit, scope })}`);
  }

  async inspectTrace(traceId: string, limit = 100, scope = 'active'): Promise<DevPilotApplicationResponse> {
    return this.get(`/traces/${encodeURIComponent(traceId)}${this.query({ limit, scope })}`);
  }

  async metricsSummary(scope = 'active'): Promise<DevPilotApplicationResponse> {
    return this.get(`/metrics/summary${this.query({ scope })}`);
  }

  async portfolioStatus(): Promise<DevPilotApplicationResponse> {
    return this.get('/portfolio/status', { retryNetworkErrors: true });
  }

  async projectStatus(filters: { workspace_id?: string; expected_state_fingerprint?: string } = {}): Promise<DevPilotApplicationResponse<GuidedSdlcProjectStatusResponseData>> {
    return this.get(`/guided-sdlc/status${this.query(filters)}`, { retryNetworkErrors: true }) as unknown as Promise<DevPilotApplicationResponse<GuidedSdlcProjectStatusResponseData>>;
  }



  async projectEntryDryRun(payload: { intake: Record<string, unknown>; timeout_seconds?: number }): Promise<DevPilotApplicationResponse> {
    return this.post('/project-entry/dry-run', { intake: payload.intake, timeout_seconds: payload.timeout_seconds ?? PROJECT_ENTRY_PROBE_TIMEOUT_SECONDS }, { timeoutMs: PROJECT_ENTRY_PLANNING_TIMEOUT_MS });
  }

  async projectEntryRevalidate(payload: { intake: Record<string, unknown>; expected_plan_hash: string; expected_preimage_hash: string; timeout_seconds?: number }): Promise<DevPilotApplicationResponse> {
    return this.post('/project-entry/revalidate', { ...payload, timeout_seconds: payload.timeout_seconds ?? PROJECT_ENTRY_PROBE_TIMEOUT_SECONDS }, { timeoutMs: PROJECT_ENTRY_PLANNING_TIMEOUT_MS });
  }

  async projectEntryRequestExecutionApproval(payload: { intake: Record<string, unknown>; expected_plan_hash: string; expected_preimage_hash: string; reason?: string; ttl_minutes?: number; timeout_seconds?: number }): Promise<DevPilotApplicationResponse> {
    return this.post('/project-entry/execution-approval-request', { ...payload, reason: payload.reason ?? 'Execute reviewed GSDLC-03-D bootstrap plan.', ttl_minutes: payload.ttl_minutes ?? 30, timeout_seconds: payload.timeout_seconds ?? PROJECT_ENTRY_PROBE_TIMEOUT_SECONDS }, { timeoutMs: PROJECT_ENTRY_PLANNING_TIMEOUT_MS });
  }

  async projectEntryExecute(payload: { intake: Record<string, unknown>; expected_plan_hash: string; expected_preimage_hash: string; approval_id: string; dependency_mode?: string; fault_stage?: string; timeout_seconds?: number }): Promise<DevPilotApplicationResponse> {
    try {
      return await this.post(
        '/project-entry/execute',
        { ...payload, dependency_mode: payload.dependency_mode ?? 'defer-network', timeout_seconds: payload.timeout_seconds ?? PROJECT_ENTRY_PROBE_TIMEOUT_SECONDS },
        { timeoutMs: PROJECT_ENTRY_EXECUTION_TIMEOUT_MS },
      );
    } catch (error) {
      if (error instanceof DevPilotApiError && error.status === 408) {
        throw new DevPilotApiError(
          'La ejecución excedió el presupuesto UI. El estado server-side es incierto: no vuelvas a ejecutar hasta reconciliar el workspace.',
          408,
          { state: 'execution_unknown', action: 'reconcile_before_retry', timeout_ms: PROJECT_ENTRY_EXECUTION_TIMEOUT_MS },
          '/project-entry/execute',
          error.durationMs,
        );
      }
      throw error;
    }
  }

  async authCapabilities(workspaceId = 'devpilot-local'): Promise<DevPilotApplicationResponse> {
    return this.get(`/auth/capabilities${this.query({ workspace_id: workspaceId })}`, { retryNetworkErrors: true });
  }

  async listApprovals(filters: { status?: string; limit?: number } = {}): Promise<DevPilotApplicationResponse> {
    return this.get(`/approvals${this.query(filters)}`, { timeoutMs: APPROVAL_CENTER_READ_TIMEOUT_MS, retryNetworkErrors: true });
  }

  async showApproval(approvalId: string): Promise<DevPilotApplicationResponse> {
    return this.get(`/approvals/${encodeURIComponent(approvalId)}`, { timeoutMs: APPROVAL_CENTER_READ_TIMEOUT_MS, retryNetworkErrors: true });
  }

  async requestApproval(payload: { tool_id: string; action: string; subject: string; actor?: string; reason: string; scope?: string; ttl_minutes?: number }): Promise<DevPilotApplicationResponse> {
    return this.post('/approvals/request', payload, { timeoutMs: APPROVAL_CENTER_DECISION_TIMEOUT_MS });
  }

  async decideApproval(approvalId: string, decision: 'approve' | 'deny', payload: { actor?: string; reason: string }): Promise<DevPilotApplicationResponse> {
    return this.post(`/approvals/${encodeURIComponent(approvalId)}/${decision}`, payload, { timeoutMs: APPROVAL_CENTER_DECISION_TIMEOUT_MS });
  }

  async runDryRunAction(payload: { action_id: string; target?: string; goal?: string; strict?: boolean; include_code_review?: boolean }): Promise<DevPilotApplicationResponse> {
    return this.post('/actions/dry-run', payload, {
      timeoutMs: ACTION_DRY_RUN_TIMEOUT_MS,
    });
  }

  async settingsWorkspace(): Promise<DevPilotApplicationResponse> {
    return this.get('/settings/workspace', { retryNetworkErrors: true });
  }

  async settingsProviders(): Promise<DevPilotApplicationResponse> {
    return this.get('/settings/providers', {
      timeoutMs: PROVIDER_SETTINGS_READ_TIMEOUT_MS,
      retryNetworkErrors: true,
    });
  }

  async settingsPolicy(): Promise<DevPilotApplicationResponse> {
    return this.get('/settings/policy', { retryNetworkErrors: true });
  }

  async securityPosture(): Promise<DevPilotApplicationResponse> {
    return this.get('/security/posture', { retryNetworkErrors: true });
  }

  async operatorDashboard(writeReport = false): Promise<DevPilotApplicationResponse<OperatorDashboardResponseData>> {
    return this.get(`/operator/dashboard${this.query({ write_report: writeReport })}`, { retryNetworkErrors: true });
  }

  async planProviderChange(payload: { provider_id: string; changes: Record<string, unknown>; actor?: string; reason?: string }): Promise<DevPilotApplicationResponse> {
    return this.post('/settings/providers/plan', payload, {
      timeoutMs: PROVIDER_PLAN_TIMEOUT_MS,
    });
  }

  async listJobs(filters: { workspace_id?: string; capability_id?: string; status?: string; limit?: number; offset?: number } = {}): Promise<DevPilotApplicationResponse> {
    return this.get(`/jobs${this.query(filters)}`, { timeoutMs: REPORTS_REQUEST_TIMEOUT_MS, retryNetworkErrors: true });
  }

  async inspectJob(jobId: string): Promise<DevPilotApplicationResponse> {
    return this.get(`/jobs/${encodeURIComponent(jobId)}`, { timeoutMs: REPORTS_REQUEST_TIMEOUT_MS });
  }

  async jobLogs(jobId: string, cursor = 0, limit = 100): Promise<DevPilotApplicationResponse> {
    return this.get(`/jobs/${encodeURIComponent(jobId)}/logs${this.query({ cursor, limit })}`, { timeoutMs: REPORTS_REQUEST_TIMEOUT_MS });
  }

  async cancelJob(jobId: string, payload: { actor: string; reason: string }): Promise<DevPilotApplicationResponse> {
    return this.post(`/jobs/${encodeURIComponent(jobId)}/cancel`, payload, { timeoutMs: REPORTS_REQUEST_TIMEOUT_MS });
  }

  async retryJob(jobId: string, payload: { actor: string; reason: string }): Promise<DevPilotApplicationResponse> {
    return this.post(`/jobs/${encodeURIComponent(jobId)}/retry`, payload, { timeoutMs: REPORTS_REQUEST_TIMEOUT_MS });
  }

  async qualityOperations(): Promise<DevPilotApplicationResponse> {
    return this.get('/quality/operations', { timeoutMs: REPORTS_REQUEST_TIMEOUT_MS, retryNetworkErrors: true });
  }

  async qualityBaseline(): Promise<DevPilotApplicationResponse> {
    return this.get('/quality/baseline', { timeoutMs: REPORTS_REQUEST_TIMEOUT_MS, retryNetworkErrors: true });
  }

  async qualityTestImpact(changedPaths: string[]): Promise<DevPilotApplicationResponse> {
    return this.post('/quality/test-impact/plan', { changed_paths: changedPaths }, { timeoutMs: READINESS_REQUEST_TIMEOUT_MS });
  }

  async qualityPlanJob(payload: { operation_id: string; workspace_id: string; parameters: Record<string, unknown>; idempotency_key: string; approval_id?: string; full_regression_confirmation?: string }): Promise<DevPilotApplicationResponse> {
    return this.post('/quality/jobs/plan', payload, { timeoutMs: READINESS_REQUEST_TIMEOUT_MS });
  }

  async qualityExecuteJob(jobId: string): Promise<DevPilotApplicationResponse> {
    return this.post(`/quality/jobs/${encodeURIComponent(jobId)}/execute`, {}, { timeoutMs: READINESS_REQUEST_TIMEOUT_MS });
  }

  async qualityEvidencePackage(limit = 100): Promise<DevPilotApplicationResponse> {
    return this.post('/quality/evidence/package', { limit }, { timeoutMs: READINESS_REQUEST_TIMEOUT_MS });
  }

  async aiOperations(): Promise<DevPilotApplicationResponse> {
    return this.get('/ai/operations', { timeoutMs: READINESS_REQUEST_TIMEOUT_MS });
  }

  async aiStatus(): Promise<DevPilotApplicationResponse> {
    return this.get('/ai/status', { timeoutMs: READINESS_REQUEST_TIMEOUT_MS });
  }

  async aiPlanJob(payload: { operation_id: string; workspace_id: string; parameters: Record<string, unknown>; idempotency_key: string; approval_id?: string }): Promise<DevPilotApplicationResponse> {
    return this.post('/ai/jobs/plan', payload, { timeoutMs: READINESS_REQUEST_TIMEOUT_MS });
  }

  async aiExecuteJob(jobId: string): Promise<DevPilotApplicationResponse> {
    return this.post(`/ai/jobs/${encodeURIComponent(jobId)}/execute`, {}, { timeoutMs: READINESS_REQUEST_TIMEOUT_MS });
  }

  async aiJobResult(jobId: string): Promise<DevPilotApplicationResponse> {
    return this.get(`/ai/jobs/${encodeURIComponent(jobId)}/result`, { timeoutMs: READINESS_REQUEST_TIMEOUT_MS });
  }

  async aiEvidencePackage(limit = 100): Promise<DevPilotApplicationResponse> {
    return this.post('/ai/evidence/package', { limit }, { timeoutMs: READINESS_REQUEST_TIMEOUT_MS });
  }

  async listWorkspaceDocuments(filters: { limit?: number; offset?: number; query?: string; extension?: string; category?: string } = {}): Promise<DevPilotApplicationResponse> {
    return this.get(`/workspace/documents${this.query(filters)}`, { timeoutMs: REPORTS_REQUEST_TIMEOUT_MS, retryNetworkErrors: true });
  }

  async readWorkspaceDocument(documentId: string): Promise<DevPilotApplicationResponse> {
    return this.get(`/workspace/documents/${encodeURIComponent(documentId)}`, { timeoutMs: REPORTS_REQUEST_TIMEOUT_MS });
  }

  async workspaceDocumentMetadata(documentId: string): Promise<DevPilotApplicationResponse> {
    return this.get(`/workspace/documents/${encodeURIComponent(documentId)}/metadata`, { timeoutMs: REPORTS_REQUEST_TIMEOUT_MS });
  }

  async workspaceDocumentHistory(documentId: string, limit = 20, offset = 0): Promise<DevPilotApplicationResponse> {
    return this.get(`/workspace/documents/${encodeURIComponent(documentId)}/history${this.query({ limit, offset })}`, { timeoutMs: REPORTS_REQUEST_TIMEOUT_MS });
  }

  async workspaceDocumentDiff(documentId: string, baseRef = 'HEAD', maxBytes = 262144): Promise<DevPilotApplicationResponse> {
    return this.get(`/workspace/documents/${encodeURIComponent(documentId)}/diff${this.query({ base_ref: baseRef, max_bytes: maxBytes })}`, { timeoutMs: REPORTS_REQUEST_TIMEOUT_MS });
  }

  async workspaceDocumentLinks(documentId: string): Promise<DevPilotApplicationResponse> {
    return this.get(`/workspace/documents/${encodeURIComponent(documentId)}/links`, { timeoutMs: REPORTS_REQUEST_TIMEOUT_MS });
  }

  async searchWorkspaceDocuments(query: string, limit = 50, offset = 0): Promise<DevPilotApplicationResponse> {
    return this.get(`/workspace/documents/search${this.query({ query, limit, offset })}`, { timeoutMs: REPORTS_REQUEST_TIMEOUT_MS, retryNetworkErrors: true });
  }

  async artifactDraft(documentId: string): Promise<DevPilotApplicationResponse> {
    return this.get(`/workspace/artifact-drafts/${encodeURIComponent(documentId)}`, { timeoutMs: REPORTS_REQUEST_TIMEOUT_MS });
  }

  async artifactDraftHistory(documentId: string): Promise<DevPilotApplicationResponse> {
    return this.get(`/workspace/artifact-drafts/${encodeURIComponent(documentId)}/history`, { timeoutMs: REPORTS_REQUEST_TIMEOUT_MS });
  }

  async saveArtifactDraft(documentId: string, payload: { content: string; expected_source_sha256: string; expected_revision_sha256?: string | null; event?: 'SAVE' | 'AUTOSAVE' }): Promise<DevPilotApplicationResponse> {
    return this.post(`/workspace/artifact-drafts/${encodeURIComponent(documentId)}/save`, payload, { timeoutMs: READINESS_REQUEST_TIMEOUT_MS });
  }

  async discardArtifactDraft(documentId: string, payload: { expected_source_sha256: string; expected_revision_sha256?: string | null }): Promise<DevPilotApplicationResponse> {
    return this.post(`/workspace/artifact-drafts/${encodeURIComponent(documentId)}/discard`, payload, { timeoutMs: READINESS_REQUEST_TIMEOUT_MS });
  }

  async recoverArtifactDraft(documentId: string, payload: { revision_sha256: string; expected_source_sha256: string; expected_revision_sha256?: string | null }): Promise<DevPilotApplicationResponse> {
    return this.post(`/workspace/artifact-drafts/${encodeURIComponent(documentId)}/recover`, payload, { timeoutMs: READINESS_REQUEST_TIMEOUT_MS });
  }

  async previewArtifactImport(payload: { source_type: 'PASTE' | 'UPLOAD' | 'IMPORT'; destination_path: string; source_label?: string | null; source_reference?: string | null; original_filename?: string | null; declared_mime?: string | null; text_content?: string | null; content_base64?: string | null }): Promise<DevPilotApplicationResponse> {
    return this.post('/workspace/artifact-imports/preview', payload, { timeoutMs: READINESS_REQUEST_TIMEOUT_MS });
  }

  async persistArtifactImport(payload: { source_type: 'PASTE' | 'UPLOAD' | 'IMPORT'; destination_path: string; expected_preview_sha256: string; source_label?: string | null; source_reference?: string | null; original_filename?: string | null; declared_mime?: string | null; text_content?: string | null; content_base64?: string | null }): Promise<DevPilotApplicationResponse> {
    return this.post('/workspace/artifact-imports/persist', payload, { timeoutMs: READINESS_REQUEST_TIMEOUT_MS });
  }

  async recentArtifactImports(limit = 20): Promise<DevPilotApplicationResponse> {
    return this.get(`/workspace/artifact-imports/recent${this.query({ limit })}`, { timeoutMs: REPORTS_REQUEST_TIMEOUT_MS });
  }

  async planWorkspaceValidations(payload: { scopes?: string[]; document_ids?: string[]; strict?: boolean; timeout_seconds?: number } = {}): Promise<DevPilotApplicationResponse> {
    return this.post('/workspace/validations/plan', {
      operation: 'workspace.validations.plan',
      payload,
      dry_run: true,
    }, { timeoutMs: READINESS_REQUEST_TIMEOUT_MS, retryNetworkErrors: true });
  }

  async executeWorkspaceValidations(payload: { plan_id: string; plan_hash: string; plan: Record<string, unknown> }): Promise<DevPilotApplicationResponse> {
    return this.post('/workspace/validations/execute', {
      operation: 'workspace.validations.execute',
      payload,
      dry_run: false,
    }, { timeoutMs: 120000 });
  }

  async workspaceValidationStatus(jobId: string): Promise<DevPilotApplicationResponse> {
    return this.get(`/workspace/validations/${encodeURIComponent(jobId)}`, { timeoutMs: REPORTS_REQUEST_TIMEOUT_MS });
  }

  async workspaceTraceability(): Promise<DevPilotApplicationResponse> {
    return this.get('/workspace/traceability', { timeoutMs: READINESS_REQUEST_TIMEOUT_MS, retryNetworkErrors: true });
  }

  async planWorkspaceEdit(payload: { document_id: string; document_sha_before: string; proposed_content: string }): Promise<DevPilotApplicationResponse> {
    return this.post('/workspace/edit-plans/plan', { operation: 'workspace.edits.plan', payload, dry_run: true }, { timeoutMs: READINESS_REQUEST_TIMEOUT_MS });
  }

  async workspaceEditPlanStatus(planId: string): Promise<DevPilotApplicationResponse> {
    return this.get(`/workspace/edit-plans/${encodeURIComponent(planId)}`, { timeoutMs: REPORTS_REQUEST_TIMEOUT_MS });
  }

  async recheckWorkspaceEditPlan(planId: string, planHash: string): Promise<DevPilotApplicationResponse> {
    return this.post(`/workspace/edit-plans/${encodeURIComponent(planId)}/recheck`, { operation: 'workspace.edits.recheck', payload: { plan_hash: planHash }, dry_run: true }, { timeoutMs: READINESS_REQUEST_TIMEOUT_MS });
  }

  async requestWorkspaceEditApplyApproval(planId: string, payload: { plan_hash: string; actor: string; reason: string; ttl_minutes?: number }): Promise<DevPilotApplicationResponse> {
    return this.post(`/workspace/edit-plans/${encodeURIComponent(planId)}/approval-request`, payload, { timeoutMs: READINESS_REQUEST_TIMEOUT_MS });
  }

  async applyWorkspaceEdit(planId: string, payload: { plan_hash: string; approval_id: string; actor: string }): Promise<DevPilotApplicationResponse> {
    return this.post(`/workspace/edit-plans/${encodeURIComponent(planId)}/apply`, payload, { timeoutMs: READINESS_REQUEST_TIMEOUT_MS });
  }

  async workspaceEditExecutionStatus(executionId: string): Promise<DevPilotApplicationResponse> {
    return this.get(`/workspace/edit-executions/${encodeURIComponent(executionId)}`, { timeoutMs: REPORTS_REQUEST_TIMEOUT_MS });
  }

  async requestWorkspaceEditRollbackApproval(executionId: string, payload: { actor: string; reason: string; ttl_minutes?: number }): Promise<DevPilotApplicationResponse> {
    return this.post(`/workspace/edit-executions/${encodeURIComponent(executionId)}/rollback-approval-request`, payload, { timeoutMs: READINESS_REQUEST_TIMEOUT_MS });
  }

  async rollbackWorkspaceEdit(executionId: string, payload: { approval_id: string; actor: string }): Promise<DevPilotApplicationResponse> {
    return this.post(`/workspace/edit-executions/${encodeURIComponent(executionId)}/rollback`, payload, { timeoutMs: READINESS_REQUEST_TIMEOUT_MS });
  }

  async workspaceGitStatus(): Promise<DevPilotApplicationResponse> {
    return this.get('/workspace/git/status', { timeoutMs: REPORTS_REQUEST_TIMEOUT_MS, retryNetworkErrors: true });
  }

  async workspaceGitHistory(limit = 20): Promise<DevPilotApplicationResponse> {
    return this.get(`/workspace/git/history${this.query({ limit })}`, { timeoutMs: REPORTS_REQUEST_TIMEOUT_MS });
  }

  async workspaceGitCompare(baseRef = 'HEAD', headRef = 'HEAD'): Promise<DevPilotApplicationResponse> {
    return this.get(`/workspace/git/compare${this.query({ base_ref: baseRef, head_ref: headRef })}`, { timeoutMs: REPORTS_REQUEST_TIMEOUT_MS });
  }

  async planWorkspaceGitCommit(payload: { document_ids: string[]; commit_message: string; author_name: string; author_email: string }): Promise<DevPilotApplicationResponse> {
    return this.post('/workspace/git/plans', payload, { timeoutMs: READINESS_REQUEST_TIMEOUT_MS });
  }

  async workspaceGitPlanStatus(planId: string): Promise<DevPilotApplicationResponse> {
    return this.get(`/workspace/git/plans/${encodeURIComponent(planId)}`, { timeoutMs: REPORTS_REQUEST_TIMEOUT_MS });
  }

  async requestWorkspaceGitStageApproval(planId: string, payload: { plan_hash: string; actor: string; reason: string; ttl_minutes?: number }): Promise<DevPilotApplicationResponse> {
    return this.post(`/workspace/git/plans/${encodeURIComponent(planId)}/stage-approval-request`, payload, { timeoutMs: READINESS_REQUEST_TIMEOUT_MS });
  }

  async stageWorkspaceGitPlan(planId: string, payload: { plan_hash: string; approval_id: string; actor: string }): Promise<DevPilotApplicationResponse> {
    return this.post(`/workspace/git/plans/${encodeURIComponent(planId)}/stage`, payload, { timeoutMs: READINESS_REQUEST_TIMEOUT_MS });
  }

  async workspaceGitExecutionStatus(executionId: string): Promise<DevPilotApplicationResponse> {
    return this.get(`/workspace/git/executions/${encodeURIComponent(executionId)}`, { timeoutMs: REPORTS_REQUEST_TIMEOUT_MS });
  }

  async requestWorkspaceGitCommitApproval(executionId: string, payload: { actor: string; reason: string; ttl_minutes?: number }): Promise<DevPilotApplicationResponse> {
    return this.post(`/workspace/git/stage-executions/${encodeURIComponent(executionId)}/commit-approval-request`, payload, { timeoutMs: READINESS_REQUEST_TIMEOUT_MS });
  }

  async commitWorkspaceGitExecution(executionId: string, payload: { approval_id: string; actor: string }): Promise<DevPilotApplicationResponse> {
    return this.post(`/workspace/git/stage-executions/${encodeURIComponent(executionId)}/commit`, payload, { timeoutMs: READINESS_REQUEST_TIMEOUT_MS });
  }

  async planWorkspaceGitBranch(branchName: string): Promise<DevPilotApplicationResponse> {
    return this.post('/workspace/git/branches/plan', { branch_name: branchName }, { timeoutMs: READINESS_REQUEST_TIMEOUT_MS });
  }

  async requestWorkspaceGitBranchApproval(planId: string, payload: { plan_hash: string; actor: string; reason: string; ttl_minutes?: number }): Promise<DevPilotApplicationResponse> {
    return this.post(`/workspace/git/branches/${encodeURIComponent(planId)}/approval-request`, payload, { timeoutMs: READINESS_REQUEST_TIMEOUT_MS });
  }

  async createWorkspaceGitBranch(planId: string, payload: { plan_hash: string; approval_id: string; actor: string }): Promise<DevPilotApplicationResponse> {
    return this.post(`/workspace/git/branches/${encodeURIComponent(planId)}/create`, payload, { timeoutMs: READINESS_REQUEST_TIMEOUT_MS });
  }


  private async authJson<T = Record<string, unknown>>(path: string, init: RequestInit): Promise<T> {
    const endpoint = `${this.baseUrl}${path}`;
    const controller = new AbortController();
    const timeoutId = globalThis.setTimeout(() => controller.abort(), this.requestTimeoutMs);
    try {
      const csrf = init.method === 'POST' ? readBrowserCookie('devpilot_csrf') : '';
      const response = await fetch(endpoint, {
        ...init,
        credentials: 'include',
        signal: controller.signal,
        headers: { ...(init.headers ?? {}), ...(csrf ? { 'X-DevPilot-CSRF': csrf } : {}) },
      });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) {
        const message = String((payload as { error?: { message?: string } }).error?.message ?? `HTTP ${response.status}`);
        throw new DevPilotApiError(message, response.status, payload, path, 0);
      }
      return payload as T;
    } catch (error) {
      if (error instanceof DevPilotApiError) throw error;
      if (error instanceof Error && error.name === 'AbortError') throw new DevPilotApiError('Tiempo de espera agotado en autenticación local.', 408, { state: 'timeout' }, path, this.requestTimeoutMs);
      throw new DevPilotApiError('API local de autenticación no disponible.', 0, { state: 'api_down' }, path, 0);
    } finally {
      globalThis.clearTimeout(timeoutId);
    }
  }

  private async get(path: string, policy: RequestPolicy = {}): Promise<DevPilotApplicationResponse> {
    return this.request(path, { method: 'GET' }, policy);
  }

  private async post(path: string, body: unknown, policy: RequestPolicy = {}): Promise<DevPilotApplicationResponse> {
    return this.request(path, {
      method: 'POST',
      body: JSON.stringify(body),
      headers: { 'Content-Type': 'application/json' },
    }, policy);
  }

  private query(params: Record<string, string | number | boolean | undefined>): string {
    const query = new URLSearchParams();
    for (const [key, value] of Object.entries(params)) {
      if (value !== undefined && value !== '') query.set(key, String(value));
    }
    const rendered = query.toString();
    return rendered ? `?${rendered}` : '';
  }

  private async request(path: string, init: RequestInit, policy: RequestPolicy = {}): Promise<DevPilotApplicationResponse> {
    const retryDelays = policy.retryNetworkErrors
      ? [...(policy.retryDelaysMs ?? TRANSIENT_NETWORK_RETRY_DELAYS_MS)]
      : [];
    let attempt = 0;
    while (true) {
      try {
        return await this.requestOnce(path, init, normalizeTimeout(policy.timeoutMs ?? this.requestTimeoutMs), attempt + 1);
      } catch (error) {
        if (!isTransientNetworkError(error) || attempt >= retryDelays.length) throw error;
        await sleep(retryDelays[attempt]);
        attempt += 1;
      }
    }
  }

  private async requestOnce(path: string, init: RequestInit, timeoutMs: number, attempt: number): Promise<DevPilotApplicationResponse> {
    let response: Response;
    const startedAt = performance.now();
    const endpoint = `${this.baseUrl}${path}`;
    const controller = new AbortController();
    const timeoutId = globalThis.setTimeout(() => controller.abort(), timeoutMs);
    try {
      const csrf = init.method === 'POST' ? readBrowserCookie('devpilot_csrf') : '';
      response = await fetch(endpoint, {
        ...init,
        credentials: 'include',
        signal: controller.signal,
        headers: {
          ...(init.headers ?? {}),
          ...this.authHeaders(),
          ...(csrf ? { 'X-DevPilot-CSRF': csrf } : {}),
        },
      });
    } catch (error) {
      if (error instanceof Error && error.name === 'AbortError') {
        throw new DevPilotApiError(
          `Tiempo de espera agotado en ${path} después de ${timeoutMs} ms. Selecciona Reintentar o verifica la API local.`,
          408,
          { state: 'timeout', timeout_ms: timeoutMs, endpoint: path, action: 'retry' },
          path,
          Math.round(performance.now() - startedAt)
        );
      }
      throw new DevPilotApiError(
        'API local down o inaccesible: verifica que DevPilot API esté levantada en localhost, conserva 127.0.0.1 y configura el token local; no uses bind no-local como solución.',
        0,
        { error: error instanceof Error ? error.message : String(error), state: 'api_down', endpoint: path, action: 'retry' },
        path,
        Math.round(performance.now() - startedAt)
      );
    } finally {
      globalThis.clearTimeout(timeoutId);
    }
    const payload = await response.json().catch(() => ({}));
    if (!response.ok) {
      const applicationPayload = payload as Partial<DevPilotApplicationResponse>;
      const firstFinding = Array.isArray(applicationPayload.findings) ? applicationPayload.findings[0] : undefined;
      const backendReason = [
        typeof applicationPayload.message === 'string' ? applicationPayload.message : '',
        firstFinding?.id ? `[${firstFinding.id}]` : '',
        firstFinding?.message ?? '',
      ].filter(Boolean).join(' ');
      const statusHint = response.status === 401
        ? 'Sesión/autenticación local no autorizada.'
        : response.status === 403
          ? 'Solicitud bloqueada por una política, validación o autorización de DevPilot.'
          : 'Error HTTP de API local.';
      const detail = backendReason || statusHint;
      throw new DevPilotApiError(`DevPilot API respondió HTTP ${response.status} en ${path}. ${detail}`, response.status, payload, path, Math.round(performance.now() - startedAt));
    }
    const durationMs = Math.round(performance.now() - startedAt);
    return {
      ...(payload as DevPilotApplicationResponse),
      client_request: {
        endpoint: path,
        duration_ms: durationMs,
        timeout_budget_ms: timeoutMs,
        attempt,
      },
    };
  }

  private authHeaders(): Record<string, string> {
    if (!this.token) return {};
    return { 'X-DevPilot-Token': this.token };
  }
}

export function readBrowserCookie(name: string): string {
  if (!globalThis.document?.cookie) return '';
  const prefix = `${encodeURIComponent(name)}=`;
  for (const part of globalThis.document.cookie.split(';')) {
    const item = part.trim();
    if (item.startsWith(prefix)) return decodeURIComponent(item.slice(prefix.length));
  }
  return '';
}

export function readStoredToken(): string {
  const storage = globalThis.sessionStorage;
  if (!storage) return '';
  const token = storage.getItem(TOKEN_STORAGE_KEY) ?? '';
  if (!token) return '';
  const rawStoredAt = storage.getItem(TOKEN_STORED_AT_KEY);
  if (!rawStoredAt) {
    storage.setItem(TOKEN_STORED_AT_KEY, String(Date.now()));
    return token;
  }
  const storedAt = Number(rawStoredAt);
  if (!Number.isFinite(storedAt) || Date.now() - storedAt >= TOKEN_SESSION_TTL_MS) {
    clearExpiredStoredToken();
    return '';
  }
  return token;
}

export function storeToken(token: string): void {
  const storage = globalThis.sessionStorage;
  if (!storage) return;
  if (token.trim()) {
    storage.setItem(TOKEN_STORAGE_KEY, token.trim());
    storage.setItem(TOKEN_STORED_AT_KEY, String(Date.now()));
  } else clearExpiredStoredToken();
}

export function clearExpiredStoredToken(): void {
  globalThis.sessionStorage?.removeItem(TOKEN_STORAGE_KEY);
  globalThis.sessionStorage?.removeItem(TOKEN_STORED_AT_KEY);
}

export function readProjectJourneyContext(): ProjectJourneyContext | null {
  const raw = globalThis.sessionStorage?.getItem(PROJECT_JOURNEY_CONTEXT_KEY);
  if (!raw) return null;
  try {
    const parsed = JSON.parse(raw) as ProjectJourneyContext;
    if (parsed.phase !== 'entry' && parsed.phase !== 'project') return null;
    return parsed;
  } catch {
    globalThis.sessionStorage?.removeItem(PROJECT_JOURNEY_CONTEXT_KEY);
    return null;
  }
}

export function beginProjectEntryJourney(entryMode: ProjectEntryMode): void {
  clearApprovalCenterEntryHandoff();
  clearProjectEntryResumeState();
  const context: ProjectJourneyContext = { phase: 'entry', entry_mode: entryMode };
  globalThis.sessionStorage?.setItem(PROJECT_JOURNEY_CONTEXT_KEY, JSON.stringify(context));
}

export function saveProjectEntryResumeState(
  session: AuthSessionContext,
  value: Omit<ProjectEntryResumeState, 'phase' | 'actor_id' | 'session_created_at' | 'created_at_ms' | 'updated_at_ms' | 'expires_at_ms'>,
): void {
  const now = Date.now();
  const previous = readProjectEntryResumeState(session, value.entry_mode);
  const state: ProjectEntryResumeState = {
    phase: 'entry',
    entry_mode: value.entry_mode,
    actor_id: session.principal.actor_id,
    session_created_at: session.created_at,
    intake: value.intake,
    dry_run: value.dry_run,
    bootstrap_plan: value.bootstrap_plan,
    plan_hash: value.plan_hash,
    preimage_hash: value.preimage_hash,
    approval_id: value.approval_id?.trim() || undefined,
    created_at_ms: previous?.created_at_ms ?? now,
    updated_at_ms: now,
    expires_at_ms: now + PROJECT_ENTRY_RESUME_TTL_MS,
  };
  try { globalThis.sessionStorage?.setItem(PROJECT_ENTRY_RESUME_STATE_KEY, JSON.stringify(state)); } catch { /* UX resume is best-effort; server authority is unchanged. */ }
}

export function readProjectEntryResumeState(session: AuthSessionContext, expectedMode?: ProjectEntryMode): ProjectEntryResumeState | null {
  const raw = globalThis.sessionStorage?.getItem(PROJECT_ENTRY_RESUME_STATE_KEY);
  if (!raw) return null;
  try {
    const value = JSON.parse(raw) as ProjectEntryResumeState;
    const valid = value.phase === 'entry'
      && (!expectedMode || value.entry_mode === expectedMode)
      && value.actor_id === session.principal.actor_id
      && value.session_created_at === session.created_at
      && Boolean(value.plan_hash)
      && Boolean(value.preimage_hash)
      && Number.isFinite(value.expires_at_ms)
      && Date.now() <= value.expires_at_ms;
    if (!valid) {
      clearProjectEntryResumeState();
      return null;
    }
    return value;
  } catch {
    clearProjectEntryResumeState();
    return null;
  }
}

export function clearProjectEntryResumeState(): void {
  try { globalThis.sessionStorage?.removeItem(PROJECT_ENTRY_RESUME_STATE_KEY); } catch { /* best-effort UX cleanup */ }
}

export function armApprovalCenterEntryHandoff(session: AuthSessionContext, entryMode: ProjectEntryMode, approvalId: string): void {
  const now = Date.now();
  const value: ApprovalCenterEntryHandoff = {
    phase: 'entry',
    entry_mode: entryMode,
    approval_id: approvalId.trim(),
    actor_id: session.principal.actor_id,
    session_created_at: session.created_at,
    created_at_ms: now,
    expires_at_ms: now + APPROVAL_CENTER_ENTRY_HANDOFF_TTL_MS,
  };
  globalThis.localStorage?.setItem(APPROVAL_CENTER_ENTRY_HANDOFF_KEY, JSON.stringify(value));
}

export function readApprovalCenterEntryHandoff(session: AuthSessionContext, expectedApprovalId: string): ProjectJourneyContext | null {
  const raw = globalThis.localStorage?.getItem(APPROVAL_CENTER_ENTRY_HANDOFF_KEY);
  if (!raw) return null;
  try {
    const value = JSON.parse(raw) as ApprovalCenterEntryHandoff;
    const expected = expectedApprovalId.trim();
    const valid = value.phase === 'entry'
      && Boolean(expected)
      && value.approval_id === expected
      && value.actor_id === session.principal.actor_id
      && value.session_created_at === session.created_at
      && Number.isFinite(value.expires_at_ms)
      && Date.now() <= value.expires_at_ms;
    if (!valid) {
      clearApprovalCenterEntryHandoff();
      return null;
    }
    return { phase: 'entry', entry_mode: value.entry_mode };
  } catch {
    clearApprovalCenterEntryHandoff();
    return null;
  }
}

export function clearApprovalCenterEntryHandoff(): void {
  globalThis.localStorage?.removeItem(APPROVAL_CENTER_ENTRY_HANDOFF_KEY);
}

export function activateProjectJourney(context: { entry_mode: ProjectEntryMode; project_id: string; target_root: string }): void {
  clearApprovalCenterEntryHandoff();
  clearProjectEntryResumeState();
  const value: ProjectJourneyContext = {
    phase: 'project',
    entry_mode: context.entry_mode,
    project_id: context.project_id,
    target_root: context.target_root,
    activated_at: new Date().toISOString(),
  };
  globalThis.sessionStorage?.setItem(PROJECT_JOURNEY_CONTEXT_KEY, JSON.stringify(value));
}

export function clearProjectJourneyContext(): void {
  globalThis.sessionStorage?.removeItem(PROJECT_JOURNEY_CONTEXT_KEY);
  clearProjectEntryResumeState();
  clearApprovalCenterEntryHandoff();
}

export function isTransientNetworkError(error: unknown): error is DevPilotApiError {
  return error instanceof DevPilotApiError && error.status === 0;
}

function sleep(delayMs: number): Promise<void> {
  return new Promise((resolve) => globalThis.setTimeout(resolve, Math.max(0, delayMs)));
}

function normalizeTimeout(value: number | undefined): number {
  if (!Number.isFinite(value)) return DEFAULT_REQUEST_TIMEOUT_MS;
  return Math.max(1000, Math.min(Number(value), MAX_REQUEST_TIMEOUT_MS));
}
