const SECRET_KEY_PATTERN = /(token|secret|password|api[_-]?key|bearer|credential|private[_-]?key)/i;

export function escapeHtml(value: unknown): string {
  return String(value ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

function redactSecretLikeValue(key: string, value: unknown): unknown {
  if (!SECRET_KEY_PATTERN.test(key)) return value;
  if (value === null || value === undefined || value === '') return value;
  return '<redacted>';
}

export function redactSecrets(value: unknown): unknown {
  if (Array.isArray(value)) return value.map((item) => redactSecrets(item));
  if (value && typeof value === 'object') {
    const output: Record<string, unknown> = {};
    for (const [key, item] of Object.entries(value as Record<string, unknown>)) {
      output[key] = redactSecretLikeValue(key, redactSecrets(item));
    }
    return output;
  }
  return value;
}

export function safeJsonForHtml(value: unknown): string {
  return escapeHtml(JSON.stringify(redactSecrets(value ?? {}), null, 2));
}
