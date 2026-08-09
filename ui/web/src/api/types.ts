export type FindingSeverity = 'info' | 'warning' | 'block' | 'error' | string;

export interface DevPilotFinding {
  id: string;
  message: string;
  severity: FindingSeverity;
  path?: string;
  metadata?: Record<string, unknown>;
}

export interface ClientRequestMetadata {
  endpoint: string;
  duration_ms: number;
  timeout_budget_ms: number;
  attempt: number;
}

export interface DevPilotApplicationResponse<TData = Record<string, unknown>> {
  contract: 'DevPilotApplicationResponse';
  operation: string;
  ok: boolean;
  exit_code: number;
  message: string;
  data: TData;
  findings: DevPilotFinding[];
  client_request?: ClientRequestMetadata;
}

export interface DashboardSnapshot {
  workspace?: DevPilotApplicationResponse;
  readiness?: DevPilotApplicationResponse;
  standards?: DevPilotApplicationResponse;
  miasi?: DevPilotApplicationResponse;
  operator?: DevPilotApplicationResponse<OperatorDashboardResponseData>;
  portfolio?: DevPilotApplicationResponse;
}

export type DashboardStatus = 'PASS' | 'WARN' | 'FAIL' | 'BLOCK' | 'ERROR' | 'PENDING';


export interface ReportIndexItem {
  report_id: string;
  display_id?: string;
  relative_stem?: string;
  relative_path?: string;
  scope?: string;
  workspace_id?: string | null;
  nested?: boolean;
  depth?: number;
  size_bytes?: number;
  summary_loaded?: boolean;
  formats?: string[];
  paths?: Record<string, string>;
  command?: string;
  status?: string;
  ok?: boolean;
  generated_at?: string;
  modified_at?: string;
  findings_total?: number;
  findings_by_severity?: Record<string, number>;
  message?: string;
  summary?: Record<string, unknown>;
}

export interface TraceSummaryItem {
  trace_id: string;
  spans_total?: number;
  events_total?: number;
  metrics_total?: number;
  statuses?: Record<string, number>;
  span_types?: Record<string, number>;
  started_at?: string;
  ended_at?: string;
  duration_ms_total?: number;
}

export interface ReportTraceSnapshot {
  reports?: DevPilotApplicationResponse<{ summary?: Record<string, unknown>; reports?: ReportIndexItem[] }>;
  reportDetail?: DevPilotApplicationResponse;
  traces?: DevPilotApplicationResponse<{ summary?: Record<string, unknown>; traces?: TraceSummaryItem[] }>;
  traceDetail?: DevPilotApplicationResponse;
  metrics?: DevPilotApplicationResponse;
}


export interface ApprovalRecordItem {
  approval_id: string;
  subject: string;
  tool_id: string;
  action: string;
  status: string;
  actor?: string;
  reason?: string;
  created_at?: string;
  updated_at?: string;
  expires_at?: string;
  expired?: boolean;
  decided_by?: string | null;
}

export interface ApprovalCenterSnapshot {
  approvals?: DevPilotApplicationResponse<{ summary?: Record<string, unknown>; approvals?: ApprovalRecordItem[] }>;
  selected?: DevPilotApplicationResponse;
  actionResult?: DevPilotApplicationResponse;
  requestResult?: DevPilotApplicationResponse;
}


export interface SettingsSnapshot {
  workspace?: DevPilotApplicationResponse;
  providers?: DevPilotApplicationResponse;
  policy?: DevPilotApplicationResponse;
  securityPosture?: DevPilotApplicationResponse;
  providerPlan?: DevPilotApplicationResponse;
}

export interface ProviderSettingsItem {
  provider_id?: string;
  id?: string;
  kind?: string;
  enabled?: boolean;
  default_model?: string;
  endpoint?: string;
  external_api?: boolean;
  requires_api_key?: boolean;
  api_key_env?: string;
  status?: string;
}

export interface OperatorSourceRef {
  path: string;
  kind?: string;
  required?: boolean;
  available?: boolean;
  description?: string;
}

export interface OperatorDashboardSection {
  status: string;
  title?: string;
  summary?: string;
  source_refs?: OperatorSourceRef[];
  metrics?: Record<string, unknown>;
  score?: number | null;
  blocking_findings_total?: number | null;
  warnings_total?: number | null;
}

export interface OperatorNextAction {
  action_id?: string;
  command: string;
  reason: string;
  priority?: string;
  dry_run?: boolean;
  source_refs?: OperatorSourceRef[];
}

export interface OperatorDashboardSnapshot {
  schema_version: string;
  schema_id: string;
  snapshot_id: string;
  workspace_id: string;
  created_by: string;
  status: string;
  generated_at_utc: string;
  local_first: boolean;
  read_only: boolean;
  dry_run: boolean;
  network_used: boolean;
  external_api_used: boolean;
  mutations_performed: boolean;
  source_mutations_performed: boolean;
  remote_execution_enabled: boolean;
  connector_write_enabled: boolean;
  plugin_execution_enabled: boolean;
  sections: Record<string, OperatorDashboardSection>;
  recommended_next_actions: OperatorNextAction[];
  notes?: string[];
}

export interface OperatorDashboardResponseData {
  summary?: Record<string, unknown>;
  snapshot?: OperatorDashboardSnapshot;
  reports?: Record<string, string>;
}


export interface WorkspaceDocumentNode {
  node_id: string;
  document_id?: string | null;
  kind: 'folder' | 'document';
  name: string;
  relative_path: string;
  parent_id?: string | null;
  extension?: string | null;
  category: string;
  size_bytes?: number | null;
  modified_at?: string | null;
  readable: boolean;
  blocked_reason?: string | null;
}

