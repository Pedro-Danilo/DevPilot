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

export interface WorkspaceEditExecutionRecord {
  schema_id: string;
  execution_id: string;
  status: 'applied' | 'rolled-back-manual' | 'rolled-back-automatic' | 'post-validation-blocked' | string;
  plan_id: string;
  plan_hash: string;
  approval_id: string;
  approval?: WorkspaceEditApprovalRecord;
  actor: string;
  workspace_id?: string;
  relative_path: string;
  document_id: string;
  pre_sha256: string;
  post_sha256: string;
  proposed_sha256: string;
  backup_sha256: string;
  backup_ref?: string;
  evidence_ref?: string;
  report_ref?: string;
  trace_event_types?: string[];
  duration_ms?: number;
  applied_at: string;
  rollback?: Record<string, unknown> | null;
  source_write: boolean;
  git_stage: boolean;
  git_commit: boolean;
  preliminary: boolean;
}

export interface WorkspaceEditApprovalRecord {
  approval_id: string;
  subject: string;
  tool_id: string;
  action: string;
  status: string;
  actor: string;
  reason: string;
  scope: Record<string, unknown>;
  expires_at: string;
  decision_at?: string | null;
  decided_by?: string | null;
}

export interface WorkspaceGitPlanFile {
  document_id: string;
  relative_path: string;
  working_sha256: string;
  diff_sha256: string;
  size_bytes: number;
}

export interface WorkspaceGitCommitPlan {
  schema_id: string;
  plan_id: string;
  plan_hash: string;
  kind: 'commit';
  workspace_id: string;
  branch: string;
  head_before: string;
  files: WorkspaceGitPlanFile[];
  commit: { message: string; author_name: string; author_email: string };
  combined_diff: string;
  combined_diff_sha256: string;
  created_at: string;
  expires_at: string;
  preliminary: boolean;
}

export interface WorkspaceGitStageExecution {
  stage_execution_id: string;
  status: 'staged' | 'committed' | string;
  plan_id: string;
  plan_hash: string;
  stage_approval_id: string;
  branch: string;
  head_before: string;
  index_fingerprint: string;
  commit_intent_hash: string;
  files: WorkspaceGitPlanFile[];
  commit: { message: string; author_name: string; author_email: string };
  git_stage: boolean;
  git_commit: boolean;
  push_performed: boolean;
}

export interface WorkspaceGitCommitExecution {
  execution_id: string;
  status: 'committed' | string;
  stage_execution_id: string;
  commit: string;
  parent: string;
  branch: string;
  committed_paths: string[];
  commit_identity: { message: string; author_name: string; author_email: string };
  push_performed: boolean;
  hooks_executed: boolean;
}

export interface WorkspaceGitBranchPlan {
  schema_id: string;
  plan_id: string;
  plan_hash: string;
  kind: 'branch-create';
  workspace_id: string;
  current_branch: string;
  branch_name: string;
  head_before: string;
  created_at: string;
  expires_at: string;
  preliminary: boolean;
}

export interface GovernedJobOperationalSnapshot {
  phase: string;
  progress_percent: number;
  duration_seconds: number;
  heartbeat_age_seconds: number | null;
  stale: boolean;
  worker_pid_present: boolean;
  retry_of_job_id?: string | null;
  retry_job_ids?: string[];
  reconciled_orphan: boolean;
}

export interface GovernedJobSnapshot {
  job_id: string;
  capability_id: string;
  workspace_id: string;
  status: string;
  risk_class: string;
  dry_run: boolean;
  timeout_seconds: number;
  retry_limit: number;
  retry_count: number;
  heartbeat_interval_seconds: number;
  heartbeat_sequence: number;
  created_at: string;
  updated_at: string;
  last_heartbeat_at: string | null;
  approval_binding_id: string | null;
  supports_cancel: boolean;
  supports_rollback: boolean;
  correlation_id: string;
  parameter_keys: string[];
  artifact_refs: string[];
  evidence_refs: string[];
  runtime_adapter_id: string | null;
  errors: string[];
  result_summary: Record<string, unknown>;
  operational?: GovernedJobOperationalSnapshot;
}

export interface JobLogEntry { timestamp: string; level: string; phase: string; message: string; }

export interface QualityOperationItem {
  operation_id: string; label: string; capability_id: string; kind: string; risk_class: string; requires_approval: boolean; supports_cancel: boolean; timeout_seconds: number; allowed_keys: string[];
}

