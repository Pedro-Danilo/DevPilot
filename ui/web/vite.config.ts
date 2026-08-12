import { defineConfig } from 'vite';

const UOC011_HEADERS = {
  'Content-Security-Policy': "default-src 'self'; base-uri 'self'; frame-ancestors 'none'; object-src 'none'; form-action 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; script-src 'self'; connect-src 'self' http://127.0.0.1:8787 http://localhost:8787 ws://127.0.0.1:5173 ws://localhost:5173",
  'X-Content-Type-Options': 'nosniff',
  'X-Frame-Options': 'DENY',
  'Referrer-Policy': 'no-referrer',
  'Permissions-Policy': 'geolocation=(), microphone=(), camera=()',
  'Cache-Control': 'no-store',
  'Cross-Origin-Opener-Policy': 'same-origin',
};

export default defineConfig({
  server: {
    host: '127.0.0.1',
    port: 5173,
    strictPort: true,
    headers: UOC011_HEADERS,
  },
  preview: {
    host: '127.0.0.1',
    port: 5173,
    strictPort: true,
    headers: UOC011_HEADERS,
  },
});