export interface WorkspaceDocumentBreadcrumb {
  label: string;
  relative_path?: string | null;
}

export interface WorkspaceDocumentResource extends WorkspaceDocumentNode {
  sha256?: string;
  encoding?: string;
  content?: string;
  structured?: unknown;
  breadcrumbs?: WorkspaceDocumentBreadcrumb[];
}

export interface WorkspaceDocumentGitCommit {
  commit: string;
  short_commit: string;
  author_name?: string | null;
  author_email?: string | null;
  authored_at?: string | null;
  subject: string;
}

export interface WorkspaceDocumentInspectionMetadata extends WorkspaceDocumentNode {
  sha256: string;
  encoding: string;
  frontmatter?: {
    has_frontmatter: boolean;
    fields: Record<string, unknown>;
    parse_warnings?: string[];
    source?: string;
  };
  classification?: {
    level: 'required' | 'recommended' | 'optional' | string;
    source?: string;
    badges?: string[];
  };
  git?: {
    is_git_repo: boolean;
    status?: Record<string, unknown>;
    last_commit?: WorkspaceDocumentGitCommit | null;
    history_available?: boolean;
    read_only?: boolean;
  };
}

export interface WorkspaceDocumentHistoryData {
  summary?: Record<string, unknown>;
  document?: Record<string, unknown>;
  commits?: WorkspaceDocumentGitCommit[];
}

export interface WorkspaceDocumentDiffData {
  summary?: Record<string, unknown>;
  document?: Record<string, unknown>;
  git_status?: Record<string, unknown>;
  diff?: string;
}

export interface WorkspaceDocumentLink {
  label?: string;
  target?: string;
  kind?: string;
  anchor?: string | null;
  resolved?: boolean;
  resolved_relative_path?: string;
  document_id?: string | null;
  source_document_id?: string;
  source_relative_path?: string;
  reason?: string;
}

export interface WorkspaceDocumentLinksData {
  summary?: Record<string, unknown>;
  outgoing?: WorkspaceDocumentLink[];
  incoming?: WorkspaceDocumentLink[];
}

export interface WorkspaceDocumentSearchResult {
  document_id: string;
  relative_path: string;
  title: string;
  category: string;
  classification: string;
  sha256: string;
  size_bytes: number;
  match_count: number;
  line_number?: number | null;
  snippet?: string;
}

export interface WorkspaceDocumentSearchData {
  summary?: Record<string, unknown>;
  results?: WorkspaceDocumentSearchResult[];
}

export interface WorkspaceValidationNavigation {
  relative_path?: string;
  document_id?: string | null;
  line?: number | null;
  section?: string | null;
}

export interface WorkspaceValidationArtifact {
  role: string;
  relative_path: string;
  document_id: string;
  sha256: string;
  size_bytes: number;
  required: boolean;
}

export interface WorkspaceValidationPlan {
  schema_id: string;
  plan_id: string;
  plan_hash: string;
  workspace_id?: string;
  strict: boolean;
  scopes: string[];
  artifacts: WorkspaceValidationArtifact[];
  budgets?: Record<string, number>;
  created_at?: string;
  expires_after_seconds?: number;
  preliminary?: boolean;
}

export interface WorkspaceValidationStep {
  scope: string;
  status: string;
  ok: boolean;
  exit_code: number;
  message: string;
  duration_ms?: number;
  data?: Record<string, unknown>;
  findings?: DevPilotFinding[];
}

export interface WorkspaceValidationJobData {
  summary?: Record<string, unknown>;
  job?: {
    job_id: string;
    status: string;
    started_at?: string;
    ended_at?: string;
    trace_path?: string;
    report_paths?: Record<string, string>;
    event_ref?: Record<string, string>;
  };
  steps?: WorkspaceValidationStep[];
  safety?: Record<string, unknown>;
}

export interface WorkspaceTraceabilitySource extends WorkspaceValidationNavigation {
  excerpt?: string;
}

export interface WorkspaceTraceabilityRecord {
  requirement_id: string;
  story_ids: string[];
  risk_ids: string[];
  control_ids: string[];
  test_ids: string[];
  sources?: WorkspaceTraceabilitySource[];
  navigation?: WorkspaceTraceabilitySource | null;
  coverage?: Record<string, boolean>;
}

export interface WorkspaceTraceabilityData {
  traceability?: {
    schema_id?: string;
    summary?: Record<string, unknown>;
    matrix?: WorkspaceTraceabilityRecord[];
    source_paths?: string[];
    notes?: string[];
  };
  safety?: Record<string, unknown>;
}


export interface WorkspaceEditPlanDocument {
  document_id: string;
  relative_path: string;
  extension: string;
  document_sha_before: string;
  proposed_sha256: string;
  size_before_bytes: number;
  size_after_bytes: number;
}

export interface WorkspaceEditPlan {
  schema_id: string;
  plan_id: string;
  plan_hash: string;
  workspace_id?: string;
  document: WorkspaceEditPlanDocument;
  proposed_content: string;
  diff: { format: 'unified'; content: string; sha256: string; bytes: number; additions: number; deletions: number; hunks: number; changed_lines: number; truncated: boolean };
  validation: Record<string, unknown>;
  risk: { level: string; score: number; reasons: string[]; approval_required_for_apply: boolean; apply_policy_deferred_to: string; source_write_enabled: boolean };
  policy: Record<string, unknown>;
  preview: { mode: string; content_sha256: string };
  patch_evidence: { filename: string; sha256: string; executed: boolean; source_mutated: boolean };
  created_at: string;
  expires_at: string;
  preliminary: boolean;
}

export interface WorkspaceEditPlanResponseData {
  summary?: Record<string, unknown>;
  plan?: WorkspaceEditPlan;
  safety?: Record<string, unknown>;
}
