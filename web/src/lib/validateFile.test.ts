import { describe, expect, test } from 'vitest';
import { dictionary } from './i18n';
import { MAX_FILE_BYTES, validateFile } from './validateFile';

const pdf = (name = 'a.pdf', type = 'application/pdf') =>
  new File(['%PDF-1.7\n...'], name, { type });

const { pl, en } = dictionary;

describe('validateFile', () => {
  test('accepts a PDF', async () => {
    expect(await validateFile(pdf(), en)).toBeNull();
  });

  test('accepts a PDF with an empty mime type but .pdf extension', async () => {
    expect(await validateFile(pdf('Umowa.PDF', ''), en)).toBeNull();
  });

  test('rejects another file type', async () => {
    expect(await validateFile(new File(['hello'], 'a.txt', { type: 'text/plain' }), en)).toMatch(
      /PDF/,
    );
  });

  test('rejects a file with a wrong signature', async () => {
    const file = new File(['not a pdf at all'], 'a.pdf', { type: 'application/pdf' });
    expect(await validateFile(file, en)).toMatch(/valid PDF/);
  });

  test('rejects an empty file', async () => {
    expect(await validateFile(new File([], 'a.pdf', { type: 'application/pdf' }), en)).toMatch(
      /empty/,
    );
  });

  test('rejects a file over the limit', async () => {
    const file = pdf();
    Object.defineProperty(file, 'size', { value: MAX_FILE_BYTES + 1 });
    expect(await validateFile(file, en)).toMatch(/10 MB/);
  });

  test.each([
    ['notPdf', new File(['hello'], 'a.txt', { type: 'text/plain' })],
    ['empty', new File([], 'a.pdf', { type: 'application/pdf' })],
    ['badSignature', new File(['not a pdf at all'], 'a.pdf', { type: 'application/pdf' })],
  ] as const)('returns the %s message in both languages', async (key, file) => {
    expect(await validateFile(file, pl)).toBe(pl.validation[key]);
    expect(await validateFile(file, en)).toBe(en.validation[key]);
    expect(pl.validation[key]).not.toBe(en.validation[key]);
  });

  test('the size message is localised', async () => {
    const file = pdf();
    Object.defineProperty(file, 'size', { value: MAX_FILE_BYTES + 1 });
    expect(await validateFile(file, pl)).toBe('Plik jest za duży. Maksymalny rozmiar to 10 MB.');
  });
});
