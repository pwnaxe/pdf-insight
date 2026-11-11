import { useState } from 'react';
import { downloadJson } from '../lib/download';
import type { AnalysisResult } from '../lib/schema';
import { card, cardTitle, mutedText, primaryButton, secondaryButton } from './ui';

export function JsonPreview({ result }: { result: AnalysisResult }) {
  const [status, setStatus] = useState('');
  const json = JSON.stringify(result, null, 2);

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(json);
      setStatus('Copied.');
    } catch {
      setStatus('Could not copy.');
    }
  };

  return (
    <section className={card}>
      <h2 className={cardTitle}>JSON</h2>
      <div className="mb-4 flex flex-wrap items-center gap-2">
        <button type="button" className={primaryButton} onClick={() => downloadJson(result)}>
          Download JSON
        </button>
        <button type="button" className={secondaryButton} onClick={copy}>
          Copy JSON
        </button>
        <span role="status" className={mutedText}>
          {status}
        </span>
      </div>
      <details>
        <summary className="w-fit cursor-pointer rounded text-sm font-medium text-indigo-700 focus-visible:ring-2 focus-visible:ring-indigo-600 focus-visible:ring-offset-2 focus-visible:outline-none">
          Preview JSON
        </summary>
        <pre
          tabIndex={0}
          className="mt-3 max-h-96 overflow-auto rounded-lg border border-slate-200 bg-slate-50 p-4 font-mono text-xs text-slate-800 focus-visible:ring-2 focus-visible:ring-indigo-600 focus-visible:outline-none"
        >
          {json}
        </pre>
      </details>
    </section>
  );
}
