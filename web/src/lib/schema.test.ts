import { describe, expect, test } from 'vitest';
import { validResult } from './fixtures';
import { AnalysisResultSchema } from './schema';

function clone(): Record<string, unknown> {
  return structuredClone(validResult) as unknown as Record<string, unknown>;
}

describe('AnalysisResultSchema', () => {
  test('accepts a valid result', () => {
    expect(AnalysisResultSchema.safeParse(validResult).success).toBe(true);
  });

  test('accepts null title and date', () => {
    const data = structuredClone(validResult);
    data.document.title = null;
    data.document.date = null;
    expect(AnalysisResultSchema.safeParse(data).success).toBe(true);
  });

  test('rejects a currency symbol instead of an ISO code', () => {
    const data = structuredClone(validResult);
    data.amounts = data.amounts.map((a) => ({ ...a, currency: 'zł' }));
    expect(AnalysisResultSchema.safeParse(data).success).toBe(false);
  });

  test('rejects a malformed date', () => {
    const data = structuredClone(validResult);
    data.dates = data.dates.map((d) => ({ ...d, date: '12.03.2026' }));
    expect(AnalysisResultSchema.safeParse(data).success).toBe(false);
  });

  test('rejects a date that does not exist', () => {
    const data = structuredClone(validResult);
    data.document.date = '2026-02-30';
    expect(AnalysisResultSchema.safeParse(data).success).toBe(false);
  });

  test('rejects more than 7 key points', () => {
    const data = structuredClone(validResult);
    data.keyPoints = Array.from({ length: 8 }, (_, i) => `punkt ${i}`);
    expect(AnalysisResultSchema.safeParse(data).success).toBe(false);
  });

  test('rejects an unknown document type', () => {
    const data = structuredClone(validResult) as unknown as { document: { type: string } };
    data.document.type = 'pozew';
    expect(AnalysisResultSchema.safeParse(data).success).toBe(false);
  });

  test('rejects a missing field', () => {
    const data = clone();
    delete data.summary;
    expect(AnalysisResultSchema.safeParse(data).success).toBe(false);
  });
});
