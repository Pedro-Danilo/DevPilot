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