export interface QualityJobPlanData {
  job?: GovernedJobSnapshot;
  plan?: { job_id: string; operation_id: string; capability_id: string; parameters: Record<string, unknown>; approval_id?: string | null; timeout_seconds: number };
  plan_ref?: string;
}

export interface AiOperationItem {
  operation_id: string;
  label: string;
  capability_id: string;
  kind: string;
  risk_class: string;
  requires_approval: boolean;
  supports_cancel: boolean;
  timeout_seconds: number;
  allowed_keys: string[];
}


// DEVPL-GSDLC-01-E — actor-neutral Project Status API contract.
export interface GuidedSdlcNextAction {
  action_id?: string;
  kind?: string;
  priority?: number;
  reason_code?: string;
  explanation?: string;
  navigation_target?: string;
  approval_needed?: boolean;
  mutating?: boolean;
  dry_run_required?: boolean;
  available?: boolean;
  disabled_reason?: string | null;
  expected_evidence?: string[];
}


export interface MiasiRequiredControl {
  kind: string;
  artifact_id: string;
  lifecycle: string;
  ready: boolean;
}

export interface MiasiApplicabilityStatus {
  status?: 'APPLICABLE' | 'NOT_APPLICABLE' | 'REVIEW_REQUIRED' | string;
  gate_status?: 'PASS' | 'BLOCK' | string;
  reason_codes?: string[];
  risk_level?: string;
  required_controls?: MiasiRequiredControl[];
  missing_controls?: string[];
  blockers?: Array<Record<string, unknown>>;
  agent_execution_allowed?: boolean;
  rag_execution_allowed?: boolean;
  execution_reason_code?: string;
  reevaluation_required?: boolean;
}

export interface GuidedSdlcProjectStatus {
  workspace_id?: string;
  project_id?: string;
  phase?: string;
  current_step?: string;
  lifecycle_status?: string;
  progress?: Record<string, unknown>;
  mipsoftware?: Record<string, unknown>;
  miasi?: MiasiApplicabilityStatus;
  artifact_readiness?: Record<string, unknown>;
  planning?: Record<string, unknown>;
  blockers?: Array<Record<string, unknown>>;
  pending_approvals?: Array<Record<string, unknown>>;
  quality?: Record<string, unknown>;
  git?: Record<string, unknown>;
  revalidation?: Record<string, unknown>;
  model_budget?: Record<string, unknown>;
  freshness?: Record<string, unknown>;
  source_refs?: string[];
  reason?: string | null;
}

export interface GuidedSdlcProjectStatusResponseData {
  ui_state: 'READY' | 'EMPTY' | 'BLOCKED' | 'REVALIDATION_REQUIRED' | 'STALE' | 'UNKNOWN' | string;
  workspace_id?: string | null;
  project_status: GuidedSdlcProjectStatus;
  next_action: GuidedSdlcNextAction;
  read_only: boolean;
  actor_neutral: boolean;
  network_used: boolean;
  external_api_used: boolean;
  mutations_performed: boolean;
}

export interface AuthPrincipal {
  actor_id: string;
  username: string;
  display_name: string;
  roles: string[];
  workspace_scopes: string[];
  auth_method: string;
}

export interface AuthSessionContext {
  authenticated: true;
  principal: AuthPrincipal;
  created_at: string;
  last_seen_at: string;
  absolute_expires_at: string;
  idle_timeout_seconds: number;
  rotation_counter: number;
  session_secret_exposed?: false;
}

export interface AuthBootstrapStatus {
  ok: boolean;
  first_run_required: boolean;
  runtime_auth_store: string;
  runtime_store_version: number;
  remote_login_enabled: boolean;
  public_api_enabled: boolean;
}

export interface AuthSessionStatus {
  ok: boolean;
  state: 'missing' | 'unknown' | 'active' | 'expired' | 'revoked' | 'stale' | string;
  authenticated: boolean;
  reason_code: string;
  secret_exposed: false;
}

export interface AuthSessionEnvelope { ok: boolean; session: AuthSessionContext; }


export type ProjectEntryMode = 'CREATE_NEW' | 'OPEN_EXISTING' | 'IMPORT_GIT';
export interface ProjectEntryDryRunData { dry_run?: Record<string, unknown>; bootstrap_plan?: Record<string, unknown>; writes_performed?: boolean; network_used?: boolean; }

export interface ArtifactDraftRevisionSummary {
  revision: number;
  revision_sha256: string;
  parent_revision_sha256?: string | null;
  content_sha256: string;
  event: 'SAVE' | 'AUTOSAVE' | 'RECOVER' | string;
  actor: string;
  actor_role: string;
  created_at: string;
  recovered_from_sha256?: string | null;
  lifecycle_state: 'DRAFT';
  source_type: 'MANUAL';
}

