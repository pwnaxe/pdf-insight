import { expect, test } from 'vitest';
import { jsonFileName } from './download';
import { formatAmount, formatDate } from './format';

test('formats a date per language', () => {
  expect(formatDate('2026-03-12', 'en')).toBe('12 March 2026');
  expect(formatDate('2026-03-12', 'pl')).toBe('12 marca 2026');
});

test('formats an amount with its currency', () => {
  expect(formatAmount(184500, 'PLN', 'en')).toContain('184,500.00');
  expect(formatAmount(184500, 'PLN', 'pl').replace(/\s/g, ' ')).toContain('184 500,00');
});

test('falls back for an unknown currency code', () => {
  expect(formatAmount(5, 'ZZ1', 'pl')).toContain('ZZ1');
});

test('builds the download name', () => {
  expect(jsonFileName('Umowa.pdf')).toBe('Umowa.insight.json');
  expect(jsonFileName('.pdf')).toBe('document.insight.json');
});
