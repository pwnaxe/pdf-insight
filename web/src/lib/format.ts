import { localeFor, type Lang } from './i18n';

export function formatAmount(value: number, currency: string, lang: Lang): string {
  const locale = localeFor(lang);
  try {
    return new Intl.NumberFormat(locale, { style: 'currency', currency }).format(value);
  } catch {
    return `${new Intl.NumberFormat(locale).format(value)} ${currency}`;
  }
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
