import type { HistoryEntry } from '../lib/history';
import { formatDateTime } from '../lib/format';
import { card, mutedText, primaryButton, secondaryButton } from './ui';

type Props = {
  entries: HistoryEntry[];
  onOpen: (entry: HistoryEntry) => void;
  onDelete: (id: string) => void;
  onClear: () => void;
};

export function HistoryPanel({ entries, onOpen, onDelete, onClear }: Props) {
  return (
    <section className={card} aria-labelledby="history-title">
      <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
        <h2 id="history-title" className="text-lg font-semibold">
          History
        </h2>
        {entries.length > 0 && (
          <button type="button" className={secondaryButton} onClick={onClear}>
            Clear history
          </button>
        )}
      </div>
      {entries.length === 0 ? (
        <p className={mutedText}>No saved analyses.</p>
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
                <span className={mutedText}>{formatDateTime(entry.savedAt)}</span>
              </div>
              <div className="flex flex-wrap gap-2">
                <button type="button" className={primaryButton} onClick={() => onOpen(entry)}>
                  Open
                </button>
                <button
                  type="button"
                  className={secondaryButton}
                  aria-label={`Delete ${entry.result.document.fileName}`}
                  onClick={() => onDelete(entry.id)}
                >
                  Delete
                </button>
              </div>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
