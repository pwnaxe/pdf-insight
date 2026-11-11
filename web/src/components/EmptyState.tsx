import { useI18n } from '../lib/i18n';

export function EmptyState() {
  const { t } = useI18n();
  return <p className="py-4 text-center text-sm text-slate-600">{t.empty}</p>;
}
