import { useState } from 'react';
import { useI18n } from '../lib/i18n';
import { downloadJson } from '../lib/download';
import type { AnalysisResult } from '../lib/schema';
import { card, cardTitle, focusRing, mutedText, primaryButton, secondaryButton } from './ui';

export function JsonPreview({ result }: { result: AnalysisResult }) {
  const { t } = useI18n();
  const [status, setStatus] = useState('');
  const json = JSON.stringify(result, null, 2);

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(json);
      setStatus(t.copied);
    } catch {
      setStatus(t.copyFailed);
    }
  };

  return (
    <section className={card}>
      <h2 className={cardTitle}>{t.json}</h2>
      <div className="mb-4 flex flex-wrap items-center gap-2">
        <button type="button" className={primaryButton} onClick={() => downloadJson(result)}>
          {t.downloadJson}
        </button>
        <button type="button" className={secondaryButton} onClick={copy}>
          {t.copyJson}
        </button>
        <span role="status" className={mutedText}>
          {status}
        </span>
      </div>
      <details>
        <summary
          className={`w-fit cursor-pointer rounded text-sm font-semibold text-accent-800 underline-offset-4 hover:underline ${focusRing}`}
        >
          {t.previewJson}
        </summary>
        <pre
          tabIndex={0}
          className="mt-3 max-h-96 overflow-auto rounded-md bg-ink-950 p-4 font-mono text-xs leading-relaxed text-ink-100 focus-visible:ring-2 focus-visible:ring-accent-600 focus-visible:ring-offset-2 focus-visible:ring-offset-ink-50 focus-visible:outline-none"
        >
          {json}
        </pre>
      </details>
    </section>
  );
}
