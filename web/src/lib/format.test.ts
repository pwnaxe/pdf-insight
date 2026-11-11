import { expect, test } from 'vitest';
import { jsonFileName } from './download';
import { formatAmount, formatDate } from './format';

test('formats a date in Polish', () => {
  expect(formatDate('2026-03-12')).toBe('12 marca 2026');
});

test('formats an amount with its currency', () => {
  expect(formatAmount(184500, 'PLN').replace(/\s/g, ' ')).toContain('184 500,00');
});

test('falls back for an unknown currency code', () => {
  expect(formatAmount(5, 'ZZ1')).toContain('ZZ1');
});

test('builds the download name', () => {
  expect(jsonFileName('Umowa.pdf')).toBe('Umowa.insight.json');
  expect(jsonFileName('.pdf')).toBe('dokument.insight.json');
});
