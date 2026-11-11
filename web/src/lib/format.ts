import { localeFor, type Lang } from './i18n';
import type { DatePrecision } from './schema';

export function formatAmountValue(value: number, lang: Lang): string {
  return new Intl.NumberFormat(localeFor(lang), {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value);
}

export function formatDate(iso: string, lang: Lang): string {
  const date = new Date(`${iso}T00:00:00Z`);
  if (Number.isNaN(date.getTime())) return iso;
  return new Intl.DateTimeFormat(localeFor(lang), { dateStyle: 'long', timeZone: 'UTC' }).format(
    date,
  );
}

export function formatDateTime(iso: string, lang: Lang): string {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return iso;
  return new Intl.DateTimeFormat(localeFor(lang), {
    dateStyle: 'short',
    timeStyle: 'short',
  }).format(date);
}

export function formatPreciseDate(iso: string, precision: DatePrecision, lang: Lang): string {
  if (precision === 'day') return formatDate(iso, lang);
  if (precision === 'year') return iso;
  const date = new Date(`${iso}-01T00:00:00Z`);
  if (Number.isNaN(date.getTime())) return iso;
  // a standalone month name: Polish would otherwise decline it ("marca")
  return new Intl.DateTimeFormat(localeFor(lang), {
    month: 'long',
    year: 'numeric',
    timeZone: 'UTC',
  }).format(date);
}
