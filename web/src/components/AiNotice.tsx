import { useI18n } from '../lib/i18n';

export function AiNotice() {
  const { t } = useI18n();
  return (
    <p className="rounded-lg border border-l-4 border-slate-200 border-l-indigo-600 bg-white px-4 py-3 text-sm text-slate-700">
      {t.aiNotice}
    </p>
  );
}
