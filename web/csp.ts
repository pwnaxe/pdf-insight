export function apiOrigin(apiUrl: string | undefined): string | null {
  if (!apiUrl) return null;
  try {
    const { origin } = new URL(apiUrl);
    return origin === 'null' ? null : origin;
  } catch {
    return null;
  }
}

export function buildCsp(apiUrl: string | undefined): string {
  const connect = ["'self'", apiOrigin(apiUrl)].filter(Boolean).join(' ');
  return [
    "default-src 'self'",
    "script-src 'self'",
    "style-src 'self'",
    "img-src 'self' data:",
    "font-src 'self'",
    `connect-src ${connect}`,
    "object-src 'none'",
    "base-uri 'self'",
    "form-action 'none'",
  ].join('; ');
}
