import { describe, expect, it } from 'vitest';
import { apiOrigin, buildCsp } from './csp';

describe('apiOrigin', () => {
  it('strips path and trailing slash', () => {
    expect(apiOrigin('https://api.example.com/v1/')).toBe('https://api.example.com');
  });

  it('keeps a non-default port', () => {
    expect(apiOrigin('http://localhost:8787')).toBe('http://localhost:8787');
  });

  it.each([undefined, '', 'not a url', 'data:text/plain,x'])('returns null for %j', (value) => {
    expect(apiOrigin(value)).toBeNull();
  });
});

describe('buildCsp', () => {
  it('adds the API origin to connect-src', () => {
    const csp = buildCsp('https://pdf-insight-api.pixelhorizon.dev/');
    expect(csp).toContain("connect-src 'self' https://pdf-insight-api.pixelhorizon.dev;");
  });

  it('falls back to self when the API URL is missing or invalid', () => {
    expect(buildCsp(undefined)).toContain("connect-src 'self';");
    expect(buildCsp('nonsense')).toContain("connect-src 'self';");
  });

  it('never allows inline or eval', () => {
    const csp = buildCsp('https://api.example.com');
    expect(csp).not.toContain('unsafe-inline');
    expect(csp).not.toContain('unsafe-eval');
    expect(csp).toContain("script-src 'self';");
    expect(csp).toContain("object-src 'none'");
    expect(csp).toContain("form-action 'none'");
  });
});
