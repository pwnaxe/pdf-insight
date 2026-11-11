import { describe, expect, test } from 'vitest';
import { validResult } from './fixtures';
import { AnalysisResultSchema, datePrecision } from './schema';

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

  test.each([
    ['2024', 'year'],
    ['2024-05', 'month'],
    ['2024-05-17', 'day'],
  ] as const)('accepts reduced precision date %s', (date, precision) => {
    const data = structuredClone(validResult);
    data.dates = [{ date, precision, context: 'x' }];
    expect(AnalysisResultSchema.safeParse(data).success).toBe(true);
    expect(datePrecision(date)).toBe(precision);
  });

  test.each([
    ['2024', 'day'],
    ['2024-05', 'year'],
    ['2024-13', 'month'],
    ['24', 'year'],
  ] as const)('rejects date %s with precision %s', (date, precision) => {
    const data = structuredClone(validResult);
    data.dates = [{ date, precision, context: 'x' }];
    expect(AnalysisResultSchema.safeParse(data).success).toBe(false);
  });

  test('derives precision for entries saved without it', () => {
    const data = clone() as { dates: Record<string, unknown>[] };
    data.dates = [{ date: '2024-05', context: 'x' }];
    const parsed = AnalysisResultSchema.safeParse(data);
    expect(parsed.success && parsed.data.dates[0]?.precision).toBe('month');
  });

  test('document date must be a full day', () => {
    for (const date of ['2026', '2026-03']) {
      const data = structuredClone(validResult);
      data.document.date = date;
      expect(AnalysisResultSchema.safeParse(data).success).toBe(false);
    }
  });

  test('subtype is optional, lowercase and short', () => {
    const data = structuredClone(validResult);
    delete (data.document as { subtype?: unknown }).subtype;
    expect(AnalysisResultSchema.safeParse(data).success).toBe(true);
    data.document.subtype = 'cv';
    expect(AnalysisResultSchema.safeParse(data).success).toBe(true);
    for (const bad of ['CV', '', 'x'.repeat(31)]) {
      data.document.subtype = bad;
      expect(AnalysisResultSchema.safeParse(data).success).toBe(false);
    }
  });
});
