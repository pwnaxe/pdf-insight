import type { HistoryEntry } from '../lib/history';
import { useI18n } from '../lib/i18n';
import { formatDateTime } from '../lib/format';
import { card, mutedText, primaryButton, secondaryButton } from './ui';

type Props = {
  entries: HistoryEntry[];
  onOpen: (entry: HistoryEntry) => void;
  onDelete: (id: string) => void;
  onClear: () => void;
};

export function HistoryPanel({ entries, onOpen, onDelete, onClear }: Props) {
  const { lang, t } = useI18n();
  return (
    <section className={card} aria-labelledby="history-title">
      <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
        <h2 id="history-title" className="text-lg font-semibold">
          {t.history}
        </h2>
        {entries.length > 0 && (
          <button type="button" className={secondaryButton} onClick={onClear}>
            {t.clearHistory}
          </button>
        )}
      </div>
      {entries.length === 0 ? (
        <p className={mutedText}>{t.noHistory}</p>
      ) : (
        <ul data-testid="history" className="divide-y divide-slate-200">
          {entries.map((entry) => (
            <li
              key={entry.id}
              className="flex flex-wrap items-center justify-between gap-3 py-3 first:pt-0 last:pb-0"
            >
              <div className="flex min-w-0 flex-col">
                <span className="font-medium [overflow-wrap:anywhere] break-words">
                  {entry.result.document.fileName}
                </span>
                <span className={mutedText}>{formatDateTime(entry.savedAt, lang)}</span>
              </div>
              <div className="flex flex-wrap gap-2">
                <button type="button" className={primaryButton} onClick={() => onOpen(entry)}>
                  {t.open}
                </button>
                <button
                  type="button"
                  className={secondaryButton}
                  aria-label={t.deleteAria(entry.result.document.fileName)}
                  onClick={() => onDelete(entry.id)}
                >
                  {t.delete}
                </button>
              </div>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
