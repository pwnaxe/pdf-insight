import { useI18n } from '../lib/i18n';

export function AiNotice() {
  const { t } = useI18n();
  return (
    <p className="rounded-md border border-l-4 border-ink-200 border-l-accent-600 bg-white px-4 py-3 text-sm text-ink-700">
      {t.aiNotice}
    </p>
  );
}