export interface ArtifactDraftRevision extends ArtifactDraftRevisionSummary {
  content: string;
  session_principal: string;
  source_preimage_sha256: string;
  approved_evidence: false;
  source_mutations_performed: false;
}

export interface ArtifactDraftRecord {
  schema_id: 'devpilot.gsdlc04b.artifact_draft_store_record.v1';
  workspace_id: string;
  document_id: string;
  relative_path: string;
  extension: '.md' | '.json' | string;
  source_type: 'MANUAL';
  lifecycle_state: 'DRAFT';
  source_preimage_sha256: string;
  base_commit: string;
  author_actor: string;
  author_role: string;
  session_principal: string;
  active: boolean;
  current_revision_sha256?: string | null;
  created_at: string;
  updated_at: string;
  revisions: ArtifactDraftRevision[];
  source_conflict?: boolean;
  approved_evidence: false;
  source_mutations_performed: false;
}

export type ArtifactImportSourceType = 'PASTE' | 'UPLOAD' | 'IMPORT';

export interface ArtifactImportPreview {
  preview_sha256: string;
  source_type: ArtifactImportSourceType;
  relative_path: string;
  extension: '.md' | '.json';
  original_filename?: string | null;
  declared_mime?: string | null;
  original_size_bytes: number;
  encoding: string;
  source_label?: string | null;
  source_reference?: string | null;
  original_sha256: string;
  normalized_sha256: string;
  destination_exists: boolean;
  destination_preimage_sha256?: string | null;
  normalized_content: string;
  diff: string;
  secret_warning: boolean;
  secret_values_exposed: false;
}

export interface ArtifactImportRecord {
  schema_id: 'devpilot.gsdlc04c.artifact_import_record.v1';
  import_id: string;
  workspace_id: string;
  relative_path: string;
  extension: '.md' | '.json';
  source_type: ArtifactImportSourceType;
  lifecycle_state: 'DRAFT';
  original_filename?: string | null;
  declared_mime?: string | null;
  original_size_bytes: number;
  source_label?: string | null;
  source_reference?: string | null;
  original_sha256: string;
  normalized_sha256: string;
  encoding: string;
  normalized_content: string;
  destination_exists: boolean;
  destination_preimage_sha256?: string | null;
  preview_sha256: string;
  diff: string;
  artifact: Record<string, unknown>;
  created_at: string;
  updated_at: string;
  source_mutations_performed: false;
  workspace_writes_performed: false;
  runtime_store_write: true;
  network_used: false;
  external_api_used: false;
  secret_warning: false;
}

export interface ArtifactReviewFinding {
  id: string;
  message: string;
  severity: 'info' | 'warning' | 'fail' | 'block' | 'error';
  line?: number | null;
  section?: string | null;
  metadata?: Record<string, unknown>;
}

export interface ArtifactReviewRecord {
  schema_id: 'devpilot.gsdlc04d.artifact_review_record.v1';
  review_id: string;
  source_kind: 'IMPORT' | 'MANUAL';
  source_ref: string;
  workspace_id: string;
  status: 'FINDINGS' | 'APPROVAL_REQUIRED' | 'APPROVED' | 'FROZEN' | 'REVALIDATION_REQUIRED';
  relative_path: string;
  content_sha256: string;
  base_sha256: string;
  findings: ArtifactReviewFinding[];
  validation: Record<string, unknown>;
  plan?: Record<string, any> | null;
  artifact: Record<string, any>;
  execution_id?: string;
  approval_id?: string;
  approved_sha256?: string;
  freeze_record?: Record<string, unknown>;
  reconciliation?: {
    status?: 'UNCHANGED' | 'REVALIDATION_REQUIRED';
    change_kind?: 'unchanged' | 'modified' | 'renamed' | 'deleted';
    original_relative_path?: string;
    detected_relative_path?: string | null;
    previous_approved_sha256?: string | null;
    current_normalized_sha256?: string | null;
    approval_valid?: boolean;
    auto_reverted?: boolean;
    hidden_merge?: boolean;
    git_branch_at_freeze?: string | null;
    git_branch_current?: string | null;
    branch_changed?: boolean;
    git_head_current?: string | null;
    git_status_porcelain?: string;
    git_diff?: string;
    source_provenance?: Record<string, unknown>;
    checked_at?: string;
  };
  approval_valid: boolean;
}
