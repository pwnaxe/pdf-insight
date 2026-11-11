import { describe, expect, test } from 'vitest';
import { MAX_FILE_BYTES, validateFile } from './validateFile';

const pdf = (name = 'a.pdf', type = 'application/pdf') =>
  new File(['%PDF-1.7\n...'], name, { type });

describe('validateFile', () => {
  test('accepts a PDF', async () => {
    expect(await validateFile(pdf())).toBeNull();
  });

  test('accepts a PDF with an empty mime type but .pdf extension', async () => {
    expect(await validateFile(pdf('Umowa.PDF', ''))).toBeNull();
  });

  test('rejects another file type', async () => {
    expect(await validateFile(new File(['hello'], 'a.txt', { type: 'text/plain' }))).toMatch(/PDF/);
  });

  test('rejects a file with a wrong signature', async () => {
    const file = new File(['not a pdf at all'], 'a.pdf', { type: 'application/pdf' });
    expect(await validateFile(file)).toMatch(/valid PDF/);
  });

  test('rejects an empty file', async () => {
    expect(await validateFile(new File([], 'a.pdf', { type: 'application/pdf' }))).toMatch(/empty/);
  });

  test('rejects a file over the limit', async () => {
    const file = pdf();
    Object.defineProperty(file, 'size', { value: MAX_FILE_BYTES + 1 });
    expect(await validateFile(file)).toMatch(/10 MB/);
  });
});
