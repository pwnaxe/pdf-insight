import { useI18n } from '../lib/i18n';

export function InjectionBadge() {
  const { t } = useI18n();
  return (
    <div
      data-testid="injection"
      className="flex gap-3 rounded-xl border-2 border-red-700 bg-amber-100 p-5 text-red-950 shadow-sm"
      role="alert"
    >
      <svg
        className="mt-0.5 size-6 shrink-0 text-red-700"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
        aria-hidden="true"
      >
        <path d="M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0Z" />
        <path d="M12 9v4M12 17h.01" />
      </svg>
      <p>
        <strong className="block text-base font-semibold">{t.injectionTitle}</strong>{' '}
        {t.injectionBody}
      </p>
    </div>
  );
}
