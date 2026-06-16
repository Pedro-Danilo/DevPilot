export type FindingSeverity = 'info' | 'warning' | 'block' | 'error' | string;

export interface DevPilotFinding {
  id: string;
  message: string;
  severity: FindingSeverity;
  path?: string;
  metadata?: Record<string, unknown>;
}

export interface DevPilotApplicationResponse<TData = Record<string, unknown>> {
  contract: 'DevPilotApplicationResponse';
  operation: string;
  ok: boolean;
  exit_code: number;
  message: string;
  data: TData;
  findings: DevPilotFinding[];
}

export interface DashboardSnapshot {
  workspace?: DevPilotApplicationResponse;
  readiness?: DevPilotApplicationResponse;
  standards?: DevPilotApplicationResponse;
  miasi?: DevPilotApplicationResponse;
}

export type DashboardStatus = 'PASS' | 'WARN' | 'BLOCK' | 'PENDING';


export interface ReportIndexItem {
  report_id: string;
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
