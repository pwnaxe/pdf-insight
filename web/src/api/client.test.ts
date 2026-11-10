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
  expect(await analyzePdf(file)).toEqual(validResult);
});

test('maps an error code to a Polish message', async () => {
  stubFetch(Response.json({ error: { code: 'NO_TEXT', message: 'x' } }, { status: 422 }));
  await expect(analyzePdf(file)).rejects.toThrow(/warstwy tekstowej/);
});

test('rejects a body that fails validation', async () => {
  stubFetch(Response.json({ foo: 1 }));
  await expect(analyzePdf(file)).rejects.toThrow('nieoczekiwanym formacie');
});

test('reports a network failure', async () => {
  stubFetch(new TypeError('Failed to fetch'));
  await expect(analyzePdf(file)).rejects.toThrow(/połączyć/);
});
