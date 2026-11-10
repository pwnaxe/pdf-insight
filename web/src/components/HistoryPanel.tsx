import type { HistoryEntry } from '../lib/history';
import { formatDateTime } from '../lib/format';

type Props = {
  entries: HistoryEntry[];
  onOpen: (entry: HistoryEntry) => void;
  onDelete: (id: string) => void;
  onClear: () => void;
};

export function HistoryPanel({ entries, onOpen, onDelete, onClear }: Props) {
  return (
    <section className="card" aria-labelledby="history-title">
      <div className="history-head">
        <h2 id="history-title">Historia</h2>
        {entries.length > 0 && (
          <button type="button" className="button button--secondary" onClick={onClear}>
            Wyczyść historię
          </button>
        )}
      </div>
      {entries.length === 0 ? (
        <p className="muted">Brak zapisanych analiz.</p>
      ) : (
        <ul className="history">
          {entries.map((entry) => (
            <li key={entry.id}>
              <div className="history-info">
                <span className="break">{entry.result.document.fileName}</span>
                <span className="muted">{formatDateTime(entry.savedAt)}</span>
              </div>
              <div className="actions">
                <button type="button" className="button" onClick={() => onOpen(entry)}>
                  Otwórz
                </button>
                <button
                  type="button"
                  className="button button--secondary"
                  aria-label={`Usuń ${entry.result.document.fileName}`}
                  onClick={() => onDelete(entry.id)}
                >
                  Usuń
                </button>
              </div>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
