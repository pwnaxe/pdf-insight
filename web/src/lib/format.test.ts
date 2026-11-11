import { expect, test } from 'vitest';
import { jsonFileName } from './download';
import { formatAmountValue, formatDate, formatPreciseDate } from './format';

test('formats a date per language', () => {
  expect(formatDate('2026-03-12', 'en')).toBe('12 March 2026');
  expect(formatDate('2026-03-12', 'pl')).toBe('12 marca 2026');
});

test('formats an amount value with two decimals', () => {
  expect(formatAmountValue(184500, 'en')).toBe('184,500.00');
  expect(formatAmountValue(184500, 'pl').replace(/\s/g, ' ')).toBe('184 500,00');
  expect(formatAmountValue(8600.5, 'en')).toBe('8,600.50');
});

test('builds the download name', () => {
  expect(jsonFileName('Umowa.pdf')).toBe('Umowa.insight.json');
  expect(jsonFileName('.pdf')).toBe('document.insight.json');
});

test('formats dates by precision', () => {
  expect(formatPreciseDate('2024', 'year', 'pl')).toBe('2024');
  expect(formatPreciseDate('2024-05', 'month', 'en')).toBe('May 2024');
  expect(formatPreciseDate('2024-03', 'month', 'pl')).toBe('marzec 2024');
  expect(formatPreciseDate('2024-05-17', 'day', 'en')).toBe('17 May 2024');
});
