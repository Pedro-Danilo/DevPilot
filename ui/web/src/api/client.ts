import type { DevPilotApplicationResponse } from './types';

export const DEFAULT_API_BASE = 'http://127.0.0.1:8787/api/v1';
export const TOKEN_STORAGE_KEY = 'devpilot.apiToken';

export class DevPilotApiError extends Error {
  readonly status: number;
  readonly payload: unknown;

  constructor(message: string, status: number, payload: unknown) {
    super(message);
    this.name = 'DevPilotApiError';
    this.status = status;
    this.payload = payload;
  }
}

export interface DevPilotApiClientOptions {
  baseUrl?: string;
  token?: string;
}

export class DevPilotApiClient {
  readonly baseUrl: string;
  readonly token: string;

  constructor(options: DevPilotApiClientOptions = {}) {
    this.baseUrl = (options.baseUrl ?? DEFAULT_API_BASE).replace(/\/$/, '');
    this.token = options.token ?? readStoredToken();
  }

  async workspaceStatus(): Promise<DevPilotApplicationResponse> {
    return this.get('/workspace/status');
  }

  async applicationContract(): Promise<DevPilotApplicationResponse> {
    return this.get('/application/contract');
  }

  async standardsStatus(): Promise<DevPilotApplicationResponse> {
    return this.get('/standards/status');
  }

  async miasiStatus(): Promise<DevPilotApplicationResponse> {
    return this.get('/miasi/status');
  }

  async readiness(strict = true): Promise<DevPilotApplicationResponse> {
    return this.post('/validation/readiness', {
      operation: 'validation.readiness',
      payload: { strict },
      dry_run: true,
    });
  }


  async listReports(filters: { limit?: number; severity?: string; status?: string; command?: string } = {}): Promise<DevPilotApplicationResponse> {
    return this.get(`/reports${this.query(filters)}`);
  }

  async readReport(reportId: string, format = 'json'): Promise<DevPilotApplicationResponse> {
    return this.get(`/reports/${encodeURIComponent(reportId)}${this.query({ format })}`);
  }

  async listTraces(limit = 20): Promise<DevPilotApplicationResponse> {
    return this.get(`/traces${this.query({ limit })}`);
  }

  async inspectTrace(traceId: string, limit = 100): Promise<DevPilotApplicationResponse> {
    return this.get(`/traces/${encodeURIComponent(traceId)}${this.query({ limit })}`);
  }

  async metricsSummary(): Promise<DevPilotApplicationResponse> {
    return this.get('/metrics/summary');
  }

  private async get(path: string): Promise<DevPilotApplicationResponse> {
    return this.request(path, { method: 'GET' });
  }

  private async post(path: string, body: unknown): Promise<DevPilotApplicationResponse> {
    return this.request(path, {
      method: 'POST',
      body: JSON.stringify(body),
      headers: { 'Content-Type': 'application/json' },
    });
  }

  private query(params: Record<string, string | number | boolean | undefined>): string {
    const query = new URLSearchParams();
    for (const [key, value] of Object.entries(params)) {
      if (value !== undefined && value !== '') query.set(key, String(value));
    }
    const rendered = query.toString();
    return rendered ? `?${rendered}` : '';
  }

  private async request(path: string, init: RequestInit): Promise<DevPilotApplicationResponse> {
    const response = await fetch(`${this.baseUrl}${path}`, {
      ...init,
      headers: {
        ...(init.headers ?? {}),
        ...this.authHeaders(),
      },
    });
    const payload = await response.json().catch(() => ({}));
    if (!response.ok) {
      throw new DevPilotApiError(`DevPilot API respondió HTTP ${response.status}`, response.status, payload);
    }
    return payload as DevPilotApplicationResponse;
  }

  private authHeaders(): Record<string, string> {
    if (!this.token) {
      return {};
    }
    return { 'X-DevPilot-Token': this.token };
  }
}

export function readStoredToken(): string {
  return globalThis.sessionStorage?.getItem(TOKEN_STORAGE_KEY) ?? '';
}

export function storeToken(token: string): void {
  if (token.trim()) {
    globalThis.sessionStorage?.setItem(TOKEN_STORAGE_KEY, token.trim());
  } else {
    globalThis.sessionStorage?.removeItem(TOKEN_STORAGE_KEY);
  }
}
