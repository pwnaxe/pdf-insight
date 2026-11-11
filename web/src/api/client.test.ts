import { afterEach, expect, test, vi } from 'vitest';
import { validResult } from '../lib/fixtures';
import { analyzePdf } from './client';

const file = new File(['%PDF-1.7'], 'a.pdf', { type: 'application/pdf' });

afterEach(() => vi.unstubAllGlobals());

function stubFetch(response: Response | Error) {
  vi.stubGlobal(
    'fetch',
    vi.fn(() => (response instanceof Error ? Promise.reject(response) : Promise.resolve(response))),
  );
}

test('returns a validated result', async () => {
  stubFetch(Response.json(validResult));
  expect(await analyzePdf(file, 'en')).toEqual(validResult);
});

test.each([
  ['en', /text layer/],
  ['pl', /warstwy tekstowej/],
] as const)('maps an error code to a %s message', async (lang, message) => {
  stubFetch(Response.json({ error: { code: 'NO_TEXT', message: 'x' } }, { status: 422 }));
  await expect(analyzePdf(file, lang)).rejects.toThrow(message);
});

test('falls back to the server message for an unknown code', async () => {
  stubFetch(
    Response.json({ error: { code: 'OTHER', message: 'Niestandardowy błąd.' } }, { status: 400 }),
  );
  await expect(analyzePdf(file, 'pl')).rejects.toThrow('Niestandardowy błąd.');
});

test('sends the language as a form field', async () => {
  stubFetch(Response.json(validResult));
  await analyzePdf(file, 'en');
  const init = vi.mocked(fetch).mock.calls[0]?.[1];
  expect((init?.body as FormData).get('lang')).toBe('en');
});

test.each([
  ['en', 'unexpected format'],
  ['pl', 'nieoczekiwanym formacie'],
] as const)('rejects a body that fails validation (%s)', async (lang, message) => {
  stubFetch(Response.json({ foo: 1 }));
  await expect(analyzePdf(file, lang)).rejects.toThrow(message);
});

test('reports a network failure', async () => {
  stubFetch(new TypeError('Failed to fetch'));
  await expect(analyzePdf(file, 'en')).rejects.toThrow(/connect/);
});

test.each([
  [429, 'en', /Too many requests/],
  [413, 'en', /too large/],
  [502, 'en', /error \(502\)/],
  [429, 'pl', /Zbyt wiele żądań/],
  [413, 'pl', /za duży/],
  [502, 'pl', /błąd \(502\)/],
] as const)('maps HTTP %i (%s) without a JSON body', async (status, lang, message) => {
  stubFetch(new Response('<html>nginx</html>', { status }));
  await expect(analyzePdf(file, lang)).rejects.toThrow(message);
});
